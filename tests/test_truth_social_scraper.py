import json
from types import SimpleNamespace

from src.enums import Platform
from src.scrapers import truth_social_scraper as tss
from src.scrapers.truth_social_scraper import TruthSocialScraper, FlareSolverrResponse


class DummyResponse:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_get_user_id_uses_lookup(monkeypatch):
    scraper = TruthSocialScraper()

    def fake_request(url):
        return DummyResponse({'id': '321'})

    monkeypatch.setattr(scraper, "_make_request", fake_request)
    user_id = scraper.get_user_id("someuser")
    assert user_id == "321"


def test_get_user_id_falls_back_to_search(monkeypatch):
    scraper = TruthSocialScraper()
    monkeypatch.setattr(scraper, "_make_request", lambda url: None)
    monkeypatch.setattr(scraper, "_search_user_id", lambda username: "fallback-id")

    assert scraper.get_user_id("anotheruser") == "fallback-id"


def test_get_posts_adds_platform(monkeypatch):
    scraper = TruthSocialScraper()
    monkeypatch.setattr(scraper, "get_user_id", lambda username: "42")

    def fake_request(url):
        assert "statuses" in url
        return DummyResponse([
            {
                "id": "abc123",
                "content": "<p>Market updates incoming.</p>",
                "account": {"username": "truthuser"}
            }
        ])

    monkeypatch.setattr(scraper, "_make_request", fake_request)
    posts = scraper.get_posts("truthuser", max_results=2)

    assert len(posts) == 1
    post = posts[0]
    assert post["id"] == "abc123"
    assert post["platform"] == Platform.TRUTH_SOCIAL.value
    assert post["account"]["username"] == "truthuser"


def test_get_posts_handles_fetch_failure(monkeypatch, caplog):
    scraper = TruthSocialScraper()
    monkeypatch.setattr(scraper, "get_user_id", lambda username: "missing")
    monkeypatch.setattr(scraper, "_make_request", lambda url: None)

    posts = scraper.get_posts("unknown")
    assert posts == []
    assert any("Failed to fetch posts" in record.message for record in caplog.records)


def test_make_request_via_flaresolverr_success(monkeypatch):
    scraper = TruthSocialScraper(use_flaresolverr=True, flaresolverr_url="http://solver:8191")

    def fake_post(url, json=None, timeout=None):
        assert url.endswith("/v1")
        assert json["cmd"] == "request.get"

        payload = {
            "status": "ok",
            "solution": {
                "status": 200,
                "headers": {"content-type": "application/json"},
                "response": json_module.dumps({"message": "hello"})
            }
        }

        return SimpleNamespace(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: payload
        )

    json_module = json
    monkeypatch.setattr(tss.requests, "post", fake_post)

    response = scraper._make_request("https://truthsocial.com/api/v1/example")
    assert isinstance(response, FlareSolverrResponse)
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_make_request_via_flaresolverr_handles_error(monkeypatch):
    scraper = TruthSocialScraper(use_flaresolverr=True)

    def fake_post(url, json=None, timeout=None):
        payload = {"status": "error", "message": "solver failed"}
        return SimpleNamespace(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: payload
        )

    monkeypatch.setattr(tss.requests, "post", fake_post)
    result = scraper._make_request("https://truthsocial.com/api/v1/example")
    assert result is None
