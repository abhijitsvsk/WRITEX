from .base_ant import Ant, AntResult
from typing import Dict, Any, Union
import os
from src.analysis.style_analyzer import StyleAnalyzer, await_module_availability


class StyleAnt(Ant):
    """
    Ant responsible for extracting visual and tonal style from documents.
    Wraps src.analysis.style_analyzer.
    """

    def execute(self, payload: Union[str, Dict], context: Dict[str, Any]) -> AntResult:
        try:
            # Payload can be a file path (str) or a dict with file_path
            file_path = (
                payload if isinstance(payload, str) else payload.get("file_path")
            )

            if not file_path or not os.path.exists(file_path):
                return AntResult(success=False, error=f"Invalid file path: {file_path}")

            api_key = os.getenv("GROQ_API_KEY") or context.get("api_key")
            analyzer = StyleAnalyzer(api_key=api_key)

            # Analyze Visual Style
            visual_style = analyzer.analyze_visual_style(file_path)

            # Analyze Tonal Style (requires extraction first)
            text_content = analyzer.extract_text(file_path, file_path.split(".")[-1])
            style_guide = analyzer.analyze_style(text_content)

            result_data = {"visual_style": visual_style, "style_guide": style_guide}

            return AntResult(success=True, data=result_data)

        except Exception as e:
            return AntResult(success=False, error=str(e))
