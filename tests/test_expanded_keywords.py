#!/usr/bin/env python3
"""
Test script to demonstrate expanded keyword coverage
Shows how the new keyword database catches more market-relevant terms
"""
from src.analyzers.market_analyzer import MarketImpactAnalyzer
from src.data.keywords import get_keyword_stats

def test_expanded_keywords():
    """Test that new keywords are detected correctly"""
    analyzer = MarketImpactAnalyzer()
    stats = get_keyword_stats()
    
    print("=" * 70)
    print("EXPANDED KEYWORD DATABASE TEST")
    print("=" * 70)
    print(f"\n📊 Keyword Database: {stats['total_keywords']} total keywords loaded")
    print()
    
    # Test cases with new keywords
    test_cases = [
        {
            'name': 'Monetary Policy - Rate Hike',
            'text': 'Fed announces emergency rate hike to combat inflation',
            'expect_keywords': ['fed', 'announce', 'rate hike', 'inflation']
        },
        {
            'name': 'Crypto Regulation',
            'text': 'SEC declares new regulations for Bitcoin and Ethereum mining',
            'expect_keywords': ['sec', 'regulation', 'bitcoin', 'ethereum', 'mining']
        },
        {
            'name': 'Trade Policy - Quota',
            'text': 'US imposes new import quotas and duties on steel',
            'expect_keywords': ['impose', 'import', 'quota', 'duty']
        },
        {
            'name': 'Geopolitical - Iran Sanctions',
            'text': 'Breaking: US enforces severe sanctions on Iran nuclear program',
            'expect_keywords': ['enforce', 'sanction', 'iran']
        },
        {
            'name': 'Tech Antitrust',
            'text': 'DOJ launches antitrust investigation into Google and Amazon',
            'expect_keywords': ['antitrust', 'google', 'amazon']
        },
        {
            'name': 'Energy Policy',
            'text': 'OPEC announces drastic crude oil production cuts',
            'expect_keywords': ['opec', 'announce', 'crude', 'oil']
        },
        {
            'name': 'Banking Crisis',
            'text': 'Treasury unveils emergency bailout for major banks facing default',
            'expect_keywords': ['treasury', 'bailout', 'bank', 'default']
        },
        {
            'name': 'Military Action',
            'text': 'Pentagon confirms military deployment near North Korea',
            'expect_keywords': ['military', 'north korea']
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"🧪 Test {i}: {test['name']}")
        print(f"{'─' * 70}")
        print(f"📝 Text: \"{test['text']}\"")
        print()
        
        result = analyzer.analyze(test['text'])
        
        if result:
            print(f"✅ Analysis Complete")
            print(f"   Impact Level: {result['impact_level']}")
            print(f"   Score: {result['impact_score']}")
            
            # Show detected keywords
            keywords = result['details'].get('keywords', {})
            if keywords:
                print(f"\n   📌 Detected Keywords:")
                for category, kw_list in keywords.items():
                    if kw_list:
                        kw_str = ', '.join([f"{k} (×{w})" for k, w in kw_list])
                        print(f"      {category.upper()}: {kw_str}")
            
            # Show critical triggers
            if 'critical_triggers' in result['details']:
                print(f"\n   🚨 Critical Triggers:")
                for trigger in result['details']['critical_triggers']:
                    print(f"      ⚠️  {trigger}")
            
            # Show action verbs
            if 'actions' in result['details'] and result['details']['actions']:
                actions = result['details']['actions']['actions']
                action_str = ', '.join([f"{a} (×{w})" for a, w in actions])
                print(f"\n   ⚡ Action Verbs: {action_str}")
            
            # Check if expected keywords were found
            found_count = 0
            for expect in test['expect_keywords']:
                # Check in all keyword categories
                found = False
                for category, kw_list in keywords.items():
                    if any(expect.lower() in kw.lower() for kw, _ in kw_list):
                        found = True
                        break
                
                # Also check in actions
                if not found and 'actions' in result['details'] and result['details']['actions']:
                    if any(expect.lower() in action.lower() for action, _ in result['details']['actions']['actions']):
                        found = True
                
                if found:
                    found_count += 1
            
            coverage = (found_count / len(test['expect_keywords'])) * 100
            print(f"\n   📊 Expected Keywords Coverage: {found_count}/{len(test['expect_keywords'])} ({coverage:.0f}%)")
            
        else:
            print(f"❌ No analysis result (no market-relevant content detected)")
    
    print(f"\n{'=' * 70}")
    print("EXPANDED KEYWORD TEST COMPLETE")
    print("=" * 70)
    print(f"\n✅ Database now covers:")
    print(f"   • Trade policy (tariffs, quotas, duties, sanctions)")
    print(f"   • Monetary policy (Fed, interest rates, QE)")
    print(f"   • Crypto/blockchain (Bitcoin, Ethereum, mining, DeFi)")
    print(f"   • Geopolitical risks (China, Russia, Iran, N. Korea)")
    print(f"   • Banking/finance (bailouts, defaults, bankruptcies)")
    print(f"   • Energy markets (OPEC, oil, gas, crude)")
    print(f"   • Tech regulation (antitrust, privacy, semiconductors)")
    print(f"   • Military/defense (deployments, strikes, conflicts)")
    print(f"   • Economic indicators (GDP, CPI, inflation, recession)")
    print(f"   • Major companies (FAANG, Tesla, etc.)")
    print()


if __name__ == "__main__":
    test_expanded_keywords()
