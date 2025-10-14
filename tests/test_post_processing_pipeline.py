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

    pipeline = PostProcessingPipeline(
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
    )

    return SimpleNamespace(
        pipeline=pipeline,
        config=config,
        market_analyzer=market_analyzer,
        llm_analyzer=llm_analyzer,
        output_formatter=output_formatter,
        discord_notifier=discord_notifier,
        discord_all_posts_notifier=discord_all_posts_notifier,
        is_processed_fn=is_processed_fn,
        mark_processed_fn=mark_processed_fn,
    )


def sample_post(**overrides):
    defaults = {
        "id": "post_1",
        "content": "<p>This is a significant announcement about markets.</p>",
        "created_at": "2024-01-01T12:00:00+00:00",
        "account": {"username": "truthuser", "display_name": "Truth User"},
        "platform": Platform.TRUTH_SOCIAL.value,
        "media_attachments": [],
    }
    defaults.update(overrides)
    return defaults


def test_process_post_runs_full_pipeline():
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

    ctx.market_analyzer.analyze.assert_called_once()
    ctx.llm_analyzer.analyze.assert_called_once()
    ctx.llm_analyzer.save_training_data.assert_called_once()
    ctx.output_formatter.persist_analysis.assert_called_once()
    persist_kwargs = ctx.output_formatter.persist_analysis.call_args.kwargs
    assert persist_kwargs["post_id"] == "post_1"
    assert persist_kwargs["username"] == "truthuser"
    ctx.discord_all_posts_notifier.send_market_alert.assert_called_once()
    ctx.discord_notifier.send_market_alert.assert_called_once()
    ctx.mark_processed_fn.assert_called_once()


def test_skips_short_or_processed_posts():
    ctx = make_pipeline(
        is_processed_fn=MagicMock(side_effect=lambda _collection, post_id: post_id == "processed")
    )

    short_post = sample_post(id="short", content="<p>Too short.</p>")
    processed_post = sample_post(id="processed")

    ctx.pipeline.process_posts([short_post, processed_post], mongo_collection=MagicMock())

    ctx.market_analyzer.analyze.assert_not_called()
    ctx.llm_analyzer.analyze.assert_not_called()
    ctx.discord_notifier.send_market_alert.assert_not_called()
    ctx.mark_processed_fn.assert_not_called()


def test_posts_processed_in_chronological_order():
    ctx = make_pipeline()

    ctx.market_analyzer.analyze.return_value = {
        "impact_level": "🟠 HIGH",
        "impact_score": 30,
        "alert_emoji": "🟠",
        "details": {},
        "summary": "High impact"
    }
    ctx.llm_analyzer.analyze.return_value = {
        "score": 60,
        "urgency": "medium",
        "reasoning": "",
    }
    ctx.llm_analyzer.quality_check_analysis.return_value = {"approved": True}

    older = sample_post(
        id="older",
        created_at="2024-01-01T12:00:00+00:00",
        content="<p>Oldest post with enough content for analysis purposes.</p>"
    )
    newer = sample_post(
        id="newer",
        created_at="2024-01-02T12:00:00+00:00",
        content="<p>Newer post with enough content for analysis purposes.</p>"
    )

    ctx.pipeline.process_posts([newer, older], mongo_collection=MagicMock())

    mark_calls = ctx.mark_processed_fn.call_args_list
    assert mark_calls[0].args[1]['id'] == 'older'
    assert mark_calls[1].args[1]['id'] == 'newer'
