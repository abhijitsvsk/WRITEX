import json
import io
import docx
from src.core.compiler import DocumentCompiler
from src.validation.validator import DocumentValidator
from src.file_formatting.formatting import generate_report

class MockSummary:
    def __init__(self):
        self.test_files = []
        self.detailed_analysis = {}
    def to_json(self):
        return json.dumps({"project_type": "Web App", "tech_stack": "Python"})

context = {
    "title": "Pipeline Test",
    "team_names_raw": ["Alice", "Bob"],
    "degree": "B.Tech",
    "department": "CSE",
    "university": "TU",
    "academic_year": "2026",
    "objectives": "Testing"
}

summary = MockSummary()

# Instead of letting it hit the API, mock the entire `generate_subsection_body`
compiler = DocumentCompiler(api_key="mock")

def mock_gen_body(chapter, sub, sum_str, ctx):
    return f"This is {chapter} - {sub}. [Figure 1.1: Test Architecture]"
compiler.generator.generate_subsection_body = mock_gen_body
compiler.generator.generate_section = lambda sec, sum_str, ctx: f"Fake abstract."

full_structure = compiler.compile_structure(context, summary)

print("--- Pre-Validation Structure (TOC/LOF) ---")
for item in full_structure:
    if item['type'] in ['toc', 'lof', 'section_header']:
        print(f"  {item['type']}: {item['text']}")

validator = DocumentValidator()
healed = validator.validate_and_heal(full_structure)

print("--- Post-Validation Structure (TOC/LOF) ---")
for item in healed:
    if item['type'] in ['toc', 'lof', 'section_header']:
        print(f"  {item['type']}: {item['text']}")

buf = io.BytesIO()
generate_report(healed, buf)
buf.seek(0)
with open('d:/writex/streamlit_test_output.docx', 'wb') as f:
    f.write(buf.read())

print("Pipeline execution complete. Checking DOCX...")
doc = docx.Document('d:/writex/streamlit_test_output.docx')
import zipfile
z = zipfile.ZipFile('d:/writex/streamlit_test_output.docx')
txt = z.read('word/document.xml').decode('utf-8')
print("TOC SDT:", "Table of Contents" in txt)
print("LOF SDT:", "Table of Figures" in txt)
print("Captions:", [p.text for p in doc.paragraphs if p.style.name == "Caption"])
