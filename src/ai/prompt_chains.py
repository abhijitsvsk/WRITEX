"""
Prompt Chain System for WriteX
Decomposes generation into: Plan → Draft → Polish
Includes few-shot examples per section type and rolling narrative memory.
Zero external dependencies - works with Groq free tier models.
"""

import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from .utils import generate_with_retry, ACADEMIC_SYSTEM_PROMPT
from .provider_client import create_ai_client


# ─── Few-Shot Examples ───
# Stored as dict for zero-file-IO; can be moved to JSON files later
FEW_SHOT_EXAMPLES = {
    "introduction_background": {
        "context": {
            "project_type": "Machine Learning",
            "tech_stack": ["Python", "PyTorch", "Transformers", "HuggingFace"],
            "problem_statement": "Manual document formatting is inconsistent and error-prone.",
        },
        "output": (
            "The proliferation of deep learning architectures has transformed natural language processing, "
            "yet the automation of academic document preparation remains largely rule-based and brittle. "
            "Current approaches rely on rigid templates that fail to capture the nuanced formatting "
            "requirements of institutional guidelines. This project addresses this gap by introducing "
            "an intelligent formatting engine that combines structural analysis with generative AI "
            "to produce compliant academic reports from raw codebases."
        ),
    },
    "introduction_problem_definition": {
        "context": {
            "project_type": "Web Application",
            "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
            "problem_statement": "Existing tools lack integration between code analysis and document generation.",
        },
        "output": (
            "Despite the maturity of static analysis tools and document generation libraries, "
            "no existing solution bridges the semantic gap between source code architecture "
            "and academic reporting requirements. Developers manually extract design decisions, "
            "algorithm choices, and module interactions — a process that is both time-consuming "
            "and prone to inconsistency. The absence of an automated pipeline that understands "
            "both code semantics and academic discourse conventions creates a persistent bottleneck "
            "in project documentation workflows."
        ),
    },
    "literature_survey_existing_approaches": {
        "context": {
            "project_type": "Data Analysis",
            "tech_stack": ["Python", "pandas", "scikit-learn", "matplotlib"],
            "algorithms_used": ["RandomForest", "KMeans", "PCA"],
        },
        "output": (
            "Three predominant approaches characterize the current landscape of automated "
            "report generation. Template-based systems (e.g., Jinja2, Pandoc) offer structural "
            "consistency but lack semantic understanding of code artifacts. LLM-only pipelines "
            "provide narrative fluency but hallucinate technical details without grounded context. "
            "Rule-based formatters (e.g., python-docx styling) enforce visual compliance but "
            "require manual content authoring. Each approach addresses a subset of requirements "
            "while introducing critical limitations: templates cannot adapt to novel project "
            "structures, pure LLM outputs lack factual grounding, and formatters demand "
            "explicit content specification."
        ),
    },
    "methodology_data_acquisition": {
        "context": {
            "project_type": "General Software",
            "tech_stack": ["Python", "AST", "zipfile"],
            "modules": ["CodeAnalyzer", "CodeParser", "ProjectSummary"],
        },
        "output": (
            "The data acquisition phase ingests the project codebase through a secure ZIP "
            "extraction pipeline. The analyzer employs a scoring heuristic that prioritizes "
            "entry points (main.py, app.py), core modules, and test files while excluding "
            "configuration, dependency, and binary assets. Each source file undergoes "
            "language-specific parsing: Python files leverage the built-in ast module for "
            "exact syntactic structure extraction, while JavaScript, TypeScript, and Java "
            "files use regex-based pattern matching for class and function identification. "
            "This multi-language approach ensures broad coverage without external parser "
            "dependencies, maintaining the zero-budget constraint."
        ),
    },
    "methodology_classification": {
        "context": {
            "project_type": "Machine Learning",
            "tech_stack": ["Python", "scikit-learn", "numpy"],
            "algorithms_used": ["RandomForest", "SVM", "KMeans"],
        },
        "output": (
            "The classification module employs a two-stage approach. First, a rule-based "
            "pre-filter categorizes files by language, directory depth, and naming conventions "
            "(e.g., test_*, *config.py). Second, an AST-driven feature extractor computes "
            "structural signatures — import graphs, class hierarchies, function complexity "
            "metrics — which feed a lightweight scikit-learn classifier trained on a curated "
            "dataset of 2,000 labeled files. The RandomForest model achieves 94% accuracy "
            "on held-out data while maintaining sub-millisecond inference latency, "
            "eliminating the need for heavy transformer-based classification."
        ),
    },
    "implementation_core_logic": {
        "context": {
            "project_type": "General Software",
            "tech_stack": ["Python", "python-docx", "lxml"],
            "modules": ["DocumentCompiler", "ReportGenerator", "StyleAnalyzer"],
        },
        "output": (
            "The core logic resides in the DocumentCompiler orchestrator, which sequences "
            "generation according to a fixed academic schema (REPORT_SCHEMA). Each subsection "
            "invokes the ReportGenerator through a prompt chain: planning, drafting, and "
            "polishing stages. The compiler maintains a rolling narrative memory — a condensed "
            "summary of previously generated sections — which is injected into subsequent "
            "prompts to ensure terminological consistency and prevent repetitive openings. "
            "Rate limiting is enforced via a token-bucket algorithm per provider, "
            "with exponential backoff on 429/5xx responses."
        ),
    },
    "results_dataset_overview": {
        "context": {
            "project_type": "Machine Learning",
            "tech_stack": ["Python", "pandas", "scikit-learn"],
            "test_metrics_data": "accuracy: 0.94, precision: 0.91, recall: 0.89, f1: 0.90",
        },
        "output": (
            "The evaluation dataset comprises 2,000 source files across 15 open-source "
            "Python projects, spanning web frameworks, data science libraries, and CLI tools. "
            "Files were manually labeled into seven categories: entry_point, core_logic, "
            "configuration, test, utility, model_definition, and interface. The class "
            "distribution reflects real-world skew: core_logic (35%), utility (25%), "
            "test (20%), configuration (10%), with remaining categories under 5% each. "
            "Stratified 5-fold cross-validation ensures robust performance estimates "
            "across all categories."
        ),
    },
    "conclusions_future_scope": {
        "context": {
            "project_type": "General Software",
            "tech_stack": ["Python", "FastAPI", "Groq API"],
        },
        "output": (
            "This project demonstrates that a deterministic schema combined with "
            "prompt-chained LLM generation can produce structurally sound, factually "
            "grounded academic reports from raw codebases. The architecture achieves "
            "zero-hallucination code extraction through semantic search over AST-derived "
            "snippets, while native Word field construction ensures rendering fidelity "
            "across viewers. Future work includes: (1) expanding language support via "
            "tree-sitter grammars, (2) integrating local embedding models for fully "
            "offline semantic search, (3) adding a web-based refinement interface for "
            "interactive section regeneration, and (4) formalizing the schema as a "
            "versioned specification to enable community-contributed templates."
        ),
    },
}


# ─── Narrative Memory ───
class NarrativeMemory:
    """
    Rolling buffer of previous section summaries to maintain coherence.
    Summarizes each generated section to ~3 bullets via LLM.
    """

    def __init__(self, generator, max_chars: int = 6000):
        self.generator = generator
        self.max_chars = max_chars
        self.buffer = ""
        self.section_summaries = []  # List of (title, summary)

    def add_section(self, section_title: str, content: str):
        """Summarize and store a section."""
        summary = self._summarize(content)
        self.section_summaries.append((section_title, summary))
        self._rebuild_buffer()

    def _summarize(self, content: str) -> str:
        """LLM-based summarization to 3 bullets."""
        if not content or len(content) < 200:
            return content[:200] + "..." if len(content) > 200 else content

        prompt = f"""
        Summarize the following academic section in EXACTLY 3 bullet points.
        Capture: (1) main thesis, (2) key technical details, (3) conclusion/transition.
        No markdown, no extra text. Just 3 lines starting with "- ".

        Content:
        {content[:3000]}
        """
        try:
            result = generate_with_retry(
                self.generator.model,
                prompt,
                max_retries=2,
                base_delay=1,
            )
            # Extract bullet lines
            bullets = re.findall(r"^[-•]\s*(.+)$", result, re.MULTILINE)
            if len(bullets) >= 3:
                return "\n".join(f"- {b}" for b in bullets[:3])
        except Exception:
            pass
        # Fallback: first 3 sentences
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        return "\n".join(f"- {s}" for s in sentences[:3])

    def _rebuild_buffer(self):
        """Rebuild buffer from recent summaries, respecting max_chars."""
        parts = []
        for title, summary in reversed(self.section_summaries):
            part = f"## {title}\n{summary}\n"
            if len("\n".join(parts)) + len(part) > self.max_chars:
                break
            parts.insert(0, part)
        self.buffer = "\n".join(parts)

    def get_context(self) -> str:
        """Get formatted context for prompt injection."""
        if not self.buffer:
            return "No previous sections generated yet."
        return f"PREVIOUS SECTIONS SUMMARY (for coherence — do not repeat content):\n{self.buffer}\n"


# ─── Prompt Chain ───
class PromptChain:
    """
    Three-stage generation: Plan → Draft → Polish.
    Each stage uses a focused prompt with few-shot examples.
    """

    def __init__(self, generator, memory: NarrativeMemory):
        self.gen = generator
        self.memory = memory
        self.client = generator.model  # Groq/DeepSeek client

    def generate_subsection(
        self,
        chapter_title: str,
        subsection_title: str,
        project_summary: Dict,
        user_context: Dict,
    ) -> str:
        """Main entry point: runs full chain and returns final JSON blocks."""

        # 1. PLAN
        outline = self._plan(chapter_title, subsection_title, project_summary, user_context)
        if not outline:
            return self._fallback_json("Planning failed")

        # 2. DRAFT
        draft = self._draft(chapter_title, subsection_title, outline, project_summary, user_context)
        if not draft:
            return self._fallback_json("Drafting failed")

        # 3. POLISH
        polished = self._polish(chapter_title, subsection_title, draft, project_summary, user_context)
        if not polished:
            return self._fallback_json("Polishing failed")

        return polished

    def _plan(
        self,
        chapter: str,
        subsection: str,
        summary: Dict,
        context: Dict,
    ) -> Optional[str]:
        """Stage 1: Generate a structured outline."""

        example = self._get_example(f"{chapter.lower().replace(' ', '_')}_{subsection.lower().replace(' ', '_')}")

        prompt = f"""
        {ACADEMIC_SYSTEM_PROMPT}

        {self.memory.get_context()}

        TASK: Create a detailed outline for the subsection "{subsection}" in chapter "{chapter}".

        PROJECT CONTEXT:
        - Title: {context.get('title')}
        - Problem: {context.get('problem_statement')}
        - Tech Stack: {summary.get('tech_stack', [])}
        - Key Modules: {summary.get('modules', [])[:5]}
        - Algorithms: {summary.get('algorithms_used', [])}

        FEW-SHOT EXAMPLE (style reference only — do not copy content):
        {json.dumps(example, indent=2) if example else "No example available."}

        OUTPUT FORMAT (JSON):
        {{
            "key_points": ["point 1", "point 2", "point 3", "point 4"],
            "technical_terms": ["term1", "term2"],
            "code_snippet_targets": ["function_or_class_name1", "function_or_class_name2"],
            "figure_suggestion": "Description of diagram if relevant, else null",
            "transition_from_previous": "One sentence linking from previous section"
        }}

        CONSTRAINTS:
        - 4-5 key points maximum
        - code_snippet_targets MUST be from valid targets in context (see below)
        - figure_suggestion only for technical chapters (Methodology, Implementation, Results)
        - transition_from_previous should reference previous section by name

        VALID CODE TARGETS: {self._get_valid_targets(context)}
        """
        try:
            result = generate_with_retry(self.client, prompt, max_retries=2, base_delay=1)
            return self._extract_json(result)
        except Exception as e:
            print(f"[PromptChain] Plan failed: {e}")
            return None

    def _draft(
        self,
        chapter: str,
        subsection: str,
        outline: str,
        summary: Dict,
        context: Dict,
    ) -> Optional[str]:
        """Stage 2: Write full content following outline."""

        example = self._get_example(f"{chapter.lower().replace(' ', '_')}_{subsection.lower().replace(' ', '_')}")

        prompt = f"""
        {ACADEMIC_SYSTEM_PROMPT}

        {self.memory.get_context()}

        TASK: Write the FULL academic content for subsection "{subsection}" (chapter: "{chapter}").

        OUTLINE TO FOLLOW:
        {outline}

        PROJECT CONTEXT:
        - Title: {context.get('title')}
        - Problem: {context.get('problem_statement')}
        - Tech Stack: {summary.get('tech_stack', [])}
        - Modules: {summary.get('modules', [])[:5]}
        - Algorithms: {summary.get('algorithms_used', [])}

        FEW-SHOT EXAMPLE (tone/style reference):
        {json.dumps(example, indent=2) if example else "No example available."}

        OUTPUT FORMAT (JSON - STRICT):
        {{
            "blocks": [
                {{"type": "paragraph", "text": "Academic paragraph 1 (150-200 words). No headings."}},
                {{"type": "paragraph", "text": "Academic paragraph 2 (150-200 words)."}},
                {{"type": "code_extraction", "target_name": "exact_function_name_from_valid_targets"}},
                {{"type": "paragraph", "text": "Paragraph explaining the code (100-150 words)."}},
                {{"type": "image_insertion", "filename": "diagram_filename.png"}}
            ]
        }}

        HARD RULES:
        1. NO markdown headings (#, ##). Pure paragraphs only.
        2. NO raw filenames (formatting.py). Use abstract names (The Formatting Engine).
        3. code_extraction targets MUST be from: {self._get_valid_targets(context)}
        4. 2-3 paragraphs + 1-2 code blocks + optional 1 figure per subsection.
        5. Third-person objective. No "we/our".
        6. Total ~350-450 words across paragraphs.
        7. Ground ALL claims in project metadata. No invented metrics.
        """
        try:
            result = generate_with_retry(
                self.client,
                prompt,
                max_retries=2,
                base_delay=1,
                response_format={"type": "json_object"},
            )
            return self._extract_json(result)
        except Exception as e:
            print(f"[PromptChain] Draft failed: {e}")
            return None

    def _polish(
        self,
        chapter: str,
        subsection: str,
        draft_json: str,
        summary: Dict,
        context: Dict,
    ) -> Optional[str]:
        """Stage 3: Polish for academic tone, coherence, constraint compliance."""

        prompt = f"""
        {ACADEMIC_SYSTEM_PROMPT}

        TASK: Polish the following JSON block structure for academic quality.
        Fix: repetitive sentence starters, weak transitions, vague terminology.
        Preserve: all block types, target_names, structure.

        INPUT JSON:
        {draft_json}

        PROJECT CONTEXT:
        - Title: {context.get('title')}
        - Style Guide: {context.get('style_guide', 'Standard academic')[:500]}

        RULES:
        1. Ensure each paragraph opens differently (no 2 starting with "The system" or "This module").
        2. Strengthen technical precision: "handles" → "orchestrates", "uses" → "leverages".
        3. Verify code_extraction targets exist in valid list.
        4. Remove any hallucinated citations, metrics, or author names.
        5. Maintain exact JSON schema: {{"blocks": [...]}}
        6. Do not add/remove blocks — only refine paragraph text.

        OUTPUT: Corrected JSON only.
        """
        try:
            result = generate_with_retry(
                self.client,
                prompt,
                max_retries=2,
                base_delay=1,
                response_format={"type": "json_object"},
            )
            return self._extract_json(result)
        except Exception as e:
            print(f"[PromptChain] Polish failed: {e}")
            return draft_json  # Return draft if polish fails

    def _get_example(self, key: str) -> Optional[Dict]:
        """Retrieve few-shot example by normalized key."""
        return FEW_SHOT_EXAMPLES.get(key)

    def _get_valid_targets(self, context: Dict) -> str:
        """Extract valid code targets from detailed_analysis."""
        analysis = context.get("detailed_analysis")
        if not analysis:
            return "core_logic_functions"
        targets = []
        if hasattr(analysis, "functions"):
            targets.extend([f.name for f in analysis.functions[:30]])
        if hasattr(analysis, "classes"):
            targets.extend([c.name for c in analysis.classes[:20]])
        return ", ".join(targets[:50]) if targets else "core_logic_functions"

    def _extract_json(self, text: str) -> Optional[str]:
        """Robust JSON extraction from LLM response."""
        text = text.strip()
        # Try direct parse
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        # Try markdown code block
        for fence in ["```json", "```"]:
            if fence in text:
                parts = text.split(fence)
                if len(parts) >= 2:
                    candidate = parts[1].split("```")[0].strip()
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        pass
        # Try regex find
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                json.loads(match.group(0))
                return match.group(0)
            except json.JSONDecodeError:
                pass
        return None

    def _fallback_json(self, reason: str) -> str:
        """Minimal valid JSON on failure."""
        return json.dumps({
            "blocks": [{
                "type": "paragraph",
                "text": f"Content generation encountered an issue: {reason}. This section requires manual review."
            }]
        })


# ─── Integration Helper ───
def create_prompt_chain(generator) -> PromptChain:
    """Factory to create PromptChain with shared NarrativeMemory."""
    memory = NarrativeMemory(generator)
    return PromptChain(generator, memory)