import re
from typing import Any


class DataSanitizer:
    """
    Scrub PII and secrets (like AWS keys, tokens, passwords) before sending
    AST representations to the Groq LLM API.
    """

    # Pre-compiled high-risk patterns
    SECRET_PATTERNS = [
        # AWS Access Key ID
        re.compile(
            r'(?i)(?:aws_?)?(?:access_?)?key_?(?:id)?\s*[:=]\s*["\']?(AKIA[0-9A-Z]{16})["\']?'
        ),
        # AWS Secret Access Key
        re.compile(
            r'(?i)(?:aws_?)?(?:secret_?)?(?:access_?)?key\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?'
        ),
        # Generic API Keys / Passwords
        re.compile(
            r'(?i)(?:api_?key|token|password|secret|pwd)\s*[:=]\s*["\']([^"\']{8,})["\']'
        ),
        # Google API Key / GCP Secrets
        re.compile(
            r'(?i)(?:gcp_?)?(?:api_?)?key\s*[:=]\s*["\'](AIza[0-9A-Za-z-_]{35})["\']'
        ),
    ]

    PII_PATTERNS = [
        # Standard Email pattern
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    ]

    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """Sanitizes a single string."""
        if not isinstance(text, str):
            return text

        redacted = text

        # Scrub Secrets (Replacing captured groups with Redacted tags)
        for pattern in cls.SECRET_PATTERNS:

            def _repl(match):
                if match.lastindex and match.lastindex >= 1:
                    secret_val = match.group(1)
                    return match.group(0).replace(secret_val, "[REDACTED_SECRET]")
                return match.group(0)

            redacted = pattern.sub(_repl, redacted)

        # Scrub PII
        for pattern in cls.PII_PATTERNS:
            redacted = pattern.sub("[REDACTED_PII]", redacted)

        return redacted

    @classmethod
    def sanitize_payload(cls, payload: Any) -> Any:
        """Recursively sanitizes dictionaries and lists (e.g., AST Project Summary)."""
        if isinstance(payload, str):
            return cls.sanitize_string(payload)
        elif isinstance(payload, dict):
            return {k: cls.sanitize_payload(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [cls.sanitize_payload(i) for i in payload]
        return payload
