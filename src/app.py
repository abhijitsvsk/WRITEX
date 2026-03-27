import sys
import os
import json
import io
import re
import time
import traceback
from pathlib import Path

# Third-party imports
import streamlit as st
import docx  # type: ignore
from dotenv import load_dotenv
import uuid

# Special Requests & Conflict Resolution
from src.models.constraints import SpecialRequest, ConflictRecord, ResolvedConstraints
from src.ai.request_interpreter import interpret_request, RequestInterpretationError, PARAMETER_LABELS
from src.validation.conflict_resolver import detect_conflicts, normalise_reference_params, check_single_conflict

# --- Page Config ---
st.set_page_config(page_title="Writex - AI Document Formatter", page_icon="📝")

# --- Setup ---
load_dotenv()
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

# Feature Toggle for upcoming Map-Reduce AST integration
USE_EXPERIMENTAL_FEATURES = False

# --- Imports ---
from src.file_formatting.formatting import generate_report
from src.analysis.style_analyzer import StyleAnalyzer
from src.analysis.code_analyzer import CodeAnalyzer
from src.ai.report_generator import ReportGenerator
from src.core.compiler import DocumentCompiler, REPORT_SCHEMA
from src.validation.validator import DocumentValidator


def run_formatting(text_content, api_key_val, style_name):
    # Keep lightweight formatting for Tabs 1 & 2
    from src.ai.structurer import structure_text

    if not api_key_val:
        return
    with st.spinner("Structuring..."):
        try:
            struct = structure_text(
                text_content, api_key=api_key_val, style_name=style_name
            )
            json_match = re.search(r"\[.*\]", struct, re.DOTALL)
            data = json.loads(json_match.group(0)) if json_match else []

            buf = io.BytesIO()
            generate_report(data, buf, style_name=style_name)
            st.download_button("Download", buf.getvalue(), "formatted.docx")
        except Exception as e:
            st.error(str(e))


# --- Main UI ---
st.title("📝 Writex: Academic Report Engine")
print("--- App Reloaded with Team Input ---")

with st.sidebar:
    api_key = st.text_input(
        "Groq API Key", type="password", value=os.environ.get("GROQ_API_KEY", "")
    )
    st.header("Formatting")
    style_opts = ["Standard", "IEEE", "APA"]
    sel_style = st.selectbox("Style", style_opts)
    
    st.markdown("---")
    if st.button("🧹 Clear Session State (Start Fresh)"):
        st.session_state.clear()
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📄 Text", "📂 File", "🎓 Academic Report (Strict)"])

with tab1:
    txt = st.text_area("Raw Text")
    if st.button("Format Text"):
        run_formatting(txt, api_key, sel_style)

with tab2:
    upl = st.file_uploader("Upload Doc/Txt")
    if upl and st.button("Format File"):
        run_formatting("File content...", api_key, sel_style)

with tab3:
    st.header("Code to B.Tech Report")
    st.info("Generates a strict 6-chapter academic report with standard Front Matter.")

    col1, col2 = st.columns(2)
    with col1:
        proj_zip = st.file_uploader("Project ZIP", type=["zip"], key="project_zip")
        sample_rep = st.file_uploader(
            "Upload Sample Report (PDF/DOCX)",
            type=["pdf", "docx"],
            help="Optional. Upload a sample to mimic its style.",
            key="sample_report",
        )
        test_metrics = st.file_uploader(
            "Upload Evaluation Metrics/Datasets (CSV/JSON/TXT)",
            type=["csv", "json", "txt"],
            help="Optional. Upload raw test data to generate genuine authentic academic metrics.",
            key="test_metrics",
        )

    with col2:
        title = st.text_input("Project Title", value="My Project")
        degree = st.text_input("Degree", value="B.Tech Computer Science")
        university = st.text_input("University/College", value="My University")
        department = st.text_input(
            "Department", value="Computer Science and Engineering"
        )
        academic_year = st.text_input("Academic Year", value="2025–2026")

    st.subheader("Team & Signatories")
    col1, col2 = st.columns(2)
    principal = col1.text_input("Principal Name", value="")
    hod = col2.text_input("HOD Name", value="")

    col3, col4 = st.columns(2)
    guide = col3.text_input("Project Guide Name", value="")
    guide_designation = col4.text_input(
        "Guide Designation", value="Assistant Professor"
    )

    hod_designation = st.text_input("HOD Designation", value="Professor & HoD")

    # Dynamic Team Inputs
    if "team_count" not in st.session_state:
        st.session_state.team_count = 4  # Default to 4 as per user hint

    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex

    # --- Special Requests Session State ---
    if 'special_request' not in st.session_state:
        st.session_state.special_request = None
    if 'request_confirmed' not in st.session_state:
        st.session_state.request_confirmed = False
    if 'reference_params' not in st.session_state:
        st.session_state.reference_params = {}
    if 'reference_extracted' not in st.session_state:
        st.session_state.reference_extracted = False
    if 'conflicts' not in st.session_state:
        st.session_state.conflicts = []
    if 'resolved_constraints' not in st.session_state:
        st.session_state.resolved_constraints = None
    if 'generation_state' not in st.session_state:
        st.session_state.generation_state = 'IDLE'

    def add_member():
        st.session_state.team_count += 1
        
    def remove_member():
        if st.session_state.team_count > 1:
            st.session_state.team_count -= 1

    st.subheader("Team Members")
    team_names = []
    for i in range(st.session_state.team_count):
        tn = st.text_input(f"Member {i+1} Name", key=f"s_name_{i}")
        if tn:
            team_names.append(tn)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.button("➕ Add Team Member", on_click=add_member)
    with btn_col2:
        st.button("➖ Remove Member", on_click=remove_member)

    # helper for context
    name = "\n".join(team_names)

    # --- SPECIAL REQUESTS PANEL ---
    with st.expander("✨ Special Requests (optional)"):
        if st.session_state.request_confirmed and st.session_state.special_request:
            sr = st.session_state.special_request
            st.success(f"✅ Confirmed: {sr.interpreted_summary}")
            if sr.parameters:
                st.json(sr.parameters)
            if sr.custom_directives:
                st.caption("Custom directives: " + "; ".join(sr.custom_directives))
            if st.button("🔄 Change Request", key="sr_change"):
                st.session_state.special_request = None
                st.session_state.request_confirmed = False
                st.session_state.conflicts = []
                st.session_state.resolved_constraints = None
                st.session_state.generation_state = 'IDLE'
                st.rerun()
        elif st.session_state.special_request and not st.session_state.request_confirmed:
            sr = st.session_state.special_request
            st.info(f"I understood: {sr.interpreted_summary}")
            if sr.parameters:
                st.json(sr.parameters)
            conf_col, rej_col = st.columns(2)
            with conf_col:
                if st.button("✅ Confirm", key="sr_confirm"):
                    st.session_state.request_confirmed = True
                    st.rerun()
            with rej_col:
                if st.button("❌ Re-enter", key="sr_reject"):
                    st.session_state.special_request = None
                    st.session_state.request_confirmed = False
                    st.rerun()
        else:
            sr_text = st.text_area(
                "Describe any special requirements for your report.",
                placeholder="e.g. 'make the whole report under 30 pages' or 'use font size 15 throughout'",
                key="sr_input",
            )
            if st.button("📨 Send Request", key="sr_send"):
                if sr_text and sr_text.strip():
                    if api_key:
                        try:
                            from groq import Groq
                            groq_client = Groq(api_key=api_key)
                            with st.spinner("Interpreting your request..."):
                                result = interpret_request(sr_text, groq_client)
                            st.session_state.special_request = result
                            st.rerun()
                        except RequestInterpretationError:
                            st.error("Could not parse your request — try rephrasing it more specifically.")
                    else:
                        st.error("🔒 Please enter your Groq API Key in the sidebar first.")
                else:
                    st.warning("Please type a request before sending.")

    # --- Conflict Resolution UI (if state is RESOLVING) ---
    if st.session_state.generation_state == 'RESOLVING' and st.session_state.conflicts:
        st.markdown("---")
        st.subheader("⚠️ Conflict Resolution Required")
        # Restore notice if user refreshed mid-resolution
        if any(c.resolved_value is None for c in st.session_state.conflicts):
            st.info("You have unresolved conflicts from your previous session." if st.session_state.generation_state == 'RESOLVING' else "")

        all_resolved = True
        for i, conflict in enumerate(st.session_state.conflicts):
            if conflict.resolved_value is not None:
                st.success(f"✅ {conflict.parameter_label}: Resolved to {conflict.resolved_value} (source: {conflict.resolution_source})")
                continue

            all_resolved = False
            st.warning(
                f"Conflict on **{conflict.parameter_label}**: "
                f"Your reference report uses **{conflict.reference_value}**, "
                f"your special request says **{conflict.request_value}**."
            )

            option = st.radio(
                f"How should we resolve {conflict.parameter_label}?",
                [
                    f"Follow reference ({conflict.reference_value})",
                    f"Follow special request ({conflict.request_value})",
                    "Enter a new request for this parameter",
                ],
                key=f"conflict_radio_{i}",
            )

            if option.startswith("Follow reference"):
                if st.button(f"Apply reference value for {conflict.parameter_label}", key=f"apply_ref_{i}"):
                    conflict.resolved_value = conflict.reference_value
                    conflict.resolution_source = "reference"
                    st.rerun()
            elif option.startswith("Follow special request"):
                if st.button(f"Apply request value for {conflict.parameter_label}", key=f"apply_req_{i}"):
                    conflict.resolved_value = conflict.request_value
                    conflict.resolution_source = "request"
                    st.rerun()
            else:
                new_val_text = st.text_area(
                    f"Enter a new value for {conflict.parameter_label} only",
                    placeholder=f"Enter a new value for {conflict.parameter_label} only",
                    key=f"new_val_{i}",
                )
                if st.button(f"Submit new value for {conflict.parameter_label}", key=f"submit_new_{i}"):
                    if new_val_text and new_val_text.strip() and api_key:
                        try:
                            from groq import Groq
                            groq_client = Groq(api_key=api_key)
                            with st.spinner("Re-interpreting..."):
                                new_sr = interpret_request(
                                    new_val_text, groq_client,
                                    focus_parameter=conflict.parameter_key
                                )
                            new_value = new_sr.parameters.get(conflict.parameter_key)
                            if new_value is None:
                                st.error("The interpreter did not return a value for this parameter. Try again.")
                            else:
                                # Uses cached extraction — do not call StyleAnalyzer here
                                ref_params = st.session_state.reference_params
                                still_conflicts = check_single_conflict(
                                    conflict.parameter_key, new_value, ref_params
                                )
                                if still_conflicts:
                                    conflict.request_value = new_value
                                    st.warning(f"New value {new_value} still conflicts with reference ({ref_params.get(conflict.parameter_key)}). Please choose again.")
                                    st.rerun()
                                else:
                                    conflict.resolved_value = new_value
                                    conflict.resolution_source = "new_request"
                                    st.rerun()
                        except RequestInterpretationError:
                            st.error("Could not parse your request — try rephrasing it more specifically.")

        if all_resolved:
            if st.button("✅ Proceed to Generation", type="primary", key="proceed_gen"):
                st.session_state.generation_state = 'GENERATING'
                st.rerun()
        # Block the rest of the page while resolving
        if not all_resolved:
            st.stop()

    # Determine if Generate button should be disabled
    _sr_started_not_confirmed = (
        st.session_state.special_request is not None
        and not st.session_state.request_confirmed
    )

    if st.button(
        "Generate Academic Report",
        type="primary",
        disabled=_sr_started_not_confirmed,
    ) or st.session_state.generation_state == 'GENERATING':
        if not api_key:
            st.error("🔒 Please enter your Groq API Key in the sidebar to proceed.")
        elif not proj_zip:
            st.error("📂 Please upload your Project ZIP file to generate the report.")
        elif not name.strip():
            st.error("👥 Please enter at least one Team Member name.")
        else:
            try:
                import zipfile
                analyzer = CodeAnalyzer()
                with st.spinner("Analyzing Codebase (In-Memory)..."):
                    try:
                        summary = analyzer.analyze_zip(proj_zip)
                    except zipfile.BadZipFile:
                        st.error("❌ Invalid or corrupted ZIP file. Please ensure you uploaded a valid ZIP archive.")
                        st.stop()
                    except ValueError as ve:
                        st.error(f"❌ {ve}")
                        st.stop()
                
                if getattr(summary, "total_files", 0) == 0:
                    st.error("❌ The uploaded ZIP file contains zero recognizable codebase files. Please upload a valid project structure.")
                    st.stop()
                    
                st.success(f"Analyzed {summary.total_files} files securely in memory.")

                if getattr(summary, "is_truncated", False):
                    st.warning(f"⚠️ Monorepo Detected: Analyzing {analyzer.max_files} of {summary.total_files} files, prioritised by structural relevance. Secondary files were ignored.")
                    
                python_count = summary.languages.get("Python", 0)
                other_count = sum(v for k, v in summary.languages.items() if k != "Python")
                if other_count > 0 and other_count >= python_count:
                    st.warning("⚠️ Non-Python Codebase Detected: Deep pythonic AST parsing is limited. The system has fallen back to generalized Regex extraction.")
                
                # --- EXPERIMENTAL MAP-REDUCE AST PARSER ---
                if USE_EXPERIMENTAL_FEATURES:
                    with st.spinner("🧪 [Experimental] Running Map-Reduce AST Extraction..."):
                        import zipfile
                        from src.ast_analysis import extract_file_structure, build_mermaid_diagram, generate_basic_summary
                        
                        ast_data = []
                        try:
                            with zipfile.ZipFile(proj_zip, "r") as z:
                                for info in z.infolist():
                                    if info.filename.endswith(".py") and not info.is_dir() and "venv" not in info.filename:
                                        content = z.read(info).decode("utf-8", errors="ignore")
                                        ast_data.append(extract_file_structure(content, info.filename))
                                        
                            if ast_data:
                                mermaid_graph = build_mermaid_diagram(ast_data)
                                st.info("AST Extraction Complete. Generated Dependency Graph:")
                                st.code(mermaid_graph, language="mermaid")
                                
                                st.info("Sample Map-Reduce File Summary (Groundwork):")
                                st.write(generate_basic_summary(ast_data[0]))
                                
                        except Exception as e:
                            st.warning(f"Experimental AST pipeline issue: {e}")
                # ------------------------------------------


                # Style Analysis
                style_guide = ""
                sample_sections = {}
                raw_text = ""
                if sample_rep:
                    with st.spinner("Analyzing Sample Style (plus OCR if needed)..."):
                        sa = StyleAnalyzer(api_key=api_key)
                        ext = sample_rep.name.split(".")[-1].lower()
                        sample_rep.seek(0)
                        raw_text = sa.extract_text(sample_rep, ext)
                        style_guide = sa.analyze_style(raw_text)
                        sample_rep.seek(0)
                        sample_sections = sa.extract_specific_sections(sample_rep, ext)
                    st.toast("Style & Templates Extracted!", icon="🎨")

                    # --- REFERENCE EXTRACTION CACHING (Step B) ---
                    if sample_rep and not st.session_state.reference_extracted:
                        try:
                            with st.spinner("Reading reference document formatting..."):
                                sample_rep.seek(0)
                                ref_ext = sample_rep.name.split(".")[-1].lower()
                                if ref_ext == "docx":
                                    visual_params = sa.analyze_visual_style(sample_rep)
                                    st.session_state.reference_params = normalise_reference_params(visual_params)
                                else:
                                    st.session_state.reference_params = {}
                                st.session_state.reference_extracted = True
                        except Exception:
                            st.session_state.reference_params = {}
                            st.session_state.reference_extracted = True
                            st.warning("Could not read formatting from your reference document — special requests will be applied without conflict checking.")

                    # --- CONFLICT DETECTION (Step C) ---
                    if (
                        st.session_state.request_confirmed
                        and st.session_state.special_request
                        and st.session_state.reference_extracted
                        and st.session_state.reference_params
                        and st.session_state.generation_state != 'GENERATING'
                    ):
                        # Uses cached extraction — do not call StyleAnalyzer here
                        ref_params = st.session_state.reference_params
                        req_params = st.session_state.special_request.parameters
                        conflicts = detect_conflicts(req_params, ref_params)
                        if conflicts:
                            st.session_state.conflicts = conflicts
                            st.session_state.generation_state = 'RESOLVING'
                            st.rerun()
                        else:
                            st.session_state.conflicts = []
                            st.session_state.generation_state = 'GENERATING'

                test_metrics_text = ""
                if test_metrics:
                    try:
                        raw_metrics = test_metrics.getvalue().decode("utf-8", errors="ignore")
                        if test_metrics.name.lower().endswith(".json"):
                            import json
                            try:
                                parsed = json.loads(raw_metrics)
                                if isinstance(parsed, list) and len(parsed) > 100:
                                    test_metrics_text = json.dumps(parsed[:100], indent=2)
                                else:
                                    test_metrics_text = json.dumps(parsed, indent=2)
                            except json.JSONDecodeError:
                                test_metrics_text = raw_metrics[:5000]
                        else:
                            test_metrics_text = raw_metrics[:5000]
                    except Exception:
                        pass  # nosec B110

                gen = ReportGenerator(api_key)
                
                # API Connection / Captive Portal Defense
                import requests
                try:
                    test_req = requests.get("https://api.groq.com", timeout=3)
                    if 'text/html' in test_req.headers.get('Content-Type', '').lower():
                        st.error("❌ Network Intercepted: A Captive Portal or Firewall is blocking the API request. Please log in to your network.")
                        st.stop()
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
                    st.error("❌ Network Blocked: Cannot establish a secure connection to api.groq.com. Please check your firewall or VPN.")
                    st.stop()
                except requests.exceptions.RequestException:
                    pass

                try:
                    gen.model.models.list()
                except Exception as e:
                    err_str = str(e).lower()
                    if "401" in err_str or "unauthorized" in err_str:
                        st.error("❌ Invalid Groq API Key. Please verify your credentials and try again.")
                        st.stop()
                    else:
                        st.error(f"❌ API Connection Failed: {e}")
                        st.stop()
                        
                gen.clear_cache()  # Force an isolated fresh run
                

                # Extract structured metadata from sample if provided
                sample_metadata = {}
                if sample_rep and raw_text:
                    with st.spinner("Extracting High-Level Metadata from Sample..."):
                        sample_metadata = gen.extract_metadata_from_sample(raw_text)

                with st.spinner("Deriving project context from codebase..."):
                    context = gen.derive_project_context(summary.to_json())

                # Pronoun logic: single student = I/my, team = We/our
                # If name isn't provided, see if sample threw us a list
                final_names = name.strip()
                if not final_names and sample_metadata.get("team_names"):
                    if isinstance(sample_metadata["team_names"], list):
                        final_names = "\n".join(sample_metadata["team_names"])
                    else:
                        final_names = str(sample_metadata["team_names"])

                # Determine mode based on line breaks and clean to Title Case
                name_lines = [
                    n.strip().title() for n in final_names.split("\n") if n.strip()
                ]
                name_count = len(name_lines)
                pronoun_mode = "singular" if name_count <= 1 else "plural"

                # Format for inline sentence
                if name_count == 0:
                    inline_names = ""
                elif name_count == 1:
                    inline_names = name_lines[0]
                elif name_count == 2:
                    inline_names = f"{name_lines[0]} and {name_lines[1]}"
                else:
                    inline_names = (
                        ", ".join(name_lines[:-1]) + f", and {name_lines[-1]}"
                    )

                context.update(
                    {
                        "title": (
                            title
                            if title and title != "My Project"
                            else sample_metadata.get("title", title)
                        ),
                        "student_name": inline_names,
                        "team_names_raw": name_lines,
                        "degree": (
                            degree
                            if degree != "B.Tech Computer Science"
                            else sample_metadata.get("degree", degree)
                        ),
                        "principal": principal or sample_metadata.get("principal", ""),
                        "guide": guide or sample_metadata.get("guide", ""),
                        "hod": hod or sample_metadata.get("hod", ""),
                        "guide_designation": guide_designation,
                        "hod_designation": hod_designation,
                        "university": (
                            university
                            if university != "My University"
                            else sample_metadata.get("university", university)
                        ),
                        "department": (
                            department
                            if department != "Computer Science and Engineering"
                            else sample_metadata.get("department", department)
                        ),
                        "academic_year": (
                            academic_year
                            if academic_year != "2025–2026"
                            else sample_metadata.get("academic_year", academic_year)
                        ),
                        "pronoun_mode": pronoun_mode,
                        "problem_statement": context["problem_statement"],
                        "style_guide": style_guide,
                        "sample_report_provided": bool(sample_rep),
                        "sample_sections": sample_sections,
                        "has_test_files": len(summary.test_files) > 0,
                        "test_metrics_data": test_metrics_text,
                        "detailed_analysis": summary.detailed_analysis,
                        "session_id": st.session_state.session_id,
                    }
                )

                # --- BUILD RESOLVED CONSTRAINTS (Step E) ---
                resolved = None
                if st.session_state.request_confirmed and st.session_state.special_request:
                    sr = st.session_state.special_request
                    p = sr.parameters

                    # Start with request params, then overlay any conflict resolutions
                    final_params = dict(p)
                    conflict_log = list(st.session_state.conflicts) if st.session_state.conflicts else []
                    for c in conflict_log:
                        if c.resolved_value is not None:
                            final_params[c.parameter_key] = c.resolved_value

                    resolved = ResolvedConstraints(
                        page_limit=final_params.get("max_pages"),
                        font_size=final_params.get("font_size"),
                        font_name=final_params.get("font_name"),
                        line_spacing=final_params.get("line_spacing"),
                        margin_inches=final_params.get("margin_inches"),
                        min_words=final_params.get("min_words"),
                        max_words=final_params.get("max_words"),
                        custom_directives=sr.custom_directives,
                        source_log=conflict_log,
                    )
                    st.session_state.resolved_constraints = resolved

                # --- STRUCTURED GENERATION ---
                try:
                    with st.spinner(
                        "Compiling Document Structure... (this takes 2-5 min due to API rate limits)"
                    ):
                        compiler = DocumentCompiler(api_key=api_key)

                        # Callback to update UI progress bar natively
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        def update_progress(ratio, text):
                            status_text.text(text)
                            progress_bar.progress(min(ratio, 1.0))

                        full_structure = compiler.compile_structure(
                            context, summary, progress_callback=update_progress,
                            constraints=resolved,
                        )
                except RuntimeError as re_err:
                    st.error(f"❌ Document Validation Aborted: {str(re_err)}")
                    st.warning("Your project footprint is too small for the strict 6-chapter university schema. Please enable the experimental Map-Reduce V2 pipeline.")
                    st.stop()

                # --- 4. STRUCTURE VALIDATION GATE ---
                with st.spinner("Validating structural integrity and auto-healing..."):
                    validator = DocumentValidator(constraints=resolved)
                    try:
                        healed_structure = validator.validate_and_heal(full_structure)
                    except Exception as ve:
                        st.error(str(ve))
                        st.error(
                            "Document compilation halted due to unrecoverable structural validation failures."
                        )
                        st.stop()

                # --- 5. RENDER ---
                st.success("✅ Rendering DOCX...")
                buf = io.BytesIO()
                generate_report(healed_structure, buf, style_name=sel_style)
                
                # Persist output locally to protect against Wi-Fi drops mid-download
                os.makedirs("output", exist_ok=True)
                session_id = st.session_state.session_id
                backup_path = os.path.join("output", f"Report_Backup_{session_id}.docx")
                with open(backup_path, "wb") as f:
                    f.write(buf.getvalue())
                    
                # Auto-cleanup stale backups (>2 hours old)
                import time
                current_time = time.time()
                try:
                    for filename in os.listdir("output"):
                        if filename.startswith("Report_Backup_") and filename.endswith(".docx"):
                            file_path = os.path.join("output", filename)
                            if os.path.isfile(file_path):
                                if current_time - os.path.getmtime(file_path) > 7200:
                                    try:
                                        os.remove(file_path)
                                    except Exception:
                                        pass
                except Exception:
                    pass
                
                st.download_button(
                    "📥 Download Final Report", buf.getvalue(), "Academic_Report.docx"
                )

                # Reset generation state after successful completion
                st.session_state.generation_state = 'IDLE'

            except Exception as e:
                st.session_state.generation_state = 'IDLE'
                st.error(f"Failure: {e}")
                st.text(traceback.format_exc())
