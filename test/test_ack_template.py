import sys
import os
sys.path.append(os.getcwd())
from src.ai.report_generator import ReportGenerator

def test_ack_template():
    # Mock context
    user_context = {
        "title": "AI Blast System",
        "student_name": "Alice\nBob",
        "team_names_raw": ["Alice", "Bob"],
        "degree": "B.Tech",
        "principal": "Dr. Principal",
        "hod": "Prof. Head",
        "guide": "Mr. Mentor",
        "university": "Tech University",
        "department": "Computer Science",
        "pronoun_mode": "plural"
    }
    
    # Instantiate (API key not needed for strict template but required by init)
    gen = ReportGenerator(api_key="mock_key")
    
    # Generate
    ack = gen.fill_template("Acknowledgement", user_context)
    
    print("--- Generated Acknowledgement ---")
    print(ack)
    print("-------------------------------")
    
    # Assertions
    assert "Dr. Principal" in ack, "Missing Principal"
    assert "Prof. Head" in ack, "Missing HOD"
    assert "Mr. Mentor" in ack, "Missing Guide"
    assert "Tech University" in ack, "Missing University"
    assert "Computer Science" in ack, "Missing Department"
    assert "RSET" not in ack, "Should not contain hardcoded RSET"
    
    print("Test Passed: All names present.")

if __name__ == "__main__":
    test_ack_template()

