"""
Helper to format code analysis results for LLM prompts.
"""


def format_detailed_analysis_for_prompt(detailed_analysis) -> str:
    """
    Format CodeAnalysisResult into a string for LLM prompt injection.
    This replaces template-based generation with real code facts.
    """
    if not detailed_analysis:
        return "No code analysis available."

    output = []

    # Functions
    if detailed_analysis.functions:
        output.append("=== REAL FUNCTIONS FROM CODE ===")
        for func in detailed_analysis.functions[:15]:  # Limit to 15 most significant
            entry = f"- {func.signature}"
            if func.docstring:
                entry += f"\n  Purpose: {func.docstring}"
            if func.has_recursion:
                entry += "\n  [Uses recursion]"
            output.append(entry)

        if len(detailed_analysis.functions) > 15:
            output.append(
                f"... and {len(detailed_analysis.functions) - 15} more functions"
            )

    # Classes
    if detailed_analysis.classes:
        output.append("\n=== REAL CLASSES FROM CODE ===")
        for cls in detailed_analysis.classes[:10]:  # Limit to 10 classes
            entry = f"- Class: {cls.name}"
            if cls.docstring:
                entry += f"\n  Purpose: {cls.docstring}"
            if cls.methods:
                method_names = [m.name for m in cls.methods[:5]]
                entry += f"\n  Methods: {', '.join(method_names)}"
                if len(cls.methods) > 5:
                    entry += f" (+{len(cls.methods) - 5} more)"
            output.append(entry)

    # Detected patterns
    if detailed_analysis.detected_patterns:
        output.append("\n=== DETECTED ALGORITHM PATTERNS ===")
        for pattern in detailed_analysis.detected_patterns:
            output.append(f"- {pattern}")

    # Real imports (dependencies)
    if detailed_analysis.imports:
        unique_imports = list(set(detailed_analysis.imports))[:20]
        output.append(f"\n=== DEPENDENCIES (Imports) ===")
        output.append(", ".join(unique_imports))

    # Code snippets (if available)
    if detailed_analysis.code_snippets:
        output.append("\n=== CODE SNIPPETS (Sample Implementation) ===")
        snippet_count = 0
        for file_path, snippets in detailed_analysis.code_snippets.items():
            for start, end, code in snippets[:2]:  # Max 2 snippets per file
                if snippet_count >= 3:  # Max 3 total snippets
                    break
                output.append(f"\nFrom {file_path} (lines {start}-{end}):")
                output.append(f"```python\n{code}\n```")
                snippet_count += 1

    return "\n".join(output)
