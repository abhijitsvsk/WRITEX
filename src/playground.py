import json
from src.ai.structurer import structure_text
from src.file_formatting.formatting import generate_report


# ---------- Helper: clean AI output ----------
def extract_json(text: str) -> str:
    """
    Extracts the JSON array from AI output.
    This handles cases where Gemini adds extra text or markdown.
    """
    start = text.find("[")
    end = text.rfind("]") + 1

    if start == -1 or end == -1:
        raise ValueError("No JSON array found in AI output")

    return text[start:end]


# ---------- STEP 1: Read raw input text ----------
with open("src/input/raw_text.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()


# ---------- STEP 2: Call Gemini AI ----------
structured_json_text = structure_text(raw_text)

print("\n===== RAW AI OUTPUT =====\n")
print(structured_json_text)
print("\n=========================\n")


# ---------- STEP 3: Clean & parse JSON ----------
try:
    clean_json = extract_json(structured_json_text)
    structured_data = json.loads(clean_json)
except Exception as e:
    print("ERROR: Failed to parse AI JSON output")
    raise e


# ---------- STEP 4: Generate formatted Word document ----------
generate_report(structured_data, "final_report.docx")


print("\nDocument generated successfully using Gemini AI.\n")
