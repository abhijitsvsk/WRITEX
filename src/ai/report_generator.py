import os
import json
import re
from typing import Dict, Any, List
from groq import Groq
import threading
from .utils import generate_with_retry
from .code_analysis_formatter import format_detailed_analysis_for_prompt
from src.security.sanitizer import DataSanitizer
import textwrap


class ReportGenerator:
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        if not api_key:
            raise ValueError("API Key is required for ReportGenerator")
        # Initialize Groq client
        self.model = Groq(api_key=api_key)
        self.model_name = model_name

        # Free-Tier Caching System
        self.cache_dir = os.path.join("cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "report_cache.json")
        self._cache_lock = threading.Lock()
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        with self._cache_lock:
            try:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.cache, f, indent=4)
            except Exception as e:
                print(f"Failed to save cache: {e}")

    def clear_cache(self):
        """Thread-safe method to wipe the generation cache for a fresh run."""
        with self._cache_lock:
            self.cache = {}
            if os.path.exists(self.cache_file):
                try:
                    os.remove(self.cache_file)
                except Exception as e:
                    print(f"Failed to clear cache file: {e}")

    def extract_metadata_from_sample(self, sample_text: str) -> Dict[str, str]:
        """
        Extracts structural and entity metadata from a sample report using LLM.
        """
        if not sample_text:
            return {}

        prompt = f"""
        Analyze the following academic report sample and extract these specific metadata fields if they exist.
        Return ONLY a JSON object with these exact keys:
        - "title": The project title
        - "team_names": A list of student names (if single, a list of 1)
        - "guide": The name of the project guide/supervisor
        - "hod": The Head of Department name
        - "principal": The Principal name
        - "university": The parent university name
        - "department": The department name (e.g., Computer Science and Engineering)
        - "degree": The degree title (e.g., Bachelor of Technology)
        - "academic_year": The academic year (e.g., 2025-2026)
        
        If a field is not found, leave its value as null or an empty string. Output ONLY valid JSON.
        
        Sample Text:
        \"\"\"
        {sample_text[:4000]} # Limit to first 4000 chars (mostly front matter)
        \"\"\"
        """
        try:
            response = generate_with_retry(self.model, prompt)
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {}

    def generate_section(
        self,
        section_name: str,
        project_summary: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> str:
        """
        Generates content for a specific report section.
        """
        # Strict Templates for Cert/Ack
        if section_name.lower() in ["certificate", "acknowledgement", "acknowledgment"]:
            return self.fill_template(section_name, user_context)

        # Check Cache
        cache_key = f"section_{section_name}_{user_context.get('title', 'default')}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        prompt = self._build_prompt(section_name, project_summary, user_context)

        try:
            result = generate_with_retry(self.model, prompt)
            self.cache[cache_key] = result
            self._save_cache()
            return result
        except Exception as e:
            return f"Error generating section {section_name}: {str(e)}"

    def generate_subsection_body(
        self,
        chapter_title: str,
        subsection_title: str,
        project_summary: Dict,
        user_context: Dict,
    ) -> str:
        """
        Generates ONLY the body text for a specific subsection.
        Strictly forbids outputting headings or markdown titles.
        """
        # CRITICAL: Special handling for Results chapter without test data
        if chapter_title == "Results and Discussion":
            metrics_data = user_context.get("test_metrics_data", "")
            if not metrics_data and not user_context.get("has_test_files", False):
                # Provide honest fallback instead of fabricated metrics
                if (
                    "Performance Metrics" in subsection_title
                    or "Experimental Output" in subsection_title
                ):
                    return """Testing and validation were performed through manual verification during development. Automated unit tests and performance benchmarking are planned for future iterations. Preliminary functionality testing confirms that the system meets its core requirements."""
                elif "Results Analysis" in subsection_title:
                    return """The system was validated manually to ensure correctness of core functionality. Each module was tested individually before integration. While automated testing infrastructure is under development, the current implementation has been verified to work as specified in the requirements."""
        # Context Slicing - STRICT METADATA ONLY
        sliced_summary = self._slice_context(chapter_title, project_summary)

        # Security: Scrub AWS Keys & PII before dispatching to external LLM
        safe_summary = DataSanitizer.sanitize_payload(sliced_summary)

        # Cache Check
        cache_key = f"sub_{chapter_title}_{subsection_title}_{user_context.get('title', 'default')}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        metrics_context = ""
        if chapter_title == "Results and Discussion" and user_context.get(
            "test_metrics_data"
        ):
            metrics_context = f"\\n\\nREAL EXPERIMENTAL DATA SET (CRITICAL):\\n{user_context.get('test_metrics_data')}\\n\\nYou MUST use this exact experimental data to synthesize authentic, real academic metrics corresponding to the dataset."

        # Dynamic Diagram Gating: Prevent image bloat in non-technical chapters
        allowed_figure_chapters = [
            "System Architecture",
            "System Analysis and Design",
            "Implementation",
            "Proposed System",
            "Methodology",
            "Results and Discussion"
        ]
        
        figure_rule = "6. **STRICT DIAGRAM BAN**: You MUST NOT generate any `[Figure X.Y: Caption]` placeholders or diagrams whatsoever. The backend system will handle all figure insertions deterministically. Keep your output strictly textual."

        code_rule = "5. **NO CODE EXTRACTION**: Do not use `[Extract Code: X]` tags. Discuss the system logic conceptually."
        actual_code_context = ""
        
        if chapter_title == "Implementation":
            valid_targets = []
            analysis = user_context.get("detailed_analysis")
            if analysis:
                for f in analysis.functions:
                    valid_targets.append(f.name)
                for c in analysis.classes:
                    valid_targets.append(c.name)
            
            targets_str = ", ".join(valid_targets[:20]) if valid_targets else "core logic functions"
            
            code_rule = f"5. **CODE EXTRACTION ALLOWED**: You MUST use `[Extract Code: FunctionName]` or `[Extract Code: ClassName]` tags on their own lines to showcase critical logic. IMPORTANT: You MUST ONLY use the following valid targets from the actual codebase: {targets_str}. Do not hallucinate names!"

        prompt = f"""
        [PROMPT_TEMPLATE_VERSION: 1.0.0 (Production Locked)]
        You are an expert Academic Editor and Strategic System Architect writing a formal B.Tech Project Report.
        
        Project Metadata (JSON):
        {json.dumps(safe_summary, indent=2)}
        
        Context:
        Title: {user_context.get('title')}
        Problem: {user_context.get('problem_statement')}{metrics_context}
        
        Task: Write the body text for the subsection: **"{subsection_title}"** (inside Chapter: "{chapter_title}").
        
        CRITICAL NARRATIVE CONSTRAINTS (HARD RULES):
        1. **NO HEADINGS**: Do NOT output markdown headings (no #, ##, ###). Write ONLY pure academic paragraphs.
        2. **NO RAW CODE OR FILE NAMES**: Absolutely DO NOT mention specific Python filenames. Speak entirely in abstract system-level terminology (e.g., "The Text Preprocessing Module", "The Lexical Analyzer", etc.).
        3. **ACADEMIC STORYTELLING**: You must synthesize a cohesive academic narrative based on the project data. Discuss the theoretical dataset (50 academic drafts), the ETL pipeline, system architectures, and rule-based evaluation logic (Parsing Accuracy, Formatting Consistency).
        4. **LITERATURE SURVEY (IEEE FORMAT)**: If you are writing for Chapter 2 (Literature Survey), you MUST synthesize fake, highly realistic academic critiques of existing systems using strict IEEE citation format. Provide comparative analysis and explicitly identify research gaps that this project solves.
        {code_rule}
        {figure_rule}
        7. **STRICT LENGTH**: Write exactly 300-350 words. Do not trail off or include meta-commentary.
        """

        result = generate_with_retry(self.model, prompt)
        self.cache[cache_key] = result
        self._save_cache()
        return result

    def generate_chapter_intro(
        self,
        chapter_title: str,
        subsections: list,
        project_summary: Dict,
        user_context: Dict,
    ) -> str:
        """
        Generates a brief 2-3 sentence introductory paragraph for a Chapter, highlighting what will be discussed,
        before transitioning into the specific subheadings.
        """
        prompt = f"""
        Task: Write a brief introductory paragraph for the Chapter: "{chapter_title}".
        This chapter will contain the following subsections: {", ".join(subsections)}.
        
        Requirements:
        1. Write ONLY 2-3 sentences.
        2. Briefly introduce what {chapter_title} entails in the context of the project "{user_context.get('title')}".
        3. Mention that it will cover {", ".join(subsections)}.
        4. NO HEADINGS. Just pure text.
        5. DO NOT hallucinate features.
        """
        return generate_with_retry(self.model, prompt)

    def fill_template(self, section_name: str, user_context: Dict) -> str:
        """
        Returns the exact hardcoded string templates mapped from the reference sample.
        Bypasses LLM generation to guarantee zero deviations.
        """
        if section_name.lower() in ["certificate"]:
            title = user_context.get("title", "Project Title")
            team_names = user_context.get("team_names_raw") or [
                user_context.get("team_names", "Student Name")
            ]
            clean_list = [str(name).strip() for name in team_names if name]
            names_str = ", ".join(clean_list)
            degree = user_context.get("degree", "Bachelor of Technology")
            dept = user_context.get("department", "Computer Science and Engineering")
            year = user_context.get("academic_year", "2025-2026")
            university = user_context.get("university", "University")

            return (
                f'This is to certify that the project report entitled "{title}" is a bonafide '
                f"record of the work done by {names_str} of the Department of {dept}, "
                f"{university}, during the academic year {year}, in partial fulfillment of the "
                f"requirements for the award of the degree of {degree}.\n\nDate:"
            )

        elif section_name.lower() in ["acknowledgement", "acknowledgment"]:
            principal = user_context.get("principal", "the Principal")
            hod = user_context.get("hod", "the HOD")
            dept = user_context.get("department", "Computer Science and Engineering")
            title = user_context.get("title", "Project Title")
            guide = user_context.get("guide", "the Guide")
            university = user_context.get("university", "University")
            is_plural = user_context.get("pronoun_mode", "singular") == "plural"

            # Pronoun selection
            we = "We" if is_plural else "I"
            our = "our" if is_plural else "my"
            us = "us" if is_plural else "me"

            return (
                f"{we} wish to express {our} sincere gratitude towards {principal}, "
                f"Principal of {university}, and {hod}, Head of the Department of {dept}, "
                f"for providing {us} with the opportunity to undertake {our} project, {title}.\n\n"
                f"It is indeed {our} pleasure and a moment of satisfaction to express {our} "
                f"sincere gratitude to {our} project guide, {guide}, for the patience and all the "
                f"priceless advice and wisdom shared with {us} throughout the duration of this project.\n\n"
                f"We would also like to thank the faculty members of the Department of {dept} "
                f"for their valuable support and suggestions.\n\n"
                f"Last but not the least, {we.lower()} would like to express {our} sincere gratitude "
                f"towards {our} parents and friends for their continuous support and constructive ideas."
            )

        return ""

    def generate_literature_survey_body(
        self, project_summary: Dict, user_context: Dict
    ) -> str:
        """
        Generates body paragraphs for Lit Survey.
        """
        # Check Cache
        cache_key = f"lit_survey_{user_context.get('title', 'default')}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        sliced_summary = {
            "tech_stack": project_summary.get("tech_stack"),
            "modules": (project_summary.get("modules") or [])[:5],
        }

        prompt = f"""
        Task: Write a comparative literature survey body text (3-4 paragraphs).
        
        Context:
        {json.dumps(sliced_summary, indent=2)}
        
        CRITICAL NARRATIVE CONSTRAINTS (HARD RULES):
        1. Compare 3 distinct standard academic approaches relevant to this tech stack domain (e.g. Rule-based Text Processing, Deep NLP, Automated Typesetting).
        2. For each, state the **Limitation** (Technical bottleneck, like high compute cost or latency).
        3. State how THIS project proposes to solve it using deterministic rule-based algorithms.
        4. **NO HALLUCINATED CITATIONS**: Do not generate any raw citations (e.g. [1] Smith). Speak generally about algorithmic limitations without inventing fictional authors.
        5. DO NOT mention specific Python filenames. Speak in high-level system abstractions (e.g., "The lexical parsing module").
        6. NO HEADINGS. Just body text.
        7. STRICT LENGTH: Write exactly 350-400 words.
        """
        try:
            result = generate_with_retry(self.model, prompt)
            self.cache[cache_key] = result
            self._save_cache()
            return result
        except Exception as e:
            return f"Error generating survey: {e}"

    def derive_project_context(self, project_summary: Dict) -> Dict[str, str]:
        # Remove detailed_analysis before json.dumps (it's not JSON serializable)
        summary_for_json = {
            k: v for k, v in project_summary.items() if k != "detailed_analysis"
        }

        # ... (Keep existing simple context derivation, it works fine) ...
        prompt = f"""
        Analyze this project:
        {json.dumps(summary_for_json, indent=2)[:2000]}
        
        Generate concise:
        1. Problem Statement (Technical, 2 sentences).
        2. Key Objectives (3 bullet points).
        
        Return JSON: {{ "problem_statement": "...", "objectives": "..." }}
        """
        try:
            text = generate_with_retry(self.model, prompt)
            import re

            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(text)
        except:
            return {
                "problem_statement": "Technical efficiency issue.",
                "objectives": "- Optimize workflow.\n- Automate data.",
            }

    def _build_prompt(
        self, section_name: str, project_summary: Dict, user_context: Dict
    ) -> str:
        # CRITICAL TOKEN OPTIMIZATION: We no longer dump detailed code analysis.
        # This prevents 429 Errors and forces system-level abstraction.

        # Context Slicing specific to section
        sliced_summary = {}
        section_lower = section_name.lower()

        if "abstract" in section_lower or "introduction" in section_lower:
            sliced_summary = {
                "project_type": project_summary.get("project_type"),
                "problem_statement": user_context.get("problem_statement"),
                "objectives": user_context.get("objectives"),
                "tech_stack": (project_summary.get("tech_stack") or [])[:5],
            }
        elif "methodology" in section_lower or "implementation" in section_lower:
            # Pass ALL extracted modules for deep context, including classes/functions
            sliced_summary = {
                "tech_stack": project_summary.get("tech_stack") or [],
                "algorithms": project_summary.get("algorithms_used") or [],
                "modules": project_summary.get("modules") or [],
                "workflow": project_summary.get("workflow") or "",
            }
        elif "results" in section_lower or "discussion" in section_lower:
            sliced_summary = {
                "problem_statement": user_context.get("problem_statement"),
                "objectives": user_context.get("objectives"),
            }
        else:
            # Default fallback
            sliced_summary = {
                k: v
                for k, v in project_summary.items()
                if k in ["project_type", "tech_stack", "algorithms_used"]
            }

        style_instruction = ""
        if user_context.get("style_guide"):
            style_instruction = f"IMPORTANT: Follow this writing style:\n{user_context.get('style_guide')[:1500]}"

        base_prompt = f"""
        You are an expert Academic Editor and Strategic System Architect writing the **{section_name}** section for a B.Tech Computer Science project report.
        
        {style_instruction}
        
        Project Metadata (JSON):
        {json.dumps(sliced_summary, indent=2)}
        
        Evaluation Metrics (Enforced Deterministic Base):
        - Dataset: 50 unstructured academic drafts
        - Performance Metrics: Parsing Accuracy, Formatting Consistency Score, Execution Latency vs Manual Typesetting
        
        User Context:
        Title: {user_context.get('title')}
        Problem: {user_context.get('problem_statement')}
        Objectives: {user_context.get('objectives')}
        
        CRITICAL NARRATIVE CONSTRAINTS (HARD RULES):
        1. **NO RAW CODE OR FILE NAMES**: Absolutely DO NOT mention specific Python filenames like `formatting.py` or `.py` files at all. DO NOT dump raw code functions. Speak entirely in abstract system-level terminology (e.g., "The Preprocessing Module", "The Data Transformation Layer", etc.).
        2. **ACADEMIC STORYTELLING**: Synthesize a cohesive academic narrative. Discuss the theoretical dataset defined above, the ETL pipeline architecture, system latency, and rule-based evaluation metrics. Do not invent ML metrics like F1 or Recall. Ensure you portray it as a deterministic Intelligent NLP-Assisted pipeline.
        3. **INSTITUTIONAL OUTCOMES (PEO/PO/PSO/CO)**: If this section is PEO, PO, PSO, or CO, DO NOT refer to specific code, modules, or features of the project. Speak exclusively about high-level B.Tech Educational Outcomes (e.g., "Ability to design complex systems", "Demonstrating engineering life-long learning").
        4. **NO FICTIONAL REFERENCES**: DO NOT hallucinate fake citations, author names (e.g., J. Smith), or fictional textbook references under any circumstances.
        5. **NO HEADINGS**: Write ONLY pure academic paragraphs.
        6. **STRICT LENGTH**: Exactly 300-350 words. Do not trail off or write meta-text.
        """
        return base_prompt

    def _slice_context(self, chapter_title: str, project_summary: Dict) -> Dict:
        # Helper to slice context based on chapter
        full_summary = project_summary
        title = chapter_title.lower()

        if "intro" in title:
            return {
                "project_type": full_summary.get("project_type"),
                "tech_stack": full_summary.get("tech_stack"),
            }
        elif "method" in title or "implement" in title:
            return {
                "modules": full_summary.get("modules"),
                "algorithms": full_summary.get("algorithms_used"),
                "workflow": full_summary.get("workflow"),
            }
        elif "result" in title:
            return {"project_type": full_summary.get("project_type")}
        return {"tech_stack": full_summary.get("tech_stack")}
