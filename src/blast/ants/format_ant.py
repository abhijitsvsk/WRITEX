from .base_ant import Ant, AntResult
from typing import Dict, Any, List

# from src.file_formatting.formatting import generate_report # Avoid top level import if possible to prevent circular deps
import importlib


class FormatAnt(Ant):
    """
    Ant responsible for applying visual formatting to the document.
    Wraps src.file_formatting.formatting.
    """

    def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> AntResult:
        try:
            # Lazy import
            formatting_module = importlib.import_module(
                "src.file_formatting.formatting"
            )
            generate_report = formatting_module.generate_report

            # Payload should contain structure and output path
            structure = payload.get("structure")
            output_path = payload.get("output_path")

            if not structure or not output_path:
                return AntResult(
                    success=False, error="Missing structure or output_path in payload"
                )

            # Extract style preferences
            visual_style = payload.get("visual_style", {})
            style_name = payload.get("style_name", "Standard")

            generate_report(
                structure=structure,
                output_path=output_path,
                style_name=style_name,
                custom_font=visual_style.get("font_name"),
                custom_size=visual_style.get("font_size"),
                custom_spacing=visual_style.get("line_spacing"),
            )

            return AntResult(success=True, content=f"Report generated at {output_path}")

        except Exception as e:
            return AntResult(success=False, error=str(e))
