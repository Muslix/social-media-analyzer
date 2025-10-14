"""Quiet hours management utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta, UTC
from typing import Dict, List, Optional, Tuple

from zoneinfo import ZoneInfo


logger = logging.getLogger(__name__)


@dataclass
class QuietWindow:
    timezone: ZoneInfo
    start: time
    end: time

    def contains(self, aware_dt: datetime) -> Tuple[bool, Optional[datetime], Optional[datetime]]:
        """Return (is_inside, end_utc, end_local) for this quiet window."""
        local_dt = aware_dt.astimezone(self.timezone)
        local_time = local_dt.time()

        if self.start <= self.end:
            if self.start <= local_time < self.end:
                end_dt = datetime.combine(local_dt.date(), self.end, tzinfo=self.timezone)
                return True, end_dt.astimezone(UTC), end_dt
            return False, None, None

        # Window spans midnight
        if local_time >= self.start or local_time < self.end:
            end_date = local_dt.date()
            if local_time >= self.start:
                end_date = end_date + timedelta(days=1)
            end_dt = datetime.combine(end_date, self.end, tzinfo=self.timezone)
            return True, end_dt.astimezone(UTC), end_dt

        return False, None, None


class QuietHoursManager:
    def __init__(self, raw_config: Dict[str, Dict[str, List[Tuple[str, str]]]]):
        self.windows: Dict[str, List[QuietWindow]] = {}
        for label, payload in raw_config.items():
            tz_name = payload.get("timezone")
            ranges = payload.get("ranges", [])
            if not tz_name or not ranges:
                continue
            try:
                zone = ZoneInfo(tz_name)
            except Exception:
                logger.warning("Unknown timezone '%s' in quiet hours config for label %s", tz_name, label)
                continue

            window_list: List[QuietWindow] = []
            for start_str, end_str in ranges:
                try:
                    start_parts = [int(p) for p in start_str.split(':', 1)]
                    end_parts = [int(p) for p in end_str.split(':', 1)]
                    start_time = time(start_parts[0], start_parts[1] if len(start_parts) > 1 else 0)
                    end_time = time(end_parts[0], end_parts[1] if len(end_parts) > 1 else 0)
                except Exception:
                    logger.warning(
                        "Invalid quiet hour range '%s-%s' for label %s", start_str, end_str, label
                    )
                    continue
                window_list.append(QuietWindow(zone, start_time, end_time))

            if window_list:
                self.windows[label.upper()] = window_list

    def is_quiet(self, label: Optional[str], now: Optional[datetime] = None) -> bool:
        if not label:
            return False
        return self._current_window_end(label, now)[0]

    def time_until_available(
        self, label: Optional[str], now: Optional[datetime] = None
    ) -> Tuple[Optional[int], Optional[datetime]]:
        """Return seconds and local resume datetime if currently in quiet hours."""
        active, end_utc, end_local = self._current_window_end(label, now)
        if not active or not end_utc:
            return None, None
        now_utc = (now or datetime.now(UTC)).astimezone(UTC)
        delta = max(0, int((end_utc - now_utc).total_seconds()))
        return delta, end_local

    def _current_window_end(
        self, label: Optional[str], now: Optional[datetime]
    ) -> Tuple[bool, Optional[datetime], Optional[datetime]]:
        if not label:
            return False, None, None
        windows = self.windows.get(label.upper())
        if not windows:
            return False, None, None

        now = now or datetime.now(UTC)
        for window in windows:
            active, end_utc, end_local = window.contains(now)
            if active:
                return True, end_utc, end_local
        return False, None, None
