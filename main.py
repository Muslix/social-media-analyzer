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
from src.services.post_processing_pipeline import PostProcessingPipeline
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
        logger.info(
            "Successfully connected to MongoDB (posts: %s, analysis: %s)",
            config.MONGO_COLLECTION,
            config.MONGO_ANALYSIS_COLLECTION
        )
        return posts_collection, analysis_collection
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
        return []
    
    try:
        all_tweets = []
        logger.info(f"🐦 Monitoring {len(config.X_USERNAMES)} X/Twitter accounts: {', '.join(['@' + u for u in config.X_USERNAMES])}")
        
        for username in config.X_USERNAMES:
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
        
        logger.info(f"🎯 Total tweets collected from X/Twitter: {len(all_tweets)}")
        return all_tweets
    except Exception as e:
        logger.error(f"Error getting X tweets: {e}")
        return []

def get_truth_social_posts():
    """Get posts from Truth Social using direct API access (no FlareSolverr)"""
    # Check if Truth Social is enabled (either old TRUTH_USERNAME or new TRUTH_USERNAMES)
    usernames = config.TRUTH_USERNAMES if config.TRUTH_USERNAMES else ([config.TRUTH_USERNAME] if config.TRUTH_USERNAME else [])
    
    if not usernames or not truth_social_scraper:
        logger.debug("Truth Social monitoring disabled")
        return []

    try:
        all_posts: List[Dict[str, Any]] = []
        logger.info(f"🇺🇸 Monitoring {len(usernames)} Truth Social account(s): {', '.join(['@' + u for u in usernames])}")

        for username in usernames:
            posts = truth_social_scraper.get_posts(username, max_results=5)

            if posts:
                all_posts.extend(posts)
                logger.info(f"✅ Got {len(posts)} posts from Truth Social @{username}")
            else:
                logger.warning(f"⚠️  No posts retrieved for @{username}")
                logger.warning(f"⚠️  Truth Social may be using Cloudflare protection")

        logger.info(f"🎯 Total posts collected from Truth Social: {len(all_posts)}")
        return all_posts

    except Exception as e:
        logger.error(f"Error getting Truth Social posts: {e}")
        logger.warning("💡 If Cloudflare is blocking access, consider:")
        logger.warning("   1. Using a VPN/proxy")
        logger.warning("   2. Waiting and trying again later")
        logger.warning("   3. Focusing on X/Twitter monitoring only")
        return []


def collect_posts() -> List[Dict[str, Any]]:
    """Collect posts from all configured platforms"""
    all_posts: List[Dict[str, Any]] = []

    truth_posts: List[Dict[str, Any]] = []
    x_tweets: List[Dict[str, Any]] = []

    if config.TRUTH_USERNAMES or config.TRUTH_USERNAME:
        truth_posts = get_truth_social_posts()
        all_posts.extend(truth_posts)

    if config.X_ENABLED:
        x_tweets = get_x_tweets()
        all_posts.extend(x_tweets)

    logger.info(
        "📊 Total posts collected: %s (Truth Social: %s, X: %s)",
        len(all_posts),
        sum(1 for post in all_posts if post.get('platform') == Platform.TRUTH_SOCIAL.value),
        sum(1 for post in all_posts if post.get('platform') == Platform.X.value)
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
        posts_collection, analysis_collection = connect_mongodb()
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
    
    global output_formatter
    output_formatter = OutputFormatter(
        analysis_collection=analysis_collection,
        enable_file_export=config.ENABLE_FILE_EXPORT
    )

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
    )

    while True:
        try:
            posts = collect_posts()
            if not posts:
                logger.debug("No new posts collected in this cycle")
            pipeline.process_posts(posts, posts_collection)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            # Add network policy reminder here too
            if (
                "SSL handshake failed" in str(e)
                or "tlsv1 alert internal error" in str(e)
                or "TopologyDescription" in str(e)
            ):
                logger.error(
                    "MongoDB connection failed due to SSL/network error. "
                    "Reminder: Check your MongoDB Atlas Network Access Policy, firewall, and IP whitelist settings."
                )
        
        delay = int(config.REPEAT_DELAY)
        logger.info(f"Waiting {delay} seconds before next check...")
        time.sleep(delay)

if __name__ == "__main__":
    main()
