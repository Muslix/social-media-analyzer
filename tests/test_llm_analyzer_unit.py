import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.analyzers.llm_analyzer import LLMAnalyzer


@pytest.fixture
def fake_config():
    return SimpleNamespace(
        OLLAMA_URL="http://ollama.test",
        OLLAMA_MODEL="mock-model",
        OLLAMA_NUM_THREADS=0,
        LLM_ERROR_WEBHOOK_URL=None,
    )


@pytest.fixture
def llm(monkeypatch, fake_config):
    monkeypatch.setattr(LLMAnalyzer, "_verify_connection", lambda self: None)
    return LLMAnalyzer(config=fake_config, timeout=5)


def make_response(payload: dict):
    return {
        "status_code": 200,
        "json": lambda: payload,
        "raise_for_status": lambda: None,
    }


def test_parse_llm_response_handles_code_block(llm):
    raw = """
    ```json
    {
        "score": 80,
        "reasoning": "Clear policy change impacting markets.",
        "urgency": "immediate"
    }
    ```
    """
    parsed = llm._parse_llm_response(raw)
    assert parsed["score"] == 80
    assert parsed["urgency"] == "immediate"


def test_parse_llm_response_sanitizes_newlines(llm):
    raw = """
    {
        "score": 88,
        "reasoning": "Line one
Line two mentions \\\"quotes\\\" and breaks",
        "urgency": "hours",
    }
    """
    parsed = llm._parse_llm_response(raw)
    assert parsed["score"] == 88
    assert parsed["urgency"] == "hours"
    assert "Line two" in parsed["reasoning"]


def test_parse_llm_response_escapes_inner_quotes(llm):
    raw = """
    {
        "score": 92,
        "reasoning": "Markets view this as a risk-off signal where traders talk about "panic selling" across sectors.",
        "urgency": "immediate"
    }
    """
    parsed = llm._parse_llm_response(raw)
    assert parsed["score"] == 92
    assert "panic selling" in parsed["reasoning"]


def test_parse_llm_response_removes_trailing_commas(llm):
    raw = '{"score": 55, "reasoning": "Trailing comma test", "urgency": "days", "market_direction": {"stocks": "bearish",},}'
    parsed = llm._parse_llm_response(raw)
    assert parsed["market_direction"]["stocks"] == "bearish"


def test_parse_llm_response_recovers_truncated_json(llm):
    raw = '{"score": 90, "reasoning": "Tariff shock analysis", "urgency": "immediate"'
    parsed = llm._parse_llm_response(raw)
    assert parsed["score"] == 90
    assert parsed["urgency"] == "immediate"


def test_analyze_returns_result(monkeypatch, llm):
    analysis_payload = {
        "score": 70,
        "reasoning": "The announcement signals significant market impact.",
        "urgency": "hours",
        "market_direction": {
            "stocks": "bearish",
            "crypto": "neutral",
            "forex": "usd_up",
            "commodities": "down",
        },
        "affected_markets": ["stocks", "forex"],
    }

    def fake_post(url, json=None, timeout=None):
        assert url.endswith("/api/generate")
        return SimpleNamespace(
            status_code=200,
            json=lambda: {"response": json_module.dumps(analysis_payload)},
            raise_for_status=lambda: None,
        )

    json_module = json
    monkeypatch.setattr(
        "src.analyzers.llm_analyzer.requests.post",
        fake_post,
    )

    result = llm.analyze("Policy update", keyword_score=25, max_retries=1)
    assert result["score"] == 70
    assert result["keyword_score"] == 25
    assert "processing_time_seconds" in result


def test_analyze_handles_non_json_response(monkeypatch, llm):
    calls = {"count": 0}

    def fake_post(url, json=None, timeout=None):
        calls["count"] += 1
        payload = {"response": "not-json"}
        if calls["count"] > 1:
            payload["response"] = json_module.dumps(
                {"score": 55, "reasoning": "Retry succeeded", "urgency": "days"}
            )

        return SimpleNamespace(
            status_code=200,
            json=lambda: payload,
            raise_for_status=lambda: None,
        )

    json_module = json
    monkeypatch.setattr(
        "src.analyzers.llm_analyzer.requests.post",
        fake_post,
    )

    result = llm.analyze("Retry scenario", keyword_score=10, max_retries=2)
    assert result["score"] == 55
    assert calls["count"] == 2


def test_analyze_returns_none_after_failures(monkeypatch, llm, caplog):
    def fake_post(url, json=None, timeout=None):
        raise RuntimeError("connection error")

    monkeypatch.setattr(
        "src.analyzers.llm_analyzer.requests.post",
        fake_post,
    )

    result = llm.analyze("No response", keyword_score=5, max_retries=1)
    assert result is None
    assert any("LLM analysis failed" in record.message for record in caplog.records)


def test_analyze_failure_notifies_webhook(monkeypatch, fake_config):
    fake_config.LLM_ERROR_WEBHOOK_URL = "https://webhook.test"
    monkeypatch.setattr(LLMAnalyzer, "_verify_connection", lambda self: None)
    llm = LLMAnalyzer(config=fake_config, timeout=5)

    calls = {"webhook": None}

    def fake_post(url, json=None, timeout=None):
        if url.endswith("/api/generate"):
            return SimpleNamespace(
                status_code=200,
                json=lambda: {"response": "not-json"},
                raise_for_status=lambda: None,
            )
        calls["webhook"] = {"url": url, "payload": json}
        return SimpleNamespace(
            status_code=204,
            json=lambda: {},
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr("src.analyzers.llm_analyzer.requests.post", fake_post)

    result = llm.analyze("Example post text", keyword_score=15, max_retries=1)
    assert result is None
    assert calls["webhook"] is not None
    assert calls["webhook"]["url"] == "https://webhook.test"
    assert "Keyword Score" in calls["webhook"]["payload"]["content"]


def test_quality_check_analysis_parses_response(monkeypatch, llm):
    qc_payload = {
        "response": json.dumps(
            {
                "approved": False,
                "quality_score": 65,
                "issues_found": ["Missing concrete figures"],
                "suggested_fixes": {"reasoning": "Add numerical details."},
            }
        )
    }

    def fake_post(url, json=None, timeout=None):
        return SimpleNamespace(
            status_code=200,
            json=lambda: qc_payload,
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr(
        "src.analyzers.llm_analyzer.requests.post",
        fake_post,
    )

    qc_result = llm.quality_check_analysis(
        "Post text",
        {
            "score": 80,
            "reasoning": "Strong policy change.",
            "urgency": "immediate",
            "market_direction": {"stocks": "bearish", "crypto": "neutral", "forex": "usd_up", "commodities": "down"},
        },
    )
    assert qc_result["quality_score"] == 65
    assert not qc_result["approved"]
    assert "Missing concrete figures" in qc_result["issues_found"]


def test_save_training_data_writes_jsonl(tmp_path, llm):
    output_dir = tmp_path / "training"
    llm.save_training_data(
        post_text="Example post",
        keyword_score=40,
        llm_analysis={
            "score": 70,
            "reasoning": "Strong language",
            "affected_markets": ["stocks"],
            "key_events": ["Tariff announcement"],
            "urgency": "hours",
            "model": "mock",
            "processing_time_seconds": 1.5,
        },
        post_id="post-123",
        output_dir=str(output_dir),
        quality_check={"approved": True, "quality_score": 90},
    )

    jsonl_path = output_dir / "llm_training_data.jsonl"
    assert jsonl_path.exists()
    content = jsonl_path.read_text(encoding="utf-8").strip()
    record = json.loads(content)
    assert record["post_id"] == "post-123"
    assert record["keyword_score"] == 40
    assert record["quality_check"]["approved"] is True
