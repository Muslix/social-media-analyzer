#!/usr/bin/env python3
"""
Test Quality Check with deliberately bad analysis to verify it catches issues
"""
import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(message)s')

sys.path.insert(0, '.')
from src.analyzers.llm_analyzer import LLMAnalyzer

print("="*80)
print("TEST: Bad Analysis (Should be REJECTED by QC)")
print("="*80)

llm = LLMAnalyzer()

# BAD EXAMPLE 1: Mentions internal scoring ranges
bad_analysis_1 = {
    'score': 85,
    'reasoning': 'This falls into the 75-89 range because it has vague statements without concrete numbers.',
    'urgency': 'immediate',
    'market_direction': {
        'stocks': 'bearish',
        'crypto': 'bearish',
        'forex': 'usd_up',
        'commodities': 'down'
    }
}

post = "Trump announces massive tariff increases on China."

print("\n❌ BAD EXAMPLE 1: Mentions internal scoring ranges")
print(f"Reasoning: {bad_analysis_1['reasoning']}")
print("\n🔍 Running Quality Check...")

qc1 = llm.quality_check_analysis(post, bad_analysis_1)
if qc1:
    approved = "✅ APPROVED" if qc1.get('approved') else "❌ REJECTED"
    print(f"   Status: {approved}")
    print(f"   Quality Score: {qc1.get('quality_score', 0)}/100")
    if qc1.get('issues_found'):
        print(f"   Issues Found:")
        for issue in qc1.get('issues_found', []):
            print(f"      • {issue}")
    if qc1.get('suggested_fixes', {}).get('reasoning'):
        print(f"\n   💡 Suggested Fix:")
        print(f"      {qc1['suggested_fixes']['reasoning']}")
else:
    print("   ⚠️  QC Failed")

# BAD EXAMPLE 2: Technical jargon instead of market analysis
print("\n" + "="*80)
bad_analysis_2 = {
    'score': 90,
    'reasoning': 'Score is high due to concrete data points and specific numerical values mentioned in the text.',
    'urgency': 'immediate',
    'market_direction': {
        'stocks': 'bearish',
        'crypto': 'neutral',
        'forex': 'neutral',
        'commodities': 'neutral'
    }
}

print("❌ BAD EXAMPLE 2: Explains scoring logic instead of market impact")
print(f"Reasoning: {bad_analysis_2['reasoning']}")
print("\n🔍 Running Quality Check...")

qc2 = llm.quality_check_analysis("Trump announces 100% tariff on China.", bad_analysis_2)
if qc2:
    approved = "✅ APPROVED" if qc2.get('approved') else "❌ REJECTED"
    print(f"   Status: {approved}")
    print(f"   Quality Score: {qc2.get('quality_score', 0)}/100")
    if qc2.get('issues_found'):
        print(f"   Issues Found:")
        for issue in qc2.get('issues_found', []):
            print(f"      • {issue}")
    if qc2.get('suggested_fixes', {}).get('reasoning'):
        print(f"\n   💡 Suggested Fix:")
        print(f"      {qc2['suggested_fixes']['reasoning']}")
else:
    print("   ⚠️  QC Failed")

print("\n" + "="*80)
print("✅ Bad Analysis Test Complete")
print("="*80)
print("\nExpected: Both examples should be REJECTED with quality scores < 80")
