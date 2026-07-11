import re

with open(r"d:\Z_shared\writex\src\ai\report_generator.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add inspiration rule to generate_subsection_body
inspiration_code = """        if chapter_title in ["Introduction", "Literature Survey", "Conclusions And Future Scope"]:
            code_rule = "5. **NO CODE EXTRACTION**: Do not request any codebase snippets. Discuss concepts strictly theoretically."
        elif chapter_title == "Implementation":
            code_rule = f"5. **MANDATORY CORE EXTRACTION**: Because this is the Implementation chapter, you MUST output 3 to 5 codebase snippets explaining the core logic. To extract code, output a block object of type 'code_extraction' with the 'target_name' key. YOU MUST ONLY pick from these valid targets: {targets_str}."

        inspiration_text = user_context.get("inspiration_text", "")
        rewrite_mode = user_context.get("rewrite_mode", False)
        
        inspiration_rule = ""
        if inspiration_text:
            if rewrite_mode:
                inspiration_rule = f"8. **INSPIRATION STRICT REWRITE (CRITICAL)**: You have been provided with an Inspiration File. You MUST rewrite the content for this subsection to STRICTLY match the exact tone, style, and vocabulary of this Inspiration File context:\\n---\\n{inspiration_text[:4000]}\\n---"
            else:
                inspiration_rule = f"8. **INSPIRATION FORMATTING**: You have been provided with an Inspiration File. Maintain your original narrative structure, but adopt the general tone of this Inspiration File context:\\n---\\n{inspiration_text[:4000]}\\n---"

        prompt = f\"\"\"
        [PROMPT_TEMPLATE_VERSION: 1.0.0 (Production Locked)]
        You are an expert Academic Editor and Strategic System Architect writing a formal B.Tech Project Report.
        
        Project Metadata (JSON):
        {json.dumps(safe_summary, indent=2)}
        
        Context:
        Title: {user_context.get('title')}
        Problem: {user_context.get('problem_statement')}{metrics_context}
        
        Task: Write the body text for the subsection: **"{subsection_title}"** (inside Chapter: "{chapter_title}").

        OUTPUT FORMAT (CRITICAL JSON SCHEMA):
        You MUST return a strictly valid JSON object. 
        The JSON object must contain a single root key "blocks" containing a list of objects.
        Each object in the "blocks" list must have a "type" key (either "paragraph" or "code_extraction").
        - For text paragraphs, use type "paragraph" and put the academic text in the "text" key.
        - For code extraction, use type "code_extraction" and put the exact function or class name from the valid targets list into the "target_name" key.
        
        JSON Example:
        {{
            "blocks": [
                {{"type": "paragraph", "text": "This module is designed to handle user authentication and routing."}},
                {{"type": "code_extraction", "target_name": "verify_user_password"}}
            ]
        }}
        
        CRITICAL NARRATIVE CONSTRAINTS (HARD RULES):
        1. **NO HEADINGS**: Do NOT output markdown headings (no #, ##, ###) in the paragraphs.
        2. **NO RAW CODE OR FILE NAMES**: Absolutely DO NOT mention specific Python filenames within text paragraphs. Speak entirely in abstract system-level terminology.
        3. **ACADEMIC STORYTELLING**: You must synthesize a cohesive academic narrative based on the project data. Discuss the theoretical dataset, the ETL pipeline, system architectures, etc.
        4. **LITERATURE SURVEY**: If you are writing for Chapter 2, synthesize a highly authentic comparative analysis of existing systems. DO NOT insert ANY references, bibliographies, or IEEE citations.
        {code_rule}
        {figure_rule}
        7. **STRICT LENGTH**: The combined text of all paragraphs should be roughly 300-350 words. Do not trail off or include meta-commentary.
        {inspiration_rule}
        \"\"\""""

content = re.sub(
    r'        if chapter_title in \["Introduction", "Literature Survey", "Conclusions And Future Scope"\]:.*?7\. \*\*STRICT LENGTH\*\*: The combined text of all paragraphs should be roughly 300-350 words\. Do not trail off or include meta-commentary\.\s*\"\"\"',
    lambda m: inspiration_code,
    content,
    flags=re.DOTALL
)

with open(r"d:\Z_shared\writex\src\ai\report_generator.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated report_generator.py")
