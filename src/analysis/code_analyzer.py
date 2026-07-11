import os
import zipfile
import tempfile
import ast
import shutil
from pathlib import Path
from typing import List, Dict, Set
from .project_summary import ProjectSummary
from .code_parser import CodeParser, merge_analysis_results


class CodeAnalyzer:
    def __init__(self, max_files: int = 50, max_size_mb: int = 5):
        self.max_files = max_files
        self.max_size_mb = max_size_mb
        self.ignored_dirs = {
            "node_modules",
            "venv",
            ".venv",
            "__pycache__",
            ".git",
            "build",
            "dist",
            ".idea",
            ".vscode",
        }
        self.code_parser = CodeParser()  # AST-based code parser

    def analyze_zip(self, zip_file) -> ProjectSummary:
        """
        Extracts and analyzes a ZIP file (from a file-like object or path) in-memory.
        NOTE: File selection and AST extraction happen here.
        DataSanitizer strings/payload scrubbing happens later in the pipeline
        (in ReportGenerator) AFTER file selection and AST extraction are complete.
        This means the trust boundary rests at the LLM prompt payload, not at ingestion.
        """
        summary = ProjectSummary()

        # Determine file size
        try:
            if hasattr(zip_file, "size"):
                file_size = zip_file.size
            elif hasattr(zip_file, "getbuffer"):
                file_size = zip_file.getbuffer().nbytes
            elif isinstance(zip_file, str):
                file_size = os.path.getsize(zip_file)
            else:
                current_pos = zip_file.tell()
                zip_file.seek(0, 2)
                file_size = zip_file.tell()
                zip_file.seek(current_pos)
        except Exception:
            file_size = 0

        if file_size > self.max_size_mb * 1024 * 1024:
            raise ValueError(f"ZIP file exceeds maximum size of {self.max_size_mb}MB")

        try:
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                self._analyze_in_memory(zip_ref, summary)
        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file provided")

        return summary

    def _score_file(self, file_path: Path) -> int:
        score = 0
        name = file_path.name.lower()
        if name in ["app.py", "main.py", "index.js", "server.js", "manage.py", "setup.py"]:
            score += 200
        if "test" in name or "spec" in name:
            score += 50
            
        ext = file_path.suffix.lower()
        if ext in [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".go"]:
            score += 30
            
        # Penalize deep nesting
        score -= len(file_path.parts) * 5
        return score

    def _analyze_in_memory(self, zip_ref: zipfile.ZipFile, summary: ProjectSummary):
        analysis_results = []
        total_uncompressed_size = 0
        valid_files = []

        for file_info in zip_ref.infolist():
            if file_info.is_dir():
                continue
                
            # Defend against ZIP bombs by validating uncompressed size
            if file_info.file_size > 500 * 1024:
                raise ValueError(f"File {file_info.filename} exceeds 500KB uncompressed limit. Aborting to prevent OOM crash.")
            total_uncompressed_size += file_info.file_size
            if total_uncompressed_size > 20 * 1024 * 1024:
                raise ValueError("Total uncompressed size exceeds 20MB limit. Aborting to prevent OOM crash.")

            file_path = Path(file_info.filename)

            # Skip ignored directories
            if any(part in self.ignored_dirs for part in file_path.parts):
                continue
                
            # HARD EXCLUDE: Protect against small projects skipping score penalties
            name = file_path.name.lower()
            lower_parts = [p.lower() for p in file_path.parts]
            if name in ["settings.py", "config.py", ".env", "production.py", "development.py"] or name.endswith(("lock", ".json", ".xml", ".csv")):
                continue
            if "settings" in lower_parts or "config" in lower_parts or "secrets" in lower_parts:
                continue

            score = self._score_file(file_path)
            valid_files.append((file_info, file_path, score))

        # Sort by score descending for intelligent monorepo truncation
        valid_files.sort(key=lambda x: x[2], reverse=True)
        setattr(summary, "is_truncated", len(valid_files) > self.max_files)
        summary.total_files = len(valid_files)

        for file_info, file_path, score in valid_files[:self.max_files]:
            analysis_result = self._analyze_file_memory(
                file_info, zip_ref, file_path, summary
            )
            if analysis_result:
                analysis_results.append(analysis_result)

        if analysis_results:
            summary.detailed_analysis = merge_analysis_results(analysis_results)

        self._infer_project_type(summary)

    def _analyze_file_memory(
        self,
        file_info: zipfile.ZipInfo,
        zip_ref: zipfile.ZipFile,
        file_path: Path,
        summary: ProjectSummary,
    ):
        extension = file_path.suffix.lower()

        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".html": "HTML",
            ".css": "CSS",
            ".ipynb": "Jupyter Notebook",
        }

        if extension in lang_map:
            lang = lang_map[extension]
            summary.languages[lang] = summary.languages.get(lang, 0) + 1
            if lang not in summary.tech_stack:
                summary.tech_stack.append(lang)

        analysis_result = None
        
        try:
            content = zip_ref.read(file_info).decode("utf-8", errors="ignore")
        except Exception:
            return None

        # Block recursion errors from minified or auto-generated code
        if any(len(line) > 500 for line in content.split('\n')):
            return None

        if extension == ".py":
            try:
                analysis_result = self.code_parser.parse_file(file_path, content)
                self._analyze_python_ast(content, file_path.name, summary)

                if (
                    'if __name__ == "__main__":' in content
                    or "if __name__ == '__main__':" in content
                ):
                    summary.entry_points.append(file_path.name)

                if (
                    file_path.name.startswith("test_")
                    or file_path.name.endswith("_test.py")
                    or "test" in file_path.parts
                ):
                    summary.test_files.append(file_path.name)

            except Exception:
                pass  # nosec B110
        elif extension in [".js", ".jsx", ".ts", ".tsx", ".java"]:
            analysis_result = self._analyze_generic_ast(content, file_path, extension)

        return analysis_result

    def _analyze_generic_ast(self, content: str, file_path: Path, ext: str):
        from .code_parser import CodeAnalysisResult, FunctionInfo, ClassInfo
        import re
        
        result = CodeAnalysisResult()
        result.files_analyzed.append(str(file_path))
        
        try:
            if ext in [".js", ".jsx", ".ts", ".tsx"]:
                classes = re.finditer(r"class\s+([A-Z]\w*)", content)
                for match in classes:
                    result.classes.append(ClassInfo(name=match.group(1), docstring="", line_start=content[:match.start()].count('\n'), line_end=content[:match.end()].count('\n')))
                
                funcs_raw = re.finditer(r"(?:function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*\(|const\s+(\w+)\s*=\s*function)", content)
                for match in funcs_raw:
                    name = next(g for g in match.groups() if g is not None)
                    result.functions.append(FunctionInfo(name=name, signature=f"{name}()", docstring="", line_start=content[:match.start()].count('\n'), line_end=content[:match.end()].count('\n')))
                    
            elif ext == ".java":
                classes = re.finditer(r"(?:public|private|protected)?\s*class\s+([A-Z]\w*)", content)
                for match in classes:
                    result.classes.append(ClassInfo(name=match.group(1), docstring="", line_start=content[:match.start()].count('\n'), line_end=content[:match.end()].count('\n')))
                    
                funcs_raw = re.finditer(r"(?:public|private|protected|static)\s+[\w<>]+\s+(\w+)\s*\(", content)
                for match in funcs_raw:
                    name = match.group(1)
                    if name not in ["if", "for", "while", "catch", "switch"]:
                        result.functions.append(FunctionInfo(name=name, signature=f"{name}()", docstring="", line_start=content[:match.start()].count('\n'), line_end=content[:match.end()].count('\n')))
        except Exception:
            pass
            
        return result

    def _get_summary_doc(self, node):
        try:
            doc = ast.get_docstring(node)
            if not doc:
                return ""
            # Sanitize
            doc = doc.replace("\r", "").strip()
            # Split by lines
            lines = [line.strip() for line in doc.split("\n") if line.strip()]
            if lines:
                text = lines[0]
                # Limit length
                if len(text) > 60:
                    text = text[:57] + "..."
                return text
            return ""
        except:
            return ""

    def _analyze_python_ast(
        self, content: str, file_name: str, summary: ProjectSummary
    ):
        try:
            tree = ast.parse(content)

            classes = []
            functions = []

            for node in ast.walk(tree):
                # Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_library(alias.name, summary)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_library(node.module, summary)

                # ML Libraries & Algorithms Check (Heuristic)
                self._check_ml_patterns(node, summary)

                # Structure Extraction
                if isinstance(node, ast.ClassDef):
                    doc_summary = self._get_summary_doc(node)
                    classes.append(
                        f"{node.name} ({doc_summary})" if doc_summary else node.name
                    )
                elif isinstance(node, ast.FunctionDef):
                    # Check if it's a method (heuristic: indentation or name)
                    # ast.walk doesn't give context. For summary, flat list is okay.
                    if not node.name.startswith("_") or node.name == "__init__":
                        doc_summary = self._get_summary_doc(node)
                        functions.append(
                            f"{node.name} ({doc_summary})" if doc_summary else node.name
                        )

            # Add to detailed modules list
            if classes or functions:
                module_info = f"File: {file_name}\n"
                if classes:
                    module_info += (
                        f"  Classes:\n    - " + "\n    - ".join(classes) + "\n"
                    )
                if functions:
                    # Limit to 15 important functions
                    shown_funcs = functions[:15]
                    module_info += f"  Functions:\n    - " + "\n    - ".join(
                        shown_funcs
                    )
                    if len(functions) > 15:
                        module_info += f"\n    ... (+{len(functions)-15} more)"
                    module_info += "\n"

                summary.modules.append(module_info)

        except SyntaxError:
            pass

    def _add_library(self, lib_name: str, summary: ProjectSummary):
        if not lib_name:
            return
        # Filter standard lib? For now just add major ones
        major_libs = {
            "numpy",
            "pandas",
            "scikit-learn",
            "sklearn",
            "tensorflow",
            "keras",
            "torch",
            "matplotlib",
            "seaborn",
            "flask",
            "django",
            "fastapi",
            "streamlit",
            "cv2",
        }
        root_lib = lib_name.split(".")[0]
        if root_lib in major_libs and root_lib not in summary.tech_stack:
            summary.tech_stack.append(root_lib)

    def _check_ml_patterns(self, node: ast.AST, summary: ProjectSummary):
        # Heuristic to detect algorithm usage
        name = ""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and hasattr(node.func, "attr"):
                name = node.func.attr
            elif isinstance(node.func, ast.Name):
                name = node.func.id

            if name:
                # Common ML model names
                ml_keywords = {
                    "RandomForest",
                    "LinearRegression",
                    "SVM",
                    "KMeans",
                    "CNN",
                    "LSTM",
                    "ResNet",
                    "YOLO",
                }
                for key in ml_keywords:
                    if (
                        key.lower() in name.lower()
                        and key not in summary.algorithms_used
                    ):
                        summary.algorithms_used.append(key)

    def _infer_project_type(self, summary: ProjectSummary):
        # Simple heuristic
        stack_set = set(summary.tech_stack)
        if {"flask", "django", "fastapi", "streamlit"} & stack_set:
            summary.project_type = "Web Application"
        elif {"tensorflow", "torch", "keras", "sklearn", "scikit-learn"} & stack_set:
            summary.project_type = "Machine Learning"
        elif "cv2" in stack_set:
            summary.project_type = "Computer Vision"
        elif "pandas" in stack_set:
            summary.project_type = "Data Analysis"
        else:
            summary.project_type = "General Software"
