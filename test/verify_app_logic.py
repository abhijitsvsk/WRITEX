import sys
import os
import io
import json
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from src.file_formatting.formatting import generate_report

def test_formatting_logic():
    print("Testing formatting logic...")
    structure = [
        {"type": "title", "text": "Test Document"},
        {"type": "heading", "text": "Introduction"},
        {"type": "paragraph", "text": "This is a test paragraph to verify formatting logic."}
    ]
    
    # Test with BytesIO
    output_buffer = io.BytesIO()
    try:
        generate_report(structure, output_buffer)
        output_buffer.seek(0)
        size = len(output_buffer.getvalue())
        print(f"Success! Generated DOCX in memory. Size: {size} bytes")
        
        if size > 0:
             return True
        else:
             print("Error: Generated file is empty.")
             return False

    except Exception as e:
        print(f"Error during formatting: {e}")
        return False

if __name__ == "__main__":
    if test_formatting_logic():
        print("Verification passed!")
        sys.exit(0)
    else:
        print("Verification failed!")
        sys.exit(1)
