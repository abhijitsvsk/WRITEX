import io
import os
import json
import re
import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.ai.structurer import structure_text
from src.file_formatting.formatting import generate_report, StyleConfig
from src.api_academic import router as academic_router
from src.database.session import SessionLocal, get_db
from src.database.repository import JobRepository
from src.core.config import settings
from src.models.schemas import JobStatusResponse, HealthResponse

async def periodic_reconcile_loop():
    """Runs periodic reconciliation sweep every 5 minutes while the server is alive."""
    while True:
        try:
            await asyncio.sleep(300)
            with SessionLocal() as db:
                JobRepository.reconcile_stale_jobs(db, timeout_minutes=settings.STALE_JOB_TIMEOUT_MINUTES)
        except asyncio.CancelledError:
            break
        except Exception:
            # Continue running even if a single sweep encounters an issue
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run initial stale-job reconciliation sweep
    try:
        with SessionLocal() as db:
            JobRepository.reconcile_stale_jobs(db, timeout_minutes=settings.STALE_JOB_TIMEOUT_MINUTES)
    except Exception as e:
        print(f"Warning: Startup reconciliation failed: {e}")

    # Start periodic background reconciliation sweep
    sweep_task = asyncio.create_task(periodic_reconcile_loop())
    yield
    # Shutdown: Cancel periodic task gracefully
    sweep_task.cancel()
    try:
        await sweep_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="WriteX API",
    description="Academic Report Generation API",
    version="2.2.0",
    lifespan=lifespan
)

app.include_router(academic_router)

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_style_config(style_json_str: str) -> StyleConfig:
    try:
        if not style_json_str:
            return StyleConfig()
            
        cfg_dict = json.loads(style_json_str)
        align_map = {
            "Left": WD_ALIGN_PARAGRAPH.LEFT, 
            "Center": WD_ALIGN_PARAGRAPH.CENTER, 
            "Right": WD_ALIGN_PARAGRAPH.RIGHT, 
            "Justify": WD_ALIGN_PARAGRAPH.JUSTIFY
        }
        
        return StyleConfig(
            margin_inches=cfg_dict.get("margin_inches", 1.0),
            heading_font=cfg_dict.get("heading_font", "Times New Roman"),
            heading_size_pt=cfg_dict.get("heading_size_pt", 14.0),
            heading_bold=cfg_dict.get("heading_bold", True),
            chapter_alignment=align_map.get(cfg_dict.get("chapter_alignment", "Center"), WD_ALIGN_PARAGRAPH.CENTER),
            subheading_alignment=align_map.get(cfg_dict.get("subheading_alignment", "Left"), WD_ALIGN_PARAGRAPH.LEFT),
            content_font=cfg_dict.get("content_font", "Times New Roman"),
            content_size_pt=cfg_dict.get("content_size_pt", 12.0),
            content_alignment=align_map.get(cfg_dict.get("content_alignment", "Justify"), WD_ALIGN_PARAGRAPH.JUSTIFY),
            line_spacing=cfg_dict.get("line_spacing", 1.5),
            space_before_pt=cfg_dict.get("space_before_pt", 0.0),
            space_after_pt=cfg_dict.get("space_after_pt", 0.0),
            code_language=cfg_dict.get("code_language", "Auto"),
            highlight_code=cfg_dict.get("highlight_code", False),
            continuous_sections=cfg_dict.get("continuous_sections", False),
            auto_numbering=cfg_dict.get("auto_numbering", False)
        )
    except Exception as e:
        print(f"Error parsing style config: {e}")
        return StyleConfig()

def process_formatting(
    text_content: str,
    api_key: str,
    style_name: str,
    style_cfg: StyleConfig,
    images: List[UploadFile],
    image_placement: str,
    provider: str = "groq",
    model_name: Optional[str] = None,
):
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
        
    try:
        image_names = [img.filename for img in images] if images else []
        struct = structure_text(
            text_content,
            api_key=api_key,
            style_name=style_name,
            available_images=image_names,
            provider=provider,
            model_name=model_name,
        )
        
        # Extract JSON array from response
        json_match = re.search(r"\[.*\]", struct, re.DOTALL)
        data = json.loads(json_match.group(0)) if json_match else []

        if images:
            img_nodes = []
            for img in images:
                file_bytes = img.file.read()
                img_nodes.append({"type": "image", "content": file_bytes, "filename": img.filename})
                
            if image_placement == "Top":
                data = img_nodes + data
            elif image_placement == "Bottom":
                data = data + img_nodes
            else:
                # Let AI Decide logic
                new_data = []
                for block in data:
                    if block.get("type") == "image_insertion":
                        fname = block.get("filename")
                        matched = next((node for node in img_nodes if node["filename"] == fname), None)
                        if matched:
                            new_data.append(matched)
                    else:
                        new_data.append(block)
                
                # Append leftover images
                used_fnames = [b.get("filename") for b in new_data if b.get("type") == "image"]
                for node in img_nodes:
                    if node["filename"] not in used_fnames:
                        new_data.append(node)
                        
                data = new_data

        buf = io.BytesIO()
        generate_report(data, buf, style_name=style_name, style_config=style_cfg)
        buf.seek(0)
        return buf
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1")).scalar()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "version": "2.2.0",
        "database": db_status,
        "features": ["highlight_code", "auto_numbering", "no_section_break", "job_persistence", "token_bucket_rate_limiter"]
    }

@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = JobRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        title=job.title,
        output_file_path=job.output_file_path,
        error_message=job.error_message,
        execution_time_seconds=job.execution_time_seconds,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at
    )

@app.get("/api/jobs/{job_id}/download")
def download_job_output(job_id: str, db: Session = Depends(get_db)):
    job = JobRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "COMPLETED" or not job.output_file_path or not os.path.exists(job.output_file_path):
        raise HTTPException(status_code=400, detail="Report generation not ready or output missing")
    
    with open(job.output_file_path, "rb") as f:
        file_bytes = io.BytesIO(f.read())
    file_bytes.seek(0)
    return StreamingResponse(
        file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={job.title or 'report'}.docx"}
    )

@app.post("/api/format_text")
def api_format_text(
    text: str = Form(...),
    api_key: str = Form(...),
    style_name: str = Form("Academic"),
    style_config: str = Form("{}"),
    image_placement: str = Form("Let AI Decide"),
    provider: str = Form("groq"),
    model_name: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
):
    style_cfg = parse_style_config(style_config)
    buf = process_formatting(text, api_key, style_name, style_cfg, images or [], image_placement, provider, model_name)
    
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=formatted.docx"}
    )

@app.post("/api/format_file")
def api_format_file(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    style_name: str = Form("Academic"),
    style_config: str = Form("{}"),
    image_placement: str = Form("Let AI Decide"),
    provider: str = Form("groq"),
    model_name: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
):
    try:
        file_bytes = file.file.read()
        
        if file.filename.endswith('.txt'):
            file_txt = file_bytes.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            import pypdf
            pdf_io = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_io)
            file_txt = "\n".join([p.extract_text() or "" for p in reader.pages])
        elif file.filename.endswith('.docx'):
            from docx import Document
            docx_io = io.BytesIO(file_bytes)
            doc = Document(docx_io)
            file_txt = "\n".join([p.text for p in doc.paragraphs])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use PDF, DOCX, or TXT.")
            
        style_cfg = parse_style_config(style_config)
        buf = process_formatting(file_txt, api_key, style_name, style_cfg, images or [], image_placement, provider, model_name)
        
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=formatted_file.docx"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
