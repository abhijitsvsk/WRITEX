"""
LLM-powered freeform request interpreter.
Parses user text into a structured SpecialRequest via the Groq API.
"""

import json
from typing import Optional
from groq import Groq
from src.models.constraints import SpecialRequest


class RequestInterpretationError(Exception):
    """Raised when the LLM response cannot be parsed into a valid SpecialRequest."""
    pass


# Full system prompt for interpreting a complete freeform request
_FULL_SYSTEM_PROMPT = """You are a document constraint parser for an academic report generator.
The user will give you a freeform instruction about how they want their report formatted or scoped.
You must return ONLY a valid JSON object with these keys:
- "interpreted_summary": A single plain-English sentence summarising what you understood.
- "parameters": An object containing only the keys that are explicitly mentioned or strongly implied.
  Valid parameter keys: max_pages, min_pages, font_size, font_name, line_spacing, 
  margin_inches, min_words, max_words.
- "custom_directives": A list of strings for any instructions that don't map to the above keys.
Do not invent values. Do not fill keys that were not mentioned. Return nothing except the JSON object."""

# Token-optimised prompt for re-interpreting a single focused parameter during conflict resolution
_FOCUSED_SYSTEM_PROMPT_TEMPLATE = """You are a document constraint parser for an academic report generator.
The user is providing a new value for a SINGLE parameter: {parameter_label}.
The valid key for this parameter is: {parameter_key}.
You must return ONLY a valid JSON object with these keys:
- "interpreted_summary": A single plain-English sentence summarising the new value.
- "parameters": An object containing ONLY the key "{parameter_key}" with the user's new value.
- "custom_directives": An empty list.
Do not invent values. Do not add any other keys. Return nothing except the JSON object."""

# Human-readable labels for parameter keys
PARAMETER_LABELS = {
    "max_pages": "Maximum Page Count",
    "min_pages": "Minimum Page Count",
    "font_size": "Font Size",
    "font_name": "Font Name",
    "line_spacing": "Line Spacing",
    "margin_inches": "Margin Width (inches)",
    "min_words": "Minimum Word Count",
    "max_words": "Maximum Word Count",
}


def interpret_request(
    raw_text: str,
    groq_client: Groq,
    focus_parameter: Optional[str] = None,
) -> SpecialRequest:
    """
    Calls the Groq LLM to parse freeform user text into a structured SpecialRequest.

    Args:
        raw_text: The user's freeform request string.
        groq_client: An initialised Groq client instance.
        focus_parameter: If set, uses a stripped-down prompt that asks only
                         for this single parameter key. Saves tokens during
                         conflict resolution re-interpretation (Option 3).

    Returns:
        A populated SpecialRequest dataclass.

    Raises:
        RequestInterpretationError: If the LLM response cannot be parsed as valid JSON.
    """
    if focus_parameter:
        label = PARAMETER_LABELS.get(focus_parameter, focus_parameter)
        system_prompt = _FOCUSED_SYSTEM_PROMPT_TEMPLATE.format(
            parameter_label=label,
            parameter_key=focus_parameter,
        )
    else:
        system_prompt = _FULL_SYSTEM_PROMPT

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.1,
            max_tokens=512,
            response_format={"type": "json_object"},
        )

        raw_response = completion.choices[0].message.content or ""
    except Exception as e:
        raise RequestInterpretationError(
            f"LLM call failed: {e}"
        )

    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        raise RequestInterpretationError(
            f"Could not parse LLM response as JSON. Raw response: {raw_response}"
        )

    return SpecialRequest(
        raw_text=raw_text,
        interpreted_summary=parsed.get("interpreted_summary", "No summary returned."),
        parameters=parsed.get("parameters", {}),
        custom_directives=parsed.get("custom_directives", []),
    )
