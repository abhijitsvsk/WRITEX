from .base_ant import Ant, AntResult
from typing import Dict, Any
import os
from src.ai.report_generator import ReportGenerator


class ContentAnt(Ant):
    """
    Ant responsible for generating text content for a section.
    Wraps src.ai.report_generator.
    """

    def execute(self, node: Any, context: Dict[str, Any]) -> AntResult:
        try:
            api_key = os.getenv("GROQ_API_KEY") or context.get("api_key")
            if not api_key:
                return AntResult(success=False, error="Missing API Key")

            generator = ReportGenerator(api_key=api_key)

            # Prepare context for generator
            # The generator expects: section_name, project_summary_dict, user_context
            section_name = node.text if hasattr(node, "text") else "Unknown Section"

            # Extract project summary from global context
            project_summary = context.get("project_summary", {})

            # Extract user context
            user_context = context.get("user_context", {})
            user_context["current_section"] = section_name

            # Generate
            content = generator.generate_section(
                section_name=section_name,
                project_summary=project_summary,
                user_context=user_context,
            )

            if content:
                return AntResult(success=True, content=content)
            else:
                return AntResult(success=False, error="Empty content generated")

        except Exception as e:
            return AntResult(success=False, error=str(e))
