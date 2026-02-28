import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

from src.analysis.code_analyzer import CodeAnalyzer
from src.analysis.style_analyzer import StyleAnalyzer
from src.ai.report_generator import ReportGenerator
from src.core.compiler import DocumentCompiler
from src.file_formatting.formatting import generate_report
from src.ai.utils import telemetry_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== STARTING E2E PRODUCTION SIMULATION ===")
    
    # 1. Zip Extraction
    print("1. Analyzing demo.zip...")
    analyzer = CodeAnalyzer()
    summary = analyzer.analyze_zip("demo.zip")
    print(f"   Total Files Processed: {summary.total_files}")
    
    # 2. Sample Extraction
    print("2. Extracting SAMPLE REPORT FOR REFERENCE.pdf...")
    sa = StyleAnalyzer(api_key=api_key)
    with open("SAMPLE REPORT FOR REFERENCE.pdf", "rb") as f:
        raw_text = sa.extract_text(f, "pdf")
        f.seek(0)
        style_guide = sa.analyze_style(raw_text)
        f.seek(0)
        sample_sections = sa.extract_specific_sections(f, "pdf")
        
    gen = ReportGenerator(api_key=api_key)
    sample_metadata = gen.extract_metadata_from_sample(raw_text)
    
    # 3. Context Merging
    print("3. Defining Production Context...")
    base_context = gen.derive_project_context(summary.to_json())
    context = {
        "title": sample_metadata.get("title", "Test Automation System"),
        "student_name": "Prod User",
        "team_names_raw": ["Prod User", "Another User"],
        "degree": "B.Tech Computer Science",
        "principal": sample_metadata.get("principal", "Dr. Principal"),
        "guide": sample_metadata.get("guide", "Dr. Guide"),
        "hod": sample_metadata.get("hod", "Dr. HOD"),
        "guide_designation": "Assistant Professor",
        "hod_designation": "Professor & HOD",
        "university": "State University",
        "department": "Computer Science",
        "academic_year": "2025-2026",
        "pronoun_mode": "plural",
        "problem_statement": base_context["problem_statement"],
        "style_guide": style_guide,
        "sample_report_provided": True,
        "sample_sections": sample_sections,
        "has_test_files": len(summary.test_files) > 0,
        "test_metrics_data": "",
        "detailed_analysis": summary.detailed_analysis,
    }
    
    print("4. Compiling AST Structure...")
    compiler = DocumentCompiler(api_key=api_key)
    
    def log_progress(ratio, msg):
        print(f"[{ratio*100:05.1f}%] {msg}")
        
    try:
        full_structure = compiler.compile_structure(
            context, summary, progress_callback=log_progress
        )
    except Exception as e:
        print(f"\n[!] GENERATION HALTED BY VALIDATION GUARD: {e}")
        print("\n=== METRICS ===")
        print(json.dumps(telemetry_data, indent=2))
        sys.exit(1)
        
    print("5. Rendering DOCX via python-docx...")
    output_path = "E2E_Prod_Output.docx"
    generate_report(full_structure, output_path, style_name="Standard")
    
    print("\n=== E2E METRICS ===")
    print(json.dumps(telemetry_data, indent=2))
    
    print(f"\nSUCCESS: Document generated at {output_path}")

if __name__ == "__main__":
    main()
