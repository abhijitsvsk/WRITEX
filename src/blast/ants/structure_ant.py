from .base_ant import Ant, AntResult
from typing import Dict, Any, List
import json
import os
from src.ai.structurer import structure_text


class StructureAnt(Ant):
    """
    Ant responsible for determining document structure from raw text.
    Wraps src.ai.structurer.
    """

    def execute(self, payload: str, context: Dict[str, Any]) -> AntResult:
        try:
            # payload is expected to be raw text or a file path?
            # Let's assume payload is raw text or a dict with text
            raw_text = payload
            if isinstance(payload, dict):
                raw_text = payload.get("text", "")

            api_key = os.getenv("GROQ_API_KEY") or context.get("api_key")
            style_name = context.get("style_name", "Standard")

            # Call the structurer
            json_str = structure_text(raw_text, api_key=api_key, style_name=style_name)

            # Parse the result
            try:
                structure_data = json.loads(json_str)
                return AntResult(success=True, data=structure_data)
            except json.JSONDecodeError:
                return AntResult(
                    success=False,
                    error="Failed to parse structure JSON",
                    content=json_str,
                )

        except Exception as e:
            return AntResult(success=False, error=str(e))
