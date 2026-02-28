import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

load_dotenv()

try:
    from src.ai.structurer import structure_text
except ImportError:
    from ai.structurer import structure_text

def test_ai_connection():
    print("Testing AI connection with Groq (Llama 3.1 70B)...")
    text = "Title: Hello World\nThis is a test paragraph."
    try:
        result = structure_text(text)
        print("AI Response received:")
        print(result[:200] + "..." if len(result) > 200 else result)
        if "type" in result:
             return True
        else:
             print("Warning: unexpected response format")
             return True # Still a success connectivity-wise
    except Exception as e:
        with open("test_error.txt", "w") as f:
            f.write(f"Error: {e}")
        print(f"AI Connection Failed: {e}")
        return False

if __name__ == "__main__":
    if test_ai_connection():
        print("AI Connectivity Verification Passed!")
        sys.exit(0)
    else:
        sys.exit(1)
