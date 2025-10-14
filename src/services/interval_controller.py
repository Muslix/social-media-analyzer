"""Utility for computing adaptive wait intervals between fetch cycles."""
from __future__ import annotations

import random
from typing import Dict, Tuple, Optional


class IntervalController:
    """Computes randomized poll delays with optional backoff heuristics."""

    def __init__(self, config, rng: Optional[random.Random] = None) -> None:
        self.config = config
        self._rng = rng or random.Random()

    def compute_delay(self, *, blocked: bool, consecutive_empty: int) -> Tuple[int, Dict[str, int]]:
        """Return the next delay (seconds) and reasoning components."""
        base_delay = self._pick_base_delay()
        delay = base_delay
        reasons: Dict[str, int] = {"base": int(base_delay)}

        if blocked:
            blocked_delay = self._pick_blocked_delay()
            delay = max(delay, blocked_delay)
            reasons["blocked"] = int(blocked_delay)

        threshold = getattr(self.config, "EMPTY_FETCH_THRESHOLD", 0) or 0
        if threshold > 0 and consecutive_empty >= threshold:
            backoff_delay = self._compute_empty_backoff(consecutive_empty, base_delay)
            delay = max(delay, backoff_delay)
            reasons["empty_backoff"] = int(backoff_delay)

        return int(delay), reasons

    def _pick_base_delay(self) -> int:
        min_delay = getattr(self.config, "REPEAT_MIN_DELAY", None)
        max_delay = getattr(self.config, "REPEAT_MAX_DELAY", None)

        if min_delay is not None and max_delay is not None:
            low, high = sorted((int(min_delay), int(max_delay)))
            if low <= 0 or high <= 0:
                return int(self.config.REPEAT_DELAY)
            return self._rng.randint(low, high)

        return int(self.config.REPEAT_DELAY)

    def _pick_blocked_delay(self) -> int:
        min_backoff = getattr(self.config, "BLOCKED_BACKOFF_MIN", None)
        max_backoff = getattr(self.config, "BLOCKED_BACKOFF_MAX", None)

        if min_backoff is not None and max_backoff is not None:
            low, high = sorted((int(min_backoff), int(max_backoff)))
            if low > 0 and high > 0:
                return self._rng.randint(low, high)

        # Fallback: double the baseline delay when blocked
        return int(self.config.REPEAT_DELAY * 2)

    def _compute_empty_backoff(self, consecutive_empty: int, base_delay: int) -> int:
        threshold = getattr(self.config, "EMPTY_FETCH_THRESHOLD", 0) or 0
        multiplier = getattr(self.config, "EMPTY_FETCH_BACKOFF_MULTIPLIER", 1.5) or 1.5

        steps = consecutive_empty - threshold + 1
        backoff = base_delay
        for _ in range(steps):
            backoff *= multiplier

        return max(int(backoff), int(base_delay))
