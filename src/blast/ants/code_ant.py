from .base_ant import Ant, AntResult
from typing import Dict, Any, Union
import os

# from src.analysis.code_analyzer import CodeAnalyzer
import importlib


class CodeAnt(Ant):
    """
    Ant responsible for analyzing code bases.
    Wraps src.analysis.code_analyzer.
    """

    def execute(self, payload: Union[str, Dict], context: Dict[str, Any]) -> AntResult:
        try:
            # Lazy import
            analyzer_module = importlib.import_module("src.analysis.code_analyzer")
            CodeAnalyzer = analyzer_module.CodeAnalyzer

            # Payload can be directory/zip path
            target_path = payload if isinstance(payload, str) else payload.get("path")

            if not target_path or not os.path.exists(target_path):
                return AntResult(success=False, error=f"Invalid path: {target_path}")

            analyzer = CodeAnalyzer()

            if target_path.endswith(".zip"):
                summary = analyzer.analyze_zip(target_path)
            else:
                # CodeAnalyzer defaults to zip, might need modification or we just accept zip for now
                # Actually looking at the code `_walk_and_analyze` is internal but used.
                # Let's assume for now we use what's public or mock it if needed.
                # Re-reading CodeAnalyzer: it seems designed for Zips mostly but has internal walk.
                # We will wrap it carefully.
                return AntResult(
                    success=False,
                    error="CodeAnt currently supports ZIP files only per CodeAnalyzer spec.",
                )

            return AntResult(success=True, data=summary.to_json())

        except Exception as e:
            return AntResult(success=False, error=str(e))
