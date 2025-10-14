from src.data import keywords


def test_get_all_weighted_keywords_structure():
    weighted = keywords.get_all_weighted_keywords()
    assert set(weighted.keys()) == {"critical", "high", "medium", "companies"}
    assert "tariff" in weighted["critical"]
    assert weighted["critical"]["tariff"] == 10


def test_get_keyword_stats_consistency():
    stats = keywords.get_keyword_stats()
    assert stats["total_keywords"] == (
        stats["critical"]
        + stats["high"]
        + stats["medium"]
        + stats["companies"]
        + stats["action_verbs"]
    )
    assert stats["critical_combinations"] == len(keywords.CRITICAL_COMBINATIONS)
