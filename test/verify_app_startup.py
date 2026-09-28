import sys
import os
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

try:
    from src.server import app
    print("Successfully imported FastAPI app from src.server")
    assert app.title == "WriteX API"
except ImportError as e:
    print(f"Failed to import from src.server: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error verifying FastAPI startup: {e}")
    sys.exit(1)

print("FastAPI server startup verification passed.")
