from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import MagicMock

from src.enums import Platform
from src.output.formatter import OutputFormatter


def make_sample_analysis():
    return {
        "impact_level": "🟠 HIGH",
        "impact_score": 30,
        "alert_emoji": "🟠",
        "details": {"keywords": {"critical": [("tariff", 10)]}},
        "summary": "🟠 HIGH - Score: 30",
    }


def test_persist_analysis_upserts_document():
    collection = MagicMock()
    formatter = OutputFormatter(analysis_collection=collection, enable_file_export=False)

    formatter.persist_analysis(
        post_id="post42",
        platform=Platform.TRUTH_SOCIAL,
        username="truthuser",
        display_name="Truth User",
        message="Formatted message",
        raw_content="<p>content</p>",
        cleaned_content="content",
        market_analysis=make_sample_analysis(),
        llm_analysis={"score": 75, "urgency": "high"},
        media_attachments=[{"type": "image", "url": "https://cdn/img.png"}],
        post_url="https://truthsocial.com/@truthuser/posts/post42",
        post_created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    collection.update_one.assert_called_once()
    args, kwargs = collection.update_one.call_args
    update_doc = args[1]["$set"]

    assert update_doc["post"]["id"] == "post42"
    assert update_doc["analysis"]["market"]["impact_score"] == 30
    assert update_doc["impact"]["bucket"] == "high"
    assert update_doc["labels"]["author"] == "truthuser"


def test_persist_analysis_writes_exports_when_enabled(tmp_path):
    collection = MagicMock()
    formatter = OutputFormatter(
        analysis_collection=collection,
        output_dir=str(tmp_path),
        enable_file_export=True,
    )

    formatter.persist_analysis(
        post_id="critical1",
        platform=Platform.TRUTH_SOCIAL,
        username="truthuser",
        display_name="Truth User",
        message="Critical message",
        raw_content="<p>critical</p>",
        cleaned_content="critical",
        market_analysis={
            "impact_level": "🔴 CRITICAL",
            "impact_score": 80,
            "alert_emoji": "🔴",
            "details": {},
            "summary": "🔴 CRITICAL - Score: 80",
        },
        llm_analysis=None,
        media_attachments=[],
        post_url="https://truthsocial.com/@truthuser/posts/critical1",
        post_created_at=datetime(2024, 1, 2, tzinfo=UTC),
    )

    # Ensure upsert happened
    collection.update_one.assert_called_once()

    all_posts = Path(tmp_path, "truth_social_posts.txt").read_text(encoding="utf-8")
    high_impact = Path(tmp_path, "market_impact_posts.txt").read_text(encoding="utf-8")
    critical = Path(tmp_path, "CRITICAL_ALERTS.txt").read_text(encoding="utf-8")

    assert "Critical message" in all_posts
    assert "Critical message" in high_impact
    assert "Critical message" in critical


def test_persist_analysis_skips_when_no_collection(caplog):
    formatter = OutputFormatter(analysis_collection=None, enable_file_export=False)

    formatter.persist_analysis(
        post_id="noop",
        platform=Platform.TRUTH_SOCIAL,
        username="truthuser",
        display_name="Truth User",
        message="No collection",
        raw_content="raw",
        cleaned_content="clean",
        market_analysis=None,
        llm_analysis=None,
        media_attachments=None,
        post_url="https://truthsocial.com/@truthuser/posts/noop",
        post_created_at=datetime(2024, 1, 3, tzinfo=UTC),
    )

    warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
    assert any("skipping structured persistence" in msg for msg in warning_messages)
