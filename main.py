import logging
import time
from datetime import datetime, UTC
from typing import Any, Dict, List
import requests
from src.config import Config
from pymongo import MongoClient
from urllib.parse import urlencode
from functools import wraps
from ratelimit import limits, sleep_and_retry
import backoff
import re

# Import our custom modules
from src.analyzers.market_analyzer import MarketImpactAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.output.formatter import OutputFormatter
from src.output.discord_notifier import DiscordNotifier
from src.scrapers.nitter_scraper import NitterScraper
from src.scrapers.truth_social_scraper import TruthSocialScraper
from src.scrapers.rss_scraper import RSSFeedScraper
from src.services.post_processing_pipeline import PostProcessingPipeline
from src.services.quiet_hours import QuietHoursManager
from src.services.block_history import BlockHistoryRepository
from src.services.interval_controller import IntervalController
from src.services.market_impact_tracker import (
    MarketImpactTracker,
    CoinGeckoCryptoProvider,
    StooqIndexProvider,
    MarketImpactRepository,
)
from src.enums import PostStatus, MediaType, Platform

# Configure logging
config = Config()
logging.basicConfig(
    format=config.LOG_FORMAT,
    level=logging.DEBUG if config.LOG_LEVEL.upper() == 'DEBUG' else logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize analyzers and notifiers
market_analyzer = MarketImpactAnalyzer()
llm_analyzer = LLMAnalyzer(config=config)  # Always initialize LLM analyzer for training data collection
output_formatter = None  # Will be initialized after database connection
discord_notifier = DiscordNotifier(config.DISCORD_WEBHOOK_URL, username="🚨 Market Impact Bot") if config.DISCORD_NOTIFY else None
discord_all_posts_notifier = DiscordNotifier(config.DISCORD_ALL_POSTS_WEBHOOK, username=config.DISCORD_ALL_POSTS_USERNAME) if config.DISCORD_ALL_POSTS_WEBHOOK else None
discord_failure_notifier = DiscordNotifier(config.DISCORD_FAILURE_WEBHOOK, username=config.DISCORD_FAILURE_USERNAME) if config.DISCORD_FAILURE_WEBHOOK else None
nitter_scraper = NitterScraper() if config.X_ENABLED else None

# Initialize Truth Social scraper (optional FlareSolverr support)
truth_social_scraper = None
if config.TRUTH_USERNAMES or config.TRUTH_USERNAME:
    truth_social_scraper = TruthSocialScraper(
        instance=config.TRUTH_INSTANCE,
        timeout=config.REQUEST_TIMEOUT,
        use_flaresolverr=config.FLARESOLVERR_ENABLED,
        flaresolverr_url=config.FLARESOLVERR_URL,
        flaresolverr_timeout=config.FLARESOLVERR_TIMEOUT,
    )

quiet_hours_manager = QuietHoursManager(config.QUIET_HOURS_WINDOWS)
rss_scraper = RSSFeedScraper() if config.RSS_FEEDS else None

# LLM threshold for analysis (with enhanced CRITICAL_COMBINATIONS)
LLM_ANALYSIS_THRESHOLD = 20  # Posts with keyword score >= 20 get LLM analysis
DISCORD_ALERT_THRESHOLD = 25  # Only HIGH/CRITICAL go to Discord

@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, requests.exceptions.HTTPError),
    max_tries=config.MAX_RETRIES
)
def make_request(url, headers):
    """Make HTTP request with retry mechanism"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error {e.response.status_code} for URL {url}")
        logger.error(f"Response headers: {e.response.headers}")
        logger.error(f"Response body: {e.response.text[:500]}")  # First 500 chars of error response
        raise



# Legacy direct scraping helper retained for non-FlareSolverr code paths



def connect_mongodb():
    """Connect to MongoDB and return the post + analysis collections"""
    try:
        client = MongoClient(config.MONGO_DBSTRING)
        db = client[config.MONGO_DB]
        posts_collection = db[config.MONGO_COLLECTION]
        analysis_collection = db[config.MONGO_ANALYSIS_COLLECTION]
        block_history_collection = db[config.MONGO_BLOCK_HISTORY_COLLECTION]
        market_impact_collection = db[config.MARKET_IMPACT_COLLECTION]
        logger.info(
            "Successfully connected to MongoDB (posts: %s, analysis: %s, block_history: %s, market_impact: %s)",
            config.MONGO_COLLECTION,
            config.MONGO_ANALYSIS_COLLECTION,
            config.MONGO_BLOCK_HISTORY_COLLECTION,
            config.MARKET_IMPACT_COLLECTION,
        )
        return posts_collection, analysis_collection, block_history_collection, market_impact_collection
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Check for SSL handshake/network policy errors
        if (
            "SSL handshake failed" in str(e)
            or "tlsv1 alert internal error" in str(e)
            or "TopologyDescription" in str(e)
        ):
            logger.error(
                "MongoDB connection failed due to SSL/network error. "
                "Reminder: Check your MongoDB Atlas Network Access Policy, firewall, and IP whitelist settings."
            )
        raise

def is_post_processed(collection, post_id):
    """Check if a post has already been processed"""
    doc = collection.find_one({"_id": post_id})
    if not doc:
        return False
    status = doc.get("status")
    if status is None:
        return True
    return status == PostStatus.PROCESSED.value

def mark_post_processed(collection, post):
    """Mark a post as processed in MongoDB with additional metadata"""
    try:
        allowed_media_types = MediaType.allowed_values()
        doc = {
            "_id": post["id"],
            "content": post.get("content", ""),
            "created_at": post["created_at"],
            "sent_at": datetime.now(UTC),
            "username": post.get("account", {}).get("username", ""),
            "display_name": post.get("account", {}).get("display_name", ""),
            "status": PostStatus.PROCESSED.value,
            "media_attachments": [
                {
                    "type": m.get("type"),
                    "url": m.get("url") or m.get("preview_url")
                }
                for m in post.get("media_attachments", [])
                if m.get("type") in allowed_media_types
            ]
        }
        collection.insert_one(doc)
        logger.info(f"Successfully marked post {post['id']} as processed")
    except Exception as e:
        logger.error(f"Error marking post as processed: {e}")
        raise

def get_x_tweets():
    """Get tweets from X/Twitter using Nitter scraper"""
    if not config.X_ENABLED or not config.X_USERNAMES:
        logger.debug("X/Twitter monitoring disabled")
        return [], {"skipped": [], "total": 0}
    
    try:
        all_tweets = []
        usernames = config.X_USERNAMES
        logger.info(f"🐦 Monitoring {len(usernames)} X/Twitter accounts: {', '.join(['@' + u for u in usernames])}")

        quiet_skips: List[Dict[str, Any]] = []

        for username in usernames:
            location_label = config.X_ACCOUNT_LOCATIONS.get(username.lower(), config.QUIET_HOURS_DEFAULT_LOCATION)
            seconds, resume_at = quiet_hours_manager.time_until_available(location_label)
            if seconds is not None:
                resume_str = resume_at.strftime('%Y-%m-%d %H:%M %Z') if resume_at else "later"
                logger.info(
                    "⏸️ Quiet hours active for X/Twitter @%s (location %s). Next attempt after %s",
                    username,
                    location_label,
                    resume_str
                )
                quiet_skips.append({
                    "username": username,
                    "location": location_label,
                    "resume_at": resume_str,
                })
                continue

            logger.info(f"📥 Fetching tweets from @{username}...")
            tweets = nitter_scraper.get_tweets(username, max_results=5)  # Only last 5 tweets per user
            
            # Transform to common format
            for tweet in tweets:
                all_tweets.append({
                    'id': f"x_{tweet['id']}",  # Prefix with 'x_' to distinguish from Truth Social
                    'content': tweet['text'],
                    'created_at': tweet['created_at'],
                    'account': {
                        'username': username,
                        'display_name': username
                    },
                    'platform': Platform.X.value,
                    'url': tweet['url'],
                    'metrics': tweet['metrics'],
                    'media_attachments': []
                })
            
            logger.info(f"✅ Got {len(tweets)} tweets from @{username}")

        if quiet_skips and len(quiet_skips) == len(usernames) and not all_tweets:
            logger.info("⏸️ All X/Twitter accounts currently in quiet hours; skipping this cycle.")

        logger.info(f"🎯 Total tweets collected from X/Twitter: {len(all_tweets)}")
        return all_tweets, {"skipped": quiet_skips, "total": len(usernames)}
    except Exception as e:
        logger.error(f"Error getting X tweets: {e}")
        return [], {"skipped": [], "total": len(config.X_USERNAMES or [])}

def get_truth_social_posts():
    """Get posts from Truth Social using direct API access (no FlareSolverr)"""
    # Check if Truth Social is enabled (either old TRUTH_USERNAME or new TRUTH_USERNAMES)
    usernames = config.TRUTH_USERNAMES if config.TRUTH_USERNAMES else ([config.TRUTH_USERNAME] if config.TRUTH_USERNAME else [])
    
    if not usernames or not truth_social_scraper:
        logger.debug("Truth Social monitoring disabled")
        return [], {"skipped": [], "total": 0}

    try:
        all_posts: List[Dict[str, Any]] = []
        logger.info(f"🇺🇸 Monitoring {len(usernames)} Truth Social account(s): {', '.join(['@' + u for u in usernames])}")

        quiet_skips: List[Dict[str, Any]] = []

        for username in usernames:
            location_label = config.TRUTH_ACCOUNT_LOCATIONS.get(username.lower(), config.QUIET_HOURS_DEFAULT_LOCATION)
            seconds, resume_at = quiet_hours_manager.time_until_available(location_label)
            if seconds is not None:
                resume_str = resume_at.strftime('%Y-%m-%d %H:%M %Z') if resume_at else "later"
                logger.info(
                    "⏸️ Quiet hours active for Truth Social @%s (location %s). Next attempt after %s",
                    username,
                    location_label,
                    resume_str
                )
                quiet_skips.append({
                    "username": username,
                    "location": location_label,
                    "resume_at": resume_str,
                })
                continue

            posts = truth_social_scraper.get_posts(username, max_results=5)

            if posts:
                all_posts.extend(posts)
                logger.info(f"✅ Got {len(posts)} posts from Truth Social @{username}")
            else:
                logger.warning(f"⚠️  No posts retrieved for @{username}")
                logger.warning(f"⚠️  Truth Social may be using Cloudflare protection")

        if quiet_skips and len(quiet_skips) == len(usernames) and not all_posts:
            logger.info("⏸️ All Truth Social accounts currently in quiet hours; skipping this cycle.")

        logger.info(f"🎯 Total posts collected from Truth Social: {len(all_posts)}")
        return all_posts, {"skipped": quiet_skips, "total": len(usernames)}

    except Exception as e:
        logger.error(f"Error getting Truth Social posts: {e}")
        logger.warning("💡 If Cloudflare is blocking access, consider:")
        logger.warning("   1. Using a VPN/proxy")
        logger.warning("   2. Waiting and trying again later")
        logger.warning("   3. Focusing on X/Twitter monitoring only")
        return [], {"skipped": [], "total": len(usernames)}


def get_rss_posts() -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch items from configured RSS feeds."""
    if not rss_scraper or not config.RSS_FEEDS:
        return [], {"skipped": [], "total": 0}

    all_entries: List[Dict[str, Any]] = []
    quiet_skips: List[Dict[str, Any]] = []

    for label, feed_url in config.RSS_FEEDS.items():
        location_label = config.RSS_FEED_LOCATIONS.get(label.lower(), config.QUIET_HOURS_DEFAULT_LOCATION)
        seconds, resume_at = quiet_hours_manager.time_until_available(location_label)
        if seconds is not None:
            resume_str = resume_at.strftime('%Y-%m-%d %H:%M %Z') if resume_at else "later"
            logger.info(
                "⏸️ Quiet hours active for RSS feed %s (location %s). Next attempt after %s",
                label,
                location_label,
                resume_str
            )
            quiet_skips.append({
                "feed": label,
                "location": location_label,
                "resume_at": resume_str,
            })
            continue

        logger.info("📰 Fetching RSS feed %s", label)
        entries = rss_scraper.fetch(feed_url, max_entries=5)
        logger.info("✅ Got %s entries from %s", len(entries), label)

        for entry in entries:
            post_id = f"rss_{label}_{entry['id']}"
            display_name = entry.get("title") or label
            all_entries.append({
                "id": post_id,
                "content": entry.get("content") or entry.get("summary") or "",
                "created_at": entry.get("created_at"),
                "account": {
                    "username": label,
                    "display_name": display_name,
                },
                "platform": Platform.RSS.value,
                "url": entry.get("url"),
                "metrics": {},
            })

    if quiet_skips and len(quiet_skips) == len(config.RSS_FEEDS) and not all_entries:
        logger.info("⏸️ All RSS feeds currently in quiet hours; skipping this cycle.")

    return all_entries, {"skipped": quiet_skips, "total": len(config.RSS_FEEDS)}


def collect_posts() -> List[Dict[str, Any]]:
    """Collect posts from all configured platforms"""
    all_posts: List[Dict[str, Any]] = []

    truth_posts: List[Dict[str, Any]] = []
    x_tweets: List[Dict[str, Any]] = []
    rss_items: List[Dict[str, Any]] = []
    truth_meta = {"skipped": [], "total": 0}
    x_meta = {"skipped": [], "total": 0}
    rss_meta = {"skipped": [], "total": 0}

    if config.TRUTH_USERNAMES or config.TRUTH_USERNAME:
        truth_posts, truth_meta = get_truth_social_posts()
        all_posts.extend(truth_posts)

    if config.X_ENABLED:
        x_tweets, x_meta = get_x_tweets()
        all_posts.extend(x_tweets)

    if config.RSS_FEEDS:
        rss_items, rss_meta = get_rss_posts()
        all_posts.extend(rss_items)

    def _format_skip_entry(item: Dict[str, Any]) -> str:
        """Format a skipped entry for logging without assuming specific keys."""
        if "username" in item and item["username"]:
            identifier = f"@{item['username']}"
        elif "feed" in item and item["feed"]:
            identifier = item["feed"]
        else:
            identifier = item.get("label") or item.get("id") or "unknown"

        location = item.get("location") or "N/A"
        resume_at = item.get("resume_at", "later")
        return f"{identifier} ({location} → {resume_at})"

    def _log_quiet(platform: str, meta: Dict[str, Any]):
        if not meta.get("skipped"):
            return
        details = ", ".join(_format_skip_entry(item) for item in meta["skipped"])
        logger.info("⏸️ Quiet hours (%s): %s", platform, details)

    _log_quiet("Truth Social", truth_meta)
    _log_quiet("X/Twitter", x_meta)
    _log_quiet("RSS", rss_meta)

    truth_count = sum(1 for post in all_posts if post.get('platform') == Platform.TRUTH_SOCIAL.value)
    x_count = sum(1 for post in all_posts if post.get('platform') == Platform.X.value)
    rss_count = sum(1 for post in all_posts if post.get('platform') == Platform.RSS.value)

    logger.info(
        "📊 Total posts collected: %s (Truth Social: %s, X: %s, RSS: %s)",
        len(all_posts),
        truth_count,
        x_count,
        rss_count,
    )

    return all_posts


def show_legal_disclaimer():
    """Display legal disclaimer and get user consent"""
    import sys
    
    if not config.ACCEPT_LEGAL_DISCLAIMER:
        disclaimer = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ⚖️  LEGAL DISCLAIMER & WARNING ⚖️                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

This tool scrapes publicly available data from social media platforms.

⚠️  IMPORTANT LEGAL CONSIDERATIONS:

1. You are SOLELY RESPONSIBLE for compliance with:
   • Platform Terms of Service (X/Twitter, Truth Social)
   • Local, national, and international laws
   • Data protection regulations (GDPR, CCPA, etc.)

2. This tool is for EDUCATIONAL/RESEARCH purposes only
   • Not intended for commercial use without proper authorization
   • Does not guarantee legal compliance in all jurisdictions

3. Scraping Considerations:
   • Monitors PUBLICLY AVAILABLE posts only
   • Uses rate limiting and respectful delays (10min default)
   • May be against platform ToS - check before use
   • Platforms may block your IP or take legal action

4. Recommended Actions:
   • Review DISCLAIMER.md for full legal information
   • Consult a lawyer for commercial use
   • Consider using official APIs (X API) when available
   • Monitor public accounts only

📄 Full disclaimer: See DISCLAIMER.md in the project root

By continuing, you acknowledge:
✓ You have read and understood this warning
✓ You accept all risks and legal responsibility
✓ You will comply with all applicable laws and Terms of Service
✓ This is for personal research/educational use only

══════════════════════════════════════════════════════════════════════════════
"""

        logger.warning(disclaimer)
        logger.warning("Proceeding without interactive confirmation. Set ACCEPT_LEGAL_DISCLAIMER=true to suppress this banner.")


def main():
    # Show legal disclaimer first
    show_legal_disclaimer()
    
    logger.info("🚀 Starting Multi-Platform Social Media Monitor...")
    
    # Count enabled accounts
    truth_count = len(config.TRUTH_USERNAMES) if config.TRUTH_USERNAMES else (1 if config.TRUTH_USERNAME else 0)
    x_count = len(config.X_USERNAMES) if config.X_ENABLED else 0
    
    logger.info(f"  Truth Social: {'✅ Enabled' if truth_count > 0 else '❌ Disabled'} ({truth_count} account{'' if truth_count == 1 else 's'})")
    logger.info(f"  X/Twitter: {'✅ Enabled' if config.X_ENABLED else '❌ Disabled'} ({x_count} account{'' if x_count == 1 else 's'})")
    logger.info(f"  Check Interval: Every {config.REPEAT_DELAY} seconds ({config.REPEAT_DELAY // 60} minutes)")
    
    # Connect to MongoDB
    try:
        (
            posts_collection,
            analysis_collection,
            block_history_collection,
            market_impact_collection,
        ) = connect_mongodb()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB in main: {e}")
        if (
            "SSL handshake failed" in str(e)
            or "tlsv1 alert internal error" in str(e)
            or "TopologyDescription" in str(e)
        ):
            logger.error(
                "MongoDB connection failed due to SSL/network error. "
                "Reminder: Check your MongoDB Atlas Network Access Policy, firewall, and IP whitelist settings."
            )
        raise
    
    block_history_repo = BlockHistoryRepository(block_history_collection)

    if truth_social_scraper:
        truth_social_scraper.set_block_history_repo(block_history_repo)
        last = block_history_repo.get_latest_event_time(
            "truth_social",
            window_seconds=config.BLOCKED_BACKOFF_MAX or 3600
        )
        if last:
            truth_social_scraper.set_last_block_timestamp(last.timestamp())

    if nitter_scraper:
        nitter_scraper.set_block_history_repo(block_history_repo)
        last = block_history_repo.get_latest_event_time(
            "nitter",
            window_seconds=config.BLOCKED_BACKOFF_MAX or 3600
        )
        if last:
            nitter_scraper.set_last_global_outage(last.timestamp())

    global output_formatter
    output_formatter = OutputFormatter(
        analysis_collection=analysis_collection,
        enable_file_export=config.ENABLE_FILE_EXPORT
    )

    market_impact_repository = MarketImpactRepository(market_impact_collection)
    crypto_symbols = [symbol.lower() for symbol in config.MARKET_IMPACT_CRYPTO_IDS.keys()]
    index_symbols = [symbol.lower() for symbol in config.MARKET_IMPACT_INDEX_IDS.keys()]

    crypto_provider = None
    if crypto_symbols:
        crypto_provider = CoinGeckoCryptoProvider(
            id_map=config.MARKET_IMPACT_CRYPTO_IDS,
            vs_currency=config.MARKET_IMPACT_FIAT,
        )

    index_provider = None
    if index_symbols:
        index_currency_map: Dict[str, str] = {}
        for key in index_symbols:
            if "dow" in key or "dji" in key:
                index_currency_map[key] = "usd"
            elif "dax" in key or "gda" in key or "ger" in key:
                index_currency_map[key] = "eur"
        index_provider = StooqIndexProvider(
            symbol_map=config.MARKET_IMPACT_INDEX_IDS,
            currency_map=index_currency_map,
        )

    market_impact_tracker = None
    if config.MARKET_IMPACT_ENABLED and (crypto_symbols or index_symbols):
        market_impact_tracker = MarketImpactTracker(
            repository=market_impact_repository,
            crypto_provider=crypto_provider,
            index_provider=index_provider,
            enabled=True,
            crypto_symbols=crypto_symbols,
            index_symbols=index_symbols,
        )
        logger.info(
            "Market impact tracker enabled (crypto assets: %s, indices: %s)",
            ", ".join(crypto_symbols) or "none",
            ", ".join(index_symbols) or "none",
        )
    else:
        logger.info("Market impact tracker disabled or no assets configured.")

    pipeline = PostProcessingPipeline(
        config=config,
        market_analyzer=market_analyzer,
        llm_analyzer=llm_analyzer,
        output_formatter=output_formatter,
        discord_notifier=discord_notifier,
        discord_all_posts_notifier=discord_all_posts_notifier,
        llm_threshold=LLM_ANALYSIS_THRESHOLD,
        discord_threshold=DISCORD_ALERT_THRESHOLD,
        is_processed_fn=is_post_processed,
        mark_processed_fn=mark_post_processed,
        market_impact_tracker=market_impact_tracker,
        failure_notifier=discord_failure_notifier,
    )
    interval_controller = IntervalController(config)
    consecutive_empty_cycles = 0

    while True:
        posts: List[Dict[str, Any]] = []
        try:
            posts = collect_posts()
            if not posts:
                logger.debug("No new posts collected in this cycle")
            pipeline.process_posts(posts, posts_collection)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            if (
                "SSL handshake failed" in str(e)
                or "tlsv1 alert internal error" in str(e)
                or "TopologyDescription" in str(e)
            ):
                logger.error(
                    "MongoDB connection failed due to SSL/network error. "
                    "Reminder: Check your MongoDB Atlas Network Access Policy, firewall, and IP whitelist settings."
                )
            if discord_failure_notifier:
                details = {
                    "error": str(e),
                    "cycle_time": datetime.now(UTC).isoformat(),
                }
                discord_failure_notifier.send_failure_alert(
                    "Main Loop Fehler",
                    "Beim Sammeln oder Verarbeiten der Posts ist ein Fehler aufgetreten.",
                    details=details,
                )
        finally:
            if market_impact_tracker:
                market_impact_tracker.run_pending()

            if posts:
                consecutive_empty_cycles = 0
            else:
                consecutive_empty_cycles += 1

            blocked_sources: List[str] = []
            if truth_social_scraper and truth_social_scraper.had_recent_block():
                blocked_sources.append("Truth Social")
            if nitter_scraper and nitter_scraper.has_recent_outage():
                blocked_sources.append("Nitter")

            if blocked_sources:
                logger.warning(
                    "Recent access issues detected for %s; applying extended backoff.",
                    ", ".join(blocked_sources)
                )

            delay, reasons = interval_controller.compute_delay(
                blocked=bool(blocked_sources),
                consecutive_empty=consecutive_empty_cycles
            )
            reason_text = ", ".join(f"{name}={value}s" for name, value in reasons.items())
            logger.info(
                "Waiting %s seconds before next check (reasons: %s, empty streak: %s)",
                delay,
                reason_text,
                consecutive_empty_cycles
            )
            time.sleep(delay)

if __name__ == "__main__":
    main()
