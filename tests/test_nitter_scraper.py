from types import SimpleNamespace

import requests
from requests.exceptions import Timeout

from src.scrapers.nitter_scraper import NitterScraper


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def make_scraper(single_instance: str = "https://nitter.example") -> NitterScraper:
    scraper = NitterScraper(timeout=1)
    scraper.NITTER_INSTANCES = [single_instance]
    scraper.available_instances = [single_instance]
    scraper.current_instance_index = 0
    scraper._instance_cooldown_until.clear()
    scraper._degraded_instances.clear()
    scraper._health_cache.clear()
    scraper._last_health_check = None
    return scraper


def test_get_tweets_parses_html(monkeypatch):
    scraper = make_scraper()
    sample_html = """
    <div class="timeline-item">
        <div class="tweet-content">Breaking market news!</div>
        <a class="tweet-link" href="/elonmusk/status/1234567890"></a>
        <span class="tweet-date"><a title="Fri Jan 05 12:00:00 2024 UTC"></a></span>
        <div class="tweet-stats">
            <span class="icon-heart"></span><span class="tweet-stat">1.2K</span>
            <span class="icon-retweet"></span><span class="tweet-stat">300</span>
            <span class="icon-comment"></span><span class="tweet-stat">15</span>
        </div>
    </div>
    """

    monkeypatch.setattr(
        scraper,
        "session",
        SimpleNamespace(get=lambda url, timeout: FakeResponse(sample_html))
    )

    tweets = scraper.get_tweets("elonmusk", max_results=1, max_retries=1)
    assert len(tweets) == 1

    tweet = tweets[0]
    assert tweet["id"] == "1234567890"
    assert tweet["metrics"]["likes"] == 1200
    assert tweet["metrics"]["retweets"] == 300
    assert tweet["metrics"]["replies"] == 15
    assert tweet["platform"] == "x"


def test_get_tweets_marks_degraded_on_failure(monkeypatch):
    scraper = make_scraper()

    def failing_get(url, timeout):
        raise Timeout("simulated timeout")

    monkeypatch.setattr(scraper, "session", SimpleNamespace(get=failing_get))
    tweets = scraper.get_tweets("elonmusk", max_results=1, max_retries=1)

    assert tweets == []
    degraded = scraper.get_degraded_instances()
    assert degraded == ["https://nitter.example"]


def test_run_health_check_uses_cache(monkeypatch):
    scraper = make_scraper()
    response = FakeResponse("<html></html>")
    call_counter = {"value": 0}

    def first_get(url, timeout):
        call_counter["value"] += 1
        return response

    monkeypatch.setattr(scraper, "session", SimpleNamespace(get=first_get))
    first_results = scraper.run_health_check()
    assert call_counter["value"] == 1
    assert first_results["https://nitter.example"]["is_up"] is True

    def fail_get(url, timeout):
        raise AssertionError("health check should use cache")

    monkeypatch.setattr(scraper, "session", SimpleNamespace(get=fail_get))
    second_results = scraper.run_health_check()

    assert second_results == first_results
    assert call_counter["value"] == 1
