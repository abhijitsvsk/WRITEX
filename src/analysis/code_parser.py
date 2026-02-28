"""
AST-based code parser for extracting real code structure.
Part of Phase 2: Real Code Analysis
"""

import ast
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """Information about a detected function."""

    name: str
    signature: str
    docstring: str
    line_start: int
    line_end: int
    is_method: bool = False
    has_recursion: bool = False


@dataclass
class ClassInfo:
    """Information about a detected class."""

    name: str
    docstring: str
    line_start: int
    line_end: int
    methods: List[FunctionInfo] = field(default_factory=list)


@dataclass
class CodeAnalysisResult:
    """Comprehensive code analysis result - single source of truth."""

    files_analyzed: List[str] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    detected_patterns: List[str] = field(default_factory=list)
    algorithm_keywords: List[str] = field(default_factory=list)
    code_snippets: Dict[str, List[Tuple[int, int, str]]] = field(
        default_factory=dict
    )  # file -> [(start, end, code)]


class CodeParser:
    """
    AST-based code parser for extracting real code structure.
    Conservative pattern detection - defaults to "not detected" vs false positives.
    """

    def __init__(self):
        self.ml_libraries = {
            "sklearn",
            "scikit-learn",
            "tensorflow",
            "keras",
            "torch",
            "pytorch",
        }
        self.algorithm_keywords = {
            "sort",
            "sorted",
            "search",
            "binary_search",
            "recursive",
            "dynamic_programming",
            "dp",
            "greedy",
            "backtrack",
            "dfs",
            "bfs",
            "dijkstra",
            "knn",
            "kmeans",
            "lstm",
            "cnn",
        }

    def parse_file(self, file_path: Path, content: str) -> CodeAnalysisResult:
        """
        Parse a single Python file and extract structure.
        Returns CodeAnalysisResult with real, verifiable information only.
        """
        result = CodeAnalysisResult()
        result.files_analyzed.append(str(file_path))

        try:
            tree = ast.parse(content)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result.imports.append(node.module)

            # Extract top-level functions and classes
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    func_info = self._extract_function(node, is_method=False)
                    result.functions.append(func_info)

                    # Check for recursion
                    if self._has_recursion(node, node.name):
                        func_info.has_recursion = True
                        if "Recursive" not in result.detected_patterns:
                            result.detected_patterns.append("Recursive")

                elif isinstance(node, ast.ClassDef):
                    class_info = self._extract_class(node)
                    result.classes.append(class_info)

            # Detect algorithm patterns conservatively
            self._detect_patterns(tree, result)

            # Extract code snippets (5-10 lines per significant function)
            result.code_snippets[str(file_path)] = self._extract_snippets(
                content, result.functions, result.classes
            )

        except SyntaxError as e:
            # Skip files with syntax errors
            pass

        return result

    def _extract_function(
        self, node: ast.FunctionDef, is_method: bool = False
    ) -> FunctionInfo:
        """Extract function information from AST node."""
        # Build signature
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        signature = f"{node.name}({', '.join(args)})"

        # Get docstring
        docstring = ast.get_docstring(node) or ""
        if docstring and len(docstring) > 100:
            docstring = docstring[:97] + "..."

        return FunctionInfo(
            name=node.name,
            signature=signature,
            docstring=docstring,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            is_method=is_method,
        )

    def _extract_class(self, node: ast.ClassDef) -> ClassInfo:
        """Extract class information including methods."""
        docstring = ast.get_docstring(node) or ""
        if docstring and len(docstring) > 100:
            docstring = docstring[:97] + "..."

        class_info = ClassInfo(
            name=node.name,
            docstring=docstring,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
        )

        # Extract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function(item, is_method=True)
                class_info.methods.append(method_info)

        return class_info

    def _has_recursion(self, node: ast.FunctionDef, func_name: str) -> bool:
        """Check if function calls itself (recursion detection)."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == func_name:
                    return True
        return False

    def _detect_patterns(self, tree: ast.AST, result: CodeAnalysisResult):
        """
        Conservatively detect algorithm patterns.
        Only label what is clearly present - no speculation.
        """
        has_loops = False
        has_sorting = False

        for node in ast.walk(tree):
            # Detect loops (iterative approach)
            if isinstance(node, (ast.For, ast.While)):
                has_loops = True

            # Detect sorting usage
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in [
                    "sorted",
                    "sort",
                ]:
                    has_sorting = True
                    result.algorithm_keywords.append("sorting")

        # Only add patterns if clearly detected
        if has_loops and "Iterative" not in result.detected_patterns:
            result.detected_patterns.append("Iterative")

        if has_sorting and "Sorting-based" not in result.detected_patterns:
            result.detected_patterns.append("Sorting-based")

        # Check for ML library usage (conservative)
        for imp in result.imports:
            root_lib = imp.split(".")[0]
            if root_lib in self.ml_libraries:
                if "ML-based" not in result.detected_patterns:
                    # CONSERVATIVE: Don't say "ML architecture" - just "ML library detected"
                    result.detected_patterns.append("ML library detected")
                    result.algorithm_keywords.append(root_lib)

    def _extract_snippets(
        self, content: str, functions: List[FunctionInfo], classes: List[ClassInfo]
    ) -> List[Tuple[int, int, str]]:
        """
        Extract 5-10 line code snippets from significant functions.
        Returns list of (start_line, end_line, code) tuples.
        """
        snippets = []
        lines = content.split("\n")

        # Extract from top 3 functions (by line count, excluding __init__)
        significant_funcs = [
            f for f in functions if f.name != "__init__" and not f.name.startswith("_")
        ]
        significant_funcs.sort(key=lambda f: f.line_end - f.line_start, reverse=True)

        for func in significant_funcs[:3]:
            start = func.line_start - 1  # 0-indexed
            end = min(start + 10, func.line_end)  # Max 10 lines

            snippet_lines = lines[start:end]
            snippet_code = "\n".join(snippet_lines)
            snippets.append((func.line_start, end, snippet_code))

        return snippets


def merge_analysis_results(results: List[CodeAnalysisResult]) -> CodeAnalysisResult:
    """Merge multiple CodeAnalysisResult objects into one."""
    merged = CodeAnalysisResult()

    for result in results:
        merged.files_analyzed.extend(result.files_analyzed)
        merged.functions.extend(result.functions)
        merged.classes.extend(result.classes)
        merged.imports.extend(result.imports)

        # Merge unique patterns and keywords
        for pattern in result.detected_patterns:
            if pattern not in merged.detected_patterns:
                merged.detected_patterns.append(pattern)

        for keyword in result.algorithm_keywords:
            if keyword not in merged.algorithm_keywords:
                merged.algorithm_keywords.append(keyword)

        merged.code_snippets.update(result.code_snippets)

    return merged
