import sys
sys.path.append('.')

from src.ai.report_generator import ReportGenerator

# Create a mock context exactly as the app would
context = {
    "title": "CommunitySOS",
    "principal": "Rev Dr. Jaison Paul Mullerikkal CMI",
    "hod": "Dr. Sherly K K",
    "guide": "Ms. Shyama R",
    "student_name": "abhi\nrahul\nram\nsita\nradha",
    "degree": "B.Tech",
    "university": "APJ Abdul Kalam Technological University"
}

# Create generator (with dummy key since we're just testing template)
gen = ReportGenerator("dummy_key")

# Call fill_template
result = gen.fill_template("Acknowledgement", context)

print("="*80)
print("GENERATED ACKNOWLEDGEMENT:")
print("="*80)
print(result)
print("="*80)

# Also write to file
with open("ack_output.txt", "w", encoding="utf-8") as f:
    f.write(result)
print("\nOutput also written to ack_output.txt")
