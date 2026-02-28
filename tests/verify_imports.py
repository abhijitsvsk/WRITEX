
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

print(f"Project Root: {project_root}")
print(f"sys.path: {sys.path}")

try:
    print("Attempting to import src.ai.structurer...")
    from src.ai import structurer
    print("SUCCESS: src.ai.structurer imported.")
    
    print("Attempting to import src.ai.report_generator...")
    from src.ai import report_generator
    print("SUCCESS: src.ai.report_generator imported.")
    
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Exception: {e}")
    sys.exit(1)

print("All imports verified successfully.")
