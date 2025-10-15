"""Market impact tracking for post-driven events."""
from __future__ import annotations

import csv
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from io import StringIO
from typing import Any, Callable, Dict, List, Optional, Protocol

import requests

logger = logging.getLogger(__name__)


class PriceProviderError(RuntimeError):
    """Raised when a price provider fails to return data."""


class PriceProvider(Protocol):
    """Protocol describing a simple price provider."""

    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Return price data keyed by requested symbol."""


class MarketImpactRepository:
    """Persist market impact snapshots to MongoDB (with in-memory fallback)."""

    def __init__(self, collection=None) -> None:
        self.collection = collection
        self._memory: List[Dict[str, Any]] = []

    def record_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Persist a single snapshot document."""
        doc = dict(snapshot)
        doc.setdefault("_id", uuid.uuid4().hex)

        if "captured_at" in doc and isinstance(doc["captured_at"], datetime):
            captured_at = doc["captured_at"]
        else:
            captured_at = datetime.now(UTC)
        doc["captured_at"] = captured_at

        if self.collection is None:
            self._memory.append(doc)
            logger.debug("Stored market impact snapshot in memory: %s", doc)
            return

        try:
            self.collection.insert_one(doc)
            logger.debug("Stored market impact snapshot in MongoDB: %s", doc["_id"])
        except Exception as exc:  # pragma: no cover - network/database issues
            logger.warning("Failed to persist market impact snapshot to MongoDB: %s", exc)
            self._memory.append(doc)

    def memory_snapshots(self) -> List[Dict[str, Any]]:
        """Expose in-memory snapshots (primarily for testing)."""
        return list(self._memory)


@dataclass
class TrackingTask:
    """Active tracking task for an event."""

    event_id: str
    urgency: str
    interval_seconds: int
    end_time: datetime
    next_run: datetime
    crypto_symbols: List[str] = field(default_factory=list)
    index_symbols: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    run_count: int = 0


class MarketImpactTracker:
    """Schedule and capture market data snapshots for impactful events."""

    URGENCY_PROFILES: Dict[str, Dict[str, int]] = {
        "immediate": {
            "interval_seconds": 600,     # every 10 minutes
            "duration_seconds": 6 * 3600,  # 6 hours
        },
        "hours": {
            "interval_seconds": 1200,    # every 20 minutes
            "duration_seconds": 24 * 3600,  # 24 hours
        },
    }

    def __init__(
        self,
        *,
        repository: MarketImpactRepository,
        crypto_provider: Optional[PriceProvider] = None,
        index_provider: Optional[PriceProvider] = None,
        enabled: bool = True,
        crypto_symbols: Optional[List[str]] = None,
        index_symbols: Optional[List[str]] = None,
        now_fn: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.repository = repository
        self.crypto_provider = crypto_provider
        self.index_provider = index_provider
        self.enabled = enabled
        self.crypto_symbols = [sym.lower() for sym in (crypto_symbols or [])]
        self.index_symbols = [sym.lower() for sym in (index_symbols or [])]
        self._now = now_fn or (lambda: datetime.now(UTC))
        self._tasks: List[TrackingTask] = []
        self._scheduled_events: set[str] = set()

    def handle_analysis_event(
        self,
        *,
        event_id: str,
        llm_analysis: Dict[str, Any],
        market_analysis: Optional[Dict[str, Any]] = None,
        post_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Trigger tracking for an analysis event based on urgency."""
        if not self.enabled:
            return False
        if not llm_analysis:
            return False

        urgency = (llm_analysis.get("urgency") or "").strip().lower()
        if urgency not in self.URGENCY_PROFILES:
            logger.debug("Urgency '%s' not configured for impact tracking", urgency)
            return False

        metadata: Dict[str, Any] = {
            "llm_score": llm_analysis.get("score"),
            "llm_urgency": urgency,
            "llm_reasoning": llm_analysis.get("reasoning"),
            "llm_model": llm_analysis.get("model"),
            "market_score": (market_analysis or {}).get("impact_score"),
            "impact_level": (market_analysis or {}).get("impact_level"),
        }
        metadata.update(post_metadata or {})

        return self.schedule_event_tracking(
            event_id=event_id,
            urgency=urgency,
            metadata=metadata,
        )

    def schedule_event_tracking(
        self,
        *,
        event_id: str,
        urgency: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Schedule recurring snapshots for a specific event."""
        urgency_key = urgency.strip().lower()
        profile = self.URGENCY_PROFILES.get(urgency_key)

        if not self.enabled:
            logger.debug("Market impact tracker disabled; not scheduling event %s", event_id)
            return False

        if profile is None:
            logger.debug("No tracking profile for urgency '%s'", urgency)
            return False

        if not self.crypto_symbols and not self.index_symbols:
            logger.debug("No assets configured for tracking; skipping schedule for %s", event_id)
            return False

        if event_id in self._scheduled_events:
            logger.debug("Event %s already scheduled for impact tracking", event_id)
            return False

        now = self._now()
        task = TrackingTask(
            event_id=event_id,
            urgency=urgency_key,
            interval_seconds=profile["interval_seconds"],
            end_time=now + timedelta(seconds=profile["duration_seconds"]),
            next_run=now,
            crypto_symbols=self.crypto_symbols.copy(),
            index_symbols=self.index_symbols.copy(),
            metadata=metadata or {},
        )

        self._tasks.append(task)
        self._scheduled_events.add(event_id)
        logger.info(
            "Scheduled market impact tracking for %s (urgency: %s, interval: %ss, until: %s)",
            event_id,
            urgency_key,
            task.interval_seconds,
            task.end_time.isoformat(),
        )

        # Capture immediately upon scheduling
        self._capture_snapshot(task, now, initial=True)
        task.run_count += 1
        task.next_run = now + timedelta(seconds=task.interval_seconds)
        return True

    def run_pending(self, *, now: Optional[datetime] = None) -> None:
        """Execute any due tracking tasks."""
        if not self.enabled or not self._tasks:
            return

        current_time = now or self._now()
        active_tasks: List[TrackingTask] = []

        for task in self._tasks:
            while current_time >= task.next_run and current_time <= task.end_time:
                self._capture_snapshot(task, current_time)
                task.run_count += 1
                task.next_run += timedelta(seconds=task.interval_seconds)

            if current_time <= task.end_time:
                active_tasks.append(task)
            else:
                logger.debug(
                    "Completed market impact tracking for %s after %s runs",
                    task.event_id,
                    task.run_count,
                )

        self._tasks = active_tasks

    def _capture_snapshot(self, task: TrackingTask, timestamp: datetime, initial: bool = False) -> None:
        """Collect market data for a single task execution."""
        snapshot: Dict[str, Any] = {
            "event_id": task.event_id,
            "urgency": task.urgency,
            "captured_at": timestamp,
            "sequence": task.run_count,
            "interval_seconds": task.interval_seconds,
            "initial_capture": initial,
            "metadata": task.metadata,
            "crypto": {},
            "indices": {},
        }

        if self.crypto_provider and task.crypto_symbols:
            try:
                snapshot["crypto"] = self.crypto_provider.fetch_prices(task.crypto_symbols)
            except PriceProviderError as exc:
                snapshot["crypto_error"] = str(exc)
                logger.warning("Crypto provider failed for %s: %s", task.event_id, exc)

        if self.index_provider and task.index_symbols:
            try:
                snapshot["indices"] = self.index_provider.fetch_prices(task.index_symbols)
            except PriceProviderError as exc:
                snapshot["index_error"] = str(exc)
                logger.warning("Index provider failed for %s: %s", task.event_id, exc)

        self.repository.record_snapshot(snapshot)


class CoinGeckoCryptoProvider:
    """Fetch cryptocurrency spot prices from CoinGecko."""

    API_URL = "https://api.coingecko.com/api/v3/simple/price"

    def __init__(
        self,
        *,
        id_map: Optional[Dict[str, str]] = None,
        vs_currency: str = "usd",
        session: Optional[requests.Session] = None,
        timeout_seconds: int = 10,
    ) -> None:
        self.id_map = {k.lower(): v for k, v in (id_map or {}).items()}
        self.vs_currency = vs_currency
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        ids: List[str] = []
        alias_map: Dict[str, str] = {}

        for symbol in symbols:
            asset = symbol.lower()
            coingecko_id = self.id_map.get(asset)
            if not coingecko_id:
                logger.debug("No CoinGecko mapping for symbol '%s'", asset)
                continue
            if coingecko_id not in alias_map:
                ids.append(coingecko_id)
                alias_map[coingecko_id] = asset

        if not ids:
            return {}

        params = {
            "ids": ",".join(ids),
            "vs_currencies": self.vs_currency,
            "include_last_updated_at": "true",
        }

        try:
            response = self.session.get(
                self.API_URL,
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:  # pragma: no cover - network failures
            raise PriceProviderError(f"CoinGecko request failed: {exc}") from exc
        except ValueError as exc:  # pragma: no cover - JSON decode errors
            raise PriceProviderError(f"CoinGecko returned invalid JSON: {exc}") from exc

        results: Dict[str, Dict[str, Any]] = {}
        for asset_id, data in payload.items():
            symbol = alias_map.get(asset_id)
            if not symbol:
                continue

            price = data.get(self.vs_currency)
            results[symbol] = {
                "price": price,
                "currency": self.vs_currency,
                "provider": "coingecko",
                "asset_id": asset_id,
                "raw": data,
            }
        return results


class StooqIndexProvider:
    """Fetch index levels from Stooq CSV endpoint."""

    API_URL = "https://stooq.com/q/l/"

    def __init__(
        self,
        *,
        symbol_map: Dict[str, str],
        currency_map: Optional[Dict[str, str]] = None,
        session: Optional[requests.Session] = None,
        timeout_seconds: int = 10,
    ) -> None:
        self.symbol_map = {k.lower(): v for k, v in symbol_map.items() if v}
        self.currency_map = {k.lower(): v for k, v in (currency_map or {}).items()}
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for alias in symbols:
            key = alias.lower()
            stooq_symbol = self.symbol_map.get(key)
            if not stooq_symbol:
                logger.debug("No Stooq mapping for symbol '%s'", alias)
                continue

            params = {
                "s": stooq_symbol.lower(),
                "f": "sd2t2ohlcv",
                "h": "",
                "e": "csv",
            }

            try:
                response = self.session.get(
                    self.API_URL,
                    params=params,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
            except requests.RequestException as exc:  # pragma: no cover - network failures
                raise PriceProviderError(f"Stooq request failed: {exc}") from exc

            reader = csv.DictReader(StringIO(response.text))
            row = next(reader, None)
            if not row:
                continue

            close_value = row.get("Close")
            try:
                price = float(close_value) if close_value is not None else None
            except ValueError:
                price = None

            results[key] = {
                "price": price,
                "currency": self.currency_map.get(key),
                "provider": "stooq",
                "symbol": stooq_symbol,
                "raw": row,
            }

        return results
