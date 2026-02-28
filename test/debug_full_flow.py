
import sys
import os
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from src.analysis.style_analyzer import StyleAnalyzer
from src.ai.report_generator import ReportGenerator

# Mock User Context
mock_context = {
    "title": "CommunitySOS",
    "student_name": "Test Student", 
    "degree": "B.Tech",
    "guide": "Prof. New Guide",
    "hod": "Dr. New HOD",
    "university": "Test University"
}

# Sample text mimicking the user's PDF content (Merged header case)
sample_text = """
Some random text before...

Acknowledgement We wish to express our sincere gratitude towards Rev Dr. Jaison Paul Mullerikkal 
CMI, Principal of RSET, and Dr. Sherly K K, Head of the Department of Artificial 
Intelligence & Data Science for providing us with the opportunity to undertake our 
project, CommunitySOS. 
It is indeed our pleasure and a moment of satisfaction for us to express our sincere 
gratitude to our project guide Ms. Shyama R for her patience and all the priceless 
advice and wisdom she has shared with us.  
Last but not the least, We would like to express our sincere gratitude towards all other 
teachers and friends for their continuous support and constructive ideas. 
Fayas Asis 
Jain Rhonson 
Jeswin George 
Jishnu Jinesh 
Pranav P Nair

ABSTRACT
This is the abstract...
"""

print("--- 1. Testing Extraction (StyleAnalyzer) ---")
# We need to mock file_obj behavior for extract_text or just bypass it
# Let's subclass to override extract_text for testing
class MockStyleAnalyzer(StyleAnalyzer):
    def extract_text(self, file_obj, file_path):
        return sample_text

analyzer = MockStyleAnalyzer()
# path doesn't matter since we override extract_text
extracted_sections = analyzer.extract_specific_sections(None, "sample.pdf")

print(f"Extracted Acknowledgement (Length: {len(extracted_sections.get('acknowledgment', ''))}):")
print(f"'{extracted_sections.get('acknowledgment', 'MISSING')}'")

print("\n--- 2. Testing Generation Logic (ReportGenerator) ---")
# augment context with extracted sections
mock_context["sample_sections"] = extracted_sections
mock_context["sample_report_provided"] = True

generator = ReportGenerator('dummy_key')

# We want to see the PROMPT that would be sent.
# We'll peek into fill_template logic. 
# Since fill_template calls generate_with_retry, we can't easily see the prompt without modifying code 
# OR we can replicate the logic here to see what it builds.

section_name = "Acknowledgement"
base_text = ""
sample_sections = mock_context.get("sample_sections", {})
key_map = {
    "Certificate": "certificate",
    "Acknowledgement": "acknowledgment"
}
sample_key = key_map.get(section_name)

if sample_key and sample_sections.get(sample_key):
    base_text = sample_sections.get(sample_key)
    print(f"Base text found in context: Yes (Length {len(base_text)})")
else:
    print("Base text NOT found in context.")

# Replicate the prompt construction from ReportGenerator
prompt = f"""
            Task: You are a text processing engine. The user has provided a specific Acknowledgement/Certificate text.
            Your satisfying criteria:
            1. OUTPUT the provided text EXACTLY as is, word-for-word.
            2. ONLY replace the specific names/titles with the New Details provided below.
            3. DO NOT rewrite the sentence structure.
            4. DO NOT change the gratitude expressions.
            5. DO NOT add any conversational text.
            
            Original Sample Text:
            \"\"\"
            {base_text}
            \"\"\"
            
            New Details to Insert:
            - Project Title: {mock_context.get('title')}
            - Student Name: {mock_context.get('student_name')}
            - Degree: {mock_context.get('degree')}
            - Guide Name: {mock_context.get('guide', 'Guide')}
            - HOD Name: {mock_context.get('hod', 'HOD')}
            - University: {mock_context.get('university', 'University')}
            
            OUTPUT ONLY THE FINAL TEXT.
            """

print("\n--- Generated Prompt ---")
with open("debug_output.txt", "w", encoding="utf-8") as f:
    f.write(prompt)
print("Prompt written to debug_output.txt")
