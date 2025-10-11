"""
Output Formatter for Market Analysis Results
Handles formatting of analysis results for different output files
"""
from datetime import datetime, UTC
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats and saves market analysis results"""
    
    def __init__(self, output_dir: str = 'output'):
        """
        Initialize OutputFormatter
        
        Args:
            output_dir: Directory where output files will be saved (default: 'output')
        """
        self.output_dir = output_dir
        
        # Ensure output directory exists
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
    
    def save_to_files(self, output: str, market_analysis: Optional[Dict]) -> None:
        """Save output to appropriate files based on impact level"""
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
