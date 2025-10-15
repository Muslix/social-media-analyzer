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
        market_impact_tracker=None,
        failure_notifier=None,
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
        self.market_impact_tracker = market_impact_tracker
        self.failure_notifier = failure_notifier

    def process_posts(self, posts: List[Dict[str, Any]], mongo_collection) -> None:
        for post in sorted(posts, key=lambda x: x.get('created_at', '')):
            try:
                self._process_single_post(post, mongo_collection)
            except Exception as exc:
                post_id = post.get('id', 'unknown') if isinstance(post, dict) else 'unknown'
                logger.error(f"Failed to process post {post_id}: {exc}")
                self._notify_failure(
                    title="Post processing fehlgeschlagen",
                    description=f"Fehler beim Verarbeiten von Post {post_id}",
                    details={
                        "post_id": post_id,
                        "error": str(exc),
                        "platform": post.get('platform') if isinstance(post, dict) else None,
                        "created_at": post.get('created_at') if isinstance(post, dict) else None,
                    },
                )

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
        elif platform is Platform.RSS:
            post_url = post.get('url') or post.get('canonical_url') or post.get('link')
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

        if self.market_impact_tracker and llm_analysis:
            post_metadata = {
                "platform": platform.value,
                "platform_emoji": platform.emoji,
                "post_url": post_url,
                "username": username,
                "display_name": display_name,
                "post_created_at": created_at.isoformat(),
            }
            self.market_impact_tracker.handle_analysis_event(
                event_id=post['id'],
                llm_analysis=llm_analysis,
                market_analysis=market_analysis,
                post_metadata=post_metadata,
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

    def _notify_failure(self, *, title: str, description: str, details: Optional[Dict[str, Any]] = None) -> None:
        if not self.failure_notifier:
            return
        try:
            self.failure_notifier.send_failure_alert(title, description, details=details)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to send failure notification: %s", exc)

    def _apply_quality_check(self, cleaned_content: str, llm_analysis: Dict[str, Any], market_analysis: Dict[str, Any]) -> None:
        original_reasoning = llm_analysis.get('reasoning')
        original_urgency = llm_analysis.get('urgency')
        original_score = llm_analysis.get('score')

        qc_result = self.llm_analyzer.quality_check_analysis(cleaned_content, llm_analysis)

        if qc_result:
            review_meta = llm_analysis.setdefault('quality_review', {})
            review_meta.update({
                "approved": bool(qc_result.get('approved', False)),
                "issues_found": qc_result.get('issues_found', []),
                "quality_score": qc_result.get('quality_score'),
            })

            if not qc_result.get('approved', False):
                suggested_fixes = qc_result.get('suggested_fixes', {}) or {}
                review_meta['suggested_fixes'] = suggested_fixes

                reasoning_fix = (suggested_fixes.get('reasoning') or "").strip()
                if reasoning_fix:
                    if self._looks_like_final_reasoning(reasoning_fix):
                        logger.info("📝 Applying improved reasoning from quality check")
                        llm_analysis['reasoning'] = reasoning_fix
                    else:
                        logger.info("ℹ️  Reasoning suggestion looks like reviewer guidance; keeping original reasoning")
                        review_meta['suggested_reasoning_note'] = reasoning_fix
                        if original_reasoning is not None:
                            llm_analysis['reasoning'] = original_reasoning

                urgency_fix = (suggested_fixes.get('urgency') or "").strip()
                normalized_urgency = self._normalize_urgency(urgency_fix)
                if normalized_urgency:
                    logger.info(
                        "📝 Correcting urgency: %s → %s",
                        llm_analysis.get('urgency'),
                        normalized_urgency
                    )
                    llm_analysis['urgency'] = normalized_urgency
                elif urgency_fix:
                    logger.info("ℹ️  Urgency suggestion invalid (%s); keeping original urgency", urgency_fix)
                    if original_urgency is not None:
                        llm_analysis['urgency'] = original_urgency
                    review_meta['suggested_urgency_note'] = urgency_fix

                score_fix = suggested_fixes.get('score')
                if isinstance(score_fix, (int, float)) and 0 <= score_fix <= 100:
                    logger.info(
                        "📝 Adjusting score: %s → %s",
                        llm_analysis.get('score'),
                        score_fix
                    )
                    llm_analysis['score'] = int(score_fix)
                elif score_fix is not None:
                    logger.info("ℹ️  Score suggestion out of bounds (%s); keeping original score", score_fix)
                    if original_score is not None:
                        llm_analysis['score'] = original_score
                    review_meta['suggested_score_note'] = score_fix

        self.llm_analyzer.save_training_data(
            cleaned_content,
            market_analysis['impact_score'],
            llm_analysis,
            quality_check=qc_result
        )

    @staticmethod
    def _looks_like_final_reasoning(reasoning: str) -> bool:
        """Heuristic to decide if the suggested reasoning is ready for end users."""
        if not reasoning:
            return False

        lowered = reasoning.lower()
        instruction_starts = (
            "remove ", "keep ", "rewrite", "reframe", "ensure ", "avoid ",
            "do not", "don't", "make sure", "change ", "adjust ", "should ",
            "break out", "mention", "focus on"
        )
        if lowered.startswith(instruction_starts):
            return False

        # Consider it guidance if it contains multiple imperative cues
        guidance_keywords = ["remove ", " keep ", " rewrite", " reframe", " should ", " must ", " need to "]
        if any(keyword in lowered for keyword in guidance_keywords):
            # Allow short, direct rewrites such as "Dispute the claim." which look like instructions.
            if len(reasoning.split()) <= 6:
                return False

        # Final reasoning should look like prose with at least one sentence terminator.
        if '.' not in reasoning and '!' not in reasoning and '?' not in reasoning:
            return False

        return True

    @staticmethod
    def _normalize_urgency(raw_urgency: str) -> Optional[str]:
        if not raw_urgency:
            return None

        lowered = raw_urgency.strip().lower()
        valid = {"immediate", "hours", "days", "weeks"}
        if lowered in valid:
            return lowered

        aliases = {
            "hour": "hours",
            "hrs": "hours",
            "day": "days",
            "week": "weeks",
            "immediately": "immediate",
        }
        return aliases.get(lowered)

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
