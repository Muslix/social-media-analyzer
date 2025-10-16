"""Simple rate limiter utilities."""
from __future__ import annotations

import threading
import time
from typing import Optional


class RateLimiter:
    """
    Enforce a minimum interval between calls across threads.

    Example:
        limiter = RateLimiter(min_interval_seconds=2.0)
        limiter.wait()  # blocks until 2 seconds have passed since last wait()
    """

    def __init__(self, *, min_interval_seconds: float) -> None:
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")
        self.min_interval_seconds = min_interval_seconds
        self._lock = threading.Lock()
        self._last_call: Optional[float] = None

    def wait(self) -> None:
        """
        Block until the minimum interval has elapsed since the previous call.
        """
        if self.min_interval_seconds <= 0:
            return

        with self._lock:
            now = time.monotonic()
            if self._last_call is None:
                self._last_call = now
                return

            elapsed = now - self._last_call
            remaining = self.min_interval_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)
                now = time.monotonic()

            self._last_call = now
