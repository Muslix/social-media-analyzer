#!/usr/bin/env python3
"""
Test script to verify whole-word matching fixes
Ensures 'war' does NOT match in 'software' but DOES match in 'trade war'
"""
from src.analyzers.market_analyzer import MarketImpactAnalyzer

def test_whole_word_matching():
    """Test that keywords only match whole words, not substrings"""
    analyzer = MarketImpactAnalyzer()
    
    print("=" * 70)
    print("WHOLE-WORD MATCHING TEST")
    print("=" * 70)
    
    # Test 1: 'war' should NOT match in 'software'
    print("\n🧪 Test 1: 'war' in 'software' (should NOT match)")
    text1 = "We will impose Export Controls on any and all critical software."
    result1 = analyzer.analyze(text1)
    
    if result1 and 'keywords' in result1['details']:
        keywords_found = result1['details']['keywords']
        
        # Check if 'war' keyword was detected
        war_found = False
        for category, kw_list in keywords_found.items():
            for keyword, weight in kw_list:
                if keyword == 'war':
                    war_found = True
        
        if war_found:
            print("❌ FAIL: 'war' was incorrectly found in 'software'")
            print(f"   Keywords detected: {keywords_found}")
        else:
            print("✅ PASS: 'war' was NOT found in 'software'")
            print(f"   Keywords detected: {keywords_found}")
    else:
        print("✅ PASS: No market-relevant keywords detected (correct)")
    
    # Test 2: 'war' SHOULD match in 'trade war'
    print("\n🧪 Test 2: 'war' in 'trade war' (SHOULD match)")
    text2 = "This is a trade war with China."
    result2 = analyzer.analyze(text2)
    
    if result2 and 'keywords' in result2['details']:
        keywords = result2['details']['keywords']
        
        # Check for 'trade war' (compound) or both 'trade' and 'war'
        has_war = False
        has_trade = False
        
        for category, kw_list in keywords.items():
            for keyword, weight in kw_list:
                if keyword == 'war':
                    has_war = True
                if keyword == 'trade' or keyword == 'trade war':
                    has_trade = True
        
        if has_war or 'trade war' in str(keywords):
            print("✅ PASS: 'war' was correctly detected in 'trade war'")
            print(f"   Keywords detected: {keywords}")
        else:
            print("❌ FAIL: 'war' was NOT detected in 'trade war'")
            print(f"   Keywords detected: {keywords}")
    else:
        print("❌ FAIL: No analysis result (war should have been detected)")
    
    # Test 3: Real-world example - Trump's post with 'software'
    print("\n🧪 Test 3: Real Trump post mentioning 'software'")
    text3 = """Also on November 1st, we will impose Export Controls on any and all 
    critical software."""
    result3 = analyzer.analyze(text3)
    
    if result3:
        print(f"   Impact Level: {result3['impact_level']}")
        print(f"   Score: {result3['impact_score']}")
        keywords = result3['details'].get('keywords', {})
        
        # Check if 'war' was incorrectly found
        war_in_keywords = False
        for category, kw_list in keywords.items():
            for keyword, weight in kw_list:
                if keyword == 'war':
                    war_in_keywords = True
        
        if war_in_keywords:
            print("   ❌ FAIL: 'war' was found (incorrect)")
        else:
            print("   ✅ PASS: 'war' was NOT found (correct)")
        
        print(f"   Keywords found: {keywords}")
    
    # Test 4: 'ai' should not match in 'China'
    print("\n🧪 Test 4: 'ai' should NOT match in 'China'")
    text4 = "China has taken an aggressive position."
    result4 = analyzer.analyze(text4)
    
    if result4:
        keywords = result4['details'].get('keywords', {})
        
        # Check if 'ai' was incorrectly found
        ai_in_keywords = False
        for category, kw_list in keywords.items():
            for keyword, weight in kw_list:
                if keyword == 'ai':
                    ai_in_keywords = True
        
        if ai_in_keywords:
            print("   ❌ FAIL: 'ai' was found in 'China' (incorrect)")
        else:
            print("   ✅ PASS: 'ai' was NOT found in 'China' (correct)")
        
        print(f"   Keywords found: {keywords}")
    
    # Test 5: 'ai' SHOULD match when it's a standalone word
    print("\n🧪 Test 5: 'ai' SHOULD match as standalone word")
    text5 = "New AI regulations will impact tech companies."
    result5 = analyzer.analyze(text5)
    
    if result5:
        keywords = result5['details'].get('keywords', {})
        
        ai_found = False
        for category, kw_list in keywords.items():
            for keyword, weight in kw_list:
                if keyword == 'ai':
                    ai_found = True
        
        if ai_found:
            print("   ✅ PASS: 'ai' was correctly detected")
        else:
            print("   ❌ FAIL: 'ai' should have been detected")
        
        print(f"   Keywords found: {keywords}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_whole_word_matching()
