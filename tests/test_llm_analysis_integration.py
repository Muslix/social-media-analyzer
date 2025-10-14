import os
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Dict, Optional, Set, Tuple

import pytest
import requests

from src.analyzers.llm_analyzer import LLMAnalyzer


@dataclass(frozen=True)
class ProviderOverride:
    score_range: Optional[Tuple[int, int]] = None
    score_tolerance: Optional[int] = None
    expected_direction: Optional[Dict[str, Set[str]]] = None
    expected_urgency: Optional[Set[str]] = None


@dataclass(frozen=True)
class Scenario:
    name: str
    post_text: str
    keyword_score: int
    score_range: Tuple[int, int]
    score_tolerance: int
    expected_direction: Dict[str, Set[str]]
    expected_urgency: Set[str]
    provider_overrides: Dict[str, ProviderOverride] = field(default_factory=dict)


SCENARIOS = (
    Scenario(
        name="symbolic_statement_low",
        post_text=(
            "I want to thank our farmers for the amazing work they do every day. "
            "We will continue looking at ways to support rural communities over the coming years."
        ),
        keyword_score=5,
        score_range=(0, 20),
        score_tolerance=10,
        expected_direction={
            "stocks": {"neutral"},
            "crypto": {"neutral"},
            "forex": {"neutral"},
            "commodities": {"neutral"},
        },
        expected_urgency={"weeks", "days"},
        provider_overrides={
            "openrouter": ProviderOverride(
                score_range=(20, 40),
                score_tolerance=15,
            )
        },
    ),
    Scenario(
        name="cautionary_warning_mild",
        post_text=(
            "Energy regulators warned that fuel inventories are slightly below seasonal norms, "
            "but said they expect to resolve the shortfall with scheduled imports next month."
        ),
        keyword_score=30,
        score_range=(20, 40),
        score_tolerance=10,
        expected_direction={
            "stocks": {"neutral", "bearish"},
            "crypto": {"neutral"},
            "forex": {"neutral", "usd_up"},
            "commodities": {"neutral", "up"},
        },
        expected_urgency={"weeks", "days"},
    ),
    Scenario(
        name="regulatory_review_moderate",
        post_text=(
            "The Senate banking committee announced it will introduce draft legislation next week "
            "to tighten capital requirements for mid-sized banks after consulting with regulators."
        ),
        keyword_score=45,
        score_range=(40, 60),
        score_tolerance=10,
        expected_direction={
            "stocks": {"bearish", "neutral"},
            "crypto": {"neutral"},
            "forex": {"usd_up", "neutral", "usd_down"},
            "commodities": {"neutral"},
        },
        expected_urgency={"days", "hours"},
        provider_overrides={
            "openrouter": ProviderOverride(
                expected_direction={
                    "stocks": {"bearish", "neutral"},
                    "crypto": {"bearish", "neutral"},
                    "forex": {"usd_up", "neutral", "usd_down"},
                    "commodities": {"neutral", "down"},
                }
            )
        },
    ),
    Scenario(
        name="stimulus_risk_on",
        post_text=(
            "Breaking: The European Commission approved a EUR 200 billion green infrastructure "
            "stimulus program with funds already allocated and contracts set to be awarded over "
            "the coming days. Officials highlighted tax credits for renewable energy companies "
            "and accelerated procurement to boost growth."
        ),
        keyword_score=60,
        score_range=(60, 80),
        score_tolerance=15,
        expected_direction={
            "stocks": {"bullish", "neutral"},
            "crypto": {"bullish", "neutral"},
            "forex": {"usd_down", "neutral"},
            "commodities": {"up", "neutral"},
        },
        expected_urgency={"hours", "days"},
        provider_overrides={
            "openrouter": ProviderOverride(
                expected_direction={
                    "stocks": {"bullish", "neutral"},
                    "crypto": {"bullish", "neutral"},
                    "forex": {"usd_down", "neutral"},
                    "commodities": {"up", "neutral", "down"},
                }
            )
        },
    ),
    Scenario(
        name="trade_tariff_risk_off",
        post_text=(
            "Emergency update: The U.S. President signed an executive order imposing an immediate "
            "50% tariff on all Chinese semiconductor imports starting tonight at midnight. "
            "Customs officials confirmed shipments are being detained at ports right now, and "
            "advisers warn of instant retaliation from Beijing."
        ),
        keyword_score=75,
        score_range=(80, 100),
        score_tolerance=10,
        expected_direction={
            "stocks": {"bearish"},
            "crypto": {"bearish", "neutral"},
            "forex": {"usd_up"},
            "commodities": {"down", "neutral", "up"},
        },
        expected_urgency={"immediate", "hours"},
    ),
)


@pytest.fixture(scope="module")
def llm_live_analyzer():
    """Provide a live LLM analyzer instance if Ollama is reachable."""
    openrouter_enabled = os.getenv("OPENROUTER_ENABLED", "false").lower() == "true"
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    if openrouter_enabled:
        if not openrouter_api_key:
            pytest.skip("OPENROUTER_ENABLED is true but OPENROUTER_API_KEY is missing")

        config = SimpleNamespace(
            OPENROUTER_ENABLED=True,
            OPENROUTER_API_KEY=openrouter_api_key,
            OPENROUTER_MODEL=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free"),
            OPENROUTER_URL=os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions"),
            OPENROUTER_TIMEOUT=int(os.getenv("OPENROUTER_TIMEOUT", "120") or 120),
            OPENROUTER_REFERER=os.getenv("OPENROUTER_REFERER"),
            OPENROUTER_TITLE=os.getenv("OPENROUTER_TITLE"),
            OPENROUTER_MIN_INTERVAL=float(os.getenv("OPENROUTER_MIN_INTERVAL", "5") or 5),
            OLLAMA_URL=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            OLLAMA_NUM_THREADS=int(os.getenv("OLLAMA_NUM_THREADS", "0") or 0),
        )
        return LLMAnalyzer(config=config, timeout=600)

    url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    try:
        response = requests.get(f"{url}/api/tags", timeout=5)
        response.raise_for_status()
    except Exception as exc:
        pytest.skip(f"Ollama service not reachable at {url}: {exc}")

    config = SimpleNamespace(
        OLLAMA_URL=url,
        OLLAMA_MODEL=model,
        OLLAMA_NUM_THREADS=0,
    )

    return LLMAnalyzer(config=config, timeout=600)


@pytest.mark.llm
@pytest.mark.slow
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.name)
def test_llm_analysis_scenarios(llm_live_analyzer: LLMAnalyzer, scenario: Scenario):
    """Validate the live LLM returns coherent scores and directions for key scenarios."""
    analysis = llm_live_analyzer.analyze(
        scenario.post_text,
        keyword_score=scenario.keyword_score,
        max_retries=1,
    )

    assert analysis is not None, (
        f"Analysis failed for scenario '{scenario.name}'. "
        f"Raw response: { (llm_live_analyzer._last_raw_response or '')[:300] }"
    )

    score = analysis.get("score")
    assert score is not None, "LLM did not return a score"
    provider = analysis.get("provider") or ("openrouter" if os.getenv("OPENROUTER_ENABLED", "false").lower() == "true" else "ollama")
    override = scenario.provider_overrides.get(provider)

    score_range = scenario.score_range
    score_tolerance = scenario.score_tolerance
    if override:
        if override.score_range:
            score_range = override.score_range
        if override.score_tolerance is not None:
            score_tolerance = override.score_tolerance

    lower_bound = max(0, score_range[0] - score_tolerance)
    upper_bound = min(100, score_range[1] + score_tolerance)
    assert lower_bound <= score <= upper_bound, (
        f"Score {score} outside expected range {score_range} "
        f"(tolerance +/- {score_tolerance}) for scenario '{scenario.name}'"
    )

    reasoning = (analysis.get("reasoning") or "").strip()
    assert reasoning, "Reasoning text is empty"

    expected_direction = scenario.expected_direction
    if override and override.expected_direction:
        expected_direction = override.expected_direction

    market_direction = analysis.get("market_direction") or {}
    for market, allowed_values in expected_direction.items():
        value = market_direction.get(market, "neutral")
        assert value in allowed_values, (
            f"Unexpected market direction for {market}: {value} "
            f"(allowed: {sorted(allowed_values)}) in scenario '{scenario.name}' using provider '{provider}'"
        )

    urgency = analysis.get("urgency")
    expected_urgency = scenario.expected_urgency
    if override and override.expected_urgency:
        expected_urgency = override.expected_urgency

    assert urgency in expected_urgency, (
        f"Urgency '{urgency}' not in expected options {sorted(expected_urgency)} "
        f"for scenario '{scenario.name}' using provider '{provider}'"
    )

    key_events = analysis.get("key_events") or []
    assert isinstance(key_events, list), "key_events must be a list"
