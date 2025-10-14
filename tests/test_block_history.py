from datetime import datetime, UTC, timedelta

from src.services.block_history import BlockHistoryRepository


def test_in_memory_record_and_latest():
    repo = BlockHistoryRepository()
    assert repo.get_latest_event_time("truth_social") is None

    repo.record_event(source="truth_social", reason="http_403", metadata={"url": "https://example"})
    latest = repo.get_latest_event_time("truth_social")
    assert latest is not None
    assert isinstance(latest, datetime)


def test_in_memory_window_filter():
    repo = BlockHistoryRepository()
    now = datetime.now(UTC)
    old_time = now - timedelta(hours=10)

    repo._memory.append({"source": "truth_social", "reason": "old", "metadata": {}, "timestamp": old_time})
    repo.record_event(source="truth_social", reason="recent")

    latest = repo.get_latest_event_time("truth_social", window_seconds=60)
    assert latest is not None
    assert (datetime.now(UTC) - latest).total_seconds() < 10


class FakeCollection:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        self.docs.append(doc)

    def find_one(self, query, sort=None):
        source = query.get("source")
        cutoff = query.get("timestamp", {}).get("$gte") if "timestamp" in query else None
        candidates = [doc for doc in self.docs if doc["source"] == source and (cutoff is None or doc["timestamp"] >= cutoff)]
        if not candidates:
            return None
        candidates.sort(key=lambda d: d["timestamp"], reverse=True)
        return candidates[0]


def test_mongo_like_repository():
    fake_collection = FakeCollection()
    repo = BlockHistoryRepository(fake_collection)

    repo.record_event(source="nitter", reason="global_outage")
    ts = repo.get_latest_event_time("nitter")
    assert ts is not None

