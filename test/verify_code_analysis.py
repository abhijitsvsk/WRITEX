import sys
import os
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from src.analysis.code_analyzer import CodeAnalyzer
from src.analysis.project_summary import ProjectSummary

code = """
class DataProcessor:
    '''
    Processes raw data into clean format.
    Handles missing values and outliers.
    '''
    def __init__(self):
        pass

    def clean_data(self, data):
        '''
        Removes null values from the dataset.
        '''
        pass

def train_model(data):
    '''
    Trains a Random Forest model on the data.
    Returns the trained model.
    '''
    pass
"""

import ast

with open("verify_output.txt", "w", encoding="utf-8") as f:
    f.write("--- Direct AST Debug ---\n")
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            f.write(f"Class: {node.name}\n")
            doc = ast.get_docstring(node)
            f.write(f"Raw Doc: {repr(doc)}\n")
        elif isinstance(node, ast.FunctionDef):
            f.write(f"Func: {node.name}\n")
            doc = ast.get_docstring(node)
            f.write(f"Raw Doc: {repr(doc)}\n")

    f.write("\n--- Analyzer Output ---\n")
    summary = ProjectSummary()
    analyzer = CodeAnalyzer()
    analyzer._analyze_python_ast(code, "processor.py", summary)

    for mod in summary.modules:
        f.write(f"MODULE ENRTY:\n{mod}\n")
