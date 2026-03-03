"""
Per-seller in-memory rate limiter.

Tracks message counts per seller_id within a rolling 60-second window.
Uses a deque of timestamps so expired entries are automatically dropped.
Thread-safe via a threading.Lock (FastAPI runs sync code on a thread pool).
"""
import threading
import time
from collections import defaultdict, deque
from typing import Deque

# Max messages per seller per 60-second window.
SELLER_RATE_LIMIT = 10
WINDOW_SECONDS = 60

_lock = threading.Lock()
_windows: dict[str, Deque[float]] = defaultdict(deque)


def is_rate_limited(seller_id: str) -> bool:
    """
    Returns True if the seller has exceeded SELLER_RATE_LIMIT messages
    in the last WINDOW_SECONDS. Otherwise records the call and returns False.
    """
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS

    with _lock:
        window = _windows[seller_id]
        # Drop timestamps outside the rolling window
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= SELLER_RATE_LIMIT:
            return True

        window.append(now)
        return False


def current_count(seller_id: str) -> int:
    """Returns the number of messages sent by seller_id in the current window."""
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS
    with _lock:
        window = _windows[seller_id]
        while window and window[0] < cutoff:
            window.popleft()
        return len(window)
