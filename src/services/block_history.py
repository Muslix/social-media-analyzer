"""Block history persistence utilities."""
from __future__ import annotations

import logging
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BlockHistoryRepository:
    """Persist scraper block events to MongoDB or in-memory fallback."""

    def __init__(
        self,
        collection=None,
        retention_seconds: int = 7 * 24 * 3600,
    ) -> None:
        self.collection = collection
        self.retention_seconds = retention_seconds
        self._memory: List[Dict[str, Any]] = []

    def record_event(
        self,
        *,
        source: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a block event. Falls back to in-memory storage if Mongo is unavailable."""
        event = {
            "source": source,
            "reason": reason,
            "metadata": metadata or {},
            "timestamp": datetime.now(UTC),
        }

        if self.collection is None:
            self._memory.append(event)
            self._prune_memory()
            logger.debug("Recorded block event in memory: %s", event)
            return

        try:
            self.collection.insert_one(event)
            logger.debug("Recorded block event in Mongo: %s", event)
        except Exception as exc:
            logger.warning("Failed to persist block event to Mongo: %s", exc)
            self._memory.append(event)
            self._prune_memory()

    def get_latest_event_time(
        self,
        source: str,
        *,
        window_seconds: Optional[int] = None,
    ) -> Optional[datetime]:
        """Return the timestamp of the most recent block event for the source."""
        cutoff = None
        if window_seconds:
            cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)

        if self.collection is None:
            events = [
                evt for evt in self._memory
                if evt["source"] == source and (cutoff is None or evt["timestamp"] >= cutoff)
            ]
            if not events:
                return None
            return max(events, key=lambda evt: evt["timestamp"])["timestamp"]

        query: Dict[str, Any] = {"source": source}
        if cutoff:
            query["timestamp"] = {"$gte": cutoff}

        try:
            doc = self.collection.find_one(query, sort=[("timestamp", -1)])
        except Exception as exc:
            logger.warning("Failed to read block history from Mongo: %s", exc)
            return None

        if not doc:
            return None

        timestamp = doc.get("timestamp")
        if isinstance(timestamp, datetime):
            return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=UTC)
        return None

    def load_recent_events(
        self,
        sources: List[str],
        *,
        window_seconds: int,
    ) -> Dict[str, datetime]:
        """Load latest events for several sources."""
        result: Dict[str, datetime] = {}
        for source in sources:
            ts = self.get_latest_event_time(source, window_seconds=window_seconds)
            if ts:
                result[source] = ts
        return result

    def _prune_memory(self) -> None:
        """Trim in-memory history to retention window."""
        if not self._memory:
            return
        cutoff = datetime.now(UTC) - timedelta(seconds=self.retention_seconds)
        self._memory = [evt for evt in self._memory if evt["timestamp"] >= cutoff]
