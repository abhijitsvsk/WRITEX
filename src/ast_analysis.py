import ast
import os
from collections import defaultdict

def extract_file_structure(file_content: str, filepath: str) -> dict:
    """
    Safely parses Python abstract syntax trees to extract structural metadata
    without executing the code. Returns a dictionary schema ready for LLM summarization.
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return {
            "file": filepath,
            "functions": [],
            "classes": [],
            "imports": [],
            "error": "SyntaxError during AST parsing"
        }

    extracted = {
        "file": filepath,
        "functions": [],
        "classes": [],
        "imports": []
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            extracted["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            extracted["classes"].append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                extracted["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                extracted["imports"].append(node.module)

    return extracted

def generate_basic_summary(extracted_data: dict) -> str:
    """
    Optional pipeline stub: Generates a lightweight natural language summary 
    of a single file based strictly on its deterministic AST footprint.
    This avoids the hallucination risk of full-text LLM summarization.
    """
    filename = os.path.basename(extracted_data.get("file", "unknown_file"))
    funcs = extracted_data.get("functions", [])
    classes = extracted_data.get("classes", [])
    
    summary_parts = [f"The file '{filename}'"]
    
    if classes:
        summary_parts.append(f"defines {len(classes)} classes (including {', '.join(classes[:3])})")
    if funcs:
        connector = "and" if classes else "defines"
        summary_parts.append(f"{connector} {len(funcs)} functions")
        
    if not classes and not funcs:
        summary_parts.append("appears to be a configuration or dependency file with no major definitions.")
    else:
        summary_parts[-1] += "."
        
    return " ".join(summary_parts)

def build_mermaid_diagram(all_files_data: list) -> str:
    """
    Constructs a valid Mermaid.js dependency graph (`graph TD`) mapped strictly
    from the cross-file import statements found in the AST. 
    """
    if not all_files_data:
        return ""
        
    graph_lines = ["graph TD"]
    local_modules = []
    
    # Extract basenames without extension to match local imports
    for data in all_files_data:
        base = os.path.basename(data["file"]).replace(".py", "")
        if base != "__init__":
            local_modules.append(base)
            
    # Build edges only for local project dependencies (reduces noise)
    edges_found = False
    for data in all_files_data:
        source_node = os.path.basename(data["file"]).replace(".py", "")
        for imp in data.get("imports", []):
            imp_base = imp.split(".")[0]  # Grab root of module import
            if imp_base in local_modules and imp_base != source_node:
                graph_lines.append(f"    {source_node} --> {imp_base}")
                edges_found = True
                
    if not edges_found:
        graph_lines.append("    %% No internal dependencies detected")
        
    return "\n".join(graph_lines)
