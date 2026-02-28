import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from src.ai.report_generator import ReportGenerator
from src.analysis.style_analyzer import StyleAnalyzer
from src.file_formatting.formatting import generate_report
import os
import json


def main():
    print("Starting Deep Style Report Generation...")

    # Configuration
    API_KEY = os.getenv("GROQ_API_KEY")
    SAMPLE_REPORT_PATH = (
        "d:/writex/test.docx"  # extracted from previous main.py context
    )
    OUTPUT_REPORT_PATH = "d:/writex/final_report.docx"

    # Mock Project Summary
    project_summary = {
        "project_type": "AI Automation",
        "tech_stack": ["Python", "Groq API", "python-docx"],
        "modules": ["ReportGenerator", "StyleAnalyzer", "Formatter"],
        "workflow": "Analyze -> Generate -> Format",
    }

    # 1. Image/Visual Analysis
    print(f"Analyzing visual style from {SAMPLE_REPORT_PATH}...")
    analyzer = StyleAnalyzer()

    # Check if sample exists, if not create a dummy one for testing
    if not os.path.exists(SAMPLE_REPORT_PATH):
        print("Sample report not found. Creating a dummy sample...")
        from docx import Document

        doc = Document()
        doc.add_paragraph("This is a sample text in Ariel.", style=None)
        doc.save(SAMPLE_REPORT_PATH)

    visual_style = analyzer.analyze_visual_style(SAMPLE_REPORT_PATH)
    print(f"Detected Visual Style: {visual_style}")

    # 2. Text/Tone Analysis
    text_content = analyzer.extract_text(SAMPLE_REPORT_PATH, "docx")
    style_guide = analyzer.analyze_style(text_content)
    print("Style Guide Prompt Generated.")

    # 3. Content Generation
    print("Generating content...")
    # Mocking API key if not present for test
    if not API_KEY:
        print("WARNING: GROQ_API_KEY not found. Using mock generation.")
        generated_content = {
            "Introduction": "This is a generated introduction following the deep style.",
            "Methodology": "The methodology was rigorous and automated.",
        }
    else:
        generator = ReportGenerator(api_key=API_KEY)
        user_context = {
            "title": "Deep Style Automation",
            "problem_statement": "Manual reporting is inconsistent.",
            "objectives": "Automate styling.",
            "style_guide": style_guide,
        }

        # simplified generation for demo
        generated_content = {}
        for section in ["Introduction", "Methodology"]:
            generated_content[section] = generator.generate_section(
                section, project_summary, user_context
            )

    # 4. Formatting & Assembly
    print("Formatting document...")
    structure = []
    structure.append({"type": "title", "text": "Deep Style Automated Report"})

    for section, content in generated_content.items():
        structure.append({"type": "heading", "text": section})
        structure.append({"type": "paragraph", "text": content})

    # Apply Visual Styles
    generate_report(
        structure,
        OUTPUT_REPORT_PATH,
        style_name="Standard",  # Base style
        custom_font=visual_style.get("font_name"),
        custom_size=visual_style.get("font_size"),
        custom_spacing=visual_style.get("line_spacing"),
    )

    print(f"Report generated at: {OUTPUT_REPORT_PATH}")


if __name__ == "__main__":
    main()
