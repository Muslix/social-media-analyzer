#!/usr/bin/env python3
"""
Quick analysis script to fetch last 40 posts and search for crypto-related content
"""
import requests
from config import Config
from datetime import datetime
import json

config = Config()

def make_flaresolverr_request(url, headers=None, params=None):
    """Use FlareSolverr to fetch a URL"""
    flaresolverr_url = f"http://{config.FLARESOLVERR_ADDRESS}:{config.FLARESOLVERR_PORT}/v1"
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 25000,
    }
    if headers:
        payload["headers"] = headers
    if params:
        from urllib.parse import urlencode
        url = url + "?" + urlencode(params)
        payload["url"] = url

    print(f"Fetching: {url}")
    
    resp = requests.post(flaresolverr_url, json=payload)
    resp.raise_for_status()
    result = resp.json()
    if result.get("status") != "ok":
        raise Exception(f"FlareSolverr error: {result}")
    response_content = result["solution"]["response"]
    
    class FakeResponse:
        def __init__(self, content):
            self._content = content
        def json(self):
            import json
            from bs4 import BeautifulSoup
            try:
                return json.loads(self._content)
            except Exception:
                soup = BeautifulSoup(self._content, "html.parser")
                pre = soup.find("pre")
                if pre:
                    return json.loads(pre.text)
                raise
        @property
        def text(self):
            return self._content
    return FakeResponse(response_content)

def clean_html(text):
    """Remove HTML tags"""
    from bs4 import BeautifulSoup
    import re
    if not text:
        return ""
    soup = BeautifulSoup(text, 'html.parser')
    for br in soup.find_all(['br', 'p']):
        br.replace_with('\n' + br.text)
    text = soup.get_text()
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

# Crypto keywords to search for
CRYPTO_KEYWORDS = [
    'crypto', 'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency',
    'blockchain', 'digital currency', 'altcoin', 'defi', 'nft',
    'binance', 'coinbase', 'tether', 'usdt', 'stablecoin',
    'mining', 'wallet', 'ledger', 'satoshi'
]

def main():
    # Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    # Get user ID
    lookup_url = f'https://{config.TRUTH_INSTANCE}/api/v1/accounts/lookup?acct={config.TRUTH_USERNAME}'
    response = make_flaresolverr_request(lookup_url, headers)
    user_data = response.json()
    user_id = user_data['id']
    print(f"Found user ID: {user_id}\n")
    
    # Get posts
    posts_url = f'https://{config.TRUTH_INSTANCE}/api/v1/accounts/{user_id}/statuses'
    params = {
        'exclude_replies': 'true',
        'exclude_reblogs': 'true',
        'limit': '40'
    }
    
    response = make_flaresolverr_request(posts_url, params=params, headers=headers)
    posts = response.json()
    
    print(f"Retrieved {len(posts)} posts\n")
    print("="*100)
    
    crypto_posts = []
    
    for i, post in enumerate(posts, 1):
        post_id = post.get('id')
        created_at = post.get('created_at', '')
        content = post.get('content', '')
        cleaned_content = clean_html(content)
        
        # Parse datetime
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            time_str = created_at
        
        # Search for crypto keywords
        content_lower = cleaned_content.lower()
        found_keywords = [kw for kw in CRYPTO_KEYWORDS if kw in content_lower]
        
        if found_keywords:
            crypto_posts.append({
                'index': i,
                'id': post_id,
                'time': time_str,
                'keywords': found_keywords,
                'content': cleaned_content
            })
        
        # Print summary
        has_crypto = "🔶 CRYPTO" if found_keywords else ""
        print(f"{i:2}. {time_str} {has_crypto}")
        if cleaned_content and len(cleaned_content) > 10:
            preview = cleaned_content[:100].replace('\n', ' ')
            print(f"    {preview}...")
        else:
            print(f"    [No text / Media only]")
        print()
    
    # Print crypto posts in detail
    if crypto_posts:
        print("\n" + "="*100)
        print(f"🔶 FOUND {len(crypto_posts)} CRYPTO-RELATED POST(S):")
        print("="*100 + "\n")
        
        for cp in crypto_posts:
            print(f"Post #{cp['index']}")
            print(f"Time: {cp['time']}")
            print(f"Keywords found: {', '.join(cp['keywords'])}")
            print(f"Content:\n{cp['content']}")
            print("\n" + "-"*100 + "\n")
        
        # Save to file
        with open('crypto_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(f"CRYPTO POST ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*100 + "\n\n")
            for cp in crypto_posts:
                f.write(f"Post #{cp['index']}\n")
                f.write(f"Time: {cp['time']}\n")
                f.write(f"Keywords: {', '.join(cp['keywords'])}\n")
                f.write(f"\n{cp['content']}\n")
                f.write("\n" + "="*100 + "\n\n")
        print("Saved detailed analysis to: crypto_analysis.txt")
    else:
        print("\n❌ No crypto-related posts found in the last 40 posts.")

if __name__ == "__main__":
    main()
