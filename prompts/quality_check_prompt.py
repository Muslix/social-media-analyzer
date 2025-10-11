"""
Quality Check Prompt Template
Zweite Stufe: Validiert ob die Analyse professionell und Discord-ready ist
"""

QUALITY_CHECK_PROMPT = """Evaluate this market analysis for quality before sending to traders.

ORIGINAL POST:
{post_text}

PROPOSED ANALYSIS:
Score: {score}/100
Reasoning: {reasoning}
Urgency: {urgency}
Market Impact: {market_impact}

QUALITY CRITERIA - Check these:
1. Professional Language (sounds like market analyst)
2. No Internal Jargon (NO mention of "75-89", "90-100", scoring ranges, or technical rules)
3. Clear Market Impact (explains WHAT happens and WHY traders care)
4. Factual Accuracy (based on actual post content)
5. Appropriate Urgency (matches concrete actions mentioned)

EXAMPLES OF PROBLEMS:
❌ "This falls into the 75-89 range..." (mentions internal scoring)
❌ "Vague statements without specific numbers..." (technical jargon)
❌ "Score is high due to concrete data points" (explains scoring logic)

EXAMPLES OF GOOD ANALYSIS:
✅ "The 100% tariff announcement will trigger immediate selling pressure..."
✅ "China's export controls threaten global supply chains..."
✅ "November 1st deadline gives markets limited time..."

Respond with THIS EXACT JSON format (no other text, no thinking aloud):
{{
  "approved": true,
  "issues_found": [],
  "suggested_fixes": {{"reasoning": null, "urgency": null, "score": null}},
  "quality_score": 95
}}

OR if issues found:
{{
  "approved": false,
  "issues_found": ["specific issue description"],
  "suggested_fixes": {{"reasoning": "improved text", "urgency": "corrected", "score": 85}},
  "quality_score": 70
}}

RESPOND NOW WITH JSON ONLY (start with {{ immediately):"""


def build_quality_check_prompt(post_text: str, score: int, reasoning: str, 
                                urgency: str, market_impact: str) -> str:
    """Build the quality check prompt for a given analysis."""
    return QUALITY_CHECK_PROMPT.format(
        post_text=post_text,
        score=score,
        reasoning=reasoning,
        urgency=urgency,
        market_impact=market_impact
    )
