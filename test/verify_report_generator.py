
import os
import sys

# Add project root to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)

try:
    print("Attempting to import ReportGenerator...")
    from src.ai.report_generator import ReportGenerator
    print("Import successful.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found in environment. Using dummy key for init test.")
        api_key = "dummy_key"

    print("Initializing ReportGenerator...")
    generator = ReportGenerator(api_key=api_key)
    print("Initialization successful.")

except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()

print("Done.")
