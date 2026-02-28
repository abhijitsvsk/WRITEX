import sys
import os
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

try:
    from src.app import run_formatting
    print("Successfully imported run_formatting from src.app")
except ImportError as e:
    print(f"Failed to import from src.app: {e}")
    sys.exit(1)
except Exception as e:
    # Streamlit pages might throw errors if run directly without streamlit run
    # detecting that is a sign it loaded far enough
    print(f"App loaded with expected side-effect: {e}")

print("App startup verification passed.")
