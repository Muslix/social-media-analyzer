#!/usr/bin/env python3
"""
Test LLM Analyzer with different market impact scenarios
Tests urgency classification, score consistency, and market detection
"""
import sys
sys.path.insert(0, '.')

from src.analyzers.market_analyzer import MarketImpactAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer

# Simple color codes (optional, fallback to no colors)
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORS_ENABLED = True
except ImportError:
    # Fallback: no colors
    class Fore:
        CYAN = YELLOW = GREEN = RED = BLUE = WHITE = LIGHTBLACK_EX = ""
    class Style:
        BRIGHT = RESET_ALL = ""
    COLORS_ENABLED = False

# Test scenarios with expected urgency levels
TEST_SCENARIOS = {
    "IMMEDIATE - Major Tariff Announcement": {
        "post": """BREAKING: The United States will impose a 200% tariff on all Chinese electric vehicles, 
effective immediately. This action is necessary to protect American workers and our automotive industry. 
The tariffs take effect at midnight tonight. China must respect fair trade practices.""",
        "expected_urgency": "immediate",
        "expected_score_range": (80, 100),
        "expected_markets": ["stocks", "crypto"],
        "description": "Presidential tariff announcement with immediate effect"
    },
    
    "IMMEDIATE - War Declaration": {
        "post": """After careful consideration and consultation with military advisors, I am authorizing 
military strikes against Iranian nuclear facilities. This operation will commence within the next 12 hours. 
We have no choice but to protect American interests and our allies in the region. God bless America.""",
        "expected_urgency": "immediate",
        "expected_score_range": (90, 100),
        "expected_markets": ["stocks", "commodities", "crypto", "forex"],
        "description": "Military action announcement - extreme market impact"
    },
    
    "IMMEDIATE - Fed Rate Decision": {
        "post": """The Federal Reserve has just announced an emergency 1.5% interest rate cut to combat 
the current economic situation. This is the largest single rate cut in over a decade. Markets should 
stabilize as credit becomes more accessible. Statement effective immediately.""",
        "expected_urgency": "immediate",
        "expected_score_range": (85, 100),
        "expected_markets": ["stocks", "crypto", "forex"],
        "description": "Emergency Fed decision - immediate market reaction"
    },
    
    "HOURS - Major Sanctions": {
        "post": """Today I am signing an executive order imposing comprehensive sanctions on Russia's 
energy sector. All Russian oil imports will be banned starting Monday. European allies have agreed 
to coordinate similar measures. This is in response to continued aggression.""",
        "expected_urgency": "hours",
        "expected_score_range": (70, 90),
        "expected_markets": ["commodities", "stocks", "forex"],
        "description": "Sanctions with specific start date - hours to react"
    },
    
    "HOURS - Crypto Regulation": {
        "post": """The SEC will classify all cryptocurrency exchanges as securities platforms, effective 
next week. All exchanges must register within 30 days or face shutdown. This is necessary to protect 
investors. Gary Gensler will provide details at tomorrow's press conference.""",
        "expected_urgency": "hours",
        "expected_score_range": (75, 95),
        "expected_markets": ["crypto", "stocks"],
        "description": "Major crypto regulatory change - market reaction within hours"
    },
    
    "DAYS - Trade Negotiation": {
        "post": """Had a very productive call with President Xi. We discussed trade relations and agreed 
to resume negotiations next month. Both sides are committed to finding a fair deal. Progress is being 
made, and I'm optimistic about reducing tensions.""",
        "expected_urgency": "days",
        "expected_score_range": (40, 65),
        "expected_markets": ["stocks", "forex"],
        "description": "Positive trade talks - gradual market pricing"
    },
    
    "DAYS - Policy Proposal": {
        "post": """I am proposing a new infrastructure bill that will invest $2 trillion over 10 years 
in American roads, bridges, and technology. This will create millions of jobs and boost our economy. 
Congress will vote on this legislation in the coming weeks.""",
        "expected_urgency": "days",
        "expected_score_range": (35, 60),
        "expected_markets": ["stocks"],
        "description": "Legislative proposal - markets react over days"
    },
    
    "WEEKS - Election Promise": {
        "post": """When re-elected, my administration will work to reduce corporate tax rates and 
eliminate unnecessary regulations. We will make America the best place to do business. 
Our economic plan will be released before the election.""",
        "expected_urgency": "weeks",
        "expected_score_range": (20, 45),
        "expected_markets": ["stocks"],
        "description": "Future policy promise - long-term market consideration"
    },
    
    "LOW IMPACT - General Statement": {
        "post": """Had a great meeting with business leaders today. They shared their concerns about 
the economy and workforce development. We discussed innovation and American competitiveness. 
Thank you for your time!""",
        "expected_urgency": "weeks",
        "expected_score_range": (5, 25),
        "expected_markets": [],
        "description": "General meeting - minimal market impact"
    },
    
    "IMMEDIATE - China Export Controls": {
        "post": """China has just announced they will ban all rare earth exports to the United States, 
effective immediately. This is an act of economic warfare. We will respond with our own export controls 
on semiconductor technology to China. No country can hold America hostage.""",
        "expected_urgency": "immediate",
        "expected_score_range": (85, 100),
        "expected_markets": ["stocks", "commodities", "crypto"],
        "description": "Supply chain disruption - immediate critical impact"
    }
}


def run_scenario_tests():
    """Run all test scenarios and evaluate LLM performance"""
    
    print("="*100)
    print(f"{Fore.CYAN}{Style.BRIGHT}LLM MARKET IMPACT ANALYSIS - SCENARIO TESTS{Style.RESET_ALL}")
    print("="*100)
    print()
    
    keyword_analyzer = MarketImpactAnalyzer()
    llm_analyzer = LLMAnalyzer()
    
    results = []
    
    for scenario_name, scenario_data in TEST_SCENARIOS.items():
        print(f"\n{Fore.YELLOW}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}📋 SCENARIO: {scenario_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Description: {scenario_data['description']}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*100}{Style.RESET_ALL}\n")
        
        post = scenario_data['post']
        expected_urgency = scenario_data['expected_urgency']
        expected_score_min, expected_score_max = scenario_data['expected_score_range']
        expected_markets = scenario_data['expected_markets']
        
        # Show post excerpt
        post_preview = post[:200] + "..." if len(post) > 200 else post
        print(f"{Fore.WHITE}Post Text:{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}{post_preview}{Style.RESET_ALL}\n")
        
        # Keyword Analysis
        print(f"{Fore.BLUE}1️⃣  Keyword Analysis...{Style.RESET_ALL}")
        keyword_result = keyword_analyzer.analyze(post)
        
        if keyword_result:
            keyword_score = keyword_result['impact_score']
            print(f"   {Fore.GREEN}✓{Style.RESET_ALL} Keyword Score: {Fore.CYAN}{keyword_score}{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✓{Style.RESET_ALL} Impact Level: {keyword_result['impact_level']}")
        else:
            keyword_score = 0
            print(f"   {Fore.RED}✗{Style.RESET_ALL} No keyword analysis")
        
        # LLM Analysis
        print(f"\n{Fore.BLUE}2️⃣  LLM Analysis...{Style.RESET_ALL}")
        llm_result = llm_analyzer.analyze(post, keyword_score)
        
        if llm_result:
            llm_score = llm_result.get('score', 0)
            urgency = llm_result.get('urgency', 'unknown')
            markets = llm_result.get('affected_markets', [])
            reasoning = llm_result.get('reasoning', '')
            processing_time = llm_result.get('processing_time_seconds', 0)
            
            # Display results
            print(f"   {Fore.GREEN}✓{Style.RESET_ALL} LLM Score: {Fore.CYAN}{llm_score}/100{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✓{Style.RESET_ALL} Urgency: {Fore.CYAN}{urgency.upper()}{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✓{Style.RESET_ALL} Markets: {Fore.CYAN}{', '.join(markets) if markets else 'None'}{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✓{Style.RESET_ALL} Processing: {Fore.CYAN}{processing_time}s{Style.RESET_ALL}")
            print(f"\n   {Fore.WHITE}AI Reasoning:{Style.RESET_ALL}")
            print(f"   {Fore.LIGHTBLACK_EX}{reasoning[:200]}...{Style.RESET_ALL}")
            
            # Evaluation
            print(f"\n{Fore.BLUE}3️⃣  Evaluation...{Style.RESET_ALL}")
            
            # Check urgency
            urgency_correct = urgency.lower() == expected_urgency.lower()
            urgency_icon = f"{Fore.GREEN}✓" if urgency_correct else f"{Fore.RED}✗"
            print(f"   {urgency_icon}{Style.RESET_ALL} Urgency: Expected '{Fore.YELLOW}{expected_urgency.upper()}{Style.RESET_ALL}', Got '{Fore.CYAN}{urgency.upper()}{Style.RESET_ALL}'")
            
            # Check score range
            score_in_range = expected_score_min <= llm_score <= expected_score_max
            score_icon = f"{Fore.GREEN}✓" if score_in_range else f"{Fore.RED}✗"
            print(f"   {score_icon}{Style.RESET_ALL} Score: Expected {Fore.YELLOW}{expected_score_min}-{expected_score_max}{Style.RESET_ALL}, Got {Fore.CYAN}{llm_score}{Style.RESET_ALL}")
            
            # Check markets
            markets_match = any(m in markets for m in expected_markets) if expected_markets else len(markets) == 0
            markets_icon = f"{Fore.GREEN}✓" if markets_match else f"{Fore.YELLOW}~"
            expected_markets_str = ', '.join(expected_markets) if expected_markets else 'None'
            print(f"   {markets_icon}{Style.RESET_ALL} Markets: Expected {Fore.YELLOW}{expected_markets_str}{Style.RESET_ALL}, Got {Fore.CYAN}{', '.join(markets) if markets else 'None'}{Style.RESET_ALL}")
            
            # Store result
            results.append({
                'scenario': scenario_name,
                'urgency_correct': urgency_correct,
                'score_in_range': score_in_range,
                'markets_match': markets_match,
                'llm_score': llm_score,
                'urgency': urgency,
                'expected_urgency': expected_urgency,
                'processing_time': processing_time
            })
        else:
            print(f"   {Fore.RED}✗{Style.RESET_ALL} LLM analysis failed")
            results.append({
                'scenario': scenario_name,
                'urgency_correct': False,
                'score_in_range': False,
                'markets_match': False,
                'llm_score': 0,
                'urgency': 'failed',
                'expected_urgency': expected_urgency,
                'processing_time': 0
            })
    
    # Summary
    print(f"\n\n{Fore.YELLOW}{'='*100}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}📊 TEST SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*100}{Style.RESET_ALL}\n")
    
    total_tests = len(results)
    urgency_correct = sum(1 for r in results if r['urgency_correct'])
    score_correct = sum(1 for r in results if r['score_in_range'])
    markets_correct = sum(1 for r in results if r['markets_match'])
    avg_processing = sum(r['processing_time'] for r in results) / total_tests if total_tests > 0 else 0
    
    print(f"{Fore.CYAN}Total Scenarios: {Fore.WHITE}{total_tests}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Urgency Accuracy: {Fore.WHITE}{urgency_correct}/{total_tests} ({urgency_correct/total_tests*100:.1f}%){Style.RESET_ALL}")
    print(f"{Fore.CYAN}Score Accuracy: {Fore.WHITE}{score_correct}/{total_tests} ({score_correct/total_tests*100:.1f}%){Style.RESET_ALL}")
    print(f"{Fore.CYAN}Markets Accuracy: {Fore.WHITE}{markets_correct}/{total_tests} ({markets_correct/total_tests*100:.1f}%){Style.RESET_ALL}")
    print(f"{Fore.CYAN}Avg Processing Time: {Fore.WHITE}{avg_processing:.2f}s{Style.RESET_ALL}")
    
    # Urgency breakdown
    print(f"\n{Fore.BLUE}Urgency Results:{Style.RESET_ALL}")
    for result in results:
        status = f"{Fore.GREEN}✓" if result['urgency_correct'] else f"{Fore.RED}✗"
        print(f"  {status}{Style.RESET_ALL} {result['scenario'][:50]:<50} Expected: {Fore.YELLOW}{result['expected_urgency']:<10}{Style.RESET_ALL} Got: {Fore.CYAN}{result['urgency']:<10}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}{'='*100}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        run_scenario_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
