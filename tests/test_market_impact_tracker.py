from datetime import datetime, timedelta, UTC

import pytest

from src.services.market_impact_tracker import (
    MarketImpactRepository,
    MarketImpactTracker,
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


def make_tracker(time_stub: TimeStub, **overrides):
    repository = overrides.get("repository", MarketImpactRepository())
    crypto_provider = overrides.get("crypto_provider", FakeProvider())

    tracker = MarketImpactTracker(
        repository=repository,
        crypto_provider=crypto_provider,
        index_provider=overrides.get("index_provider"),
        enabled=overrides.get("enabled", True),
        crypto_symbols=overrides.get("crypto_symbols", ["btc", "eth"]),
        index_symbols=overrides.get("index_symbols", []),
        now_fn=time_stub.now,
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
