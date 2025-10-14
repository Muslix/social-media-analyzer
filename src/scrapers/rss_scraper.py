"""RSS feed scraper utility."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import mktime
from typing import List, Dict, Optional

import feedparser
import requests


logger = logging.getLogger(__name__)


class RSSFeedScraper:
    """Fetch and normalize RSS/Atom feeds."""

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; MarketImpactBot/1.0; +https://example.com/bot)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
        })

    def fetch(self, url: str, max_entries: int = 5) -> List[Dict[str, str]]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to download RSS feed %s: %s", url, exc)
            return []

        parsed = feedparser.parse(response.content)
        if parsed.bozo:
            logger.warning("Feed parser reported issue for %s: %s", url, parsed.bozo_exception)

        entries: List[Dict[str, str]] = []
        for entry in parsed.entries[:max_entries]:
            entry_id = self._derive_id(entry, url)
            title = entry.get("title") or ""
            summary = entry.get("summary") or entry.get("description") or ""
            link = entry.get("link")
            created_at = self._extract_timestamp(entry)

            content_parts = [title.strip(), summary.strip()]
            content = "\n\n".join(part for part in content_parts if part)

            entries.append({
                "id": entry_id,
                "title": title.strip(),
                "summary": summary.strip(),
                "content": content.strip() or title.strip(),
                "created_at": created_at,
                "url": link,
            })
        return entries

    @staticmethod
    def _derive_id(entry: feedparser.FeedParserDict, fallback: str) -> str:
        for key in ("id", "guid", "link"):
            value = entry.get(key)
            if value:
                return str(value)
        title = entry.get("title")
        if title:
            return f"{fallback}#{hash(title)}"
        return f"{fallback}#{hash(str(entry))}"

    @staticmethod
    def _extract_timestamp(entry: feedparser.FeedParserDict) -> str:
        for key in ("published_parsed", "updated_parsed", "created_parsed"):
            value = entry.get(key)
            if value:
                try:
                    dt = datetime.fromtimestamp(mktime(value), tz=timezone.utc)
                    return dt.isoformat()
                except Exception:
                    continue
        return datetime.now(timezone.utc).isoformat()
