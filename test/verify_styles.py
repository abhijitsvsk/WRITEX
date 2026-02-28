import sys
from pathlib import Path
import io
import json

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

try:
    from src.file_formatting.formatting import generate_report
except ImportError:
    print("Error importing generate_report")
    sys.exit(1)

def test_styles():
    sample_structure = [
        {"type": "title", "text": "Test Document"},
        {"type": "heading", "text": "Introduction"},
        {"type": "paragraph", "text": "This is a test paragraph."}
    ]
    
    styles = ["Standard", "IEEE", "APA", "MLA", "Chicago", "Harvard", "AMA/Vancouver"]
    
    for style in styles:
        print(f"Testing style: {style}...", end="")
        try:
            output = io.BytesIO()
            generate_report(sample_structure, output, style_name=style)
            if output.getbuffer().nbytes > 0:
                print(f" Success! (Size: {output.getbuffer().nbytes} bytes)")
            else:
                print(" Failed (Empty output)")
        except Exception as e:
            print(f" Failed with error: {e}")

if __name__ == "__main__":
    test_styles()
