"""
X/Twitter Scraper using Nitter instances
Scrapes tweets without API key by rotating through public Nitter instances
"""
import requests
import logging
import time
import random
from typing import List, Dict, Optional, Any
from datetime import datetime, UTC, timedelta
from bs4 import BeautifulSoup
import re

from src.enums import Platform

logger = logging.getLogger(__name__)


class NitterScraper:
    """
    Scrapes X/Twitter via Nitter instances (no API key required)
    Rotates lazily through multiple instances with cached health state
    """
    
    # List of working Nitter instances (updated from wiki)
    NITTER_INSTANCES = [
        "https://xcancel.com",
        "https://nitter.poast.org",
        "https://nitter.privacyredirect.com",
        "https://nitter.tiekoetter.com",
        "https://nuku.trabun.org",
    ]
    INSTANCE_COOLDOWN_SECONDS = 300  # Keep degraded instances on cooldown for 5 minutes
    HEALTH_CACHE_TTL_SECONDS = 600   # Cache health check results for 10 minutes
    DEFAULT_HEALTH_CHECK_USER = "elonmusk"
    
    def __init__(
        self,
        timeout: int = 30,
        eager_instance_check: bool = False,
        health_check_username: Optional[str] = None,
        block_history=None,
        initial_outage_timestamp: Optional[float] = None,
    ):
        """
        Initialize Nitter scraper
        
        Args:
            timeout: Request timeout in seconds
            eager_instance_check: Perform instance health check at init time
            health_check_username: Account slug used during health checks
        """
        self.timeout = timeout
        self.current_instance_index = 0
        self.session = requests.Session()
        self._rng = random.Random()
        self._header_pool = self._build_header_pool()
        initial_headers = self._pick_header_fingerprint()
        logger.debug("Initial Nitter headers: %s", initial_headers)
        self.session.headers.update(initial_headers)
        self.available_instances = list(self.NITTER_INSTANCES)
        self._instance_cooldown_until: Dict[str, float] = {}
        self._degraded_instances: Dict[str, float] = {}
        self._health_cache: Dict[str, Dict[str, Any]] = {}
        self._last_health_check: Optional[float] = None
        self._last_global_outage: float = initial_outage_timestamp or 0.0
        self.block_history = block_history
        self.health_check_username = health_check_username or self.DEFAULT_HEALTH_CHECK_USER

        if eager_instance_check:
            self.run_health_check(force=True)
    
    def _get_next_instance(self) -> Optional[str]:
        """
        Rotate to next Nitter instance, skipping degraded ones that are still in cooldown.
        Returns the URL of the next available instance or None if all are currently degraded.
        """
        if not self.available_instances:
            logger.error("No Nitter instances configured.")
            return None

        total_instances = len(self.available_instances)
        now = time.time()

        for _ in range(total_instances):
            instance = self.available_instances[self.current_instance_index]
            self.current_instance_index = (self.current_instance_index + 1) % total_instances

            cooldown_until = self._instance_cooldown_until.get(instance, 0.0)
            if cooldown_until > now:
                remaining = int(cooldown_until - now)
                logger.debug(f"Skipping {instance} (cooldown {remaining}s remaining)")
                continue

            return instance

        degraded_list = ", ".join(self.get_degraded_instances())
        if degraded_list:
            logger.warning(f"All Nitter instances currently degraded: {degraded_list}")
        else:
            logger.warning("All Nitter instances are temporarily unavailable.")
        self._last_global_outage = now

        return None
    
    def _parse_tweet_date(self, date_element) -> str:
        """
        Parse Nitter date element to ISO format
        
        Args:
            date_element: BeautifulSoup element containing date information
            
        Returns:
            ISO formatted date string
        """
        fallback = datetime.now(UTC)

        if not date_element:
            return fallback.isoformat()

        try:
            # Prefer precise timestamp from title attribute (contains full datetime + UTC)
            title_attr = getattr(date_element, 'get', lambda *_: None)('title')
            if not title_attr and hasattr(date_element, 'find'):
                link = date_element.find('a')
                if link:
                    title_attr = link.get('title')

            if title_attr:
                parsed = datetime.strptime(title_attr, "%a %b %d %H:%M:%S %Y %Z")
                return parsed.replace(tzinfo=UTC).isoformat()

            # Fallback to visible text within span
            raw_text = date_element.get_text(strip=True)
            if raw_text:
                # Handle relative times like "5h" or "30m"
                match = re.fullmatch(r"(\d+)([smhd])", raw_text.lower())
                if match:
                    value, unit = match.groups()
                    value = int(value)
                    delta_map = {
                        's': timedelta(seconds=value),
                        'm': timedelta(minutes=value),
                        'h': timedelta(hours=value),
                        'd': timedelta(days=value),
                    }
                    delta = delta_map.get(unit)
                    if delta:
                        return (fallback - delta).isoformat()

                cleaned = raw_text.replace('·', ' ').replace('\xa0', ' ').strip()
                cleaned = re.sub(r'\s+', ' ', cleaned)

                if cleaned.endswith('UTC'):
                    try:
                        parsed = datetime.strptime(cleaned, "%b %d, %Y %I:%M %p UTC")
                        return parsed.replace(tzinfo=UTC).isoformat()
                    except ValueError:
                        # Some strings omit the year (e.g., "Oct 11 · 10:30 PM UTC")
                        try:
                            parsed = datetime.strptime(cleaned.replace(',', ''), "%b %d %I:%M %p UTC")
                            parsed = parsed.replace(year=fallback.year)
                            # If parsed date is in the future, roll back a year (tweets rarely future-dated)
                            if parsed.replace(tzinfo=UTC) > fallback:
                                parsed = parsed.replace(year=fallback.year - 1)
                            return parsed.replace(tzinfo=UTC).isoformat()
                        except ValueError:
                            pass

            return fallback.isoformat()

        except Exception as exc:
            logger.debug(f"Failed to parse tweet date '{date_element}': {exc}")
            return fallback.isoformat()
    
    def get_tweets(self, username: str, max_results: int = 10, max_retries: int = 3) -> List[Dict]:
        """
        Fetch recent tweets from a user via Nitter
        
        Args:
            username: X username (without @)
            max_results: Maximum number of tweets to fetch
            max_retries: Max retry attempts across different instances
            
        Returns:
            List of tweet dictionaries
        """
        for attempt in range(max_retries):
            instance = self._get_next_instance()
            if instance is None:
                logger.warning("No healthy Nitter instances available; aborting fetch temporarily.")
                break
            
            try:
                headers = self._pick_header_fingerprint()
                url = f"{instance}/{username}"
                delay = self._apply_jitter("nitter", url)
                logger.info(
                    "📥 Fetching tweets from @%s via %s (attempt %s/%s, sleep %.2fs)",
                    username,
                    instance,
                    attempt + 1,
                    max_retries,
                    delay
                )

                logger.debug("Nitter headers for this request: %s", headers)
                response = self.session.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find tweet containers
                tweet_divs = soup.find_all('div', class_='timeline-item')
                
                tweets = []
                for tweet_div in tweet_divs[:max_results]:
                    try:
                        # Extract tweet content
                        tweet_content_div = tweet_div.find('div', class_='tweet-content')
                        if not tweet_content_div:
                            continue
                        
                        text = tweet_content_div.get_text(strip=True, separator=' ')
                        
                        # Extract tweet link/ID
                        tweet_link = tweet_div.find('a', class_='tweet-link')
                        tweet_id = None
                        if tweet_link and 'href' in tweet_link.attrs:
                            # href format: /username/status/1234567890
                            match = re.search(r'/status/(\d+)', tweet_link['href'])
                            if match:
                                tweet_id = match.group(1)
                        
                        if not tweet_id:
                            continue
                        
                        # Extract date
                        date_span = tweet_div.find('span', class_='tweet-date')
                        created_at = self._parse_tweet_date(date_span)
                        
                        # Extract stats
                        stats = tweet_div.find('div', class_='tweet-stats')
                        likes = 0
                        retweets = 0
                        replies = 0
                        
                        if stats:
                            like_span = stats.find('span', class_='icon-heart')
                            if like_span:
                                like_text = like_span.find_next('span', class_='tweet-stat')
                                if like_text:
                                    likes = self._parse_number(like_text.get_text())
                            
                            retweet_span = stats.find('span', class_='icon-retweet')
                            if retweet_span:
                                rt_text = retweet_span.find_next('span', class_='tweet-stat')
                                if rt_text:
                                    retweets = self._parse_number(rt_text.get_text())
                            
                            reply_span = stats.find('span', class_='icon-comment')
                            if reply_span:
                                reply_text = reply_span.find_next('span', class_='tweet-stat')
                                if reply_text:
                                    replies = self._parse_number(reply_text.get_text())
                        
                        tweet = {
                            'id': tweet_id,
                            'text': text,
                            'created_at': created_at,
                            'username': username,
                            'platform': Platform.X.value,
                            'metrics': {
                                'likes': likes,
                                'retweets': retweets,
                                'replies': replies,
                            },
                            'url': f"https://x.com/{username}/status/{tweet_id}",
                            'source': f'nitter ({instance})'
                        }
                        
                        tweets.append(tweet)
                        
                    except Exception as e:
                        logger.debug(f"Failed to parse tweet: {e}")
                        continue
                
                if tweets:
                    logger.info(f"✅ Retrieved {len(tweets)} tweets from @{username} via {instance}")
                    self._mark_instance_success(instance)
                    return tweets

                logger.warning(f"⚠️  No tweets found for @{username} on {instance}")
                self._mark_instance_success(instance)
                # Try next instance
                continue
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️  Timeout on {instance}, trying next instance...")
                self._mark_instance_failure(instance, "timeout")
                time.sleep(2)
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️  Request failed on {instance}: {e}, trying next instance...")
                self._mark_instance_failure(instance, str(e))
                time.sleep(2)
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error on {instance}: {e}")
                self._mark_instance_failure(instance, str(e))
                time.sleep(2)
                continue
        
        logger.error(f"❌ Failed to fetch tweets from @{username} after {max_retries} attempts")
        return []
    
    def _parse_number(self, text: str) -> int:
        """
        Parse number from text (handles K, M notation)
        
        Args:
            text: Number as string (e.g., "1.2K", "3M")
            
        Returns:
            Integer value
        """
        text = text.strip().upper()
        
        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000,
        }
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    number = float(text.replace(suffix, '').replace(',', ''))
                    return int(number * multiplier)
                except:
                    return 0
        
        try:
            return int(text.replace(',', ''))
        except:
            return 0

    def _mark_instance_success(self, instance: str) -> None:
        """Mark an instance as healthy and clear any cooldown state."""
        self._instance_cooldown_until.pop(instance, None)
        if instance in self._degraded_instances:
            logger.info(f"✅ {instance} recovered from degraded state")
        self._degraded_instances.pop(instance, None)
        if not self._degraded_instances:
            self._last_global_outage = 0.0
        self._health_cache[instance] = {
            "is_up": True,
            "checked_at": datetime.now(UTC).isoformat(),
            "latency_ms": None,
            "error": None,
        }

    def _mark_instance_failure(self, instance: str, reason: str) -> None:
        """Mark an instance as degraded and apply a cooldown."""
        now = time.time()
        cooldown_until = now + self.INSTANCE_COOLDOWN_SECONDS
        previous = self._instance_cooldown_until.get(instance, 0.0)
        self._instance_cooldown_until[instance] = cooldown_until
        self._degraded_instances[instance] = cooldown_until

        truncated_reason = reason[:120] if reason else "unknown error"
        if previous <= now:
            logger.warning(
                f"⚠️  Marking {instance} as degraded for {self.INSTANCE_COOLDOWN_SECONDS}s ({truncated_reason})"
            )
        if len(self._degraded_instances) >= len(self.available_instances):
            previous_outage = self._last_global_outage
            self._last_global_outage = now
            should_record = not previous_outage or (now - previous_outage) > 1
            if should_record:
                self._record_block_event(
                    reason=truncated_reason,
                    metadata={"instance": instance}
                )

        self._health_cache[instance] = {
            "is_up": False,
            "checked_at": datetime.now(UTC).isoformat(),
            "latency_ms": None,
            "error": reason,
        }

    def get_degraded_instances(self) -> List[str]:
        """Return a sorted list of instances currently marked as degraded."""
        now = time.time()
        degraded = []
        for instance, until in list(self._degraded_instances.items()):
            if until <= now:
                # Cooldown expired; clear automatically
                self._degraded_instances.pop(instance, None)
                self._instance_cooldown_until.pop(instance, None)
                continue
            degraded.append(instance)

        degraded.sort()
        if not degraded and self._last_global_outage and (time.time() - self._last_global_outage) > self.INSTANCE_COOLDOWN_SECONDS:
            self._last_global_outage = 0.0
        return degraded

    def _build_header_pool(self) -> List[Dict[str, str]]:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 16_4 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
        ]

        accept_languages = [
            "en-US,en;q=0.8",
            "en-GB,en;q=0.7,de;q=0.5",
            "de-DE,de;q=0.9,en;q=0.6",
        ]

        accept_headers = [
            "text/html,application/xhtml+xml,application/xml;q=0.9, */*;q=0.8",
            "text/html,application/json;q=0.9, */*;q=0.7",
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
                        "Connection": "keep-alive",
                        "DNT": "1",
                        "Upgrade-Insecure-Requests": "1",
                    })
        return pool

    def _pick_header_fingerprint(self) -> Dict[str, str]:
        if not self._header_pool:
            self._header_pool = self._build_header_pool()
        return dict(self._rng.choice(self._header_pool))

    def _apply_jitter(self, label: str, url: str) -> float:
        delay = round(self._rng.uniform(0.2, 1.0), 3)
        logger.debug("Sleep %.3fs before %s request to %s", delay, label, url)
        time.sleep(delay)
        return delay

    def _record_block_event(self, reason: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not getattr(self, "block_history", None):
            return

        payload = {
            "active_instances": len(self._degraded_instances),
            "total_instances": len(self.available_instances),
        }
        if metadata:
            payload.update(metadata)

        try:
            self.block_history.record_event(
                source="nitter",
                reason=reason,
                metadata=payload,
            )
        except Exception as exc:
            logger.debug("Failed to persist Nitter block event: %s", exc)

    def has_recent_outage(self, window_seconds: int = 900) -> bool:
        """Return True if all instances were recently degraded."""
        if not self._last_global_outage:
            return False
        return (time.time() - self._last_global_outage) <= window_seconds

    def set_block_history_repo(self, repo) -> None:
        self.block_history = repo

    def set_last_global_outage(self, timestamp: Optional[float]) -> None:
        if timestamp is not None:
            self._last_global_outage = timestamp

    def run_health_check(
        self,
        username: Optional[str] = None,
        force: bool = False,
        timeout: int = 5,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Explicitly probe Nitter instances and cache the results.

        Args:
            username: Account slug to request during the probe (defaults to Elon Musk).
            force: Ignore cached health check results when True.
            timeout: Per-request timeout in seconds.

        Returns:
            Mapping of instance URL to health metadata.
        """
        now = time.time()
        if (
            not force
            and self._last_health_check
            and now - self._last_health_check < self.HEALTH_CACHE_TTL_SECONDS
            and self._health_cache
        ):
            logger.info("♻️  Using cached Nitter health check results")
            return self._health_cache

        target_user = username or self.health_check_username
        logger.info(f"🔍 Running Nitter health check using /{target_user} …")

        results: Dict[str, Dict[str, Any]] = {}
        for instance in self.NITTER_INSTANCES:
            start = time.time()
            try:
                headers = self._pick_header_fingerprint()
                self._apply_jitter("nitter_health", instance)
                response = self.session.get(
                    f"{instance}/{target_user}",
                    headers=headers,
                    timeout=timeout
                )
                latency_ms = (time.time() - start) * 1000
                is_up = response.status_code == 200
                status_info = {
                    "is_up": is_up,
                    "status_code": response.status_code,
                    "latency_ms": round(latency_ms, 1),
                    "checked_at": datetime.now(UTC).isoformat(),
                    "error": None if is_up else f"status {response.status_code}",
                }
                results[instance] = status_info

                if is_up:
                    logger.info(f"  ✅ {instance} ({latency_ms:.0f} ms)")
                    self._mark_instance_success(instance)
                else:
                    logger.warning(f"  ❌ {instance} (status {response.status_code})")
                    self._mark_instance_failure(instance, f"status {response.status_code}")

            except Exception as exc:
                latency_ms = (time.time() - start) * 1000
                message = str(exc)
                logger.warning(f"  ❌ {instance} ({message[:80]})")
                results[instance] = {
                    "is_up": False,
                    "status_code": None,
                    "latency_ms": round(latency_ms, 1),
                    "checked_at": datetime.now(UTC).isoformat(),
                    "error": message[:200],
                }
                self._mark_instance_failure(instance, message)

        self._health_cache = results
        self._last_health_check = now
        return results


if __name__ == "__main__":
    # Test the Nitter scraper
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    scraper = NitterScraper()
    
    # Test with Elon Musk's account
    test_username = "elonmusk"
    tweets = scraper.get_tweets(test_username, max_results=5)
    
    print(f"\n{'='*70}")
    print(f"Latest tweets from @{test_username}:")
    print('='*70)
    
    for i, tweet in enumerate(tweets, 1):
        print(f"\n{i}. Tweet ID: {tweet['id']}")
        print(f"   Posted: {tweet['created_at']}")
        print(f"   Text: {tweet['text'][:150]}...")
        print(f"   Likes: {tweet['metrics']['likes']:,}, Retweets: {tweet['metrics']['retweets']:,}")
        print(f"   URL: {tweet['url']}")
        print(f"   Source: {tweet['source']}")
