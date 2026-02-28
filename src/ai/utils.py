import re
import time
import random
import logging
import groq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_with_retry(model, prompt, config=None, max_retries=3, base_delay=2):
    """
    Generates content using the provided AI model (Groq/Llama 3) with exponential backoff for rate limits.

    Args:
        model: The initialized Groq client instance.
        prompt: The prompt string.
        config: Optional generation config (dict or GenerationConfig).
        max_retries: Maximum number of retries (default 3).
        base_delay: Initial delay in seconds (default 2).

    Returns:
        The generated text content.

    Raises:
        Exception: If generation fails after all retries.
    """
    for attempt in range(max_retries):
        try:
            # Check if model object has 'chat' attribute (Groq client)
            if hasattr(model, "chat"):
                completion = model.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=2048,
                    top_p=0.05,
                    seed=42,
                    stop=None,
                    stream=False,
                )
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

            # Check for Groq RateLimitError (usually 429)
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str.lower()
                or "too many requests" in error_str.lower()
            )

            if is_rate_limit:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for prompt. Last error: {e}")
                    raise e  # Re-raise if last attempt

                # Try to parse wait time from error message
                wait_time = 0
                # Groq often returns "Please try again in Xs" or similar
                match = re.search(r"try again in (\d+(\.\d+)?)s", error_str)
                if match:
                    wait_time = float(match.group(1))
                    delay = wait_time + 0.5
                    logger.warning(
                        f"Rate limit hit. API requested wait of {wait_time:.2f}s. Sleeping for {delay:.2f}s."
                    )
                else:
                    # Short exponential backoff
                    delay = (base_delay * (2**attempt)) + random.uniform(0.5, 1.5)  # nosec B311
                    logger.warning(
                        f"Rate limit hit (Attempt {attempt+1}/{max_retries}). Retrying in {delay:.2f} seconds..."
                    )

                print(f"⏳ Rate limit hit — waiting {delay:.1f}s before retry...")
                time.sleep(delay)
            else:
                logger.error(f"Non-retriable error: {e}")
                raise e  # Re-raise other errors immediately
    return ""
