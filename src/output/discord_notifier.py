"""
Discord Webhook Notifier for Market Impact Alerts
Sends beautifully formatted embeds to Discord
"""
import logging
import requests
from typing import Dict, Optional, List
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """
    Sends formatted market impact alerts to Discord via webhook
    Uses Discord embeds for rich, visually appealing notifications
    """
    
    def __init__(self, webhook_url: str, username: str = "Market Impact Bot"):
        """
        Initialize Discord Notifier
        
        Args:
            webhook_url: Discord webhook URL
            username: Bot username to display
        """
        self.webhook_url = webhook_url
        self.username = username
        
        # Color codes for different impact levels
        self.impact_colors = {
            '🔴 CRITICAL': 0xFF0000,  # Red
            '🟠 HIGH': 0xFF8C00,      # Dark Orange
            '🟡 MEDIUM': 0xFFD700,    # Gold
            '🟢 LOW': 0x00FF00,       # Green
        }
    
    def send_market_alert(self, 
                         post_text: str,
                         keyword_analysis: Optional[Dict] = None,
                         llm_analysis: Optional[Dict] = None,
                         post_url: Optional[str] = None,
                         author: str = "@realDonaldTrump",
                         post_created_at: Optional[str] = None) -> bool:
        """
        Send a market impact alert to Discord
        
        Args:
            post_text: The original post text
            keyword_analysis: Keyword-based analysis result
            llm_analysis: LLM analysis result (optional)
            post_url: URL to the original post
            author: Post author
            post_created_at: ISO timestamp when post was created
            
        Returns:
            True if sent successfully
        """
        try:
            # Determine primary impact level
            if keyword_analysis:
                impact_level = keyword_analysis.get('impact_level', '🟢 LOW')
                impact_score = keyword_analysis.get('impact_score', 0)
            else:
                impact_level = '🟢 LOW'
                impact_score = 0
            
            # Build the embed
            embed = self._build_embed(
                post_text=post_text,
                keyword_analysis=keyword_analysis,
                llm_analysis=llm_analysis,
                impact_level=impact_level,
                impact_score=impact_score,
                author=author,
                post_url=post_url,
                post_created_at=post_created_at
            )
            
            # Send to Discord
            payload = {
                "username": self.username,
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ Discord alert sent: {impact_level} (Score: {impact_score})")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send Discord alert: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending Discord alert: {e}")
            return False
    
    def _build_embed(self, 
                    post_text: str,
                    keyword_analysis: Optional[Dict],
                    llm_analysis: Optional[Dict],
                    impact_level: str,
                    impact_score: int,
                    author: str,
                    post_url: Optional[str],
                    post_created_at: Optional[str] = None) -> Dict:
        """Build a compact Discord embed with key information"""
        
        # Color based on impact level
        color = self.impact_colors.get(impact_level, 0x808080)
        
        # Title with emoji
        alert_emoji = "🚨" if "CRITICAL" in impact_level else "⚠️"
        title = f"{alert_emoji} {impact_level}: Score {impact_score}"
        
        # Longer description: Show more context (600 chars)
        description = post_text[:600] + "..." if len(post_text) > 600 else post_text
        
        # Format post timestamp
        if post_created_at:
            try:
                from zoneinfo import ZoneInfo
                post_time = datetime.fromisoformat(post_created_at.replace('Z', '+00:00'))
                
                # Convert to German time (Europe/Berlin automatically handles CET/CEST)
                german_time = post_time.astimezone(ZoneInfo('Europe/Berlin'))
                
                # Determine timezone name (CET or CEST)
                tz_name = german_time.strftime('%Z')  # Will be "CET" or "CEST"
                
                time_str = german_time.strftime(f'%B %d, %Y at %H:%M {tz_name}')
            except Exception as e:
                # Fallback to UTC
                try:
                    post_time = datetime.fromisoformat(post_created_at.replace('Z', '+00:00'))
                    time_str = post_time.strftime('%B %d, %Y at %H:%M UTC')
                except:
                    time_str = datetime.now(UTC).strftime('%B %d, %Y at %H:%M UTC')
        else:
            time_str = datetime.now(UTC).strftime('%B %d, %Y at %H:%M UTC')
        
        # Fields - only the most important
        fields = []
        
        # LLM Analysis (PRIORITY - most important)
        if llm_analysis and not llm_analysis.get('parse_error'):
            llm_score = llm_analysis.get('score', 0)
            reasoning = llm_analysis.get('reasoning', '')
            
            # Compact AI analysis
            fields.append({
                "name": f"🤖 AI Analysis: {llm_score}/100",
                "value": reasoning[:500] + ("..." if len(reasoning) > 500 else ""),
                "inline": False
            })
            
            # Markets + Urgency with Direction
            markets = llm_analysis.get('affected_markets', [])
            urgency = llm_analysis.get('urgency', 'unknown')
            market_direction = llm_analysis.get('market_direction', {})
            
            urgency_map = {'immediate': '🔴', 'hours': '🟠', 'days': '🟡', 'weeks': '🟢'}
            
            # Build readable market text with labels and directions
            market_lines = []
            market_labels = {
                'stocks': 'Stocks', 
                'crypto': 'Crypto', 
                'forex': 'USD', 
                'commodities': 'Commodities'
            }
            
            for m in markets:
                label = market_labels.get(m, m.title())
                direction = market_direction.get(m, 'neutral')
                
                # Direction emoji and text
                if m == 'forex':
                    direction_text = {
                        'usd_up': '📈 Stronger',
                        'usd_down': '📉 Weaker',
                        'neutral': '➖ Neutral'
                    }.get(direction, '➖ Neutral')
                else:
                    direction_text = {
                        'bullish': '📈 Bullish',
                        'bearish': '📉 Bearish',
                        'up': '📈 Up',
                        'down': '📉 Down',
                        'neutral': '➖ Neutral'
                    }.get(direction, '➖ Neutral')
                
                market_lines.append(f"**{label}:** {direction_text}")
            
            market_text = "\n".join(market_lines)
            urgency_emoji = urgency_map.get(urgency, '⏰')
            
            fields.append({
                "name": f"💹 Markets & Direction • {urgency_emoji} **{urgency.upper()}**",
                "value": market_text,
                "inline": False
            })
            
            # Top 3 Key Events
            events = llm_analysis.get('key_events', [])
            if events:
                events_text = "\n".join([f"• {e}" for e in events[:3]])
                fields.append({
                    "name": "📌 Key Events",
                    "value": events_text[:500],
                    "inline": False
                })
        
        # Critical Keywords (only critical triggers)
        if keyword_analysis:
            details = keyword_analysis.get('details', {})
            
            if 'critical_triggers' in details and details['critical_triggers']:
                triggers = ", ".join(details['critical_triggers'][:4])
                fields.append({
                    "name": "🔴 Critical Keywords",
                    "value": triggers[:300],
                    "inline": False
                })
            
            # Important dates
            if 'dates' in details and details['dates'].get('dates_found'):
                dates = details['dates']['dates_found'][:2]
                if dates:
                    fields.append({
                        "name": "📅 Important Dates",
                        "value": " • ".join(dates),
                        "inline": False
                    })
        
        # Build compact embed
        embed = {
            "title": title,
            "description": f"**{author}** • {time_str}\n\n{description}",
            "color": color,
            "fields": fields,
        }
        
        # Add timestamp and footer with German time
        if post_created_at:
            try:
                from zoneinfo import ZoneInfo
                post_time = datetime.fromisoformat(post_created_at.replace('Z', '+00:00'))
                german_time = post_time.astimezone(ZoneInfo('Europe/Berlin'))
                
                # Use German time for embed timestamp
                embed["timestamp"] = german_time.isoformat()
                
                # Footer with German time
                tz_name = german_time.strftime('%Z')  # CET or CEST
                footer_time = german_time.strftime(f'%d.%m.%Y um %H:%M Uhr {tz_name}')
                
                if post_url:
                    embed["footer"] = {"text": f"🔗 Zum Original • {footer_time}"}
                else:
                    embed["footer"] = {"text": footer_time}
            except Exception as e:
                # Fallback to UTC
                embed["timestamp"] = datetime.now(UTC).isoformat()
                if post_url:
                    embed["footer"] = {"text": "🔗 Click title to view original post"}
        else:
            embed["timestamp"] = datetime.now(UTC).isoformat()
            if post_url:
                embed["footer"] = {"text": "🔗 Click title to view original post"}
        
        # Add URL if available
        if post_url:
            embed["url"] = post_url
        
        return embed
    
    def send_test_message(self) -> bool:
        """Send a test message to verify webhook"""
        try:
            payload = {
                "username": self.username,
                "embeds": [{
                    "title": "✅ Discord Integration Active",
                    "description": "Market Impact Alert system is now connected to Discord!",
                    "color": 0x00FF00,
                    "fields": [
                        {
                            "name": "Status",
                            "value": "Webhook configured successfully",
                            "inline": True
                        },
                        {
                            "name": "Features",
                            "value": "• Keyword Analysis\n• AI Analysis (Qwen2.5)\n• Training Data Collection",
                            "inline": False
                        }
                    ],
                    "timestamp": datetime.now(UTC).isoformat(),
                    "footer": {
                        "text": "Truthy Market Analyzer"
                    }
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Test message sent to Discord")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send test message: {e}")
            return False


if __name__ == "__main__":
    # Test the Discord notifier
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if webhook_url:
        notifier = DiscordNotifier(webhook_url)
        
        print("Sending test message...")
        if notifier.send_test_message():
            print("✅ Test message sent!")
        else:
            print("❌ Failed to send test message")
    else:
        print("❌ DISCORD_WEBHOOK_URL not found in .env")
