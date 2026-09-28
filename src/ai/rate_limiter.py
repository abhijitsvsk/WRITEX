import time
import threading
from typing import Dict, Optional

class TokenBucketLimiter:
    """
    Thread-safe in-memory token bucket rate limiter.
    
    Refills at `refill_rate_per_sec` tokens per second up to `capacity`.
    Acquiring tokens blocks cooperatively until sufficient tokens are available or timeout expires.
    """
    def __init__(self, capacity: float = 60.0, refill_rate_per_sec: float = 1.0):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

    def acquire(self, tokens: float = 1.0, timeout: Optional[float] = 30.0) -> bool:
        """
        Cooperatively acquire `tokens`. Blocks if necessary until tokens are available.
        Returns True if acquired, False if timeout exceeded.
        """
        deadline = time.monotonic() + timeout if timeout is not None else None

        while True:
            with self._lock:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                
                # Calculate sleep duration needed for at least the missing tokens
                missing = tokens - self.tokens
                sleep_needed = missing / self.refill_rate if self.refill_rate > 0 else 0.1

            if deadline is not None and time.monotonic() + sleep_needed > deadline:
                return False

            # Sleep outside the lock so other threads can proceed
            time.sleep(min(sleep_needed, 0.2))

# Pre-configured global rate limiters per provider
_LIMITERS: Dict[str, TokenBucketLimiter] = {
    # Groq free tier / default: ~30 requests per minute burst-friendly
    "groq": TokenBucketLimiter(capacity=30.0, refill_rate_per_sec=0.5),
    # DeepSeek: ~60 requests per minute
    "deepseek": TokenBucketLimiter(capacity=60.0, refill_rate_per_sec=1.0),
    # Default fallback
    "default": TokenBucketLimiter(capacity=60.0, refill_rate_per_sec=1.0),
}
_LIMITERS_LOCK = threading.Lock()

def get_rate_limiter(provider: str) -> TokenBucketLimiter:
    """Retrieve or initialize the token bucket limiter for a given provider."""
    normalized = (provider or "default").strip().lower()
    with _LIMITERS_LOCK:
        if normalized not in _LIMITERS:
            _LIMITERS[normalized] = TokenBucketLimiter(capacity=30.0, refill_rate_per_sec=0.5)
        return _LIMITERS[normalized]
