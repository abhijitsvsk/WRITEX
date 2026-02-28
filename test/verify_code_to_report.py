
import os
import sys
import zipfile
import tempfile
import json
from pathlib import Path
from dotenv import load_dotenv

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
load_dotenv()

from src.analysis.code_analyzer import CodeAnalyzer
from src.ai.report_generator import ReportGenerator

def create_dummy_zip(filename):
    with zipfile.ZipFile(filename, 'w') as zf:
        zf.writestr('main.py', 'import numpy as np\nprint("Hello")')
        zf.writestr('README.md', '# Demo Project')
    return filename

def test_structure_lock_flow():
    print("Testing Structure Lock Flow...")
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        zip_path = create_dummy_zip(tmp.name)
        
    try:
        # 1. Analyze
        analyzer = CodeAnalyzer()
        summary = analyzer.analyze_zip(zip_path)
        print(f"Analysis: {summary.project_type}")
        
        # 2. Generator
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key: return
        
        gen = ReportGenerator(api_key)
        context = {"title": "Test", "problem_statement": "Problem", "objectives": "Obj"}
        
        # 3. Test Subsection Generation (Body Only)
        print("Generating Body for 'Result Analysis'...")
        body = gen.generate_subsection_body("Results", "Result Analysis", summary.to_json(), context)
        
        print("\n--- BODY PREVIEW ---")
        print(body[:300])
        print("--------------------")
        
        # Validation
        if "#" in body or "##" in body:
            print("FAILURE: Body contains markdown headings!")
            raise ValueError("Headings detected in body text")
            
        print("SUCCESS: Body text generated without headings.")
        
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(zip_path): os.remove(zip_path)

if __name__ == "__main__":
    test_structure_lock_flow()
