from datetime import datetime, UTC
from types import SimpleNamespace

import pytest

from src.output.discord_notifier import DiscordNotifier


@pytest.fixture
def notifier():
    return DiscordNotifier("https://discord.test/webhook", username="Test Bot")


def test_send_market_alert_success(monkeypatch, notifier, caplog):
    captured_payload = {}

    def fake_post(url, json=None, timeout=None):
        assert url == notifier.webhook_url
        captured_payload["data"] = json
        return SimpleNamespace(status_code=204, raise_for_status=lambda: None)

    monkeypatch.setattr("src.output.discord_notifier.requests.post", fake_post)

    keyword_analysis = {
        "impact_level": "🔴 CRITICAL",
        "impact_score": 90,
        "details": {"critical_triggers": ["Emergency Order"]},
        "alert_emoji": "🔴",
        "summary": "Critical impact",
    }
    llm_analysis = {
        "score": 85,
        "reasoning": "Markets likely to react sharply.",
        "urgency": "immediate",
        "affected_markets": ["stocks", "forex"],
        "market_direction": {"stocks": "bearish", "forex": "usd_up"},
    }

    result = notifier.send_market_alert(
        post_text="Major policy shift announced.",
        keyword_analysis=keyword_analysis,
        llm_analysis=llm_analysis,
        post_url="https://example.com/post/1",
        author="@market_mover",
        post_created_at=datetime(2024, 1, 1, tzinfo=UTC).isoformat(),
    )

    assert result is True
    data = captured_payload["data"]
    assert data["username"] == "Test Bot"
    embed = data["embeds"][0]
    assert "Major policy shift" in embed["description"]
    assert embed["fields"][0]["name"].startswith("🤖 AI Analysis")


def test_send_market_alert_handles_request_error(monkeypatch, notifier):
    def fake_post(url, json=None, timeout=None):
        raise RuntimeError("network down")

    monkeypatch.setattr("src.output.discord_notifier.requests.post", fake_post)

    result = notifier.send_market_alert(
        post_text="Something happened.",
        keyword_analysis=None,
        llm_analysis=None,
    )
    assert result is False
