import json
from itertools import islice
from pathlib import Path

import pytest

from src.analyzers.market_analyzer import MarketImpactAnalyzer


def test_analyze_returns_none_for_empty_text():
    analyzer = MarketImpactAnalyzer()
    assert analyzer.analyze("") is None
    assert analyzer.analyze("   ") is None


def test_analyze_detects_critical_signals():
    analyzer = MarketImpactAnalyzer()
    text = (
        "Breaking: The executive order imposes a 50% tariff effective immediately on imports. "
        "This aggressive action targets major trading partners."
    )

    result = analyzer.analyze(text)
    assert result is not None
    assert result["impact_score"] >= 50
    assert "critical_triggers" in result["details"]
    assert result["impact_level"].startswith("🔴")
    assert result["details"]["percentages"]["values"][0] == 50.0
    assert result["details"]["keywords"]["critical"]


def test_keyword_density_preserves_high_signal_text():
    analyzer = MarketImpactAnalyzer()
    dense_text = " ".join(["tariff"] * 40 + ["china"] * 40 + ["tariffs"] * 20)

    adjusted, _, meta = analyzer._analyze_keywords(dense_text.lower())

    assert adjusted == meta["raw_score"]
    assert meta["length_factor"] == pytest.approx(1.0)
    assert meta["density_factor"] == pytest.approx(1.0)
    assert meta["combined_factor"] == pytest.approx(1.0)
    assert meta["unique_keywords_matched"] == 3
    assert meta["keyword_occurrences"] == 100
    assert meta["keywords_per_100_words"] == pytest.approx(100.0, rel=0.01)


def test_keyword_density_penalizes_sparse_long_text():
    analyzer = MarketImpactAnalyzer()
    long_tokens = ["word"] * 995 + ["tariff"] * 5  # 1000 words with sparse hits
    long_text = " ".join(long_tokens)

    adjusted, _, meta = analyzer._analyze_keywords(long_text.lower())

    assert meta["raw_score"] == 10  # tariff weight counted once
    assert meta["keyword_occurrences"] == 5
    assert meta["keywords_per_100_words"] == pytest.approx(0.5, rel=0.05)
    assert meta["density_factor"] < 0.2
    assert meta["combined_factor"] == pytest.approx(0.2, rel=0.01)
    assert adjusted == int(round(meta["raw_score"] * meta["combined_factor"]))
    assert meta["word_count"] == 1000
    assert meta["length_factor"] < 1.0


def _load_training_entries(limit: int = 100):
    data_path = Path(__file__).resolve().parent.parent / "training_data/llm_training_data.jsonl"
    entries = []
    with data_path.open("r", encoding="utf-8") as handle:
        for line in islice(handle, limit):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            entries.append(payload)
    return entries


def test_training_data_keyword_ordering():
    entries = [e for e in _load_training_entries() if e.get("keyword_score")]
    assert entries, "Expected at least one entry with keyword_score in training data"

    analyzer = MarketImpactAnalyzer()
    lowest_entry = min(entries, key=lambda item: item["keyword_score"])
    highest_entry = max(entries, key=lambda item: item["keyword_score"])

    low_adj, _, low_meta = analyzer._analyze_keywords(lowest_entry["post_text"].lower())
    high_adj, _, high_meta = analyzer._analyze_keywords(highest_entry["post_text"].lower())

    assert high_adj >= low_adj
    assert high_meta["raw_score"] >= low_meta["raw_score"]
    assert 0.2 <= high_meta["combined_factor"] <= 1.0
    assert 0.2 <= low_meta["combined_factor"] <= 1.0


def test_training_data_keyword_meta_invariants():
    analyzer = MarketImpactAnalyzer()
    samples = [e for e in _load_training_entries(30) if e.get("post_text")]
    assert samples, "Training data did not provide any text samples"

    for entry in samples:
        adjusted, _, meta = analyzer._analyze_keywords(entry["post_text"].lower())
        if meta["raw_score"] == 0:
            assert adjusted == 0
            continue
        assert meta["keyword_occurrences"] >= meta["unique_keywords_matched"] >= 1
        assert adjusted <= meta["raw_score"]
        assert 0.2 <= meta["combined_factor"] <= 1.0
        assert meta["keywords_per_100_words"] >= 0
