import io
import pytest
from docx import Document

from src.file_formatting.formatting import generate_report
from src.validation.validator import DocumentValidator

def test_ast_validation_and_report_stress():
    stress_ast = [
        {"type": "title", "text": "Stress Test Report"},
        {"type": "title_page_body", "text": "Mock Submission Data\nJohn Doe"},
        {"type": "section_header", "text": "CERTIFICATE"},
        {"type": "paragraph", "text": "This is to certify that this report is bonafide..."},
        {"type": "section_header", "text": "ACKNOWLEDGEMENT"},
        {"type": "paragraph", "text": "I thank my guide and faculty members..."},
        {"type": "section_header", "text": "ABSTRACT"},
        {"type": "paragraph", "text": "This is the abstract paragraph."},
        {"type": "toc"},
        {"type": "lof"},
        {"type": "chapter", "text": "INTRODUCTION"},
        {"type": "paragraph", "text": "Introduction text. " * 30},
        {"type": "subheading", "text": "Background"},
        {"type": "paragraph", "text": "Background text. " * 30},
        {"type": "paragraph", "text": "    "},  # Whitespace drop test
        {"type": "paragraph", "text": "[Figure 1.1: System Architecture Diagram]"},
        {"type": "figure", "caption": "System Architecture Diagram"},
        {"type": "chapter", "text": "METHODOLOGY"},
        {"type": "subheading", "text": "Design"},
        {"type": "paragraph", "text": "Design text. " * 40},
        {"type": "code_block", "text": "def mock_func():\n    pass\n"},
        {"type": "subsubheading", "text": "Algorithm"},
        {"type": "paragraph", "text": "Algorithm details. " * 50}
    ]

    validator = DocumentValidator()
    healed_ast = validator.validate_and_heal(stress_ast)

    assert len(healed_ast) > 0
    # Whitespace paragraph should have been healed/removed
    assert not any(item.get("type") == "paragraph" and not item.get("text", "").strip() for item in healed_ast)

    buf = io.BytesIO()
    generate_report(healed_ast, buf, style_name="Standard")
    buf.seek(0)

    doc = Document(buf)
    assert len(doc.paragraphs) > 15
