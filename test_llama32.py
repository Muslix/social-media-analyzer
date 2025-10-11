#!/usr/bin/env python3
"""
Test Llama 3.2 3B vs Qwen3 8B
Compare performance, quality, and speed
"""

import json
import time
from colorama import Fore, Style, init
from src.analyzers.llm_analyzer import LLMAnalyzer

init(autoreset=True)

# Test post: China 100% tariff announcement
TEST_POST = """It has just been learned that China has taken an extraordinarily aggressive position on Trade in sending an extremely hostile letter to the World, stating that they were going to, effective November 1st, 2025, impose large scale Export Controls on virtually every product they make, and some not even made by them. This affects ALL Countries, without exception, and was obviously a plan devised by them years ago. It is absolutely unheard of in International Trade, and a moral disgrace in dealing with other Nations.Based on the fact that China has taken this unprecedented position, and speaking only for the U.S.A., and not other Nations who were similarly threatened, starting November 1st, 2025 (or sooner, depending on any further actions or changes taken by China), the United States of America will impose a Tariff of 100% on China, over and above any Tariff that they are currently paying. Also on November 1st, we will impose Export Controls on any and all critical software.It is impossible to believe that China would have taken such an action, but they have, and the rest is History. Thank you for your attention to this matter!DONALD J. TRUMPPRESIDENT OF THE UNITED STATES OF AMERICA"""

KEYWORD_SCORE = 172  # From market_impact_posts.txt


def test_model(model_name: str, analyzer: LLMAnalyzer, post_text: str, keyword_score: int):
    """Test a single model"""
    print(f"\n{'='*80}")
    print(f"{Fore.CYAN}🧪 Testing: {model_name}{Style.RESET_ALL}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    try:
        result = analyzer.analyze(post_text, keyword_score)
        
        elapsed = time.time() - start_time
        
        # Display results
        print(f"{Fore.GREEN}✅ Analysis completed in {elapsed:.2f}s{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}📊 RESULTS:{Style.RESET_ALL}")
        print(f"  Score: {result.get('score', 'N/A')}/100")
        print(f"  Urgency: {result.get('urgency', 'N/A')}")
        
        print(f"\n{Fore.YELLOW}🎯 Market Direction:{Style.RESET_ALL}")
        market_dir = result.get('market_direction', {})
        print(f"  Stocks:      {market_dir.get('stocks', 'N/A')}")
        print(f"  Crypto:      {market_dir.get('crypto', 'N/A')}")
        print(f"  Forex:       {market_dir.get('forex', 'N/A')}")
        print(f"  Commodities: {market_dir.get('commodities', 'N/A')}")
        
        print(f"\n{Fore.YELLOW}💡 Reasoning:{Style.RESET_ALL}")
        reasoning = result.get('reasoning', 'N/A')
        # Wrap reasoning text
        max_width = 75
        words = reasoning.split()
        current_line = "  "
        for word in words:
            if len(current_line) + len(word) + 1 > max_width:
                print(current_line)
                current_line = "  " + word
            else:
                current_line += " " + word if current_line != "  " else word
        if current_line.strip():
            print(current_line)
        
        print(f"\n{Fore.YELLOW}📅 Key Events:{Style.RESET_ALL}")
        for event in result.get('key_events', []):
            print(f"  • {event}")
        
        print(f"\n{Fore.YELLOW}📆 Important Dates:{Style.RESET_ALL}")
        for date in result.get('important_dates', []):
            print(f"  • {date}")
        
        # Performance metrics
        print(f"\n{Fore.BLUE}⚡ Performance:{Style.RESET_ALL}")
        print(f"  Time:   {elapsed:.2f}s")
        print(f"  Model:  {model_name}")
        print(f"  Size:   {'~2GB' if '3b' in model_name.lower() else '~5.2GB'}")
        
        return {
            'model': model_name,
            'elapsed': elapsed,
            'score': result.get('score', 0),
            'result': result,
            'success': True
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
        print(f"  Time: {elapsed:.2f}s")
        
        return {
            'model': model_name,
            'elapsed': elapsed,
            'error': str(e),
            'success': False
        }


def main():
    print(f"\n{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🚀 LLM MODEL COMPARISON TEST{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}📝 Test Post:{Style.RESET_ALL}")
    print(f"  Source: Donald J. Trump (@realDonaldTrump)")
    print(f"  Date: October 10, 2025 at 08:50 PM UTC")
    print(f"  Topic: 100% tariff on China + Export Controls")
    print(f"  Keyword Score: {KEYWORD_SCORE}/100 (CRITICAL)")
    
    # Test both models
    results = []
    
    # 1. Llama 3.2 3B
    print(f"\n{Fore.CYAN}{'─'*80}{Style.RESET_ALL}")
    llama_analyzer = LLMAnalyzer(model="llama3.2:3b")
    results.append(test_model("Llama 3.2 3B Instruct", llama_analyzer, TEST_POST, KEYWORD_SCORE))
    
    # 2. Qwen3 8B
    print(f"\n{Fore.CYAN}{'─'*80}{Style.RESET_ALL}")
    qwen_analyzer = LLMAnalyzer(model="qwen3:8b")
    results.append(test_model("Qwen3 8B", qwen_analyzer, TEST_POST, KEYWORD_SCORE))
    
    # Comparison summary
    print(f"\n{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}📊 COMPARISON SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}\n")
    
    successful_results = [r for r in results if r['success']]
    
    if len(successful_results) == 2:
        llama_result = successful_results[0]
        qwen_result = successful_results[1]
        
        print(f"{Fore.YELLOW}⚡ Speed:{Style.RESET_ALL}")
        print(f"  Llama 3.2 3B: {llama_result['elapsed']:.2f}s")
        print(f"  Qwen3 8B:     {qwen_result['elapsed']:.2f}s")
        
        speed_diff = ((qwen_result['elapsed'] - llama_result['elapsed']) / qwen_result['elapsed']) * 100
        if llama_result['elapsed'] < qwen_result['elapsed']:
            print(f"  {Fore.GREEN}✅ Llama 3.2 is {abs(speed_diff):.1f}% faster{Style.RESET_ALL}")
        else:
            print(f"  {Fore.GREEN}✅ Qwen3 is {abs(speed_diff):.1f}% faster{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}🎯 Scores:{Style.RESET_ALL}")
        print(f"  Llama 3.2 3B: {llama_result['score']}/100")
        print(f"  Qwen3 8B:     {qwen_result['score']}/100")
        
        print(f"\n{Fore.YELLOW}💾 Model Size:{Style.RESET_ALL}")
        print(f"  Llama 3.2 3B: ~2GB")
        print(f"  Qwen3 8B:     ~5.2GB")
        print(f"  {Fore.GREEN}✅ Llama 3.2 uses 61% less disk space{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}🎯 Market Direction Comparison:{Style.RESET_ALL}")
        llama_markets = llama_result['result'].get('market_direction', {})
        qwen_markets = qwen_result['result'].get('market_direction', {})
        
        for market in ['stocks', 'crypto', 'forex', 'commodities']:
            llama_dir = llama_markets.get(market, 'N/A')
            qwen_dir = qwen_markets.get(market, 'N/A')
            match = "✅" if llama_dir == qwen_dir else "⚠️"
            print(f"  {market.capitalize():12} | Llama: {llama_dir:10} | Qwen: {qwen_dir:10} {match}")
        
        print(f"\n{Fore.YELLOW}💡 Recommendation:{Style.RESET_ALL}")
        if abs(llama_result['score'] - qwen_result['score']) <= 10:
            if llama_result['elapsed'] < qwen_result['elapsed'] * 0.8:
                print(f"  {Fore.GREEN}✅ Use Llama 3.2 3B - Similar quality, much faster!{Style.RESET_ALL}")
            else:
                print(f"  {Fore.YELLOW}⚖️  Both models perform similarly{Style.RESET_ALL}")
        else:
            if qwen_result['score'] > llama_result['score']:
                print(f"  {Fore.YELLOW}⚖️  Qwen3 8B more accurate, Llama 3.2 faster{Style.RESET_ALL}")
            else:
                print(f"  {Fore.GREEN}✅ Use Llama 3.2 3B - Better score AND faster!{Style.RESET_ALL}")
    
    else:
        print(f"{Fore.RED}❌ Some models failed, cannot compare{Style.RESET_ALL}")
        for result in results:
            if not result['success']:
                print(f"  {result['model']}: {result.get('error', 'Unknown error')}")
    
    print(f"\n{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
