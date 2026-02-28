import win32com.client as win32
import os
import sys

try:
    word = win32.Dispatch('Word.Application')
    word.Visible = False

    doc_path = os.path.abspath(r'd:\writex\streamlit_test_output.docx')
    out_path = os.path.abspath(r'd:\writex\streamlit_test_output_updated.docx')

    doc = word.Documents.Open(doc_path, ReadOnly=True)
    
    # Try updating everything
    for field in doc.Fields:
        field.Update()
        
    doc.SaveAs2(out_path)
    doc.Close()
    print("Saved updated doc as " + out_path)
    
    # Read text back to verify
    doc2 = word.Documents.Open(out_path, ReadOnly=True)
    text = doc2.Content.Text
    
    if "Table of Contents" in text and "Introduction" in text:
        print("SUCCESS: TOC populated!")
    else:
        print("FAIL: TOC is still empty.")
        
    doc2.Close()
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'word' in locals():
        word.Quit()
