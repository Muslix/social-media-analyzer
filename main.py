import logging
import time
from datetime import datetime, UTC
import requests
from src.config import Config
from pymongo import MongoClient
from urllib.parse import urlencode
from functools import wraps
from ratelimit import limits, sleep_and_retry
import backoff
from bs4 import BeautifulSoup
import re

# Import our custom modules
from src.analyzers.market_analyzer import MarketImpactAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.output.formatter import OutputFormatter
from src.output.discord_notifier import DiscordNotifier

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
llm_analyzer = LLMAnalyzer() if config.DISCORD_NOTIFY else None
output_formatter = OutputFormatter()
discord_notifier = DiscordNotifier(config.DISCORD_WEBHOOK_URL, username="🚨 Market Impact Bot") if config.DISCORD_NOTIFY else None

# LLM threshold for analysis
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



def make_flaresolverr_request(url, headers=None, params=None):
    """Use FlareSolverr to fetch a URL and return a response-like object."""
    flaresolverr_url = f"http://{config.FLARESOLVERR_ADDRESS}:{config.FLARESOLVERR_PORT}/v1"
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 25000,
    }
    if headers:
        payload["headers"] = headers
    if params:
        from urllib.parse import urlencode
        url = url + "?" + urlencode(params)
        payload["url"] = url

    logger.info(f"Making FlareSolverr request: {url} (params={params})")

    try:
        resp = requests.post(flaresolverr_url, json=payload)
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") != "ok":
            logger.error(f"FlareSolverr error: {result}")
            raise Exception(f"FlareSolverr error: {result}")
        response_content = result["solution"]["response"]
        logger.debug(f"FlareSolverr raw response (first 500 chars): {response_content[:500]}")
        # Mimic a requests.Response object for .json() and .text
        class FakeResponse:
            def __init__(self, content):
                self._content = content
            def json(self):
                import json
                from bs4 import BeautifulSoup
                # Try to parse as JSON directly
                try:
                    return json.loads(self._content)
                except Exception:
                    # Try to extract JSON from <pre>...</pre> in HTML
                    soup = BeautifulSoup(self._content, "html.parser")
                    pre = soup.find("pre")
                    if pre:
                        try:
                            return json.loads(pre.text)
                        except Exception as e:
                            logger.error(f"Failed to parse JSON from <pre>: {e}")
                            logger.error(f"<pre> content (first 500 chars): {pre.text[:500]}")
                            raise
                    logger.error("No <pre> tag found in FlareSolverr HTML response")
                    logger.error(f"HTML content (first 500 chars): {self._content[:500]}")
                    raise
            @property
            def text(self):
                return self._content
        return FakeResponse(response_content)
    except Exception as e:
        logger.error(f"FlareSolverr request failed for {url}: {e}")
        raise



def connect_mongodb():
    """Connect to MongoDB and return the collection"""
    try:
        client = MongoClient(config.MONGO_DBSTRING)
        db = client[config.MONGO_DB]
        collection = db[config.MONGO_COLLECTION]
        logger.info("Successfully connected to MongoDB")
        return collection
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
    return collection.find_one({"_id": post_id}) is not None

def mark_post_processed(collection, post):
    """Mark a post as processed in MongoDB with additional metadata"""
    try:
        doc = {
            "_id": post["id"],
            "content": post.get("content", ""),
            "created_at": post["created_at"],
            "sent_at": datetime.now(UTC),
            "username": post.get("account", {}).get("username", ""),
            "display_name": post.get("account", {}).get("display_name", ""),
            "media_attachments": [
                {
                    "type": m.get("type"),
                    "url": m.get("url") or m.get("preview_url")
                }
                for m in post.get("media_attachments", [])
                if m.get("type") in ["image", "video", "gifv"]
            ]
        }
        collection.insert_one(doc)
        logger.info(f"Successfully marked post {post['id']} as processed")
    except Exception as e:
        logger.error(f"Error marking post as processed: {e}")
        raise

def save_to_file(message, media_attachments=None, market_analysis=None):
    """Save post to files using OutputFormatter"""
    output = output_formatter.format_analysis_output(message, market_analysis, media_attachments)
    output_formatter.save_to_files(output, market_analysis)

def get_truth_social_posts():
    """Get posts from Truth Social using Mastodon API via ScrapeOps proxy"""
    try:
        # Prepare headers that look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': f'https://{config.TRUTH_INSTANCE}/@{config.TRUTH_USERNAME}',
            'Origin': f'https://{config.TRUTH_INSTANCE}'
        }

        # First get the user ID
        lookup_url = f'https://{config.TRUTH_INSTANCE}/api/v1/accounts/lookup?acct={config.TRUTH_USERNAME}'
        
        response = make_flaresolverr_request(lookup_url, headers)
        user_data = response.json()
        
        if not user_data or 'id' not in user_data:
            raise ValueError(f"Could not find user ID for {config.TRUTH_USERNAME}")
            
        user_id = user_data['id']
        logger.debug(f"Found user ID: {user_id}")
        
        # Now get their posts
        posts_url = f'https://{config.TRUTH_INSTANCE}/api/v1/accounts/{user_id}/statuses'
        params = {
            'exclude_replies': 'true',
            'exclude_reblogs': 'true',
            'limit': '40'
        }
        
        response = make_flaresolverr_request(posts_url, params=params, headers=headers)
        posts = response.json()
        
        if not isinstance(posts, list):
            raise ValueError(f"Invalid posts response: {posts}")
            
        logger.info(f"Retrieved {len(posts)} posts")
        return posts
        
    except Exception as e:
        logger.error(f"Error getting Truth Social posts: {e}")
        return []

def main():
    logger.info("Starting Truth Social monitor...")
    
    # Connect to MongoDB
    try:
        mongo_collection = connect_mongodb()
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

    while True:
        try:
            # Get posts
            posts = get_truth_social_posts()
            
            # Process posts in chronological order (oldest first)
            # This ensures Discord timeline shows posts in correct order (newest at bottom)
            for post in sorted(posts, key=lambda x: x.get('created_at', ''), reverse=False):
                # Validate post structure
                if not isinstance(post, dict) or 'id' not in post:
                    logger.warning(f"Invalid post structure: {post}")
                    continue
                
                # Get and clean the content using BeautifulSoup
                from bs4 import BeautifulSoup
                content = post.get('content') or post.get('text', '')
                soup = BeautifulSoup(content, 'html.parser')
                cleaned_content = soup.get_text().strip()
                
                # Skip posts without meaningful text content (minimum 20 characters)
                if not cleaned_content or len(cleaned_content.strip()) < 20:
                    logger.debug(f"Post {post['id']} has insufficient text content ({len(cleaned_content.strip())} chars), skipping")
                    continue
                    
                # Skip if already processed
                if is_post_processed(mongo_collection, post['id']):
                    logger.debug(f"Post {post['id']} already processed, skipping")
                    continue
                
                logger.info(f"Processing new post {post['id']} with {len(cleaned_content)} characters of text")
                
                # Analyze market impact using keyword analyzer
                market_analysis = market_analyzer.analyze(cleaned_content)
                if market_analysis:
                    logger.info(f"Market analysis: {market_analysis['summary']}")
                
                # LLM Analysis for high-impact posts (if Discord enabled)
                llm_analysis = None
                if config.DISCORD_NOTIFY and market_analysis and market_analysis['impact_score'] >= 20:
                    logger.info(f"Running LLM analysis (score >= 20)...")
                    llm_analysis = llm_analyzer.analyze(cleaned_content, market_analysis['impact_score'])
                    
                    # Save training data only if LLM analysis succeeded
                    if llm_analysis:
                        # Quality check the analysis before saving/sending
                        qc_result = llm_analyzer.quality_check_analysis(cleaned_content, llm_analysis)
                        
                        if qc_result and not qc_result.get('approved', False):
                            # Apply suggested fixes if available
                            suggested_fixes = qc_result.get('suggested_fixes', {})
                            if suggested_fixes.get('reasoning'):
                                logger.info(f"📝 Applying improved reasoning from quality check")
                                llm_analysis['reasoning'] = suggested_fixes['reasoning']
                            if suggested_fixes.get('urgency'):
                                logger.info(f"📝 Correcting urgency: {llm_analysis.get('urgency')} → {suggested_fixes['urgency']}")
                                llm_analysis['urgency'] = suggested_fixes['urgency']
                            if suggested_fixes.get('score') is not None:
                                logger.info(f"📝 Adjusting score: {llm_analysis.get('score')} → {suggested_fixes['score']}")
                                llm_analysis['score'] = suggested_fixes['score']
                        
                        # Save training data with quality info
                        llm_analyzer.save_training_data(
                            cleaned_content, 
                            market_analysis['impact_score'], 
                            llm_analysis,
                            quality_check=qc_result
                        )
                    else:
                        logger.warning(f"⚠️  LLM analysis failed for post {post['id']} - will NOT send Discord alert")
                
                # Prepare simple message for file output
                created_at = datetime.fromisoformat(post.get('created_at', '').replace('Z', '+00:00'))
                account = post.get('account', {})
                username = account.get('username') or config.TRUTH_USERNAME
                display_name = account.get('display_name', username)
                post_type = config.POST_TYPE.capitalize()
                message = f"**New {post_type} from {display_name} (@{username})**\n{cleaned_content}\n*Posted at: {created_at.strftime('%B %d, %Y at %I:%M %p %Z')}*"
                
                media_attachments = post.get('media_attachments', [])
                
                # Save to file with market analysis
                save_to_file(message, media_attachments, market_analysis)
                
                # Send to Discord ONLY if LLM analysis succeeded (for high-impact posts)
                if config.DISCORD_NOTIFY and discord_notifier and market_analysis:
                    # Only send HIGH or CRITICAL alerts to Discord
                    if market_analysis['impact_score'] >= 25:  # HIGH or CRITICAL
                        # Require successful LLM analysis before sending to Discord
                        if llm_analysis:
                            post_url = f"https://truthsocial.com/@{config.TRUTH_USERNAME}/posts/{post['id']}"
                            discord_notifier.send_market_alert(
                                post_text=cleaned_content,
                                keyword_analysis=market_analysis,
                                llm_analysis=llm_analysis,
                                post_url=post_url,
                                author=f"@{config.TRUTH_USERNAME}",
                                post_created_at=post.get('created_at')
                            )
                        else:
                            logger.warning(f"⚠️  Skipping Discord alert for high-impact post due to failed LLM analysis (keyword score: {market_analysis['impact_score']})")

                
                # Mark as processed only if successfully saved
                mark_post_processed(mongo_collection, post)
                
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
