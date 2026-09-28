import io
import os
import json
import uuid
import time
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from src.models.constraints import SpecialRequest, ConflictRecord, ResolvedConstraints
from src.ai.request_interpreter import interpret_request, RequestInterpretationError
from src.validation.conflict_resolver import detect_conflicts, normalise_reference_params, check_single_conflict
from src.analysis.style_analyzer import StyleAnalyzer
from src.analysis.code_analyzer import CodeAnalyzer
from src.ai.report_generator import ReportGenerator
from src.utils.github_import import download_github_repo
from src.database.session import get_db
from src.database.repository import JobRepository
from src.database.models import ConstraintAudit

router = APIRouter()

@router.post("/api/format_academic_report")
def api_format_academic_report(
    api_key: str = Form(...),
    title: str = Form("My Project"),
    degree: str = Form("B.Tech Computer Science"),
    university: str = Form("My University"),
    department: str = Form("Computer Science and Engineering"),
    academic_year: str = Form("2025–2026"),
    principal: str = Form(""),
    hod: str = Form(""),
    guide: str = Form(""),
    guide_designation: str = Form("Assistant Professor"),
    hod_designation: str = Form("Professor & HoD"),
    team_names: str = Form(""), # Comma or newline separated
    special_request_text: str = Form(""),
    resolved_conflicts: str = Form("{}"), # JSON string of previously resolved conflicts
    github_url: str = Form(""),
    rewrite_mode: str = Form("false"),
    proj_zip: UploadFile = File(None),
    sample_rep: UploadFile = File(None),
    test_metrics: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
        
    if not proj_zip and not github_url:
        raise HTTPException(status_code=400, detail="Please upload your Project ZIP file or provide a GitHub URL.")

    if not team_names.strip():
        raise HTTPException(status_code=400, detail="Please enter at least one Team Member name.")

    start_time = time.monotonic()

    # Create persistent job tracking row
    job = JobRepository.create_job(
        db,
        title=title,
        degree=degree,
        university=university,
        department=department,
        academic_year=academic_year,
        status="ANALYZING",
        progress=10
    )

    try:
        # 1. Parse special request if provided
        sr_obj = None
        if special_request_text.strip():
            try:
                from groq import Groq
                groq_client = Groq(api_key=api_key)
                sr_obj = interpret_request(special_request_text, groq_client)
            except Exception as e:
                JobRepository.fail_job(db, job.id, f"Could not parse special request: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Could not parse special request: {str(e)}")

        # 2. Extract formatting from sample report
        ref_params = {}
        sample_bytes = None
        raw_text = ""
        style_guide = ""
        sample_sections = {}
        
        sa = StyleAnalyzer(api_key=api_key)
        if sample_rep:
            sample_bytes = sample_rep.file.read()
            sample_io = io.BytesIO(sample_bytes)
            ext = sample_rep.filename.split(".")[-1].lower()
            
            raw_text = sa.extract_text(sample_io, ext)
            style_guide = sa.analyze_style(raw_text)
            
            sample_io.seek(0)
            sample_sections = sa.extract_specific_sections(sample_io, ext)
            
            if ext == "docx":
                sample_io.seek(0)
                try:
                    visual_params = sa.analyze_visual_style(sample_io)
                    ref_params = normalise_reference_params(visual_params)
                except Exception:
                    ref_params = {}

        # 3. Detect Conflicts
        resolved_dict = json.loads(resolved_conflicts) if resolved_conflicts else {}
        if sr_obj and ref_params and not resolved_dict:
            conflicts = detect_conflicts(sr_obj.parameters, ref_params)
            if conflicts:
                # Record conflict audit rows in database
                for c in conflicts:
                    audit = ConstraintAudit(
                        job_id=job.id,
                        parameter_key=c.parameter_key,
                        parameter_label=c.parameter_label,
                        reference_value=str(c.reference_value),
                        request_value=str(c.request_value),
                        resolution_source="pending"
                    )
                    db.add(audit)
                db.commit()

                conflict_data = []
                for c in conflicts:
                    conflict_data.append({
                        "parameter_key": c.parameter_key,
                        "parameter_label": c.parameter_label,
                        "request_value": c.request_value,
                        "reference_value": c.reference_value
                    })
                return JSONResponse(status_code=409, content={"conflicts": conflict_data})

        # Record resolved conflict audit rows if user submitted resolutions
        if resolved_dict:
            for k, v in resolved_dict.items():
                audit = ConstraintAudit(
                    job_id=job.id,
                    parameter_key=k,
                    parameter_label=k.replace("_", " ").title(),
                    resolved_value=str(v),
                    resolution_source="user_resolved"
                )
                db.add(audit)
            db.commit()

        # 4. Ingest Codebase
        analyzer = CodeAnalyzer()
        active_zip_io = None
        
        if github_url and not proj_zip:
            try:
                active_zip_io = download_github_repo(github_url)
            except Exception as e:
                JobRepository.fail_job(db, job.id, f"Failed to download GitHub repo: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Failed to download GitHub repo: {str(e)}")
        else:
            active_zip_io = io.BytesIO(proj_zip.file.read())

        try:
            summary = analyzer.analyze_zip(active_zip_io)
        except Exception as e:
            JobRepository.fail_job(db, job.id, f"Invalid or corrupted ZIP file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid or corrupted ZIP file: {str(e)}")

        if getattr(summary, "total_files", 0) == 0:
            JobRepository.fail_job(db, job.id, "The uploaded ZIP file contains zero recognizable codebase files.")
            raise HTTPException(status_code=400, detail="The uploaded ZIP file contains zero recognizable codebase files.")

        # Heartbeat update: progress 40%
        JobRepository.update_progress(db, job.id, "COMPILING", 40)

        # 5. Extract Test Metrics
        test_metrics_text = ""
        if test_metrics:
            try:
                raw_metrics = (test_metrics.file.read()).decode("utf-8", errors="ignore")
                if test_metrics.filename.lower().endswith(".json"):
                    parsed = json.loads(raw_metrics)
                    test_metrics_text = json.dumps(parsed[:100] if isinstance(parsed, list) and len(parsed) > 100 else parsed, indent=2)
                else:
                    test_metrics_text = raw_metrics[:5000]
            except Exception:
                pass

        # 6. Prepare Generator Context
        gen = ReportGenerator(api_key)
        
        sample_metadata = {}
        if sample_rep and raw_text:
            sample_metadata = gen.extract_metadata_from_sample(raw_text)

        context = gen.derive_project_context(summary.to_json())

        # Format Names
        name_lines = [n.strip().title() for n in team_names.replace(',', '\n').split("\n") if n.strip()]
        name_count = len(name_lines)
        pronoun_mode = "singular" if name_count <= 1 else "plural"

        if name_count == 0:
            inline_names = ""
        elif name_count == 1:
            inline_names = name_lines[0]
        elif name_count == 2:
            inline_names = f"{name_lines[0]} and {name_lines[1]}"
        else:
            inline_names = ", ".join(name_lines[:-1]) + f", and {name_lines[-1]}"

        context.update({
            "title": title if title and title != "My Project" else sample_metadata.get("title", title),
            "student_name": inline_names,
            "team_names_raw": name_lines,
            "degree": degree if degree != "B.Tech Computer Science" else sample_metadata.get("degree", degree),
            "principal": principal or sample_metadata.get("principal", ""),
            "guide": guide or sample_metadata.get("guide", ""),
            "hod": hod or sample_metadata.get("hod", ""),
            "guide_designation": guide_designation,
            "hod_designation": hod_designation,
            "university": university if university != "My University" else sample_metadata.get("university", university),
            "department": department if department != "Computer Science and Engineering" else sample_metadata.get("department", department),
            "academic_year": academic_year if academic_year != "2025–2026" else sample_metadata.get("academic_year", academic_year),
            "pronoun_mode": pronoun_mode,
            "style_guide": style_guide,
            "sample_report_provided": bool(sample_rep),
            "inspiration_text": raw_text[:3000] if raw_text else "",
            "rewrite_mode": rewrite_mode.lower() == "true",
            "sample_sections": sample_sections,
            "has_test_files": len(summary.test_files) > 0,
            "test_metrics_data": test_metrics_text,
            "detailed_analysis": summary.detailed_analysis,
            "session_id": job.id,
        })

        # 7. Apply Constraints
        resolved = None
        if sr_obj:
            final_params = dict(sr_obj.parameters)
            for k, v in resolved_dict.items():
                final_params[k] = v
                
            resolved = ResolvedConstraints(
                page_limit=final_params.get("max_pages"),
                font_size=final_params.get("font_size"),
                font_name=final_params.get("font_name"),
                line_spacing=final_params.get("line_spacing"),
                margin_inches=final_params.get("margin_inches"),
                min_words=final_params.get("min_words"),
                tone=final_params.get("tone"),
                custom_directives=sr_obj.custom_directives
            )

        # Heartbeat update: progress 70%
        JobRepository.update_progress(db, job.id, "FORMATTING", 70)

        # 8. Generate!
        out_buf = io.BytesIO()
        try:
            gen.generate_academic_report(
                project_context=context,
                output_path=out_buf,
                special_constraints=resolved,
                summary=summary,
            )
        except Exception as e:
            JobRepository.fail_job(db, job.id, f"Generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
            
        out_buf.seek(0)
        execution_time = int(time.monotonic() - start_time)

        # Save to reports cache directory
        reports_dir = os.path.join("cache", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        report_file_path = os.path.join(reports_dir, f"{job.id}.docx")
        try:
            with open(report_file_path, "wb") as f:
                f.write(out_buf.getvalue())
        except Exception:
            report_file_path = ""

        # Complete job in DB
        JobRepository.complete_job(db, job.id, output_path=report_file_path, execution_time=execution_time)

        return StreamingResponse(
            out_buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": "attachment; filename=Academic_Report.docx",
                "X-WriteX-Job-ID": job.id,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        JobRepository.fail_job(db, job.id, str(e))
        raise HTTPException(status_code=500, detail=str(e))
