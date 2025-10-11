#!/usr/bin/env python3
"""
Test LLM Analyzer with real Trump China tariff post
Compare Keyword vs LLM analysis
"""
import sys
sys.path.insert(0, '.')

from src.analyzers.market_analyzer import MarketImpactAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
import json

# Real Trump post that caused crypto crash
TRUMP_CHINA_POST = """
It has just been learned that China has taken an extraordinarily aggressive position on Trade in sending an extremely hostile letter to the World, stating that they were going to, effective November 1st, 2025, impose large scale Export Controls on virtually every product they make, and some not even made by them. This affects ALL Countries, without exception, and was obviously a plan devised by them years ago. It is absolutely unheard of in International Trade, and a moral disgrace in dealing with other Nations.

Based on the fact that China has taken this unprecedented position, and speaking only for the U.S.A., and not other Nations who were similarly threatened, starting November 1st, 2025 (or sooner, depending on any further actions or changes taken by China), the United States of America will impose a Tariff of 100% on China, over and above any Tariff that they are currently paying. Also on November 1st, we will impose Export Controls on any and all critical software.

It is impossible to believe that China would have taken such an action, but they have, and the rest is History. Thank you for your attention to this matter!
"""

def test_comparison():
    """Compare keyword-based vs LLM analysis"""
    
    print("="*80)
    print("KEYWORD vs LLM ANALYSIS COMPARISON")
    print("="*80)
    print(f"\nPost Text (first 200 chars):\n{TRUMP_CHINA_POST[:200]}...\n")
    
    # 1. Keyword Analysis
    print("\n" + "─"*80)
    print("1️⃣  KEYWORD-BASED ANALYSIS")
    print("─"*80)
    
    keyword_analyzer = MarketImpactAnalyzer()
    keyword_result = keyword_analyzer.analyze(TRUMP_CHINA_POST)
    
    if keyword_result:
        print(f"Impact Level: {keyword_result['impact_level']}")
        print(f"Score: {keyword_result['impact_score']}")
        print(f"\nCritical Triggers: {keyword_result['details'].get('critical_triggers', [])}")
        
        keywords = keyword_result['details'].get('keywords', {})
        print(f"\nTop Keywords Found:")
        for category, kw_list in keywords.items():
            if kw_list:
                print(f"  {category.upper()}: {[k for k, w in kw_list[:3]]}")
        
        keyword_score = keyword_result['impact_score']
    else:
        print("No keyword analysis available")
        keyword_score = 0
    
    # 2. LLM Analysis
    print("\n" + "─"*80)
    print("2️⃣  LLM-BASED ANALYSIS (Qwen2.5:3b)")
    print("─"*80)
    print("Analyzing with LLM... (may take a few seconds)\n")
    
    llm_analyzer = LLMAnalyzer()
    llm_result = llm_analyzer.analyze(TRUMP_CHINA_POST, keyword_score)
    
    if llm_result:
        print(f"LLM Score: {llm_result.get('score', 'N/A')}/100")
        print(f"Keyword Score: {llm_result.get('keyword_score', 'N/A')}/100")
        print(f"Processing Time: {llm_result.get('processing_time_seconds', 'N/A')}s")
        print(f"\nReasoning:\n  {llm_result.get('reasoning', 'N/A')}")
        print(f"\nAffected Markets: {', '.join(llm_result.get('affected_markets', []))}")
        print(f"Urgency: {llm_result.get('urgency', 'N/A')}")
        print(f"\nKey Events:")
        for event in llm_result.get('key_events', []):
            print(f"  • {event}")
    else:
        print("❌ LLM analysis failed")
    
    # 3. Comparison
    print("\n" + "="*80)
    print("📊 COMPARISON")
    print("="*80)
    
    if keyword_result and llm_result:
        print(f"\nKeyword Score: {keyword_score}")
        print(f"LLM Score:     {llm_result.get('score', 0)}")
        print(f"Difference:    {abs(keyword_score - llm_result.get('score', 0))}")
        
        print(f"\n⏱️  Processing Time:")
        print(f"  Keyword Analysis: Instant (~0.01s)")
        print(f"  LLM Analysis:     {llm_result.get('processing_time_seconds', 0)}s")
        
        print(f"\n💡 Insight:")
        if llm_result.get('score', 0) > keyword_score:
            print(f"  LLM detected {llm_result.get('score', 0) - keyword_score} points MORE impact")
            print(f"  LLM reasoning: {llm_result.get('reasoning', '')[:100]}...")
        elif llm_result.get('score', 0) < keyword_score:
            print(f"  LLM scored {keyword_score - llm_result.get('score', 0)} points LOWER")
            print(f"  LLM may have contextual understanding that keywords missed")
        else:
            print(f"  Scores match! Both methods agree on impact level.")
    
    # 4. Save training data
    if llm_result:
        print("\n" + "="*80)
        print("💾 SAVING TRAINING DATA")
        print("="*80)
        llm_analyzer.save_training_data(TRUMP_CHINA_POST, keyword_score, llm_result)
        print("✅ Training data saved to training_data/llm_training_data.jsonl")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    test_comparison()
