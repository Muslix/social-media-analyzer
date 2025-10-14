import os
import logging
from typing import Dict, List, Tuple
from dotenv import load_dotenv


def _parse_account_locations(raw: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not raw:
        return mapping
    for entry in raw.split(','):
        entry = entry.strip()
        if not entry or ':' not in entry:
            continue
        username, label = entry.split(':', 1)
        username = username.strip().lower()
        label = label.strip().upper()
        if username and label:
            mapping[username] = label
    return mapping


def _parse_quiet_hours(raw: str) -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
    """
    Parse quiet hours string (e.g., "US|America/New_York|00:00-06:00,22:00-23:00;EU|Europe/Berlin|02:00-05:00")
    into structure {label: {"timezone": tz, "ranges": [(start,end), ...]}}
    """
    result: Dict[str, Dict[str, List[Tuple[str, str]]]] = {}
    if not raw:
        return result

    for chunk in raw.split(';'):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split('|')
        if len(parts) != 3:
            logging.warning("Skipping invalid QUIET_HOURS entry: %s", chunk)
            continue
        label, tz_name, ranges_str = [p.strip() for p in parts]
        if not label or not tz_name or not ranges_str:
            logging.warning("Skipping incomplete QUIET_HOURS entry: %s", chunk)
            continue

        label = label.upper()
        ranges: List[Tuple[str, str]] = []
        for window in ranges_str.split(','):
            window = window.strip()
            if not window or '-' not in window:
                logging.warning("Skipping invalid quiet hour window '%s' in entry '%s'", window, chunk)
                continue
            start, end = [t.strip() for t in window.split('-', 1)]
            if not start or not end:
                logging.warning("Incomplete quiet hour window '%s' in entry '%s'", window, chunk)
                continue
            ranges.append((start, end))

        if not ranges:
            continue

        result[label] = {
            "timezone": tz_name,
            "ranges": ranges,
        }

    return result


def _parse_feed_definitions(raw: str) -> Dict[str, str]:
    feeds: Dict[str, str] = {}
    if not raw:
        return feeds
    for chunk in raw.split(';'):
        chunk = chunk.strip()
        if not chunk or '|' not in chunk:
            logging.warning("Skipping invalid RSS feed entry: %s", chunk)
            continue
        label, url = chunk.split('|', 1)
        label = label.strip().lower()
        url = url.strip()
        if not label or not url:
            logging.warning("Skipping incomplete RSS feed entry: %s", chunk)
            continue
        feeds[label] = url
    return feeds

load_dotenv()

class ConfigValidationError(Exception):
    pass

class Config(object):
    LOG_FORMAT = os.getenv("LOG_FORMAT") or '%(asctime)s - %(levelname)s - %(message)s \t - %(name)s (%(filename)s).%(funcName)s(%(lineno)d) '
    LOG_LEVEL = os.getenv("LOG_LEVEL") or 'INFO'
    APPNAME = os.getenv("APPNAME") or 'Truth Social Monitor'
    ENV = os.getenv("ENV") or "DEV"
    REPEAT_DELAY = int(os.getenv("REPEAT_DELAY") or 300)  # 5 minutes default
    REPEAT_MIN_DELAY = int(os.getenv("REPEAT_MIN_DELAY")) if os.getenv("REPEAT_MIN_DELAY") else None
    REPEAT_MAX_DELAY = int(os.getenv("REPEAT_MAX_DELAY")) if os.getenv("REPEAT_MAX_DELAY") else None
    BLOCKED_BACKOFF_MIN = int(os.getenv("BLOCKED_BACKOFF_MIN")) if os.getenv("BLOCKED_BACKOFF_MIN") else None
    BLOCKED_BACKOFF_MAX = int(os.getenv("BLOCKED_BACKOFF_MAX")) if os.getenv("BLOCKED_BACKOFF_MAX") else None
    EMPTY_FETCH_THRESHOLD = int(os.getenv("EMPTY_FETCH_THRESHOLD") or 3)
    EMPTY_FETCH_BACKOFF_MULTIPLIER = float(os.getenv("EMPTY_FETCH_BACKOFF_MULTIPLIER") or 1.5)

    # Discord configuration
    DISCORD_NOTIFY = os.getenv("DISCORD_NOTIFY", 'True').lower() == 'true'
    DISCORD_USERNAME = os.getenv("DISCORD_USERNAME") or "Market Impact Bot"
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    
    # Discord secondary channel for ALL filtered posts (keyword score > 0)
    DISCORD_ALL_POSTS_WEBHOOK = os.getenv("DISCORD_ALL_POSTS_WEBHOOK")
    DISCORD_ALL_POSTS_USERNAME = os.getenv("DISCORD_ALL_POSTS_USERNAME") or "Posted But Not Relevant"
    LLM_ERROR_WEBHOOK_URL = os.getenv("LLM_ERROR_WEBHOOK_URL")
    
    # MongoDB configuration
    MONGO_DBSTRING = os.getenv("MONGO_DBSTRING")
    MONGO_DB = os.getenv("MONGO_DB") or "truthsocial"
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION") or "posts"
    MONGO_ANALYSIS_COLLECTION = os.getenv("MONGO_ANALYSIS_COLLECTION") or "analysis_results"
    MONGO_BLOCK_HISTORY_COLLECTION = os.getenv("MONGO_BLOCK_HISTORY_COLLECTION") or "scraper_block_history"
    ENABLE_FILE_EXPORT = os.getenv("ENABLE_FILE_EXPORT", 'false').lower() == 'true'

    # Truth Social configuration
    TRUTH_USERNAMES = [u.strip() for u in os.getenv("TRUTH_USERNAMES", '').split(',') if u.strip()]
    TRUTH_USERNAME = os.getenv("TRUTH_USERNAME")  # Deprecated: use TRUTH_USERNAMES instead
    TRUTH_INSTANCE = os.getenv("TRUTH_INSTANCE") or "truthsocial.com"
    POST_TYPE = os.getenv("POST_TYPE") or "post"  # Default to "post" if not specified

    # X/Twitter Configuration (via Nitter scraping)
    X_ENABLED = os.getenv("X_ENABLED", 'False').lower() == 'true'
    X_USERNAMES = [u.strip() for u in os.getenv("X_USERNAMES", '').split(',') if u.strip()]
    
    # Request configuration
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT") or 30)
    MAX_RETRIES = int(os.getenv("MAX_RETRIES") or 3)

    # Optional FlareSolverr support for Cloudflare-protected instances
    FLARESOLVERR_ENABLED = os.getenv("FLARESOLVERR_ENABLED", 'false').lower() == 'true'
    FLARESOLVERR_ADDRESS = os.getenv("FLARESOLVERR_ADDRESS") or "localhost"
    FLARESOLVERR_PORT = int(os.getenv("FLARESOLVERR_PORT") or 8191)
    FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL") or f"http://{FLARESOLVERR_ADDRESS}:{FLARESOLVERR_PORT}"
    FLARESOLVERR_TIMEOUT = int(os.getenv("FLARESOLVERR_TIMEOUT") or 60)

    # OpenRouter LLM configuration
    OPENROUTER_ENABLED = os.getenv("OPENROUTER_ENABLED", 'false').lower() == 'true'
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL") or "openai/gpt-oss-20b:free"
    OPENROUTER_URL = os.getenv("OPENROUTER_URL") or "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER")
    OPENROUTER_TITLE = os.getenv("OPENROUTER_TITLE")
    OPENROUTER_TIMEOUT = int(os.getenv("OPENROUTER_TIMEOUT") or 120)
    OPENROUTER_MIN_INTERVAL = float(os.getenv("OPENROUTER_MIN_INTERVAL") or 5.0)

    # Ollama LLM configuration
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or "llama3.2:3b"
    OLLAMA_URL = os.getenv("OLLAMA_URL") or "http://localhost:11434"
    OLLAMA_NUM_THREADS = int(os.getenv("OLLAMA_NUM_THREADS") or 4)  # 0 = auto-detect

    # Quiet hours configuration
    QUIET_HOURS_RAW = os.getenv("QUIET_HOURS", "")
    QUIET_HOURS_WINDOWS = _parse_quiet_hours(QUIET_HOURS_RAW)
    QUIET_HOURS_DEFAULT_LOCATION = (os.getenv("QUIET_HOURS_DEFAULT_LOCATION") or "").strip().upper() or None
    TRUTH_ACCOUNT_LOCATIONS = _parse_account_locations(os.getenv("TRUTH_ACCOUNT_LOCATIONS", ""))
    X_ACCOUNT_LOCATIONS = _parse_account_locations(os.getenv("X_ACCOUNT_LOCATIONS", ""))
    RSS_FEEDS = _parse_feed_definitions(os.getenv("RSS_FEEDS", ""))
    RSS_FEED_LOCATIONS = _parse_account_locations(os.getenv("RSS_FEED_LOCATIONS", ""))

    # Legal disclaimer acceptance (for non-interactive mode)
    ACCEPT_LEGAL_DISCLAIMER = os.getenv("ACCEPT_LEGAL_DISCLAIMER", 'false').lower() == 'true'

    def __init__(self):
        self.validate_config()

    def validate_config(self):
        """Validate required configuration settings"""
        errors = []

        # Either Truth Social or X/Twitter must be enabled
        if not self.TRUTH_USERNAMES and not self.TRUTH_USERNAME and not self.X_ENABLED:
            errors.append("Either TRUTH_USERNAMES (or TRUTH_USERNAME) or X_ENABLED must be configured")
        
        # If X is enabled, require usernames
        if self.X_ENABLED:
            if not self.X_USERNAMES:
                errors.append("X_USERNAMES is required when X_ENABLED is true")

        if self.DISCORD_NOTIFY:
            if not self.DISCORD_WEBHOOK_URL:
                errors.append("DISCORD_WEBHOOK_URL is required when DISCORD_NOTIFY is enabled")

        if self.OPENROUTER_ENABLED and not self.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is required when OPENROUTER_ENABLED is true")

        if not self.MONGO_DBSTRING:
            errors.append("MONGO_DBSTRING is required")

        if errors:
            raise ConfigValidationError("\n".join(errors))

        return True
