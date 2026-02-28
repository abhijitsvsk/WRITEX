import os
import json
from groq import Groq
from .utils import generate_with_retry


def structure_text(raw_text, api_key=None, style_name="Standard"):
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "Groq API Key is missing. Please provide it or set GROQ_API_KEY environment variable."
        )

    client = Groq(api_key=api_key)

    # Style-specific casing rules
    casing_instruction = "Follow standard capitalization rules."
    if style_name in ["IEEE", "APA"]:
        casing_instruction = "HEADINGS must be in Sentence case (only first word capitalized, except proper nouns)."
    elif style_name in ["Chicago", "MLA"]:
        casing_instruction = "HEADINGS must be in Title Case (Capitalize Major Words)."

    prompt = f"""
You are a document structure detection system.

Your Goal: Detect structure and format text according to {style_name} style rules.

Rules:
1. DO NOT rewrite, summarize, or paraphrase content logic.
2. DO fix capitalization based on style:
   - {casing_instruction}
   - Title: Always Title Case.
3. Classify each block as: 
   - title (Document Title)
   - chapter (Level 1: e.g., "1. Introduction")
   - heading (Level 1: if not using chapters)
   - subheading (Level 2: e.g., "1.1 Background")
   - subsubheading (Level 3: e.g., "1.1.1 History")
   - paragraph (Body text)
   - reference (Bibliography items)
   - code (Programming code snippets)
   - figure_caption (Captions starting with "Figure X:")
4. If you see a list of references/bibliography at the end, mark each item as "reference".
5. If you see code snippets (often in triple backticks), mark them as "code" and keep the formatting intact.

Return ONLY valid JSON in this format:

[
  {{ "type": "title", "text": "..." }},
  {{ "type": "chapter", "text": "..." }},
  {{ "type": "subheading", "text": "..." }},
  {{ "type": "paragraph", "text": "..." }},
  {{ "type": "reference", "text": "..." }}
]

Raw text:
{raw_text}
"""

    models_to_try = ["llama-3.3-70b-versatile", "llama3-70b-8192"]

    last_error = None

    # We still use the retry utility, but we pass the client as 'model'
    # The utility now checks for .chat attribute which Groq client has

    try:
        # Use valid JSON mode if possible, but Groq JSON mode requires explicit json_object
        # For now we rely on the prompt instructions and text parsing or client enforced json
        # Llama 3.1 is good at following format.

        # Note: generate_with_retry handles the specific call structure
        response_text = generate_with_retry(client, prompt, max_retries=3)

        if not response_text:
            raise ValueError("Empty response from AI model.")

        # Ensure we get just the JSON
        response_text = response_text.strip()

        # Robust regex extraction for list
        import re

        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if match:
            response_text = match.group(0)
        else:
            # Fallback to existing logic if regex fails (unlikely if list is present)
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

        return response_text

    except Exception as e:
        raise ValueError(f"Groq generation failed: {e}")
