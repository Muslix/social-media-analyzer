from types import SimpleNamespace
from unittest.mock import MagicMock

from src.services.post_processing_pipeline import PostProcessingPipeline
from src.enums import Platform


def make_pipeline(**overrides):
    config = overrides.get(
        "config",
        SimpleNamespace(TRUTH_USERNAME="truthuser", POST_TYPE="post")
    )

    market_analyzer = overrides.get("market_analyzer", MagicMock())
    llm_analyzer = overrides.get("llm_analyzer", MagicMock())
    output_formatter = overrides.get("output_formatter", MagicMock())
    discord_notifier = overrides.get("discord_notifier", MagicMock())
    discord_all_posts_notifier = overrides.get("discord_all_posts_notifier", MagicMock())
    is_processed_fn = overrides.get("is_processed_fn", MagicMock(return_value=False))
    mark_processed_fn = overrides.get("mark_processed_fn", MagicMock())

    pipeline = SimpleNamespace(
        pipeline=PostProcessingPipeline(
            config=config,
            market_analyzer=market_analyzer,
            llm_analyzer=llm_analyzer,
            output_formatter=output_formatter,
            discord_notifier=discord_notifier,
            discord_all_posts_notifier=discord_all_posts_notifier,
            llm_threshold=20,
            discord_threshold=25,
            is_processed_fn=is_processed_fn,
            mark_processed_fn=mark_processed_fn,
        ),
        config=config,
        market_analyzer=market_analyzer,
        llm_analyzer=llm_analyzer,
        output_formatter=output_formatter,
        discord_notifier=discord_notifier,
        discord_all_posts_notifier=discord_all_posts_notifier,
        is_processed_fn=is_processed_fn,
        mark_processed_fn=mark_processed_fn,
    )
    return pipeline


def sample_post(**overrides):
    base = {
        "id": "post_1",
        "content": "<p>Important article about markets.</p>",
        "created_at": "2024-01-01T12:00:00+00:00",
        "account": {"username": "truthuser", "display_name": "Truth User"},
        "platform": Platform.RSS.value,
        "media_attachments": [],
        "url": "https://example.com/article"
    }
    base.update(overrides)
    return base


def test_discord_notifier_receives_post_url():
    ctx = make_pipeline()

    market_analysis = {
        "impact_level": "🟠 HIGH",
        "impact_score": 30,
        "alert_emoji": "🟠",
        "details": {},
        "summary": "High impact"
    }
    ctx.market_analyzer.analyze.return_value = market_analysis

    llm_result = {
        "score": 70,
        "urgency": "high",
        "reasoning": "Markets likely to react",
        "processing_time_seconds": 1.2,
    }
    ctx.llm_analyzer.analyze.return_value = llm_result
    ctx.llm_analyzer.quality_check_analysis.return_value = {"approved": True}

    posts = [sample_post()]
    ctx.pipeline.process_posts(posts, mongo_collection=MagicMock())

    ctx.discord_all_posts_notifier.send_market_alert.assert_called_once()
    args, kwargs = ctx.discord_all_posts_notifier.send_market_alert.call_args
    assert kwargs["post_url"] == "https://example.com/article"
