"""Shared enumerations used across the analyzer."""
from enum import Enum


class PostStatus(Enum):
    """Processing states we track in MongoDB."""

    PROCESSED = "processed"


class Platform(Enum):
    """Social media platforms supported by the analyzer."""

    TRUTH_SOCIAL = "truthsocial"
    X = "x"

    @classmethod
    def from_value(cls, value: str) -> "Platform":
        try:
            return cls(value)
        except ValueError:
            return cls.TRUTH_SOCIAL

    @property
    def emoji(self) -> str:
        return "🐦" if self is Platform.X else "🇺🇸"

    def default_post_type(self, fallback: str) -> str:
        return "Tweet" if self is Platform.X else fallback.capitalize()


class MediaType(Enum):
    """Supported media attachment types."""

    IMAGE = "image"
    VIDEO = "video"
    GIF = "gifv"

    @classmethod
    def allowed_values(cls) -> set[str]:
        return {member.value for member in cls}


class ImpactLevel(Enum):
    """Discrete market impact levels with associated alert emoji."""

    LOW = ("🟢 LOW", "ℹ️")
    MEDIUM = ("🟡 MEDIUM", "⚠️")
    HIGH = ("🟠 HIGH", "🚨")
    CRITICAL = ("🔴 CRITICAL", "🚨🚨🚨")

    def __init__(self, label: str, alert_emoji: str) -> None:
        self.label = label
        self.alert_emoji = alert_emoji


__all__ = [
    "PostStatus",
    "Platform",
    "MediaType",
    "ImpactLevel",
]
