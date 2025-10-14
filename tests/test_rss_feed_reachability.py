import os

import pytest
import requests
from dotenv import load_dotenv

from src.config import _parse_feed_definitions


load_dotenv()

RSS_FEED_DEFINITION = os.getenv("RSS_FEEDS", "").strip()

if not RSS_FEED_DEFINITION:
    pytestmark = pytest.mark.skip(reason="RSS_FEEDS is not set; no feeds to validate")
    RSS_FEEDS = {}
else:
    RSS_FEEDS = _parse_feed_definitions(RSS_FEED_DEFINITION)


@pytest.mark.network
@pytest.mark.parametrize("label, feed_url", RSS_FEEDS.items())
def test_rss_feed_is_reachable(label: str, feed_url: str) -> None:
    """Verify that the configured RSS feeds respond successfully with content."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; MarketImpactBot/1.0; +https://example.com/bot)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    })
    response = session.get(feed_url, timeout=20, allow_redirects=True)
    session.close()

    status_code = response.status_code
    assert status_code < 400, f"{label} feed returned status code {status_code}"
    assert response.content.strip(), f"{label} feed returned empty response body"
