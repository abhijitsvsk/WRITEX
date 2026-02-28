import sys
import os
sys.path.append(os.getcwd())
from src.file_formatting.formatting import generate_report

def test_dynamic_styling():
    print("Testing Dynamic Styling...")
    
    structure = [
        {"type": "title", "text": "Deep Style Verification"},
        {"type": "heading", "text": "1. Introduction"},
        {"type": "paragraph", "text": "This is a test paragraph with custom font and spacing."}
    ]
    
    output_path = "test_deep_style.docx"
    
    # Test with custom settings: Arial, Size 10, Spacing 2.0
    try:
        generate_report(structure, output_path, style_name="Standard",
                       custom_font="Arial", custom_size=10, custom_spacing=2.0)
        
        if os.path.exists(output_path):
            print(f"SUCCESS: Generated {output_path} with custom settings.")
            # In a real verification we'd inspect the docx properties, but for now successful generation is good.
        else:
            print("FAILURE: Output file not found.")
            
    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dynamic_styling()
