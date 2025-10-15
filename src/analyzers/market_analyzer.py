"""
Advanced Market Impact Analyzer
Analyzes social media posts for potential market impact using multiple techniques
"""
import math
import re
from typing import Any, Dict, List, Optional, Tuple

# Import comprehensive keyword database
from src.data.keywords import (
    get_all_weighted_keywords,
    CRITICAL_COMBINATIONS,
    AGGRESSIVE_TERMS,
    ECONOMIC_ENTITIES,
    GEOPOLITICAL_ENTITIES,
    ACTION_VERBS
)

from src.enums import ImpactLevel


class MarketImpactAnalyzer:
    """Intelligent market impact analysis with multiple detection strategies"""
    
    def __init__(self):
        # Load comprehensive keyword database from keywords.py
        self.weighted_keywords = get_all_weighted_keywords()
        
        # Critical keyword combinations that indicate major events
        self.critical_combinations = CRITICAL_COMBINATIONS
        
        # Aggressive/urgent sentiment indicators
        self.aggressive_terms = AGGRESSIVE_TERMS
        
        # Economic institutions and regulatory bodies
        self.economic_entities = ECONOMIC_ENTITIES
        
        # Geopolitical entities (countries, regions, alliances)
        self.geopolitical_entities = GEOPOLITICAL_ENTITIES
        
        # Action verbs indicating policy changes
        self.action_verbs = ACTION_VERBS
    
    def analyze(self, text: str) -> Optional[Dict]:
        """
        Comprehensive market impact analysis
        Returns dict with impact level, score, and detailed breakdown
        """
        if not text:
            return None
        
        text_lower = text.lower()
        total_score = 0
        analysis_details = {}
        
        # 1. Keyword-based scoring
        keyword_score, found_keywords, keyword_meta = self._analyze_keywords(text_lower)
        total_score += keyword_score
        analysis_details['keywords'] = found_keywords
        analysis_details['keyword_meta'] = keyword_meta
        
        # 2. Percentage and numeric pattern analysis
        percentage_score, percentage_data = self._analyze_percentages(text)
        total_score += percentage_score
        analysis_details['percentages'] = percentage_data
        
        # 3. Date and timeline analysis
        date_score, date_data = self._analyze_dates(text_lower)
        total_score += date_score
        analysis_details['dates'] = date_data
        
        # 4. Monetary values analysis
        money_score, money_data = self._analyze_monetary_values(text)
        total_score += money_score
        analysis_details['monetary'] = money_data
        
        # 5. Critical combinations check
        critical_triggers = self._check_critical_combinations(text_lower)
        if critical_triggers:
            total_score += 20 * len(critical_triggers)
            analysis_details['critical_triggers'] = critical_triggers
        
        # 6. Sentiment and urgency analysis
        sentiment_score, sentiment_data = self._analyze_sentiment(text_lower)
        total_score = int(total_score * sentiment_data['multiplier'])
        analysis_details['sentiment'] = sentiment_data
        
        # 7. Entity recognition (countries, institutions)
        entity_score, entities = self._recognize_entities(text_lower)
        total_score += entity_score
        analysis_details['entities'] = entities
        
        # 8. Action verb detection (announces, implements, etc.)
        action_score, actions = self._detect_action_verbs(text_lower)
        total_score += action_score
        analysis_details['actions'] = actions
        
        # Skip if no market relevance detected
        if total_score == 0:
            return None
        
        # Determine impact level
        impact_level = self._calculate_impact_level(total_score, critical_triggers)

        return {
            'impact_level': impact_level.label,
            'impact_score': total_score,
            'alert_emoji': impact_level.alert_emoji,
            'details': analysis_details,
            'summary': f"{impact_level.alert_emoji} {impact_level.label} - Score: {total_score}"
        }
    
    def _analyze_keywords(self, text: str) -> Tuple[int, Dict[str, List[Tuple[str, int]]], Dict[str, Any]]:
        """Analyze weighted keywords with whole-word matching and length-aware normalization."""
        raw_score = 0
        found: Dict[str, List[Tuple[str, int]]] = {}
        unique_keywords_matched = 0
        keyword_occurrences = 0
        
        for category, keywords in self.weighted_keywords.items():
            for keyword, weight in keywords.items():
                # Use word boundaries to match whole words only
                # \b ensures 'war' matches in 'trade war' but NOT in 'software'
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if category not in found:
                        found[category] = []
                    found[category].append((keyword, weight))
                    raw_score += weight
                    unique_keywords_matched += 1
                    keyword_occurrences += len(matches)

        # Normalize score for extremely long texts so keyword density matters more than raw length.
        word_count = max(len(re.findall(r'\w+', text)), 1)
        baseline_words = 250  # No penalty up to this length
        min_length_factor = 0.35  # Prevent over-penalizing even very long posts

        if word_count <= baseline_words or raw_score == 0:
            length_factor = 1.0
        else:
            length_factor = math.sqrt(baseline_words / word_count)
            length_factor = max(min_length_factor, min(length_factor, 1.0))

        # Additional density-based dampening: plenty of keywords across very few words keeps the score high,
        # while sparse keywords across thousands of words get scaled down further.
        keywords_per_100_words = (
            (keyword_occurrences * 100.0) / word_count if keyword_occurrences else 0.0
        )
        baseline_density = 6.0  # Expect ~6 impactful matches per 100 words to keep full weight
        if keyword_occurrences == 0:
            density_factor = 1.0
        else:
            density_factor = min(1.0, keywords_per_100_words / baseline_density)

        # Combine factors; allow the combined factor to drop lower than the standalone length floor,
        # but never let it reach zero if we actually matched keywords.
        combined_factor = max(0.2, length_factor * density_factor) if raw_score > 0 else 0

        adjusted_score = int(round(raw_score * combined_factor))

        meta = {
            "raw_score": raw_score,
            "adjusted_score": adjusted_score,
            "word_count": word_count,
            "baseline_words": baseline_words,
            "length_factor": length_factor,
            "density_factor": density_factor,
            "combined_factor": combined_factor,
            "unique_keywords_matched": unique_keywords_matched,
            "keyword_occurrences": keyword_occurrences,
            "keywords_per_100_words": keywords_per_100_words,
            "baseline_density": baseline_density,
        }
        
        return adjusted_score, found, meta
    
    def _analyze_percentages(self, text: str) -> Tuple[int, Dict]:
        """
        Smart percentage analysis - any significant percentage gets scored
        High percentages (>50%) get extra weight
        """
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
        
        if not percentages:
            return 0, {}
        
        score = 0
        data = {
            'values': [],
            'impact': []
        }
        
        for pct_str in percentages:
            pct = float(pct_str)
            data['values'].append(pct)
            
            # Score based on magnitude
            if pct >= 100:
                impact_score = 15  # 100%+ is HUGE
                data['impact'].append(f"{pct}% - EXTREME")
                score += impact_score
            elif pct >= 75:
                impact_score = 12
                data['impact'].append(f"{pct}% - VERY HIGH")
                score += impact_score
            elif pct >= 50:
                impact_score = 10
                data['impact'].append(f"{pct}% - HIGH")
                score += impact_score
            elif pct >= 25:
                impact_score = 7
                data['impact'].append(f"{pct}% - SIGNIFICANT")
                score += impact_score
            elif pct >= 10:
                impact_score = 5
                data['impact'].append(f"{pct}% - MODERATE")
                score += impact_score
            else:
                impact_score = 2
                data['impact'].append(f"{pct}% - MINOR")
                score += impact_score
        
        return score, data
    
    def _analyze_dates(self, text: str) -> Tuple[int, Dict]:
        """Detect specific dates and effective dates (indicates concrete action)"""
        # Match dates in various formats
        date_patterns = [
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d+(?:st|nd|rd|th)?,?\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'effective\s+(?:immediately|now|today)',
            r'starting\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)',
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        if not dates:
            return 0, {}
        
        # Specific dates = concrete action = higher score
        score = len(dates) * 5
        
        # Extra score for "effective immediately" or "effective [date]" with word boundaries
        if re.search(r'\beffective\s+immediately\b', text, re.IGNORECASE) or re.search(r'\beffective\s+now\b', text, re.IGNORECASE):
            score += 10
        
        return score, {
            'dates_found': dates,
            'count': len(dates),
            'immediate_action': bool(re.search(r'\beffective\s+(?:immediately|now)\b', text, re.IGNORECASE))
        }
    
    def _analyze_monetary_values(self, text: str) -> Tuple[int, Dict]:
        """Detect large monetary amounts (billions, trillions)"""
        # Match dollar amounts with magnitude
        pattern = r'\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(billion|trillion|million)'
        matches = re.findall(pattern, text.lower())
        
        if not matches:
            return 0, {}
        
        score = 0
        data = {'amounts': []}
        
        for amount, magnitude in matches:
            amount_clean = amount.replace(',', '')
            
            if magnitude == 'trillion':
                score += 15
                data['amounts'].append(f"${amount} {magnitude} - MASSIVE")
            elif magnitude == 'billion':
                score += 10
                data['amounts'].append(f"${amount} {magnitude} - MAJOR")
            else:  # million
                score += 5
                data['amounts'].append(f"${amount} {magnitude} - SIGNIFICANT")
        
        return score, data
    
    def _check_critical_combinations(self, text: str) -> List[str]:
        """Check for critical keyword combinations with whole-word matching"""
        triggers = []
        
        # Also check for percentage + tariff combination
        if re.search(r'\d+\s*%', text) and re.search(r'\btariff\b', text, re.IGNORECASE):
            triggers.append('Major Tariff Increase')
        
        for combo, description in self.critical_combinations:
            # Check all keywords with word boundaries
            if all(re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE) for keyword in combo):
                triggers.append(description)
        
        return triggers
    
    def _analyze_sentiment(self, text: str) -> Tuple[int, Dict]:
        """Analyze aggressive/urgent sentiment with whole-word matching"""
        count = 0
        for term in self.aggressive_terms:
            # Use word boundaries for multi-word terms
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                count += 1
        
        # Multiplier increases with aggressive language
        multiplier = 1.0 + (count * 0.1)  # +10% per aggressive term
        
        return 0, {
            'aggressive_terms_count': count,
            'multiplier': multiplier,
            'is_aggressive': count > 0
        }
    
    def _recognize_entities(self, text: str) -> Tuple[int, Dict]:
        """Recognize economic institutions and geopolitical entities with whole-word matching"""
        score = 0
        entities = {
            'economic': [],
            'geopolitical': []
        }
        
        for entity in self.economic_entities:
            pattern = r'\b' + re.escape(entity) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                entities['economic'].append(entity)
                score += 3
        
        for entity in self.geopolitical_entities:
            pattern = r'\b' + re.escape(entity) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                entities['geopolitical'].append(entity)
                score += 4  # Geopolitical = higher risk
        
        return score, entities if (entities['economic'] or entities['geopolitical']) else {}
    
    def _detect_action_verbs(self, text: str) -> Tuple[int, Dict]:
        """Detect action verbs that indicate policy changes with whole-word matching"""
        score = 0
        found_actions = []
        
        # Use imported ACTION_VERBS from keywords.py
        for verb, weight in self.action_verbs.items():
            pattern = r'\b' + re.escape(verb) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_actions.append((verb, weight))
                score += weight
        
        return score, {'actions': found_actions} if found_actions else {}
    
    def _calculate_impact_level(self, score: int, critical_triggers: List[str]) -> ImpactLevel:
        """Determine impact level based on score and triggers"""
        if critical_triggers or score >= 50:
            return ImpactLevel.CRITICAL
        elif score >= 25:
            return ImpactLevel.HIGH
        elif score >= 10:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
