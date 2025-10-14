"""
Truth Social Scraper
Supports direct Mastodon API access and optional FlareSolverr fallback
"""
import logging
import json
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote_plus

import requests

from src.enums import Platform

logger = logging.getLogger(__name__)


class FlareSolverrResponse:
    """Minimal response wrapper to mimic requests.Response for FlareSolverr"""

    def __init__(self, status_code: int, headers: Dict[str, Any], body: str, url: str):
        self.status_code = status_code
        self.headers = headers or {}
        self._text = body or ""
        self.url = url

    @property
    def text(self) -> str:
        return self._text

    def json(self) -> Any:
        try:
            return json.loads(self._text)
        except json.JSONDecodeError:
            from bs4 import BeautifulSoup  # Lazy import to keep dependency optional at runtime

            soup = BeautifulSoup(self._text, "html.parser")
            pre = soup.find("pre")
            if pre:
                return json.loads(pre.text)
            raise

    def raise_for_status(self):
        if self.status_code >= 400:
            http_error = requests.HTTPError(f"{self.status_code} Error for url: {self.url}", response=self)
            raise http_error


class TruthSocialScraper:
    """
    Scrapes Truth Social using public Mastodon API endpoints.
    When FlareSolverr is enabled, requests are proxied through it to solve Cloudflare challenges.
    """

    def __init__(
        self,
        instance: str = "truthsocial.com",
        timeout: int = 30,
        use_flaresolverr: bool = False,
        flaresolverr_url: Optional[str] = None,
        flaresolverr_timeout: int = 60,
        block_history=None,
        initial_block_timestamp: Optional[float] = None,
    ):
        """
        Initialize Truth Social scraper

        Args:
            instance: Truth Social instance domain
            timeout: Request timeout in seconds
            use_flaresolverr: Whether to proxy requests through FlareSolverr
            flaresolverr_url: Base URL to the FlareSolverr service (without /v1 suffix)
            flaresolverr_timeout: Max solve time (seconds) for FlareSolverr
        """
        self.instance = instance
        self.base_url = f"https://{instance}"
        self.timeout = timeout
        self.use_flaresolverr = use_flaresolverr
        self.flaresolverr_timeout = flaresolverr_timeout
        base_solver_url = flaresolverr_url or "http://localhost:8191"
        self.flaresolverr_url = f"{base_solver_url.rstrip('/')}/v1"
        self.session = requests.Session()
        self._rng = random.Random()
        self._randomized_headers = self._build_header_pool()
        self._last_block_timestamp: float = initial_block_timestamp or 0.0
        self.block_history = block_history

        initial_headers = self._pick_header_fingerprint()
        logger.debug("Initial Truth Social headers: %s", initial_headers)
        self.session.headers.update(initial_headers)
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[Any]:
        """
        Make HTTP request with retry logic

        Args:
            url: URL to fetch
            max_retries: Maximum retry attempts
            
        Returns:
            Response object or None if failed
        """
        if self.use_flaresolverr:
            return self._make_request_via_flaresolverr(url, max_retries)

        for attempt in range(max_retries):
            try:
                logger.debug(f"Request to {url} (attempt {attempt + 1}/{max_retries})")
                headers = self._pick_header_fingerprint()
                delay = self._apply_jitter("truth_social", url)
                logger.debug(
                    "Using headers for request (sleep %.2fs): %s",
                    delay,
                    headers
                )

                response = self.session.get(url, headers=headers, timeout=self.timeout)

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"⏱️  Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                # Check for Cloudflare challenge
                if response.status_code == 403 or 'cf-ray' in response.headers:
                    logger.warning(f"⚠️  Cloudflare protection detected on {url}")
                    logger.warning(f"⚠️  Truth Social may be blocking automated access")
                    self._mark_block_event(
                        reason="http_403",
                        metadata={"url": url, "status": response.status_code}
                    )
                    return None
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️  Timeout on attempt {attempt + 1}/{max_retries}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️  Request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _make_request_via_flaresolverr(self, url: str, max_retries: int = 3) -> Optional[FlareSolverrResponse]:
        """Proxy request through FlareSolverr to bypass Cloudflare challenges."""
        for attempt in range(max_retries):
            try:
                logger.debug(f"FlareSolverr request to {url} (attempt {attempt + 1}/{max_retries})")
                headers = self._pick_header_fingerprint()
                delay = self._apply_jitter("truth_social_flaresolverr", url)
                logger.debug(
                    "Proxy headers via FlareSolverr (sleep %.2fs): %s",
                    delay,
                    headers
                )
                payload = {
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": int(self.flaresolverr_timeout * 1000),
                    "headers": headers,
                }
                response = requests.post(
                    self.flaresolverr_url,
                    json=payload,
                    timeout=self.flaresolverr_timeout + 5
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as exc:
                logger.warning(f"⚠️  FlareSolverr request failed: {exc}")
                if attempt < max_retries - 1:
                    sleep_for = min(2 ** attempt, 30)
                    logger.debug(f"Retrying in {sleep_for} seconds...")
                    time.sleep(sleep_for)
                    continue
                return None

            try:
                result = response.json()
            except json.JSONDecodeError:
                logger.error("Failed to decode FlareSolverr response payload")
                return None

            if result.get("status") != "ok":
                logger.warning(f"⚠️  FlareSolverr error: {result}")
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
                self._mark_block_event(
                    reason=f"flaresolverr_status_{result.get('status')}",
                    metadata={"url": url}
                )
                return None

            solution = result.get("solution", {})
            status_code = int(solution.get("status") or 200)
            headers = solution.get("headers") or {}
            body = solution.get("response", "")

            # If Cloudflare still blocks access, stop retrying to avoid loops
            if status_code == 403 and any("cloudflare" in str(val).lower() for val in headers.values()):
                logger.warning("⚠️  Cloudflare challenge persists even after FlareSolverr attempt")
                self._mark_block_event(
                    reason="http_403",
                    metadata={"url": url, "status": status_code}
                )
                return None

            flare_response = FlareSolverrResponse(status_code, headers, body, url)
            try:
                flare_response.raise_for_status()
            except requests.HTTPError as exc:
                logger.warning(f"⚠️  FlareSolverr returned HTTP error: {exc}")
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
                self._mark_block_event(
                    reason="flaresolverr_http_error",
                    metadata={"url": url, "error": str(exc)}
                )
                return None

            return flare_response

        return None
    
    def set_block_history_repo(self, repo) -> None:
        self.block_history = repo

    def set_last_block_timestamp(self, timestamp: Optional[float]) -> None:
        if timestamp is not None:
            self._last_block_timestamp = timestamp

    def _mark_block_event(self, reason: str = "unknown", metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record that we hit Cloudflare or another blocking event."""
        self._last_block_timestamp = time.time()
        if not getattr(self, "block_history", None):
            return

        payload = {"instance": self.instance}
        if metadata:
            payload.update(metadata)

        try:
            self.block_history.record_event(
                source="truth_social",
                reason=reason,
                metadata=payload,
            )
        except Exception as exc:
            logger.debug("Failed to persist Truth Social block event: %s", exc)

    def had_recent_block(self, window_seconds: int = 1800) -> bool:
        """Whether a blocking event was seen within the given window."""
        if not self._last_block_timestamp:
            return False
        return (time.time() - self._last_block_timestamp) <= window_seconds

    def _build_header_pool(self) -> List[Dict[str, str]]:
        """Construct a pool of believable browser headers for rotation."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        ]

        accept_languages = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8,de;q=0.6",
            "de-DE,de;q=0.9,en;q=0.6",
        ]

        accept_headers = [
            "application/json, text/plain, */*",
            "application/activity+json, application/json;q=0.9, */*;q=0.7",
        ]

        pool: List[Dict[str, str]] = []
        for ua in user_agents:
            for lang in accept_languages:
                for accept in accept_headers:
                    pool.append({
                        "User-Agent": ua,
                        "Accept": accept,
                        "Accept-Language": lang,
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Site": "same-origin",
                    })

        return pool

    def _pick_header_fingerprint(self) -> Dict[str, str]:
        """Select a random header fingerprint from the pool."""
        if not self._randomized_headers:
            self._randomized_headers = self._build_header_pool()
        return dict(self._rng.choice(self._randomized_headers))

    def _apply_jitter(self, label: str, url: str) -> float:
        """Sleep for a small randomised interval before making a request."""
        delay = round(self._rng.uniform(0.35, 1.25), 3)
        logger.debug("Sleep %.3fs before %s request to %s", delay, label, url)
        time.sleep(delay)
        return delay
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Resolve a Truth Social username to an internal Mastodon user ID."""
        candidates = [username]
        if '@' not in username:
            candidates.append(f"{username}@{self.instance}")

        for candidate in candidates:
            url = f"{self.base_url}/api/v1/accounts/lookup?acct={candidate}"
            response = self._make_request(url)
            if not response:
                continue

            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to parse lookup JSON for @{username}")
                continue

            user_id = data.get('id')
            if user_id:
                logger.debug(f"Found user ID for @{username} via {candidate}: {user_id}")
                return user_id

        # Fallback: use search endpoint (less strict but noisier)
        search_id = self._search_user_id(username)
        if search_id:
            logger.debug(f"Resolved user ID for @{username} via search: {search_id}")
            return search_id

        logger.warning(f"No user ID found for @{username}")
        return None

    def _search_user_id(self, username: str) -> Optional[str]:
        """Fallback search using Mastodon search API."""
        query = username if username.startswith('@') else f"@{username}"
        url = (
            f"{self.base_url}/api/v2/search?"
            f"q={quote_plus(query)}&type=accounts&limit=5"
        )

        response = self._make_request(url)
        if not response:
            return None

        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse search JSON for @{username}")
            return None

        accounts = data.get('accounts', [])
        normalized_username = username.strip('@').lower()
        for account in accounts:
            acct = account.get('acct', '').lower()
            handle_root = acct.split('@')[0]

            if handle_root == normalized_username or acct == normalized_username:
                user_id = account.get('id')
                if user_id:
                    return user_id
        return None
    
    def get_posts(self, username: str, max_results: int = 5) -> List[Dict]:
        """
        Fetch recent posts from a Truth Social user
        
        Args:
            username: Truth Social username (without @)
            max_results: Maximum number of posts to fetch
            
        Returns:
            List of post dictionaries
        """
        logger.info(f"📥 Fetching posts from Truth Social @{username}...")
        
        # Get user ID first
        user_id = self.get_user_id(username)
        if not user_id:
            logger.error(f"❌ Could not find user @{username}")
            return []
        
        # Fetch user's statuses
        url = f"{self.base_url}/api/v1/accounts/{user_id}/statuses"
        params = {
            'exclude_replies': 'true',
            'exclude_reblogs': 'true',
            'limit': str(max_results)
        }
        
        # Build URL with params
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"
        
        response = self._make_request(full_url)
        if not response:
            logger.error(f"❌ Failed to fetch posts for @{username}")
            return []
        
        try:
            posts = response.json()
            
            if not isinstance(posts, list):
                logger.warning(f"Unexpected response format for @{username}: {type(posts)}")
                return []
            
            # Add platform identifier
            for post in posts:
                post['platform'] = Platform.TRUTH_SOCIAL.value
                if 'account' not in post:
                    post['account'] = {'username': username}
            
            logger.info(f"✅ Got {len(posts)} posts from Truth Social @{username}")
            return posts
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse posts JSON for @{username}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test if Truth Social API is accessible
        
        Returns:
            True if accessible, False otherwise
        """
        logger.info(f"🔍 Testing connection to {self.instance}...")
        
        # Try to fetch instance info
        url = f"{self.base_url}/api/v1/instance"
        response = self._make_request(url)
        
        if response:
            logger.info(f"✅ Connection successful to {self.instance}")
            return True
        else:
            logger.warning(f"⚠️  Could not connect to {self.instance}")
            logger.warning(f"⚠️  Truth Social may be using Cloudflare protection")
            return False


if __name__ == "__main__":
    # Test the scraper
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    scraper = TruthSocialScraper()
    
    # Test connection first
    if not scraper.test_connection():
        logger.error("❌ Cannot connect to Truth Social. Cloudflare protection may be active.")
        logger.info("💡 Options:")
        logger.info("   1. Wait and try again later")
        logger.info("   2. Use a VPN/proxy")
        logger.info("   3. Disable Truth Social monitoring (use X/Twitter only)")
        sys.exit(1)
    
    # Test with a known account (adjust as needed)
    test_username = "realDonaldTrump"  # Example - change as needed
    
    posts = scraper.get_posts(test_username, max_results=3)
    
    print(f"\n{'='*70}")
    print(f"Latest posts from @{test_username}:")
    print('='*70)
    
    if posts:
        for i, post in enumerate(posts, 1):
            from bs4 import BeautifulSoup
            content = post.get('content', '')
            soup = BeautifulSoup(content, 'html.parser')
            clean_text = soup.get_text()
            
            print(f"\n{i}. Post ID: {post['id']}")
            print(f"   Posted: {post.get('created_at')}")
            print(f"   Text: {clean_text[:150]}...")
    else:
        print("\n❌ No posts retrieved. Check if Cloudflare is blocking access.")
