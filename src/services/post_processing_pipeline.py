"""Post processing pipeline that orchestrates analysis and notifications."""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Callable

from bs4 import BeautifulSoup

from src.enums import Platform

logger = logging.getLogger(__name__)


class PostProcessingPipeline:
    """Encapsulates the end-to-end processing of fetched posts."""

    def __init__(
        self,
        *,
        config,
        market_analyzer,
        llm_analyzer,
        output_formatter,
        discord_notifier,
        discord_all_posts_notifier,
        llm_threshold: int,
        discord_threshold: int,
        is_processed_fn: Callable[[Any, str], bool],
        mark_processed_fn: Callable[[Any, Dict[str, Any]], None],
    ) -> None:
        self.config = config
        self.market_analyzer = market_analyzer
        self.llm_analyzer = llm_analyzer
        self.output_formatter = output_formatter
        self.discord_notifier = discord_notifier
        self.discord_all_posts_notifier = discord_all_posts_notifier
        self.llm_threshold = llm_threshold
        self.discord_threshold = discord_threshold
        self.is_processed_fn = is_processed_fn
        self.mark_processed_fn = mark_processed_fn

    def process_posts(self, posts: List[Dict[str, Any]], mongo_collection) -> None:
        for post in sorted(posts, key=lambda x: x.get('created_at', '')):
            try:
                self._process_single_post(post, mongo_collection)
            except Exception as exc:
                post_id = post.get('id', 'unknown') if isinstance(post, dict) else 'unknown'
                logger.error(f"Failed to process post {post_id}: {exc}")

    def _process_single_post(self, post: Dict[str, Any], mongo_collection) -> None:
        if not isinstance(post, dict) or 'id' not in post:
            logger.warning(f"Invalid post structure: {post}")
            return

        content = post.get('content') or post.get('text', '')
        soup = BeautifulSoup(content, 'html.parser')
        cleaned_content = soup.get_text().strip()

        if not cleaned_content or len(cleaned_content) < 20:
            logger.debug(
                "Post %s has insufficient text content (%s chars), skipping",
                post['id'],
                len(cleaned_content)
            )
            return

        if self.is_processed_fn(mongo_collection, post['id']):
            logger.debug(f"Post {post['id']} already processed, skipping")
            return

        logger.info(
            "Processing new post %s with %s characters of text",
            post['id'],
            len(cleaned_content)
        )

        market_analysis = self.market_analyzer.analyze(cleaned_content)
        if market_analysis:
            logger.info(f"Market analysis: {market_analysis['summary']}")

        llm_analysis = None
        if market_analysis and market_analysis['impact_score'] >= self.llm_threshold:
            logger.info(
                "🤖 Running LLM analysis (keyword score: %s >= %s)...",
                market_analysis['impact_score'],
                self.llm_threshold
            )
            llm_analysis = self.llm_analyzer.analyze(cleaned_content, market_analysis['impact_score'])

            if llm_analysis:
                logger.info(
                    "✅ LLM analysis complete - Score: %s, Urgency: %s",
                    llm_analysis.get('score'),
                    llm_analysis.get('urgency')
                )
                self._apply_quality_check(cleaned_content, llm_analysis, market_analysis)
            else:
                logger.warning(
                    "⚠️  LLM analysis failed for post %s - will NOT send Discord alert",
                    post['id']
                )

        created_at = self._normalize_created_at(post.get('created_at'))
        account = post.get('account', {})
        username = account.get('username') or self.config.TRUTH_USERNAME or 'unknown'
        display_name = account.get('display_name', username)
        platform = Platform.from_value(post.get('platform', Platform.TRUTH_SOCIAL.value))
        platform_emoji = platform.emoji
        post_type = platform.default_post_type(self.config.POST_TYPE)

        message = (
            f"**{platform_emoji} New {post_type} from {display_name} (@{username})**\n"
            f"{cleaned_content}\n"
            f"*Posted at: {created_at.strftime('%B %d, %Y at %I:%M %p %Z')}*"
        )

        media_attachments = post.get('media_attachments', []) or []

        if platform is Platform.X:
            post_url = post.get('url', f"https://x.com/{username}")
        else:
            post_url = f"https://truthsocial.com/@{username}/posts/{post['id']}"

        self._persist_analysis(
            post=post,
            platform=platform,
            username=username,
            display_name=display_name,
            message=message,
            cleaned_content=cleaned_content,
            raw_content=post.get('content') or post.get('text', ''),
            market_analysis=market_analysis,
            llm_analysis=llm_analysis,
            media_attachments=media_attachments,
            post_url=post_url,
            created_at=created_at,
        )

        if (
            self.discord_all_posts_notifier
            and market_analysis
            and market_analysis['impact_score'] > 0
        ):
            logger.info(
                "📨 Sending to 'Posted But Not Relevant' channel (keyword score: %s)",
                market_analysis['impact_score']
            )
            self.discord_all_posts_notifier.send_market_alert(
                post_text=cleaned_content,
                keyword_analysis=market_analysis,
                llm_analysis=None,
                post_url=post_url,
                author=f"{platform_emoji} @{username}",
                post_created_at=post.get('created_at')
            )

        if (
            self.discord_notifier
            and market_analysis
            and market_analysis['impact_score'] >= self.discord_threshold
        ):
            if llm_analysis:
                logger.info(
                    "🚨 Sending HIGH IMPACT alert (score: %s)",
                    market_analysis['impact_score']
                )
                self.discord_notifier.send_market_alert(
                    post_text=cleaned_content,
                    keyword_analysis=market_analysis,
                    llm_analysis=llm_analysis,
                    post_url=post_url,
                    author=f"{platform_emoji} @{username}",
                    post_created_at=post.get('created_at')
                )
            else:
                logger.warning(
                    "⚠️  Skipping Discord alert for high-impact post due to failed LLM analysis (keyword score: %s)",
                    market_analysis['impact_score']
                )

        self.mark_processed_fn(mongo_collection, post)

    def _apply_quality_check(self, cleaned_content: str, llm_analysis: Dict[str, Any], market_analysis: Dict[str, Any]) -> None:
        qc_result = self.llm_analyzer.quality_check_analysis(cleaned_content, llm_analysis)

        if qc_result and not qc_result.get('approved', False):
            suggested_fixes = qc_result.get('suggested_fixes', {})
            if suggested_fixes.get('reasoning'):
                logger.info("📝 Applying improved reasoning from quality check")
                llm_analysis['reasoning'] = suggested_fixes['reasoning']
            if suggested_fixes.get('urgency'):
                logger.info(
                    "📝 Correcting urgency: %s → %s",
                    llm_analysis.get('urgency'),
                    suggested_fixes['urgency']
                )
                llm_analysis['urgency'] = suggested_fixes['urgency']
            if suggested_fixes.get('score') is not None:
                logger.info(
                    "📝 Adjusting score: %s → %s",
                    llm_analysis.get('score'),
                    suggested_fixes['score']
                )
                llm_analysis['score'] = suggested_fixes['score']

        self.llm_analyzer.save_training_data(
            cleaned_content,
            market_analysis['impact_score'],
            llm_analysis,
            quality_check=qc_result
        )

    def _persist_analysis(
        self,
        *,
        post: Dict[str, Any],
        platform: Platform,
        username: str,
        display_name: str,
        message: str,
        cleaned_content: str,
        raw_content: str,
        market_analysis: Optional[Dict[str, Any]],
        llm_analysis: Optional[Dict[str, Any]],
        media_attachments: List[Dict[str, Any]],
        post_url: str,
        created_at: datetime,
    ) -> None:
        if not self.output_formatter:
            logger.debug("No output formatter configured; skipping persistence for %s", post.get('id'))
            return

        try:
            self.output_formatter.persist_analysis(
                post_id=post['id'],
                platform=platform,
                username=username,
                display_name=display_name,
                message=message,
                raw_content=raw_content,
                cleaned_content=cleaned_content,
                market_analysis=market_analysis,
                llm_analysis=llm_analysis,
                media_attachments=media_attachments,
                post_url=post_url,
                post_created_at=created_at,
                processed_at=datetime.now(UTC),
                source_post=post,
            )
        except Exception as exc:
            logger.error("Failed to persist analysis for %s: %s", post.get('id'), exc)

    @staticmethod
    def _normalize_created_at(created_at_str: Optional[str]) -> datetime:
        if not created_at_str:
            return datetime.now(UTC)

        try:
            return datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        except ValueError:
            logger.debug("Failed to parse created_at '%s', using current time", created_at_str)
            return datetime.now(UTC)
