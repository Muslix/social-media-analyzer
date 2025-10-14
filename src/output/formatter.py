"""
Output Formatter for Market Analysis Results
Handles formatting of analysis results for different output files
"""
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats and persists market analysis results."""
    
    def __init__(
        self,
        analysis_collection=None,
        output_dir: str = 'output',
        enable_file_export: bool = False
    ):
        """
        Initialize OutputFormatter
        
        Args:
            analysis_collection: MongoDB collection used for structured persistence
            output_dir: Directory where export files will be saved
            enable_file_export: Whether to keep writing legacy text exports
        """
        self.analysis_collection = analysis_collection
        self.enable_file_export = enable_file_export
        self.output_dir = output_dir
        
        self.output_files = {}
        if self.enable_file_export:
            os.makedirs(output_dir, exist_ok=True)
            self.output_files = {
                'all': os.path.join(output_dir, 'truth_social_posts.txt'),
                'high_impact': os.path.join(output_dir, 'market_impact_posts.txt'),
                'critical': os.path.join(output_dir, 'CRITICAL_ALERTS.txt')
            }
    
    def format_analysis_output(self, message: str, market_analysis: Optional[Dict], 
                               media_attachments: Optional[List] = None) -> str:
        """Format a complete output with market analysis"""
        separator = "\n" + "="*80 + "\n"
        
        output = separator
        output += f"Timestamp: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        # Add market analysis if present
        if market_analysis:
            output += self._format_market_analysis(market_analysis)
        
        output += separator
        output += message + "\n"
        
        # Add media attachments
        if media_attachments:
            output += "\n--- Media Attachments ---\n"
            for media in media_attachments:
                if media.get('type') in ['image', 'video', 'gifv']:
                    url = media.get('url') or media.get('preview_url')
                    if url:
                        output += f"[{media.get('type').upper()}] {url}\n"
        
        output += separator + "\n"
        
        return output
    
    def _format_market_analysis(self, analysis: Dict) -> str:
        """Format market analysis section"""
        output = f"\n{analysis['alert_emoji']} MARKET ANALYSIS: {analysis['summary']}\n"
        output += f"Impact Level: {analysis['impact_level']}\n"
        output += f"Impact Score: {analysis['impact_score']}\n"
        
        details = analysis.get('details', {})
        
        # Critical triggers
        if details.get('critical_triggers'):
            output += f"\n🔴 CRITICAL TRIGGERS:\n"
            for trigger in details['critical_triggers']:
                output += f"  ⚠️  {trigger}\n"
        
        # Keywords
        if details.get('keywords'):
            output += f"\n📌 Detected Keywords:\n"
            for category, kw_list in details['keywords'].items():
                kw_str = ', '.join([f"{kw} (×{weight})" for kw, weight in kw_list])
                output += f"  - {category.upper()}: {kw_str}\n"
        
        # Percentages
        if details.get('percentages') and details['percentages'].get('values'):
            pct_data = details['percentages']
            output += f"\n📊 PERCENTAGES DETECTED:\n"
            for impact_str in pct_data.get('impact', []):
                output += f"  - {impact_str}\n"
        
        # Monetary amounts
        if details.get('monetary') and details['monetary'].get('amounts'):
            output += f"\n💰 MONETARY AMOUNTS:\n"
            for amount_str in details['monetary']['amounts']:
                output += f"  - {amount_str}\n"
        
        # Dates
        if details.get('dates') and details['dates'].get('dates_found'):
            date_data = details['dates']
            output += f"\n📅 DATES/TIMELINES:\n"
            for date in date_data['dates_found']:
                output += f"  - {date}\n"
            if date_data.get('immediate_action'):
                output += f"  ⚡ IMMEDIATE ACTION INDICATED\n"
        
        # Entities
        if details.get('entities'):
            entities = details['entities']
            if entities.get('geopolitical'):
                output += f"\n🌍 Geopolitical Entities: {', '.join(entities['geopolitical'])}\n"
            if entities.get('economic'):
                output += f"\n🏛️  Economic Institutions: {', '.join(entities['economic'])}\n"
        
        # Actions
        if details.get('actions') and details['actions'].get('actions'):
            output += f"\n⚡ Action Verbs: "
            actions_str = ', '.join([f"{verb} (×{weight})" for verb, weight in details['actions']['actions']])
            output += actions_str + "\n"
        
        # Sentiment
        if details.get('sentiment') and details['sentiment'].get('is_aggressive'):
            sentiment = details['sentiment']
            output += f"\n🔥 Aggressive/Hostile Language Detected ({sentiment['aggressive_terms_count']} terms)\n"
            output += f"   Sentiment Multiplier: {sentiment['multiplier']:.1f}x\n"
        
        return output
    
    def _normalize_media(self, media_attachments: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Normalize media attachments to a compact schema."""
        normalized: List[Dict[str, Any]] = []
        if not media_attachments:
            return normalized

        for media in media_attachments:
            if not isinstance(media, dict):
                continue
            normalized.append({
                "type": media.get("type"),
                "url": media.get("url") or media.get("remote_url") or media.get("preview_url"),
                "preview_url": media.get("preview_url"),
                "description": media.get("description") or media.get("alt"),
            })
        return normalized

    def persist_analysis(
        self,
        *,
        post_id: str,
        platform,
        username: str,
        display_name: str,
        message: str,
        raw_content: str,
        cleaned_content: str,
        market_analysis: Optional[Dict[str, Any]],
        llm_analysis: Optional[Dict[str, Any]],
        media_attachments: Optional[List[Dict[str, Any]]],
        post_url: str,
        post_created_at,
        processed_at=None,
        source_post: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist analysis results to structured storage (and optional exports)."""
        processed_at = processed_at or datetime.now(UTC)
        platform_value = getattr(platform, "value", str(platform))
        platform_emoji = getattr(platform, "emoji", None)

        impact_level = market_analysis.get('impact_level') if market_analysis else None
        impact_score = market_analysis.get('impact_score') if market_analysis else None
        impact_level_upper = impact_level.upper() if isinstance(impact_level, str) else ""
        is_critical = bool(
            impact_level and (
                'CRITICAL' in impact_level_upper
                or '🔴' in impact_level
            )
        )
        is_high = bool(
            impact_level and (
                'HIGH' in impact_level_upper
                or '🟠' in impact_level
            )
        ) or is_critical
        impact_bucket = 'critical' if is_critical else ('high' if is_high else 'informational')

        record = {
            "_id": post_id,
            "post": {
                "id": post_id,
                "platform": platform_value,
                "platform_emoji": platform_emoji,
                "username": username,
                "display_name": display_name,
                "url": post_url,
            },
            "content": {
                "raw": raw_content,
                "cleaned": cleaned_content,
                "presentation": message,
            },
            "analysis": {
                "market": market_analysis,
                "llm": llm_analysis,
            },
            "impact": {
                "level": impact_level,
                "score": impact_score,
                "bucket": impact_bucket,
                "is_high": is_high,
                "is_critical": is_critical,
            },
            "media_attachments": self._normalize_media(media_attachments),
            "timestamps": {
                "post_created_at": post_created_at,
                "processed_at": processed_at,
            },
            "labels": {
                "platform": platform_value,
                "author": username,
                "impact_bucket": impact_bucket,
            },
            "source_post": source_post or {},
        }

        if self.analysis_collection is None:
            logger.warning(
                "No analysis collection configured; skipping structured persistence for %s",
                post_id
            )
        else:
            try:
                self.analysis_collection.update_one(
                    {"_id": post_id},
                    {"$set": record},
                    upsert=True
                )
                logger.debug("Persisted structured analysis for %s", post_id)
            except Exception as exc:
                logger.error("Failed to persist analysis for %s: %s", post_id, exc)
                raise

        if self.enable_file_export:
            export_payload = self.format_analysis_output(message, market_analysis, media_attachments)
            self._export_to_files(export_payload, market_analysis)

    def _export_to_files(self, output: str, market_analysis: Optional[Dict]) -> None:
        """Export output to legacy text files when enabled."""
        if not self.enable_file_export or not self.output_files:
            return

        # Always save to main file
        self._append_to_file(self.output_files['all'], output)
        logger.info(f"Saved to {self.output_files['all']}")
        
        if not market_analysis:
            return
        
        impact_level = market_analysis['impact_level']
        
        # Save HIGH and CRITICAL to market impact file
        if '🔴 CRITICAL' in impact_level or '🟠 HIGH' in impact_level:
            self._append_to_file(self.output_files['high_impact'], output)
            logger.info(f"⚠️  Also saved to {self.output_files['high_impact']} due to {impact_level}")
        
        # Save CRITICAL to special alerts file
        if '🔴 CRITICAL' in impact_level:
            self._append_to_file(self.output_files['critical'], output)
            logger.warning(f"🚨 CRITICAL ALERT saved to {self.output_files['critical']}")
    
    def _append_to_file(self, filename: str, content: str) -> None:
        """Append content to file"""
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error writing to {filename}: {e}")
            raise
