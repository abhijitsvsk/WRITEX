import re
import time
import random
import logging
from src.ai.provider_client import GROQ_DEFAULT_MODEL

# System-level persona injected into every LLM call.
# A strong system prompt is the single most effective way to prevent hallucination
# and enforce academic tone across all generated sections.
ACADEMIC_SYSTEM_PROMPT = (
    "You are a strict Academic Editor specialising in B.Tech Computer Science project reports. "
    "You write in a formal, third-person academic register. "
    "CRITICAL RULES you must ALWAYS follow:\n"
    "1. Ground ALL content in the project metadata provided. Never invent data, metrics, datasets, "
    "author names, library names, or paper references that are not in the supplied context.\n"
    "2. Never mention raw Python filenames (e.g. formatting.py). Use abstract module names "
    "(e.g. 'The Formatting Engine', 'The Parsing Module').\n"
    "3. Each section must read as a uniquely crafted academic paragraph. "
    "Never reuse the same opening sentence across sections.\n"
    "4. Do not output meta-commentary, apologies, or AI disclaimers. Output ONLY the requested content."
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global telemetry dictionary
telemetry_data = {
    "total_api_calls": 0,
    "total_retries": 0,
    "total_rate_limits": 0,
}

# Production AI Settings
TARGET_MODEL_VERSION = GROQ_DEFAULT_MODEL


def generate_with_retry(model, prompt, config=None, max_retries=10, base_delay=5, response_format=None):
    """
    Generates content using the provided AI model (Groq/Llama 3) with exponential backoff for rate limits.

    Args:
        model: The initialized Groq client instance.
        prompt: The prompt string.
        config: Optional generation config (dict or GenerationConfig).
        max_retries: Maximum number of retries (default 5).
        base_delay: Initial delay in seconds (default 2).
        response_format: Optional JSON enforcement format (e.g. {"type": "json_object"}).

    Returns:
        The generated text content.

    Raises:
        RuntimeError: If generation fails after all retries or hits a non-retriable error.
    """
    global telemetry_data
    telemetry_data["total_api_calls"] += 1
    
    for attempt in range(max_retries):
        try:
            # Check if model object has 'chat' attribute (Groq client)
            if hasattr(model, "chat"):
                target_model = getattr(model, "default_model", TARGET_MODEL_VERSION)
                kwargs = {
                    "model": target_model,
                    "messages": [
                        {"role": "system", "content": ACADEMIC_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                    "top_p": 0.9,
                    "stop": None,
                    "stream": False,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                completion = model.chat.completions.create(**kwargs)
                return completion.choices[0].message.content
            else:
                # Fallback for other potential clients or mocked objects
                if hasattr(model, "generate_content"):
                    response = model.generate_content(prompt, generation_config=config)
                    return response.text
                else:
                    raise ValueError("Unsupported model client type")

        except Exception as e:
            error_str = str(e)
            
            # Check if this error is retriable
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str.lower()
                or "too many requests" in error_str.lower()
            )
            
            is_server_error = (
                "503" in error_str
                or "500" in error_str
                or "502" in error_str
                or "504" in error_str
                or "over capacity" in error_str.lower()
                or "internal server error" in error_str.lower()
            )

            if is_rate_limit or is_server_error:
                if is_rate_limit:
                    telemetry_data["total_rate_limits"] += 1
                
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for prompt. Last error: {e}")
                    raise RuntimeError(f"API Error: Exhausted maximum retries ({max_retries}). {error_str}")

                # Determine delay
                wait_time = 0
                match = re.search(r"try again in (\d+(\.\d+)?)s", error_str)
                if match:
                    wait_time = float(match.group(1))
                    delay = wait_time + 1.0
                    logger.warning(
                        f"Retry triggered by API message. Wait of {wait_time:.2f}s. Sleeping for {delay:.2f}s."
                    )
                else:
                    # Generic exponential backoff for 429 or 5xx
                    delay = (base_delay * (2**attempt)) + random.uniform(0.5, 1.5)
                    
                    if is_server_error:
                        # Be slightly more patient for server-side issues
                        delay += 2.0
                        logger.warning(
                            f"Server error / Over capacity hit (Attempt {attempt+1}/{max_retries}). Retrying in {delay:.2f}s..."
                        )
                    else:
                        logger.warning(
                            f"Rate limit hit (Attempt {attempt+1}/{max_retries}). Retrying in {delay:.2f}s..."
                        )

                print(f"API Busy/Error ({'503' if is_server_error else '429'}) — waiting {delay:.1f}s...")
                time.sleep(delay)
                telemetry_data["total_retries"] += 1
            else:
                logger.error(f"Non-retriable error: {e}")
                raise RuntimeError(f"API Error: {error_str}")
                
    raise RuntimeError("Unexpected failure: exited retry loop without returning or raising.")
