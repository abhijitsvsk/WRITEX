
import sys
import os
from pathlib import Path
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.analysis.code_analyzer import CodeAnalyzer
from src.analysis.project_summary import ProjectSummary
from src.ai.report_generator import ReportGenerator

def test_code_extraction():
    print("Testing Code Extraction...")
    
    # Create dummy python file
    dummy_code = """
import os

class DataProcessor:
    def process(self):
        pass

def main():
    print("Hello")
"""
    with open("temp_dummy.py", "w") as f:
        f.write(dummy_code)
        
    try:
        analyzer = CodeAnalyzer()
        summary = ProjectSummary()
        analyzer._analyze_python_ast(dummy_code, "temp_dummy.py", summary)
        
        print("Modules Extracted:", summary.modules)
        
        assert len(summary.modules) > 0
        assert "DataProcessor" in summary.modules[0]
        assert "main" in summary.modules[0]
        print("PASS: Code Extraction")
        
        return summary
    finally:
        if os.path.exists("temp_dummy.py"):
            os.remove("temp_dummy.py")

def test_report_generator(summary):
    print("\nTesting Report Generator...")
    
    # Mock API key
    os.environ["GEMINI_API_KEY"] = "fake_key"
    try:
        generator = ReportGenerator(api_key="fake_key")
    except:
        print("Skipping generator init check (needs valid key struct usually, but let's try)")
        return

    # User Context
    user_context = {
        "title": "Test Project",
        "student_name": "Test Student",
        "degree": "B.Tech",
        "guide_name": "Dr. Guide",
        "hod_name": "Dr. HOD"
    }
    
    # Test 1: Certificate (Strict)
    cert = generator.generate_section("Certificate", summary.to_json(), user_context)
    print("\nCertificate Output:\n", cert)
    assert "CERTIFICATE" in cert
    assert "Test Student" in cert
    assert "Test Project" in cert
    assert "LLM" not in cert # Should not call LLM
    print("PASS: Certificate Strict Mode")
    
    # Test 2: Methodology Prompt (Enriched)
    prompt = generator._build_prompt("Methodology", summary.to_json(), user_context)
    print("\nMethodology Prompt Snippet:\n", prompt[-500:])
    assert "DataProcessor" in prompt or "temp_dummy.py" in prompt
    print("PASS: Methodology Prompt Enrichment")

if __name__ == "__main__":
    summary = test_code_extraction()
    test_report_generator(summary)
