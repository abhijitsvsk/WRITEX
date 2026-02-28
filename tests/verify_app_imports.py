
import sys
from pathlib import Path

# Add the project root to sys.path if not present
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

try:
    from src.ai.structurer import structure_text
    from src.file_formatting.formatting import generate_report
    print("SUCCESS: Imports successful.")
except ImportError as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
