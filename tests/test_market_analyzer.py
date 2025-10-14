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
