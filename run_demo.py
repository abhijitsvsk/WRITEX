import os
import io
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

from src.analysis.code_analyzer import CodeAnalyzer
from src.analysis.style_analyzer import StyleAnalyzer
from src.ai.report_generator import ReportGenerator
from src.file_formatting.formatting import generate_report
from src.app import REPORT_SCHEMA

print("Analyzing Codebase (demo.zip)...")
analyzer = CodeAnalyzer()
summary = analyzer.analyze_zip("demo.zip")

print("Checking Sample Report...")
sample_path = "d:/writex/SAMPLE REPORT FOR REFERENCE.pdf"
sa = StyleAnalyzer(api_key=api_key)
raw_text = sa.extract_text(sample_path, "pdf")
style_guide = sa.analyze_style(raw_text)
sample_sections = sa.extract_specific_sections(sample_path, "pdf")

gen = ReportGenerator(api_key)
sample_metadata = gen.extract_metadata_from_sample(raw_text)

context = gen.derive_project_context(summary.to_json())

# Names from sample or default
final_names = ""
if sample_metadata.get("team_names"):
    if isinstance(sample_metadata["team_names"], list):
        final_names = "\n".join(sample_metadata["team_names"])
    else:
        final_names = str(sample_metadata["team_names"])

if not final_names: final_names = "Alice\nBob\nCharlie"

name_count = len([n for n in final_names.split('\n') if n.strip()])
pronoun_mode = "singular" if name_count <= 1 else "plural"

context.update({
    "title": sample_metadata.get("title", "Test Automation System"), 
    "student_name": final_names, 
    "degree": sample_metadata.get("degree", "B.Tech"), 
    "principal": sample_metadata.get("principal", ""),
    "guide": sample_metadata.get("guide", "Dr. Guide"),
    "hod": sample_metadata.get("hod", "Dr. HOD"),
    "university": sample_metadata.get("university", "Test University"),
    "department": sample_metadata.get("department", "CSE"),
    "academic_year": sample_metadata.get("academic_year", "2026"),
    "pronoun_mode": pronoun_mode,
    "problem_statement": context["problem_statement"],
    "style_guide": style_guide,
    "sample_sections": sample_sections,
    "has_test_files": len(summary.test_files) > 0,
    "test_metrics_data": "Epoch,Accuracy,Loss\n1,0.85,0.30\n2,0.92,0.15\n3,0.95,0.08\nOverall Accuracy: 95%\nF1-Score: 0.94",
    "detailed_analysis": summary.detailed_analysis
})

print("Metadata extracted: ", {k:v for k,v in context.items() if isinstance(v, str) and len(v) < 100})

from src.core.compiler import DocumentCompiler
compiler = DocumentCompiler(api_key=api_key)

full_structure = []

# Front Matter
full_structure.append({"type": "title", "text": context.get("title")})
full_structure.append({"type": "paragraph", "text": f"Submitted by\n{context.get('student_name')}"})
full_structure.append({"type": "page_break", "text": ""})

# Certificate
full_structure.append({"type": "title", "text": "CERTIFICATE"}) 
cert_text = gen.fill_template("Certificate", context)
full_structure.append({"type": "paragraph", "text": cert_text})
full_structure.append({"type": "signature_block", "guide": context.get("guide"), "hod": context.get("hod"), "department": context.get("department")})
full_structure.append({"type": "page_break", "text": ""})

# Acknowledgement
full_structure.append({"type": "title", "text": "ACKNOWLEDGEMENT"})
ack_text = gen.fill_template("Acknowledgement", context)
full_structure.append({"type": "paragraph", "text": ack_text})

# TOC
full_structure.append({"type": "toc", "text": "Table of Contents", "schema": REPORT_SCHEMA})

# LOF
full_structure.append({"type": "lof", "text": "List of Figures"})

# Chapter
for chapter_idx, chapter in enumerate([REPORT_SCHEMA[0], REPORT_SCHEMA[4]]):  # Intro and Results
    full_structure.append({"type": "chapter", "text": chapter["title"]})
    for sub_title in chapter["subsections"][:2]: # 2 short subsections
        title_str = sub_title if isinstance(sub_title, str) else sub_title["title"]
        print(f"Generating {title_str}...")
        body_text = gen.generate_subsection_body(chapter["title"], title_str, summary.to_json(), context)
        full_structure.append({"type": "subheading", "text": title_str})
        full_structure.extend(compiler._parse_body_blocks(body_text, chapter["title"], context))

generate_report(full_structure, "demo_test_report.docx", style_name="Standard")
print("Done! Saved as demo_test_report.docx")
