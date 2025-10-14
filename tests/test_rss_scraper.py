from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.scrapers.rss_scraper import RSSFeedScraper

SAMPLE_FEED = """<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0">
  <channel>
    <title>Sample Feed</title>
    <item>
      <title>Article 1</title>
      <link>https://example.com/article1</link>
      <description>Summary 1</description>
      <pubDate>Mon, 14 Oct 2024 10:00:00 GMT</pubDate>
      <guid>1</guid>
    </item>
    <item>
      <title>Article 2</title>
      <link>https://example.com/article2</link>
      <description>Summary 2</description>
      <pubDate>Mon, 14 Oct 2024 11:00:00 GMT</pubDate>
      <guid>2</guid>
    </item>
  </channel>
</rss>
"""


def test_fetch_parses_entries(monkeypatch):
    scraper = RSSFeedScraper()
    response = MagicMock()
    response.content = SAMPLE_FEED
    response.raise_for_status = lambda: None
    monkeypatch.setattr(scraper.session, "get", lambda *args, **kwargs: response)

    entries = scraper.fetch("https://example.com/feed")
    assert len(entries) == 2
    assert entries[0]["title"] == "Article 1"
    assert entries[0]["url"] == "https://example.com/article1"

    dt = datetime.fromisoformat(entries[0]["created_at"])
    assert dt.tzinfo is not None


def test_fetch_handles_request_error(monkeypatch):
    scraper = RSSFeedScraper()
    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")))
    entries = scraper.fetch("https://example.com/feed")
    assert entries == []
