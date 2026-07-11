import re

with open(r"d:\Z_shared\writex\src\app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update the import at the top to include StyleConfig
import_old = "from src.file_formatting.formatting import generate_report"
import_new = "from src.file_formatting.formatting import generate_report, StyleConfig\nfrom docx.enum.text import WD_ALIGN_PARAGRAPH"
content = content.replace(import_old, import_new)

# 2. Add Advanced Formatting to Sidebar
sidebar_old = """    st.header("Formatting")
    style_opts = ["Standard", "IEEE", "APA", "Thesis", "Minimal"]
    sel_style = st.selectbox("Style", style_opts)
    
    st.markdown("---")"""

sidebar_new = """    st.header("Formatting")
    style_opts = ["Standard", "IEEE", "APA", "Thesis", "Minimal"]
    sel_style = st.selectbox("Style", style_opts)
    
    with st.expander("Advanced Custom Formatting"):
        st.caption("Override template with granular rules")
        # Load preset if exists
        import json
        preset = {}
        if os.path.exists("style_preset.json"):
            try:
                with open("style_preset.json", "r") as pf:
                    preset = json.load(pf)
            except:
                pass
                
        adv_margin = st.number_input("Margin (Inches)", value=preset.get("margin", 1.0), step=0.25)
        
        st.markdown("**Headings**")
        adv_h_font = st.selectbox("Heading Font", ["Times New Roman", "Arial", "Calibri", "Courier New"], index=["Times New Roman", "Arial", "Calibri", "Courier New"].index(preset.get("h_font", "Times New Roman")))
        adv_h_size = st.number_input("Heading Size (pt)", value=preset.get("h_size", 14.0), step=1.0)
        adv_h_align = st.selectbox("Heading Alignment", ["Left", "Center", "Right"], index=["Left", "Center", "Right"].index(preset.get("h_align", "Center")))
        adv_h_bold = st.checkbox("Heading Bold", value=preset.get("h_bold", True))
        
        st.markdown("**Content & Code**")
        adv_c_font = st.selectbox("Content Font", ["Times New Roman", "Arial", "Calibri", "Courier New"], index=["Times New Roman", "Arial", "Calibri", "Courier New"].index(preset.get("c_font", "Times New Roman")))
        adv_c_size = st.number_input("Content Size (pt)", value=preset.get("c_size", 12.0), step=1.0)
        adv_c_align = st.selectbox("Content Alignment", ["Left", "Center", "Right", "Justify"], index=["Left", "Center", "Right", "Justify"].index(preset.get("c_align", "Justify")))
        
        st.markdown("**Spacing**")
        adv_spacing = st.number_input("Line Spacing", value=preset.get("spacing", 1.5), step=0.25)
        adv_space_before = st.number_input("Space Before (pt)", value=preset.get("space_before", 0.0), step=1.0)
        adv_space_after = st.number_input("Space After (pt)", value=preset.get("space_after", 0.0), step=1.0)
        
        if st.button("💾 Save as Preset"):
            with open("style_preset.json", "w") as pf:
                json.dump({
                    "margin": adv_margin, "h_font": adv_h_font, "h_size": adv_h_size, 
                    "h_align": adv_h_align, "h_bold": adv_h_bold, "c_font": adv_c_font,
                    "c_size": adv_c_size, "c_align": adv_c_align, "spacing": adv_spacing,
                    "space_before": adv_space_before, "space_after": adv_space_after
                }, pf)
            st.success("Preset Saved!")

    align_map = {"Left": WD_ALIGN_PARAGRAPH.LEFT, "Center": WD_ALIGN_PARAGRAPH.CENTER, "Right": WD_ALIGN_PARAGRAPH.RIGHT, "Justify": WD_ALIGN_PARAGRAPH.JUSTIFY}
    
    style_config = StyleConfig(
        margin_inches=adv_margin,
        heading_font=adv_h_font,
        heading_size_pt=adv_h_size,
        heading_bold=adv_h_bold,
        heading_alignment=align_map[adv_h_align],
        content_font=adv_c_font,
        content_size_pt=adv_c_size,
        content_alignment=align_map[adv_c_align],
        line_spacing=adv_spacing,
        space_before_pt=adv_space_before,
        space_after_pt=adv_space_after
    )
    
    st.markdown("---")"""
content = content.replace(sidebar_old, sidebar_new)

# 3. Add Rewrite Toggle
sample_old = """        sample_rep = st.file_uploader(
            "Upload Sample Report (PDF/DOCX)",
            type=["pdf", "docx"],
            help="Optional. Upload a sample to mimic its style.",
            key="sample_report",
        )"""

sample_new = """        sample_rep = st.file_uploader(
            "Upload Inspiration File (PDF/DOCX/TXT)",
            type=["pdf", "docx", "txt"],
            help="Optional. Upload a file to mimic its style or content.",
            key="sample_report",
        )
        rewrite_mode = st.toggle("Rewrite Mode (Match tone strictly)", value=False, help="If enabled, AI will rewrite your text to perfectly match the inspiration file.")"""
content = content.replace(sample_old, sample_new)

# 4. Extract Inspiration text inside the main flow
# Find where context is updated.
context_old = """                        "problem_statement": context["problem_statement"],
                        "style_guide": style_guide,
                        "sample_report_provided": bool(sample_rep),"""

context_new = """                        "problem_statement": context["problem_statement"],
                        "style_guide": style_guide,
                        "sample_report_provided": bool(sample_rep),
                        "inspiration_text": inspiration_text,
                        "rewrite_mode": rewrite_mode,"""
content = content.replace(context_old, context_new)

# 5. Extract Inspiration text before context update
extract_old = """                    context["detailed_analysis"] = summary.detailed_analysis

                # --- BUILD CONTEXT DICTIONARY ---"""

extract_new = """                    context["detailed_analysis"] = summary.detailed_analysis

                # Extract Inspiration Text
                inspiration_text = ""
                if sample_rep:
                    try:
                        if sample_rep.name.endswith('.pdf'):
                            import pypdf
                            reader = pypdf.PdfReader(sample_rep)
                            for p in reader.pages:
                                inspiration_text += p.extract_text() + "\\n"
                        elif sample_rep.name.endswith('.docx'):
                            from docx import Document
                            doc = Document(sample_rep)
                            inspiration_text = "\\n".join([p.text for p in doc.paragraphs])
                        elif sample_rep.name.endswith('.txt'):
                            inspiration_text = sample_rep.getvalue().decode('utf-8')
                        sample_rep.seek(0)
                    except Exception as e:
                        st.warning(f"Failed to read inspiration file: {e}")

                # --- BUILD CONTEXT DICTIONARY ---"""
content = content.replace(extract_old, extract_new)

# 6. Pass style_config to generate_report
gen_old = """                generate_report(healed_structure, buf, style_name=sel_style)"""
gen_new = """                generate_report(healed_structure, buf, style_name=sel_style, style_config=style_config)"""
content = content.replace(gen_old, gen_new)

# We also need to fix run_formatting if it exists (for Tab 1 and Tab 2)
# But tab 3 is the main one. Let's see if run_formatting needs it.
run_form_old = """def run_formatting(text, api_key, style_name):"""
run_form_new = """def run_formatting(text, api_key, style_name):
    st.warning("Preview formatting doesn't fully utilize the new Advanced StyleConfig yet.")"""
content = content.replace(run_form_old, run_form_new)

with open(r"d:\Z_shared\writex\src\app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated app.py")
