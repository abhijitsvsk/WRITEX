import sys
import os
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

def verify_startup():
    print("Verifying FastAPI server startup...")
    try:
        from src.server import app
        assert app is not None
        assert app.title == "WriteX API"
        print("[OK] FastAPI import successful.")
        return True
    except ImportError as e:
        print(f"[FAIL] ImportError during startup: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Exception during startup: {e}")
        return False

if __name__ == "__main__":
    if verify_startup():
        print("FastAPI server startup verification PASSED.")
        sys.exit(0)
    else:
        print("FastAPI server startup verification FAILED.")
        sys.exit(1)
