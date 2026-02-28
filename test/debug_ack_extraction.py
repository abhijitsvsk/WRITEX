
import sys
import os
from pathlib import Path

# Mocking the logic from StyleAnalyzer.extract_specific_sections to debug
def extract_specific_sections_debug(text):
    extracted = {}
    
    targets = {
        "vision": ["vision of the department", "institute vision", "our vision"],
        "mission": ["mission of the department", "institute mission", "our mission"],
        "peo": ["program educational objectives", "peos"],
        "po": ["program outcomes", "pos"],
        "pso": ["program specific outcomes", "psos"],
        "certificate": ["certificate", "bonafide certificate"],
        "acknowledgment": ["acknowledgment", "acknowledgement"]
    }
    
    lines = text.split('\n')
    current_section = None
    buffer = []
    
    print(f"Total lines: {len(lines)}")
    
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        print(f"Line {i}: '{line_clean}'")
        
        # Check if this line starts a new target section
        found_new = False
        for key, keywords in targets.items():
            # DEBUG: print checks
            if any(kw in line_clean for kw in keywords):
                print(f"  -> Match keyword for {key}")
                if len(line_clean) < 50:
                    print(f"  -> Length OK ({len(line_clean)} < 50). STARTING SECTION {key}")
                    # Save previous section if exists
                    if current_section and buffer:
                        extracted[current_section] = "\n".join(buffer).strip()
                    
                    # Start new section
                    current_section = key
                    buffer = []
                    found_new = True
                    break
                else:
                    print(f"  -> Length too long ({len(line_clean)} >= 50). IGNORING.")
        
        if found_new:
            continue
            
        # If in a section, accumulate text
        if current_section:
                # Stop if we hit a generic new section
                # stricter checks to avoid false positives in body text
                stops = ["table of contents", "chapter 1", "chapter one", "list of figures", "list of tables", "abbreviations", "declaration"]
                
                is_stop = False
                if any(x in line_clean for x in stops) and len(line_clean) < 40:
                    is_stop = True
                
                # Special strict check for single-word headers
                if line_clean in ["abstract", "index", "contents"]:
                    is_stop = True

                if is_stop:
                    print(f"  -> Stop condition met by '{line_clean}'. ENDING SECTION {current_section}")
                    extracted[current_section] = "\n".join(buffer).strip()
                    current_section = None
                    buffer = []
                else:
                    buffer.append(line)
    
    # Capture last section
    if current_section and buffer:
         print(f"  -> End of text. Saving {current_section}")
         extracted[current_section] = "\n".join(buffer).strip()
         
    return extracted

# Sample text provided by user (Simulating Merged Header Case which caused failure)
sample_text = """
Some random text before...

Acknowledgement We wish to express our sincere gratitude towards Rev Dr. Jaison Paul Mullerikkal 
CMI, Principal of RSET, and Dr. Sherly K K, Head of the Department of Artificial 
Intelligence & Data Science for providing us with the opportunity to undertake our 
project, CommunitySOS. 
It is indeed our pleasure and a moment of satisfaction for us to express our sincere 
gratitude to our project guide Ms. Shyama R for her patience and all the priceless 
advice and wisdom she has shared with us.  
Last but not the least, We would like to express our sincere gratitude towards all other 
teachers and friends for their continuous support and constructive ideas. 
Fayas Asis 
Jain Rhonson 
Jeswin George 
Jishnu Jinesh 
Pranav P Nair

ABSTRACT
This is the abstract...
"""

print("--- RUNNING DEBUG ---")
result = extract_specific_sections_debug(sample_text)
print("\n--- RESULT ---")
for k, v in result.items():
    print(f"[{k}]:\n{v}\nWith length: {len(v)}")
