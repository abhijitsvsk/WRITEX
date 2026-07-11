import re

with open(r"d:\Z_shared\writex\src\app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update `run_formatting` signature and logic
run_format_old = """def run_formatting(text_content, api_key_val, style_name, style_cfg):
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
            generate_report(data, buf, style_name=style_name, style_config=style_cfg)
            st.download_button("Download", buf.getvalue(), "formatted.docx")
        except Exception as e:"""

run_format_new = """def run_formatting(text_content, api_key_val, style_name, style_cfg, uploaded_images=None, image_placement=None):
    # Keep lightweight formatting for Tabs 1 & 2
    from src.ai.structurer import structure_text

    if not api_key_val:
        return
    with st.spinner("Structuring..."):
        try:
            image_names = [img.name for img in uploaded_images] if uploaded_images else []
            struct = structure_text(
                text_content, api_key=api_key_val, style_name=style_name, available_images=image_names
            )
            json_match = re.search(r"\[.*\]", struct, re.DOTALL)
            data = json.loads(json_match.group(0)) if json_match else []

            # Handle Image AST Injection
            if uploaded_images:
                img_nodes = [{"type": "image", "content": img.getvalue(), "filename": img.name} for img in uploaded_images]
                
                if image_placement == "Top":
                    data = img_nodes + data
                elif image_placement == "Bottom":
                    data = data + img_nodes
                else:
                    # Let AI Decide logic
                    # The AI emitted {"type": "image_insertion", "filename": "x.png"}
                    new_data = []
                    for block in data:
                        if block.get("type") == "image_insertion":
                            fname = block.get("filename")
                            matched = next((node for node in img_nodes if node["filename"] == fname), None)
                            if matched:
                                new_data.append(matched)
                        else:
                            new_data.append(block)
                    
                    # Also append any leftover images that the AI missed (optional, but good for UX)
                    used_fnames = [b.get("filename") for b in new_data if b.get("type") == "image"]
                    for node in img_nodes:
                        if node["filename"] not in used_fnames:
                            new_data.append(node)
                            
                    data = new_data

            buf = io.BytesIO()
            generate_report(data, buf, style_name=style_name, style_config=style_cfg)
            st.download_button("Download", buf.getvalue(), "formatted.docx")
        except Exception as e:"""

content = content.replace(run_format_old, run_format_new)

# 2. Add Sidebar UI for Images
sidebar_old = """        code_language=adv_code_lang
    )
    
    st.markdown("---")"""

sidebar_new = """        code_language=adv_code_lang
    )
    
    with st.expander("Insert Images"):
        uploaded_images = st.file_uploader("Upload Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        image_placement = st.radio("Image Placement", ["Let AI Decide", "Top", "Bottom"])
    
    st.markdown("---")"""

content = content.replace(sidebar_old, sidebar_new)

# 3. Pass images to run_formatting calls
tab1_old = """    if st.button("Format Text"):
        run_formatting(txt, api_key, sel_style, style_config)"""

tab1_new = """    if st.button("Format Text"):
        run_formatting(txt, api_key, sel_style, style_config, uploaded_images, image_placement)"""
content = content.replace(tab1_old, tab1_new)

tab2_old = """        run_formatting(file_txt, api_key, sel_style, style_config)"""
tab2_new = """        run_formatting(file_txt, api_key, sel_style, style_config, uploaded_images, image_placement)"""
content = content.replace(tab2_old, tab2_new)


with open(r"d:\Z_shared\writex\src\app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated app.py")
