#!/usr/bin/env python3
"""
Test the Quality Check system with sample posts
"""
import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(message)s')

sys.path.insert(0, '.')
from src.analyzers.llm_analyzer import LLMAnalyzer

# Quick test first
print("="*80)
print("QUICK TEST: Simple QC")
print("="*80)
llm = LLMAnalyzer()
simple_analysis = {
    'score': 90,
    'reasoning': 'The 100% tariff on China will trigger immediate market volatility.',
    'urgency': 'immediate',
    'market_direction': {
        'stocks': 'bearish',
        'crypto': 'bearish',
        'forex': 'usd_up',
        'commodities': 'down'
    }
}
qc_simple = llm.quality_check_analysis('Breaking: 100% tariff effective November 1st', simple_analysis)
if qc_simple:
    print(f"✅ QC Success!")
    print(f"   Approved: {qc_simple.get('approved')}")
    print(f"   Quality: {qc_simple.get('quality_score')}/100")
    if qc_simple.get('issues_found'):
        print(f"   Issues: {', '.join(qc_simple.get('issues_found', []))}")
else:
    print("❌ QC Failed to parse")

print("\n" + "="*80)
print("FULL TESTS")
print("="*80)

# Test Post 1: Good concrete numbers
post1 = """It has just been learned that China has taken an extraordinarily aggressive position on Trade in sending an extremely hostile letter to the World, stating that they were going to, effective November 1st, 2025, impose large scale Export Controls on virtually every product they make, and some not even made by them. This affects ALL Countries, without exception, and was obviously a plan devised by them years ago. It is absolutely unheard of in International Trade, and a moral disgrace in dealing with other Nations. Based on the fact that China has taken this unprecedented position, and speaking on behalf of the United States of America, as your President, I will be immediately putting a 100% Tariff on all products coming from China into the United States."""

# Test Post 2: Vague threats
post2 = """Some very strange things are happening in China! They are becoming very hostile, and sending letters to Countries throughout the World, that they want to impose Export Controls on each and every element of production having to do with Rare Earths, and virtually anything else they can think of, even if it's not manufactured in China. Nobody has ever seen anything like this but, essentially, it would "clog" the Markets, and make life difficult for virtually every Country in the World, especially for China. We have been contacted by other Countries who are extremely angry at this great Trade hostility, and have asked us to take strong action, which we will!"""

llm = LLMAnalyzer()

print("\n" + "="*80)
print("TEST 1: Concrete 100% Tariff Announcement")
print("="*80)
analysis1 = llm.analyze(post1, 150)
if analysis1:
    print(f"📊 LLM Score: {analysis1.get('score', 'N/A')}/100")
    print(f"📝 Reasoning: {analysis1.get('reasoning', 'N/A')}")
    print(f"⏰ Urgency: {analysis1.get('urgency', 'N/A')}")
    
    print("\n🔍 Running Quality Check...")
    qc1 = llm.quality_check_analysis(post1, analysis1)
    if qc1:
        approved = "✅ APPROVED" if qc1.get('approved') else "⚠️  NEEDS FIXES"
        print(f"   Status: {approved}")
        print(f"   Quality Score: {qc1.get('quality_score', 0)}/100")
        if qc1.get('issues_found'):
            print(f"   Issues: {', '.join(qc1['issues_found'])}")
        if qc1.get('suggested_fixes', {}).get('reasoning'):
            print(f"   Suggested Reasoning: {qc1['suggested_fixes']['reasoning']}")
else:
    print("❌ Analysis 1 failed")

print("\n" + "="*80)
print("TEST 2: Vague Trade Threats")
print("="*80)
analysis2 = llm.analyze(post2, 75)
if analysis2:
    print(f"📊 LLM Score: {analysis2.get('score', 'N/A')}/100")
    print(f"📝 Reasoning: {analysis2.get('reasoning', 'N/A')}")
    print(f"⏰ Urgency: {analysis2.get('urgency', 'N/A')}")
    
    print("\n🔍 Running Quality Check...")
    qc2 = llm.quality_check_analysis(post2, analysis2)
    if qc2:
        approved = "✅ APPROVED" if qc2.get('approved') else "⚠️  NEEDS FIXES"
        print(f"   Status: {approved}")
        print(f"   Quality Score: {qc2.get('quality_score', 0)}/100")
        if qc2.get('issues_found'):
            print(f"   Issues: {', '.join(qc2['issues_found'])}")
        if qc2.get('suggested_fixes', {}).get('reasoning'):
            print(f"   Suggested Reasoning: {qc2['suggested_fixes']['reasoning']}")
else:
    print("❌ Analysis 2 failed")

print("\n" + "="*80)
print("✅ Quality Check Test Complete")
print("="*80)
