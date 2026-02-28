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

# --- Page Config ---
st.set_page_config(page_title="Writex - AI Document Formatter", page_icon="📝")

# --- Setup ---
load_dotenv()
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

# --- Imports ---
from src.file_formatting.formatting import generate_report
from src.analysis.style_analyzer import StyleAnalyzer
from src.analysis.code_analyzer import CodeAnalyzer
from src.ai.report_generator import ReportGenerator
from src.core.compiler import DocumentCompiler
from src.validation.validator import DocumentValidator

# --- ALL CONSTANTS ---
REPORT_SCHEMA = [
    {
        "title": "Introduction",
        "subsections": [
            "Background",
            "Problem Definition",
            "Scope and Motivation",
            "Objectives",
            "Challenges",
            "Assumptions",
            "Societal / Industrial Relevance",
            "Organization of the Report",
        ],
    },
    {
        "title": "Literature Survey",
        "subsections": [
            {
                "title": "Summary and Gaps to be Filled",
                "subsubsections": [
                    "Existing Approaches",
                    "Machine Learning Approaches",
                    "Frameworks and Tools",
                    "Advances in the Domain",
                ],
            },
            "Review of Existing Approaches",
        ],
    },
    {
        "title": "Methodology",
        "subsections": [
            "Data Acquisition and Preprocessing",
            "Classification",
            "Verification and Prioritization",
            "Visualization and Reporting",
            {
                "title": "Workflow Summary",
                "subsubsections": [
                    "Initialization and Setup",
                    "User Configuration and Data Filtering",
                    "Simulation Loop (Core Processing)",
                    "User Actions and Response",
                    "Final Output",
                ],
            },
        ],
    },
    {
        "title": "Implementation",
        "subsections": [
            "Tools and Technologies",
            "Core Logic Implementation",
            "Key Modules and Functions",
            "Code Structure",
        ],
    },
    {
        "title": "Results and Discussion",
        "subsections": ["Dataset Overview", "Experimental Output and Analysis"],
    },
    {
        "title": "Conclusions and Future Scope",
        "subsections": ["Conclusion", "Future Enhancements"],
    },
]


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
            st.download_button("Download", buf, "formatted.docx")
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
        st.session_state.team_count = (
            4  # Default to 4 as per user hint ("4 team members")
        )

    def add_member():
        st.session_state.team_count += 1

    st.subheader("Team Members")
    team_names = []
    for i in range(st.session_state.team_count):
        # Use columns to align removing logic if needed, but for now just simple inputs
        tn = st.text_input(f"Member {i+1} Name", key=f"s_name_{i}")
        if tn:
            team_names.append(tn)

    st.button("➕ Add Team Member", on_click=add_member)

    # helper for context
    name = "\n".join(team_names)

    if st.button("Generate Academic Report", type="primary"):
        if not api_key:
            st.error("🔒 Please enter your Groq API Key in the sidebar to proceed.")
        elif not proj_zip:
            st.error("📂 Please upload your Project ZIP file to generate the report.")
        elif not name.strip():
            st.error("👥 Please enter at least one Team Member name.")
        else:
            try:
                analyzer = CodeAnalyzer()
                with st.spinner("Analyzing Codebase (In-Memory)..."):
                    summary = analyzer.analyze_zip(proj_zip)
                
                if getattr(summary, "total_files", 0) == 0:
                    st.error("❌ The uploaded ZIP file contains zero recognizable codebase files. Please upload a valid project structure.")
                    st.stop()
                    
                st.success(f"Analyzed {summary.total_files} files securely in memory.")

                # Style Analysis
                style_guide = ""
                sample_sections = {}
                raw_text = ""
                if sample_rep:
                    with st.spinner("Analyzing Sample Style (plus OCR if needed)..."):
                        sa = StyleAnalyzer(api_key=api_key)
                        ext = sample_rep.name.split(".")[-1].lower()
                        raw_text = sa.extract_text(sample_rep, ext)
                        style_guide = sa.analyze_style(raw_text)
                        sample_sections = sa.extract_specific_sections(sample_rep, ext)
                    st.toast("Style & Templates Extracted!", icon="🎨")

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
                
                # API Connection Test
                try:
                    gen.model.models.list()
                except Exception as e:
                    if "401" in str(e) or "unauthorized" in str(e).lower():
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
                    }
                )

                # --- STRUCTURED GENERATION ---
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
                        context, summary, progress_callback=update_progress
                    )

                # --- 4. STRUCTURE VALIDATION GATE ---
                with st.spinner("Validating structural integrity and auto-healing..."):
                    validator = DocumentValidator()
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
                st.download_button(
                    "📥 Download Final Report", buf.getvalue(), "Academic_Report.docx"
                )

            except Exception as e:
                st.error(f"Failure: {e}")
                st.text(traceback.format_exc())
