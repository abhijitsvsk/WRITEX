
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Attempting to import src.ai.structurer...")
    import src.ai.structurer
    print("✅ Success")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
