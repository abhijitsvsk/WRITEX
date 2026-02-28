"""
Comprehensive structural validation test for the academic report pipeline.
Tests certificate, acknowledgement, compiler structure, and validator behavior.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ai.report_generator import ReportGenerator
from src.validation.validator import DocumentValidator


# ──── Mock context simulating a real user (NOT RSET-specific) ────
MOCK_CONTEXT = {
    "title": "Writex",
    "student_name": "Alice, Bob, and Charlie",
    "team_names_raw": ["Alice", "Bob", "Charlie"],
    "degree": "B.Tech Computer Science",
    "principal": "Dr. Principal Name",
    "hod": "Prof. Head Name",
    "guide": "Mr. Guide Name",
    "guide_designation": "Assistant Professor",
    "hod_designation": "Professor & HoD",
    "university": "Test University",
    "department": "Computer Science and Engineering",
    "academic_year": "2025-2026",
    "pronoun_mode": "plural",
    "problem_statement": "Technical efficiency issue.",
    "objectives": "- Optimize workflow.",
    "style_guide": "",
    "sample_report_provided": False,
    "sample_sections": {},
    "has_test_files": False,
}


def test_certificate_template():
    """Certificate should use user-provided university, not hardcoded RSET."""
    gen = ReportGenerator(api_key="mock_key")
    cert = gen.fill_template("Certificate", MOCK_CONTEXT)
    
    # Must contain user-provided values
    assert "Writex" in cert, "Missing project title"
    assert "Alice" in cert, "Missing team member Alice"
    assert "Bob" in cert, "Missing team member Bob"
    assert "Charlie" in cert, "Missing team member Charlie"
    assert "Test University" in cert, "Missing user-provided university"
    assert "B.Tech Computer Science" in cert, "Missing degree"
    assert "2025-2026" in cert, "Missing academic year"
    assert "bonafide record" in cert.lower(), "Missing 'bonafide record' phrase"
    assert "Date:" in cert, "Missing Date line"
    
    # Must NOT contain RSET-specific text
    assert "RSET" not in cert, "Certificate still contains hardcoded RSET"
    assert "Rajagiri" not in cert, "Certificate still contains hardcoded Rajagiri"
    assert "Autonomous" not in cert, "Certificate still contains hardcoded Autonomous"
    
    print("✓ Certificate template test passed")


def test_acknowledgement_template_plural():
    """Acknowledgement with plural pronoun mode (team project)."""
    gen = ReportGenerator(api_key="mock_key")
    ack = gen.fill_template("Acknowledgement", MOCK_CONTEXT)
    
    # Must contain user-provided names
    assert "Dr. Principal Name" in ack, "Missing principal name"
    assert "Prof. Head Name" in ack, "Missing HOD name"
    assert "Mr. Guide Name" in ack, "Missing guide name"
    assert "Test University" in ack, "Missing university name"
    assert "Computer Science and Engineering" in ack, "Missing department name"
    
    # Must NOT contain RSET-specific text  
    assert "RSET" not in ack, "Acknowledgement still contains hardcoded RSET"
    assert "Rajagiri" not in ack, "Acknowledgement still contains hardcoded Rajagiri"
    
    # Must use plural pronouns (We/our/us)
    assert "We wish" in ack, "Should use 'We wish' for plural mode"
    assert "our sincere" in ack, "Should use 'our' for plural mode"
    
    # Must NOT contain stray "Student Name"
    assert "Student Name" not in ack, "Stray 'Student Name' detected"
    
    print("✓ Acknowledgement plural template test passed")


def test_acknowledgement_template_singular():
    """Acknowledgement with singular pronoun mode (solo project)."""
    gen = ReportGenerator(api_key="mock_key")
    ctx = MOCK_CONTEXT.copy()
    ctx["pronoun_mode"] = "singular"
    ack = gen.fill_template("Acknowledgement", ctx)
    
    # Must use singular pronouns (I/my/me)
    assert "I wish" in ack, "Should use 'I wish' for singular mode"
    assert "my sincere" in ack, "Should use 'my' for singular mode"
    
    print("✓ Acknowledgement singular template test passed")


def test_validator_clean_structure():
    """Validator should pass a well-formed structure."""
    validator = DocumentValidator()
    
    structure = [
        {"type": "title", "text": "TEST PROJECT"},
        {"type": "title_page_body", "text": "A PROJECT REPORT..."},
        {"type": "section_header", "text": "CERTIFICATE"},
        {"type": "paragraph", "text": "This is to certify..."},
        {"type": "section_header", "text": "ACKNOWLEDGEMENT"},
        {"type": "paragraph", "text": "We wish to express..."},
        {"type": "section_header", "text": "ABSTRACT"},
        {"type": "paragraph", "text": "This project..."},
        {"type": "section_header", "text": "LIST OF FIGURES"},
        {"type": "lof", "text": "LIST OF FIGURES"},
        {"type": "toc", "text": "TABLE OF CONTENTS"},
        {"type": "chapter", "text": "Introduction"},
        {"type": "subheading", "text": "Project Overview"},
        {"type": "paragraph", "text": "Body text here."},
        {"type": "section_header", "text": "REFERENCES"},
        {"type": "paragraph", "text": "[1] Python Software Foundation."},
    ]
    
    healed = validator.validate_and_heal(structure)
    assert healed is not None, "Validator returned None"
    assert len(healed) > 0, "Validator returned empty structure"
    
    # Ensure no placeholder reference text remains
    for item in healed:
        if item.get("type") == "paragraph":
            assert "add your references here" not in item.get("text", "").lower(), \
                "Reference placeholder still present"
    
    print("✓ Validator clean structure test passed")


def test_validator_heals_reference_placeholder():
    """Validator should remove placeholder reference text."""
    validator = DocumentValidator()
    
    structure = [
        {"type": "title", "text": "TEST"},
        {"type": "section_header", "text": "CERTIFICATE"},
        {"type": "paragraph", "text": "This is to certify..."},
        {"type": "section_header", "text": "ACKNOWLEDGEMENT"},
        {"type": "paragraph", "text": "We wish..."},
        {"type": "section_header", "text": "REFERENCES"},
        {"type": "paragraph", "text": "[1] Add your references here."},
        {"type": "paragraph", "text": "Note: Replace this placeholder with actual references."},
    ]
    
    healed = validator.validate_and_heal(structure)
    
    for item in healed:
        if item.get("type") == "paragraph":
            assert "add your references here" not in item.get("text", "").lower(), \
                "Reference placeholder was not healed"
            assert "replace this placeholder" not in item.get("text", "").lower(), \
                "Reference note was not healed"
    
    print("✓ Validator reference placeholder healing test passed")


def test_validator_heals_missing_lof():
    """Validator should inject LOF before TOC if figures exist but LOF is missing."""
    validator = DocumentValidator()
    
    structure = [
        {"type": "title", "text": "TEST"},
        {"type": "section_header", "text": "CERTIFICATE"},
        {"type": "paragraph", "text": "certify..."},
        {"type": "section_header", "text": "ACKNOWLEDGEMENT"},
        {"type": "paragraph", "text": "ack..."},
        {"type": "toc", "text": "TABLE OF CONTENTS"},
        {"type": "chapter", "text": "Results"},
        {"type": "paragraph", "text": "Figure 1.1: Test diagram"},
    ]
    
    healed = validator.validate_and_heal(structure)
    
    # Check that an LOF item was injected
    lof_items = [item for item in healed if item.get("type") == "lof"]
    assert len(lof_items) > 0, "LOF was not injected despite figures being present"
    
    print("✓ Validator LOF healing test passed")


def test_no_student_name_leak():
    """When team names are provided, 'Student Name' should never appear."""
    gen = ReportGenerator(api_key="mock_key")
    cert = gen.fill_template("Certificate", MOCK_CONTEXT)
    ack = gen.fill_template("Acknowledgement", MOCK_CONTEXT)
    
    assert "Student Name" not in cert, "Certificate leaked 'Student Name'"
    assert "Student Name" not in ack, "Acknowledgement leaked 'Student Name'"
    
    print("✓ No Student Name leak test passed")


if __name__ == "__main__":
    test_certificate_template()
    test_acknowledgement_template_plural()
    test_acknowledgement_template_singular()
    test_validator_clean_structure()
    test_validator_heals_reference_placeholder()
    test_validator_heals_missing_lof()
    test_no_student_name_leak()
    print("\n🎉 ALL STRUCTURAL AUDIT TESTS PASSED")
