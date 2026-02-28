import json
import re
import base64
import zlib
import requests
import time
import concurrent.futures
from typing import Dict, Any, List
from src.ai.report_generator import ReportGenerator

# Centralized Deterministic Schema — Mirrors the sample report structure exactly
# Subsections can be strings (simple) or dicts with "title" and "subsubsections" keys
# SCHEMA_VERSION: 1.0.0 (Production Locked)
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
            {"title": "Classification", "figure": "Classification Process Workflow"},
            "Verification and Prioritization",
            "Visualization and Reporting",
            {
                "title": "Workflow Summary",
                "subsubsections": [
                    "Initialization and Setup",
                    "User Configuration and Data Filtering",
                    {"title": "Simulation Loop (Core Processing)", "figure": "Core Processing Architecture"},
                    {"title": "User Actions and Response", "figure": "User Interaction Interface"},
                    "Final Output",
                ],
            },
        ],
    },
    {
        "title": "Implementation",
        "subsections": [
            "Tools and Technologies",
            {"title": "Core Logic Implementation", "figure": "Core Logic Flowchart"},
            {"title": "Key Modules and Functions", "figure": "Module Interdependency Diagram"},
            {"title": "Code Structure", "figure": "Codebase Architecture"},
        ],
    },
    {
        "title": "Results and Discussion",
        "subsections": [
            "Dataset Overview", 
            {"title": "Experimental Output and Analysis", "figure": "Performance Metrics Graph"}
        ],
    },
    {
        "title": "Conclusions and Future Scope",
        "subsections": ["Conclusion", "Future Enhancements"],
    },
]

class DocumentCompiler:
    """
    The Core Orchestrator.
    Strictly separates UI states from structure execution.
    Handles the mathematical generation loop, LLM fetching, and native code extraction.
    """

    def __init__(self, api_key: str):
        self.generator = ReportGenerator(api_key=api_key)

    def compile_structure(
        self, context: Dict[str, Any], summary: Any, progress_callback=None
    ) -> List[Dict]:
        """
        Executes the content generation phase. Returns the pre-validation structure array.
        """
        full_structure = []

        # 1. Title Page
        full_structure.append(
            {"type": "title", "text": str(context.get("title", "Writex")).upper()}
        )
        # 2. Dynamic Title Page
        team_str = ", ".join(
            [
                str(n).strip()
                for n in (context.get("team_names_raw") or [])
                if str(n).strip()
            ]
        )
        if not team_str:
            team_str = "[Author Names]"

        degree = context.get("degree", "B.Tech Computer Science")
        dept = context.get(
            "department", "Department of Computer Science and Engineering"
        )
        univ = context.get("university", "My University")
        year = context.get("academic_year", "2025–2026")

        title_page_text = (
            f"Submitted in partial fulfillment of the requirements for the\n"
            f"award of the degree of\n"
            f"{degree}\n"
            f"in\n"
            f"{dept}\n\n"
            f"By\n"
            f"{team_str}\n\n"
            f"Under the guidance of\n"
            f"{context.get('guide', '[Guide Name]')}\n\n"
            f"{dept}\n"
            f"{univ}\n"  # Parent University / Location placeholder
            f"Location, {year}"
        )
        full_structure.append({"type": "title_page_body", "text": title_page_text})

        # 2. Certificate & Acknowledgement
        for section in ["Certificate", "Acknowledgement"]:
            full_structure.append({"type": "section_header", "text": section.upper()})
            template_text = self.generator.fill_template(section, context)
            full_structure.append({"type": "paragraph", "text": template_text})

            if section == "Certificate":
                # Add signature block for Certificate (invokes the layout engine formatter)
                full_structure.append(
                    {
                        "type": "signature_block",
                        "guide": context.get("guide"),
                        "guide_designation": context.get(
                            "guide_designation", "Assistant Professor"
                        ),
                        "hod": context.get("hod"),
                        "hod_designation": context.get(
                            "hod_designation", "Professor & HoD"
                        ),
                        "department": context.get("department"),
                    }
                )
            elif section == "Acknowledgement":
                # Add student names signature at bottom
                raw_list = context.get("team_names_raw") or []
                clean_list = [
                    str(name).strip() for name in raw_list if name and str(name).strip()
                ]
                if clean_list:
                    sig_block = "\n\n" + "\n".join(clean_list)
                    full_structure.append({"type": "paragraph", "text": sig_block})

        # 3. Dynamic Front Matter
        full_structure.extend(
            [
                {"type": "section_header", "text": "Abstract"},
                {
                    "type": "paragraph",
                    "text": self.generator.generate_section(
                        "Abstract", summary.to_json(), context
                    ),
                },
                {"type": "section_header", "text": "List of Figures"},
                {"type": "lof", "text": "List of Figures"},
                {"type": "section_header", "text": "Contents"},
                {"type": "toc", "text": "Contents"},
            ]
        )

        # 4. Core Chapters
        def _count_total_steps(schema):
            total = 0
            for c in schema:
                for sub in c.get("subsections", []):
                    total += 1  # The parent subsection
                    if isinstance(sub, dict) and "subsubsections" in sub:
                        total += len(sub.get("subsubsections", []))
            return total

        total_steps = _count_total_steps(REPORT_SCHEMA)
        current_step = 0
        expected_figures_count = 0

        # Reverted ThreadPoolExecutor due to strict API limits triggering undocumented silent truncations in LLM.
        # Ensure sequential generation and avoid burst rate limit spikes by adding throttle delays.
        for chapter_idx, chapter in enumerate(REPORT_SCHEMA):
            full_structure.append({"type": "chapter", "text": chapter["title"]})
            
            if progress_callback:
                progress_callback(
                    min(0.10 + (current_step / total_steps) * 0.85, 0.95),
                    f"Generating {chapter['title']}...",
                )

            if chapter.get("subsections"):
                sub_titles = [
                    sub["title"] if isinstance(sub, dict) else sub
                    for sub in chapter["subsections"]
                ]
                intro_text = self.generator.generate_chapter_intro(
                    chapter["title"],
                    sub_titles,
                    summary.to_json(),
                    context,
                )
                full_structure.append({"type": "paragraph", "text": intro_text})
                time.sleep(1.0) # Throttle guard to prevent API bursts

            for sub in chapter.get("subsections", []):
                sub_title = sub["title"] if isinstance(sub, dict) else sub
                
                body_text = self.generator.generate_subsection_body(
                    chapter["title"],
                    sub_title,
                    summary.to_json(),
                    context,
                )
                full_structure.append({"type": "subheading", "text": sub_title})
                full_structure.extend(
                    self._parse_body_blocks(body_text, chapter["title"], context)
                )
                
                if isinstance(sub, dict) and "figure" in sub:
                    expected_figures_count += 1
                    full_structure.append(
                        {"type": "paragraph", "text": f"[Figure {chapter_idx+1}.X: {sub['figure']}]"}
                    )
                time.sleep(1.0)

                current_step += 1
                if progress_callback:
                    progress_callback(
                        min(0.10 + (current_step / total_steps) * 0.85, 0.95),
                        f"Generating {chapter['title']} > {sub_title}...",
                    )
                
                if isinstance(sub, dict) and "subsubsections" in sub:
                    # Generate sub-subsections
                    for subsub in sub.get("subsubsections", []):
                        subsub_title = subsub["title"] if isinstance(subsub, dict) else subsub
                        subsub_key = f"{sub_title} - {subsub_title}"
                        body_sub_text = self.generator.generate_subsection_body(
                            chapter["title"],
                            subsub_key,
                            summary.to_json(),
                            context,
                        )
                        full_structure.append(
                            {"type": "subsubheading", "text": subsub_title}
                        )
                        full_structure.extend(
                            self._parse_body_blocks(
                                body_sub_text, chapter["title"], context
                            )
                        )
                        
                        if isinstance(subsub, dict) and "figure" in subsub:
                            expected_figures_count += 1
                            full_structure.append(
                                {"type": "paragraph", "text": f"[Figure {chapter_idx+1}.X: {subsub['figure']}]"}
                            )
                        time.sleep(1.0)

                        current_step += 1
                        if progress_callback:
                            progress_callback(
                                min(0.10 + (current_step / total_steps) * 0.85, 0.95),
                                f"Generating {chapter['title']} > {sub_title} > {subsub_title}...",
                            )

        # 5. References
        full_structure.append({"type": "section_header", "text": "REFERENCES"})
        ref_text = self._generate_factual_references(context, summary)
        full_structure.append({"type": "paragraph", "text": ref_text})

        # 6. Post-Reference Institutional Sections (per Sample Parity)
        institutions = [
            "Mission and Vision",
            "Program Educational Objectives (PEO)",
            "Program Outcomes (PO)",
            "Program Specific Outcomes (PSO)",
            "Course Outcomes (CO)",
        ]
        for section in institutions:
            full_structure.append({"type": "institutional_header", "text": section})
            body_text = self.generator.generate_subsection_body(
                "Institutional Requirements",
                section,
                summary.to_json(),
                context,
            )
            full_structure.extend(
                self._parse_body_blocks(
                    body_text, "Institutional Requirements", context
                )
            )
            time.sleep(1.0) # Throttle guard

            # Minor progress bump
            if progress_callback:
                progress_callback(0.97, f"Formatting {section}...")

        # 7. AST Integrity Guard Check
        self._validate_AST(full_structure, expected_figures_count)

        return full_structure

    def _validate_AST(self, full_structure: List[Dict], expected_figures_count: int):
        """
        Validates the generated AST blocks to prevent silent document corruption before rendering to Word.
        """
        chapters = 0
        figures = 0
        major_sections = 0
        subsections = 0
        
        for block in full_structure:
            text = block.get("text", "")
            lower_text = text.lower()
            
            # Check for API errors or empty failures
            if "error code:" in lower_text or "rate limit reached" in lower_text or "rror generating" in lower_text:
                raise RuntimeError(f"InternalGenerationError: Rate limit payload leaked into document body: {text[:100]}")
            
            # Basic block counting
            if block.get("type") == "chapter":
                chapters += 1
            if block.get("type") == "section_header":
                major_sections += 1
            if block.get("type") in ["subheading", "subsubheading"]:
                subsections += 1
            if block.get("type") == "paragraph" and ("[figure" in lower_text or "figure" in lower_text) and "]" in text:
                figures += 1
                
        if chapters < 5:
            raise RuntimeError(f"InternalGenerationError: Expected >= 5 Chapters, got {chapters}. AST Truncated.")
            
        # 32 subsections expected from REPORT_SCHEMA
        expected_subsection_count = 32
        if subsections < expected_subsection_count:
            raise RuntimeError(f"InternalGenerationError: Expected >= {expected_subsection_count} Subsections, got {subsections}. AST Truncated.")
            
        if figures < expected_figures_count:
            raise RuntimeError(f"InternalGenerationError: Expected >= {expected_figures_count} Figures, got {figures}. Semantic Output Degraded.")
            
        print(f"AST Validation Passed: Chapters={chapters}, Subsections={subsections}, Placeholders~={figures}, Sections={major_sections}")

    def _parse_body_blocks(
        self, body_text: str, chapter_title: str, context: Dict
    ) -> List[Dict]:
        """
        Splits the LLM output into logical blocks.
        Preserves [Figure X: Caption] tags as paragraphs which will later be formatted
        into proper captioned text placeholders by the formatting engine.
        """
        sub_structure = []

        # Scan for [Figure X: Caption] tags
        figure_pattern = re.compile(
            r"\[Figure\s*[\d\.]*[:\-]?\s*(.*?)\]", re.IGNORECASE
        )
        lines = body_text.split("\n")
        
        # Security: Strip Hallucinated Markdown Headers
        # If the LLM leaked `# Title` into the generic body text, regex strip the formatting to prevent document corruption.
        lines = [re.sub(r"^#+\s*", "", line) for line in lines]
        
        collected_text = []

        for line in lines:
            fig_match = figure_pattern.search(line)
            if fig_match:
                # Security: The LLM is explicitly banned from generating figure tags.
                # If it hallucinated one anyway, we silently drop the line to enforce 100% backend control.
                if collected_text:
                    joined = "\n".join(collected_text).strip()
                    if joined:
                        sub_structure.extend(
                            self._process_code_extraction(
                                joined, chapter_title, context
                            )
                        )
                    collected_text = []
                continue
            else:
                collected_text.append(line)

        # Flush remaining text
        if collected_text:
            joined = "\n".join(collected_text).strip()
            if joined:
                sub_structure.extend(
                    self._process_code_extraction(joined, chapter_title, context)
                )

        return sub_structure

    def _process_code_extraction(
        self, body_text: str, chapter_title: str, context: Dict
    ) -> List[Dict]:
        """
        Intercepts [Extract Code: X] tags generated by the LLM and swaps them out with
        the unformatted raw string code natively derived from the CodeAnalyzer AST.

        CRITICAL: Only permits code extraction in Chapter 4 (Implementation).
        All other chapters will render the tag as standard paragraph text to prevent code leakage.
        """
        sub_structure = []
        if "[Extract Code" not in body_text:
            sub_structure.append({"type": "paragraph", "text": body_text})
            return sub_structure

        for line in body_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            code_match = re.search(r"\[Extract Code:\s*(.*?)\]", line, re.IGNORECASE)
            if code_match and "Implementation" in chapter_title:
                target_name = code_match.group(1).strip()
                extracted = False
                analysis_data = context.get("detailed_analysis")

                if analysis_data and hasattr(analysis_data, "code_snippets"):
                    for file_path, snippets in analysis_data.code_snippets.items():
                        for snippet_tuple in snippets:
                            if len(snippet_tuple) == 3:
                                code_str = snippet_tuple[2]
                                if (
                                    f"def {target_name}" in code_str
                                    or f"class {target_name}" in code_str
                                    or target_name in code_str
                                ):
                                    sub_structure.append(
                                        {
                                            "type": "paragraph",
                                            "text": f"The implementation of {target_name} is shown below:",
                                        }
                                    )
                                    sub_structure.append(
                                        {"type": "code_block", "text": code_str}
                                    )
                                    extracted = True
                                    break
                        if extracted:
                            break

                if not extracted:
                    sub_structure.append(
                        {
                            "type": "paragraph",
                            "text": f"[Error: Code for {target_name} could not be extracted dynamically from the project zip.]",
                        }
                    )
            else:
                sub_structure.append({"type": "paragraph", "text": line})

        return sub_structure

    def _generate_factual_references(self, context: Dict, summary: Any) -> str:
        """Isolated strict reference generation loop."""
        ref_prompt = (
            f"Generate a formal 'References' section for this project.\n"
            f"STRICT RULES:\n"
            f"1. DO NOT hallucinate textbooks, random academic papers, or fake URLs.\n"
            f"2. ONLY create citation entries for the actual tech stack, libraries, and frameworks listed here: {context.get('tech_stack', summary.to_json())}\n"
            f"3. Format them formally (e.g., '[1] Python Software Foundation, \"Python Language Reference\", version 3.x...').\n"
            f"4. If there is NO tech stack data available, simply return '[1] Project Source Code and Internal Documentation.'\n"
            f"5. Do NOT include any markdown headers or intro text. Just the numbered list."
        )
        try:
            res = (
                self.generator.model.chat.completions.create(
                    model=self.generator.model_name,
                    messages=[{"role": "user", "content": ref_prompt}],
                )
                .choices[0]
                .message.content.strip()
            )
            return res
        except:
            return "[1] Project Source Code and internal libraries."
