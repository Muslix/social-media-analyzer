from datetime import datetime, timedelta, UTC
from typing import Dict, List

import pytest

from src.services.market_impact_tracker import (
    MarketImpactRepository,
    MarketImpactTracker,
    PriceProviderError,
)


class TimeStub:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


class FakeProvider:
    def __init__(self, price: float = 100.0) -> None:
        self.price = price
        self.calls = []

    def fetch_prices(self, symbols):
        self.calls.append(list(symbols))
        return {
            symbol: {
                "price": self.price,
                "currency": "usd",
                "provider": "fake",
            }
            for symbol in symbols
        }

class SequenceProvider:
    def __init__(self, prices: List[float]) -> None:
        self.prices = prices
        self.index = 0
        self.calls: List[List[str]] = []

    def fetch_prices(self, symbols):
        price = self.prices[self.index] if self.index < len(self.prices) else self.prices[-1]
        self.index += 1
        self.calls.append(list(symbols))
        return {
            symbol: {
                "price": price,
                "currency": "usd",
                "provider": "sequence",
            }
            for symbol in symbols
        }


class FailingProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error or PriceProviderError("boom")
        self.calls = 0

    def fetch_prices(self, symbols):
        self.calls += 1
        raise self.error


class FailureNotifierStub:
    def __init__(self) -> None:
        self.alerts: List[Dict[str, object]] = []

    def send_failure_alert(self, title: str, description: str, details=None) -> None:
        self.alerts.append(
            {
                "title": title,
                "description": description,
                "details": details,
            }
        )


def make_tracker(time_stub: TimeStub, **overrides):
    repository = overrides.get("repository", MarketImpactRepository(jsonl_path=None))
    crypto_provider = overrides.get("crypto_provider", FakeProvider())

    tracker = MarketImpactTracker(
        repository=repository,
        crypto_provider=crypto_provider,
        index_provider=overrides.get("index_provider"),
        enabled=overrides.get("enabled", True),
        crypto_symbols=overrides.get("crypto_symbols", ["btc", "eth"]),
        index_symbols=overrides.get("index_symbols", []),
        now_fn=time_stub.now,
        failure_notifier=overrides.get("failure_notifier"),
    )
    return tracker, repository, crypto_provider


def test_schedule_immediate_triggers_initial_snapshot():
    time_stub = TimeStub(datetime(2025, 1, 1, tzinfo=UTC))
    tracker, repo, provider = make_tracker(time_stub)

    scheduled = tracker.schedule_event_tracking(
        event_id="event-1",
        urgency="immediate",
        metadata={"post_id": "event-1"},
    )

    assert scheduled is True
    assert len(repo.memory_snapshots()) == 1
    first_snapshot = repo.memory_snapshots()[0]
    assert first_snapshot["event_id"] == "event-1"
    assert first_snapshot["crypto"]["btc"]["price"] == pytest.approx(100.0)
    assert first_snapshot["initial_capture"] is True
    assert provider.calls == [["btc", "eth"]]

    time_stub.advance(600)
    tracker.run_pending()
    assert len(repo.memory_snapshots()) == 2
    second_snapshot = repo.memory_snapshots()[1]
    assert second_snapshot["sequence"] == 1
    assert second_snapshot["initial_capture"] is False


def test_schedule_hours_completes_after_end_time():
    time_stub = TimeStub(datetime(2025, 1, 1, tzinfo=UTC))
    tracker, repo, provider = make_tracker(
        time_stub,
        crypto_symbols=["btc"],
    )

    tracker.schedule_event_tracking(event_id="event-2", urgency="hours")
    assert len(repo.memory_snapshots()) == 1  # initial capture

    # simulate a handful of scheduled captures
    for _ in range(3):
        time_stub.advance(1200)
        tracker.run_pending()

    assert len(provider.calls) >= 4  # initial + 3 scheduled captures

    # advance beyond end time to finish the task
    time_stub.advance(24 * 3600)
    tracker.run_pending()


def test_duplicate_schedule_is_ignored():
    time_stub = TimeStub(datetime(2025, 1, 1, tzinfo=UTC))
    tracker, repo, _ = make_tracker(time_stub)

    assert tracker.schedule_event_tracking(event_id="event-3", urgency="immediate") is True
    assert tracker.schedule_event_tracking(event_id="event-3", urgency="immediate") is False
    assert len(repo.memory_snapshots()) == 1


def test_handle_analysis_event_filters_urgency():
    time_stub = TimeStub(datetime(2025, 1, 1, tzinfo=UTC))
    tracker, repo, _ = make_tracker(time_stub)

    llm_analysis = {"urgency": "days", "score": 55}
    scheduled = tracker.handle_analysis_event(
        event_id="event-4",
        llm_analysis=llm_analysis,
        market_analysis={"impact_score": 40},
        post_metadata={"platform": "rss"},
    )
    assert scheduled is False
    assert repo.memory_snapshots() == []


def test_handle_analysis_event_records_metadata():
    time_stub = TimeStub(datetime(2025, 1, 1, tzinfo=UTC))
    tracker, repo, _ = make_tracker(time_stub)

    tracker.handle_analysis_event(
        event_id="event-5",
        llm_analysis={"urgency": "immediate", "score": 80, "reasoning": "Big move"},
        market_analysis={"impact_score": 60, "impact_level": "🔴 CRITICAL"},
        post_metadata={"platform": "truth_social", "post_url": "https://example"},
    )
    snapshot = repo.memory_snapshots()[0]
    assert snapshot["metadata"]["llm_score"] == 80
    assert snapshot["metadata"]["platform"] == "truth_social"


def test_multiple_events_track_independently():
    start = datetime(2025, 1, 1, tzinfo=UTC)
    time_stub = TimeStub(start)
    tracker, repo, provider = make_tracker(
        time_stub,
        crypto_symbols=["btc"],
    )

    tracker.schedule_event_tracking(event_id="event-a", urgency="hours")
    tracker.schedule_event_tracking(event_id="event-b", urgency="immediate")

    # two initial captures
    assert [snap["event_id"] for snap in repo.memory_snapshots()] == ["event-a", "event-b"]

    # advance 10 minutes -> only immediate task fires einmal
    time_stub.advance(600)
    tracker.run_pending()

    snapshots = repo.memory_snapshots()
    assert snapshots[0]["event_id"] == "event-a"
    assert snapshots[1]["event_id"] == "event-b"
    assert snapshots[2]["event_id"] == "event-b"
    assert snapshots[2]["sequence"] == 1

    # advance weitere 10 Minuten -> beide Tasks laufen
    time_stub.advance(600)
    tracker.run_pending()

    snapshots = repo.memory_snapshots()
    assert snapshots[3]["event_id"] == "event-a"
    assert snapshots[3]["sequence"] == 1
    assert snapshots[4]["event_id"] == "event-b"
    assert snapshots[4]["sequence"] == 2

    # Providers wurden bei jedem Lauf für BTC aufgerufen
    assert len(provider.calls) == 5
    assert all(call == ["btc"] for call in provider.calls)


def test_analysis_generated_after_completion(monkeypatch):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    time_stub = TimeStub(start)
    provider = SequenceProvider([100.0, 101.5, 99.4, 102.0])
    tracker, repo, _ = make_tracker(
        time_stub,
        crypto_symbols=["btc"],
        crypto_provider=provider,
    )

    monkeypatch.setattr(
        MarketImpactTracker,
        "URGENCY_PROFILES",
        {
            "immediate": {"interval_seconds": 60, "duration_seconds": 180},
            "hours": MarketImpactTracker.URGENCY_PROFILES["hours"],
        },
    )

    tracker.schedule_event_tracking(event_id="event-impact", urgency="immediate")

    for _ in range(3):
        time_stub.advance(60)
        tracker.run_pending()

    time_stub.advance(60)  # advance beyond end window
    tracker.run_pending()

    reports = repo.memory_analysis_reports()
    assert len(reports) == 1
    analysis = reports[0]

    assert analysis["event_id"] == "event-impact"
    assert analysis["urgency"] == "immediate"
    assert analysis["runs"] >= 1

    crypto_stats = analysis["assets"]["crypto"]
    assert "btc" in crypto_stats
    btc = crypto_stats["btc"]
    assert pytest.approx(btc["change"]["percent"], rel=1e-5) == pytest.approx(2.0, rel=1e-5)
    assert pytest.approx(btc["high"]["price"], rel=1e-5) == pytest.approx(102.0, rel=1e-5)
    assert pytest.approx(btc["low"]["price"], rel=1e-5) == pytest.approx(99.4, rel=1e-5)
    assert isinstance(analysis["report"], str)


def test_failure_notifier_called_when_provider_fails():
    time_stub = TimeStub(datetime(2025, 1, 1, tzinfo=UTC))
    notifier = FailureNotifierStub()
    failing_provider = FailingProvider()

    tracker, repo, _ = make_tracker(
        time_stub,
        crypto_provider=failing_provider,
        crypto_symbols=["btc"],
        failure_notifier=notifier,
    )

    scheduled = tracker.schedule_event_tracking(event_id="event-fail", urgency="immediate")
    assert scheduled is True

    # Snapshot recorded with error
    snapshot = repo.memory_snapshots()[0]
    assert snapshot["crypto_error"]

    # Failure alert dispatched
    assert notifier.alerts, "Expected failure notifier to receive alert"
    alert = notifier.alerts[0]
    assert alert["title"] == "Market Impact Snapshot fehlgeschlagen"
    assert alert["details"]["event_id"] == "event-fail"
