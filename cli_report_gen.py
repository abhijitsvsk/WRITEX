import sys
import os
from pathlib import Path

# Setup path
root_path = Path(__file__).parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from src.ai.report_generator import ReportGenerator
from src.file_formatting.formatting import generate_report
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

def main():
    print("Generating Manual Report...")
    
    # Mock Context with "User Input"
    context = {
        "title": "Blast Automation System",
        "degree": "B.Tech Computer Science",
        "student_name": "Alice Smith\nBob Jones\nCharlie Brown", # Multi-line names
        "guide": "Prof. Dumbledore",
        "hod": "Dr. McGonagall",
        "principal": "Rev. Snyder",
        "university": "Hogwarts University",
        "department": "Department of Magic",
        "pronoun_mode": "plural",
        "style_guide": "Standard",
        "problem_statement": "Manual reporting is tedious.",
        "objectives": "- Automate reports\n- Save time"
    }
    
    gen = ReportGenerator(api_key=api_key)
    
    full_structure = []
    
    # 1. Title
    full_structure.append({"type": "title", "text": context["title"]})
    
    # 2. Acknowledgement (The Key Test)
    print("Generating Acknowledgement...")
    ack_text = gen.fill_template("Acknowledgement", context)
    full_structure.append({"type": "title", "text": "ACKNOWLEDGEMENT"})
    full_structure.append({"type": "paragraph", "text": ack_text})
    
    # 3. Save
    output_path = "d:/writex/manual_report.docx"
    generate_report(full_structure, output_path)
    print(f"Report saved to {output_path}")

if __name__ == "__main__":
    main()
