import os
import logging
from dotenv import load_dotenv

load_dotenv()

class ConfigValidationError(Exception):
    pass

class Config(object):
    LOG_FORMAT = os.getenv("LOG_FORMAT") or '%(asctime)s - %(levelname)s - %(message)s \t - %(name)s (%(filename)s).%(funcName)s(%(lineno)d) '
    LOG_LEVEL = os.getenv("LOG_LEVEL") or 'INFO'
    APPNAME = os.getenv("APPNAME") or 'Truth Social Monitor'
    ENV = os.getenv("ENV") or "DEV"
    REPEAT_DELAY = int(os.getenv("REPEAT_DELAY") or 300)  # 5 minutes default

    # Discord configuration
    DISCORD_NOTIFY = os.getenv("DISCORD_NOTIFY", 'True').lower() == 'true'
    DISCORD_USERNAME = os.getenv("DISCORD_USERNAME") or "Market Impact Bot"
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    
    # Discord secondary channel for ALL filtered posts (keyword score > 0)
    DISCORD_ALL_POSTS_WEBHOOK = os.getenv("DISCORD_ALL_POSTS_WEBHOOK")
    DISCORD_ALL_POSTS_USERNAME = os.getenv("DISCORD_ALL_POSTS_USERNAME") or "Posted But Not Relevant"
    
    # MongoDB configuration
    MONGO_DBSTRING = os.getenv("MONGO_DBSTRING")
    MONGO_DB = os.getenv("MONGO_DB") or "truthsocial"
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION") or "posts"
    MONGO_ANALYSIS_COLLECTION = os.getenv("MONGO_ANALYSIS_COLLECTION") or "analysis_results"
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

    # Ollama LLM configuration
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or "llama3.2:3b"
    OLLAMA_URL = os.getenv("OLLAMA_URL") or "http://localhost:11434"
    OLLAMA_NUM_THREADS = int(os.getenv("OLLAMA_NUM_THREADS") or 4)  # 0 = auto-detect

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

        if not self.MONGO_DBSTRING:
            errors.append("MONGO_DBSTRING is required")

        if errors:
            raise ConfigValidationError("\n".join(errors))

        return True
