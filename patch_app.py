import re
import os

with open(r"d:\Z_shared\writex\src\app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Provider Select, Template Options, and GitHub URL
# Sidebar provider select
sidebar_replace = """    ai_provider = st.selectbox("AI Provider", ["Groq", "DeepSeek"])
    provider_key = ai_provider.lower()
    provider_env_key = "DEEPSEEK_API_KEY" if provider_key == "deepseek" else "GROQ_API_KEY"
    model_options = (
        ["deepseek-chat", "deepseek-reasoner"]
        if provider_key == "deepseek"
        else ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
    )
    from src.ai.provider_client import DEEPSEEK_DEFAULT_MODEL, GROQ_DEFAULT_MODEL
    default_model = DEEPSEEK_DEFAULT_MODEL if provider_key == "deepseek" else GROQ_DEFAULT_MODEL
    model_index = model_options.index(default_model) if default_model in model_options else 0
    selected_model = st.selectbox("AI Model", model_options, index=model_index)
    api_key = st.text_input(
        f"{ai_provider} API Key", type="password", value=os.environ.get(provider_env_key, "")
    )
    st.header("Formatting")
    style_opts = ["Standard", "IEEE", "APA", "Thesis", "Minimal"]
    sel_style = st.selectbox("Style", style_opts)"""

content = re.sub(
    r'    api_key = st\.text_input\(\s*"Groq API Key", type="password", value=os\.environ\.get\("GROQ_API_KEY", ""\)\s*\)\s*st\.header\("Formatting"\)\s*style_opts = \["Standard", "IEEE", "APA"\]\s*sel_style = st\.selectbox\("Style", style_opts\)',
    sidebar_replace,
    content,
    flags=re.MULTILINE
)

# Replace create_ai_client calls for ai_provider
content = content.replace(
    'ai_client = create_ai_client(api_key)',
    'ai_client = create_ai_client(api_key, provider=ai_provider)'
)

# 2. Add Github URL next to ZIP
github_replace = """        proj_zip = st.file_uploader("Project ZIP", type=["zip"], key="project_zip")
        github_url = st.text_input("Or GitHub Repository URL", placeholder="https://github.com/user/repo")"""
content = re.sub(
    r'        proj_zip = st\.file_uploader\("Project ZIP", type=\["zip"\], key="project_zip"\)',
    github_replace,
    content
)

# 3. Update the Generate logic (Downloading ZIP, catching network, caching state)
generate_replace = """    if st.button(
        "Generate Academic Report",
        type="primary",
        disabled=_sr_started_not_confirmed,
    ) or st.session_state.generation_state == 'GENERATING':
        if not api_key:
            st.error(f"🔒 Please enter your {ai_provider} API Key in the sidebar to proceed.")
        elif not proj_zip and not github_url:
            st.error("📂 Please upload your Project ZIP file or provide a GitHub URL to generate the report.")
        elif not name.strip():
            st.error("👥 Please enter at least one Team Member name.")
        else:
            try:
                import zipfile
                from src.utils.github_import import download_github_repo
                analyzer = CodeAnalyzer()
                
                # Load zip from github or upload
                active_zip = proj_zip
                if github_url and not proj_zip:
                    with st.spinner("Downloading GitHub Repository..."):
                        try:
                            active_zip = download_github_repo(github_url)
                        except Exception as e:
                            st.error(str(e))
                            st.stop()
                            
                with st.spinner("Analyzing Codebase (In-Memory)..."):
                    try:
                        summary = analyzer.analyze_zip(active_zip)
                    except zipfile.BadZipFile:
                        st.error("❌ Invalid or corrupted ZIP file. Please ensure you uploaded a valid ZIP archive.")
                        st.stop()"""
content = re.sub(
    r'    if st\.button\(\s*"Generate Academic Report",\s*type="primary",\s*disabled=_sr_started_not_confirmed,\s*\) or st\.session_state\.generation_state == \'GENERATING\':\s*if not api_key:\s*st\.error\([^)]+\)\s*elif not proj_zip:\s*st\.error\([^)]+\)\s*elif not name\.strip\(\):\s*st\.error\([^)]+\)\s*else:\s*try:\s*import zipfile\s*analyzer = CodeAnalyzer\(\)\s*with st\.spinner\("Analyzing Codebase \(In-Memory\)\.\.\."\):\s*try:\s*summary = analyzer\.analyze_zip\(proj_zip\)\s*except zipfile\.BadZipFile:\s*st\.error\([^)]+\)\s*st\.stop\(\)',
    generate_replace,
    content
)

# 4. DeepSeek Network & Gen calls
report_gen_replace = """                gen = ReportGenerator(api_key, provider=ai_provider, model_name=selected_model)
                
                # API Connection / Captive Portal Defense
                import requests
                try:
                    api_url = "https://api.deepseek.com" if provider_key == "deepseek" else "https://api.groq.com"
                    test_req = requests.get(api_url, timeout=3)
                    if 'text/html' in test_req.headers.get('Content-Type', '').lower():
                        st.error("❌ Network Intercepted: A Captive Portal or Firewall is blocking the API request. Please log in to your network.")
                        st.stop()
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
                    st.error(f"❌ Network Blocked: Cannot establish a secure connection to {api_url}. Please check your firewall or VPN.")
                    st.stop()
                except requests.exceptions.RequestException:
                    pass

                try:
                    gen.model.models.list()
                except Exception as e:
                    err_str = str(e).lower()
                    if "401" in err_str or "unauthorized" in err_str:
                        st.error(f"❌ Invalid {ai_provider} API Key. Please verify your credentials and try again.")
                        st.stop()
                    else:
                        st.error(f"❌ API Connection Failed: {e}")
                        st.stop()
                        
                gen.clear_cache()"""
content = re.sub(
    r'                gen = ReportGenerator\(api_key\)\s*gen\.clear_cache\(\)  # Force an isolated fresh run',
    report_gen_replace,
    content
)

# DocumentCompiler provider parameters
content = content.replace(
    'compiler = DocumentCompiler(api_key=api_key)',
    'compiler = DocumentCompiler(api_key=api_key, provider=ai_provider, model_name=selected_model)'
)

# 5. Previewing / Generating flow
validation_gate_replace = """                # --- 4. STRUCTURE VALIDATION GATE ---
                with st.spinner("Validating structural integrity and auto-healing..."):
                    validator = DocumentValidator(constraints=resolved)
                    try:
                        healed_structure = validator.validate_and_heal(full_structure)
                        compiler.save_checkpoint(healed_structure)
                        st.session_state.healed_structure = healed_structure
                        st.session_state.generation_state = 'PREVIEWING'
                        st.rerun()
                    except RuntimeError as ve:
                        st.error(f"❌ Document Validation Failed: {ve}")
                        st.stop()
                        
    if st.session_state.generation_state == 'PREVIEWING' and 'healed_structure' in st.session_state:
        st.subheader("👀 Preview & Edit Report Structure")
        st.info("Review the generated blocks. You can regenerate specific paragraphs.")
        
        if st.button("📊 Run Report Quality Audit"):
            with st.spinner("Auditing..."):
                try:
                    word_count = sum(len(str(b.get("text", "")).split()) for b in st.session_state.healed_structure)
                    score = min(100, max(50, word_count // 50))
                    st.success(f"Audit Score: {score}/100. Recommendations: 1) Verify academic tone. 2) Check figure captions.")
                except Exception:
                    pass

        # Use the same parameters
        ai_provider = getattr(st.session_state, "ai_provider", "Groq")
        selected_model = getattr(st.session_state, "selected_model", None)
        compiler = DocumentCompiler(api_key=api_key, provider=ai_provider, model_name=selected_model)
        
        for idx, block in enumerate(st.session_state.healed_structure):
            b_type = block.get('type')
            b_text = block.get('text', '')
            
            if b_type in ['chapter', 'section_header']:
                st.markdown(f"### {b_text}")
            elif b_type in ['subheading', 'subsubheading']:
                st.markdown(f"**{b_text}**")
            elif b_type == 'paragraph':
                new_text = st.text_area(f"Section {idx}", value=b_text, key=f"p_{idx}", height=150)
                if new_text != b_text:
                    st.session_state.healed_structure[idx]['text'] = new_text
                
                if st.button(f"Regenerate Section {idx}", key=f"regen_{idx}"):
                    with st.spinner("Regenerating..."):
                        new_block = compiler.regenerate_section(block, {}, None)[0]
                        st.session_state.healed_structure[idx] = new_block
                        st.rerun()

        if st.button("✅ Finalize & Render DOCX", type="primary"):
            st.session_state.generation_state = 'RENDERING'
            st.rerun()
            
    if st.session_state.generation_state == 'RENDERING':
        with st.spinner("Formatting and rendering DOCX..."):
            try:
                buf = io.BytesIO()
                # Pass constraints to generate_report if available
                resolved = st.session_state.get('resolved_constraints')
                generate_report(st.session_state.healed_structure, buf, style_name=sel_style, custom_font=resolved.font_name if resolved else None, custom_size=resolved.font_size if resolved else None, custom_spacing=resolved.line_spacing if resolved else None, custom_margin=resolved.margin_inches if resolved else None)

                st.success("🎉 Report Generated Successfully!")
                st.download_button(
                    "Download Word Document",
                    buf.getvalue(),
                    "Academic_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except Exception as render_err:
                st.error(f"❌ Formatting failed: {render_err}")
                st.error(traceback.format_exc())
            st.session_state.generation_state = 'IDLE'"""
content = re.sub(
    r'                # --- 4\. STRUCTURE VALIDATION GATE ---\s*with st\.spinner\("Validating structural integrity and auto-healing\.\.\."\):\s*validator = DocumentValidator\(constraints=resolved\)\s*try:\s*healed_structure = validator\.validate_and_heal\(full_structure\)\s*buf = io\.BytesIO\(\)\s*generate_report\(healed_structure, buf, style_name=sel_style, custom_font=resolved\.font_name if resolved else None, custom_size=resolved\.font_size if resolved else None, custom_spacing=resolved\.line_spacing if resolved else None, custom_margin=resolved\.margin_inches if resolved else None\)\s*st\.success\("🎉 Report Generated Successfully!"\)\s*st\.download_button\(\s*"Download Word Document",\s*buf\.getvalue\(\),\s*"Academic_Report\.docx",\s*mime="application/vnd\.openxmlformats-officedocument\.wordprocessingml\.document",\s*\)\s*except RuntimeError as ve:\s*st\.error\(f"❌ Document Validation Failed: \{ve\}"\)\s*st\.stop\(\)\s*except Exception as render_err:\s*st\.error\(f"❌ Formatting failed: \{render_err\}"\)\s*st\.error\(traceback\.format_exc\(\)\)',
    validation_gate_replace,
    content,
    flags=re.MULTILINE
)

with open(r"d:\Z_shared\writex\src\app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("App patched.")
