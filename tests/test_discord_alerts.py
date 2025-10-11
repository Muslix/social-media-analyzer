#!/usr/bin/env python3
"""
Test Discord Notifications with real market impact analysis
"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.analyzers.market_analyzer import MarketImpactAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.output.discord_notifier import DiscordNotifier

# Real Trump China tariff post
TRUMP_POST = """
It has just been learned that China has taken an extraordinarily aggressive position on Trade in sending an extremely hostile letter to the World, stating that they were going to, effective November 1st, 2025, impose large scale Export Controls on virtually every product they make, and some not even made by them. This affects ALL Countries, without exception, and was obviously a plan devised by them years ago. It is absolutely unheard of in International Trade, and a moral disgrace in dealing with other Nations.

Based on the fact that China has taken this unprecedented position, and speaking only for the U.S.A., and not other Nations who were similarly threatened, starting November 1st, 2025 (or sooner, depending on any further actions or changes taken by China), the United States of America will impose a Tariff of 100% on China, over and above any Tariff that they are currently paying. Also on November 1st, we will impose Export Controls on any and all critical software.

It is impossible to believe that China would have taken such an action, but they have, and the rest is History. Thank you for your attention to this matter!
"""

def test_discord_alert():
    """Test sending a full market impact alert to Discord"""
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not set in .env")
        return
    
    print("="*80)
    print("DISCORD MARKET IMPACT ALERT TEST")
    print("="*80)
    
    # 1. Keyword Analysis
    print("\n1️⃣  Running Keyword Analysis...")
    keyword_analyzer = MarketImpactAnalyzer()
    keyword_result = keyword_analyzer.analyze(TRUMP_POST)
    
    if keyword_result:
        print(f"   ✅ Keyword Score: {keyword_result['impact_score']}")
        print(f"   ✅ Impact Level: {keyword_result['impact_level']}")
    
    # 2. LLM Analysis
    print("\n2️⃣  Running LLM Analysis...")
    llm_analyzer = LLMAnalyzer()
    llm_result = llm_analyzer.analyze(TRUMP_POST, keyword_result['impact_score'])
    
    if llm_result:
        print(f"   ✅ LLM Score: {llm_result.get('score', 0)}/100")
        print(f"   ✅ Urgency: {llm_result.get('urgency', 'unknown')}")
        print(f"   ✅ Markets: {', '.join(llm_result.get('affected_markets', []))}")
    
    # 3. Send to Discord
    print("\n3️⃣  Sending to Discord...")
    notifier = DiscordNotifier(webhook_url, username="🚨 Market Impact Bot")
    
    # Simulated post timestamp (October 10, 2025 at 20:50 UTC)
    post_timestamp = "2025-10-10T20:50:00Z"
    
    success = notifier.send_market_alert(
        post_text=TRUMP_POST,
        keyword_analysis=keyword_result,
        llm_analysis=llm_result,
        post_url="https://truthsocial.com/@realDonaldTrump/posts/115351840469973590",
        author="@realDonaldTrump",
        post_created_at=post_timestamp
    )
    
    if success:
        print("   ✅ Alert sent to Discord!")
        print("\n" + "="*80)
        print("🎉 CHECK YOUR DISCORD CHANNEL!")
        print("="*80)
    else:
        print("   ❌ Failed to send alert")


if __name__ == "__main__":
    test_discord_alert()
