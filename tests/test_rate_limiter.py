import time
import threading
import pytest
from src.ai.rate_limiter import TokenBucketLimiter, get_rate_limiter

def test_immediate_token_acquisition():
    limiter = TokenBucketLimiter(capacity=5.0, refill_rate_per_sec=1.0)
    assert limiter.acquire(1.0, timeout=1.0) is True
    assert limiter.tokens < 5.0

def test_token_exhaustion_and_refill():
    limiter = TokenBucketLimiter(capacity=2.0, refill_rate_per_sec=5.0)
    assert limiter.acquire(2.0, timeout=0.5) is True
    
    # Needs 0.2s to refill 1 token (5 tokens/sec)
    start = time.monotonic()
    assert limiter.acquire(1.0, timeout=1.0) is True
    elapsed = time.monotonic() - start
    assert elapsed >= 0.15

def test_token_timeout_exceeded():
    limiter = TokenBucketLimiter(capacity=1.0, refill_rate_per_sec=0.1)
    assert limiter.acquire(1.0, timeout=0.1) is True
    
    # Requesting 2 tokens when refill is 0.1/sec with 0.1s timeout should fail
    assert limiter.acquire(2.0, timeout=0.1) is False

def test_multithreaded_concurrency():
    limiter = TokenBucketLimiter(capacity=50.0, refill_rate_per_sec=100.0)
    acquired_count = 0
    lock = threading.Lock()

    def worker():
        nonlocal acquired_count
        if limiter.acquire(1.0, timeout=2.0):
            with lock:
                acquired_count += 1

    threads = [threading.Thread(target=worker) for _ in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert acquired_count == 30

def test_get_rate_limiter_singleton():
    groq_limiter_1 = get_rate_limiter("groq")
    groq_limiter_2 = get_rate_limiter("GROQ")
    assert groq_limiter_1 is groq_limiter_2
