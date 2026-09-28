import io
import json
import zipfile
import docx
import pytest

from src.core.compiler import DocumentCompiler
from src.validation.validator import DocumentValidator
from src.file_formatting.formatting import generate_report

class MockSummary:
    def __init__(self):
        self.test_files = []
        self.detailed_analysis = {}
        self.tech_stack = "Python, FastAPI, Next.js"
    def to_json(self):
        return json.dumps({"project_type": "Web App", "tech_stack": self.tech_stack})

def test_deterministic_academic_pipeline():
    context = {
        "title": "Pipeline Integration Report",
        "team_names_raw": ["Alice Smith", "Bob Jones"],
        "degree": "B.Tech Computer Science",
        "department": "Department of Computer Science and Engineering",
        "university": "State Technical University",
        "academic_year": "2025–2026",
        "objectives": "- Comprehensive pipeline test.",
        "guide": "Dr. Advisor",
        "hod": "Dr. Dept Head",
        "guide_designation": "Associate Professor",
        "hod_designation": "Professor & HoD",
        "pronoun_mode": "plural",
    }
    summary = MockSummary()

    compiler = DocumentCompiler(api_key="mock_deterministic_key")
    from src.ai.rate_limiter import TokenBucketLimiter
    compiler.rate_limiter = TokenBucketLimiter(capacity=1000.0, refill_rate_per_sec=1000.0)

    # Mock all AI generation calls deterministically
    compiler.generator.generate_chapter_intro = lambda ch, subs, sum_str, ctx: (
        f"This chapter introduces {ch} covering {', '.join(subs)}."
    )
    compiler.generator.generate_subsection_body = lambda ch, sub, sum_str, ctx: (
        f"Detailed academic discussion for {ch} - {sub}. "
        "The architecture demonstrates robust separation of concerns."
    )
    compiler.generator.generate_section = lambda sec, sum_str, ctx: (
        f"This abstract provides an overview of the {context['title']} project."
    )

    # 1. Compile structure
    full_structure = compiler.compile_structure(context, summary)
    assert len(full_structure) > 20

    types = [item["type"] for item in full_structure]
    assert "title" in types
    assert "chapter" in types
    assert "toc" in types
    assert "lof" in types

    # 2. Validate and heal
    validator = DocumentValidator()
    healed = validator.validate_and_heal(full_structure)
    assert len(healed) >= len(full_structure)

    # 3. Generate DOCX in memory
    buf = io.BytesIO()
    generate_report(healed, buf, style_name="Academic")
    buf.seek(0)

    # 4. Verify DOCX document integrity
    doc = docx.Document(buf)
    assert len(doc.paragraphs) > 10

    # Verify that headings exist
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert len(headings) > 0

    # Verify zip XML contains Word elements
    buf.seek(0)
    with zipfile.ZipFile(buf) as z:
        xml_content = z.read("word/document.xml").decode("utf-8")
        assert "document" in xml_content
