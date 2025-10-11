#!/usr/bin/env python3
"""
Deep analysis - fetch multiple pages of posts to go back further in time
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

# Extended search keywords
SEARCH_KEYWORDS = {
    'crypto': ['crypto', 'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency', 'blockchain', 
               'digital currency', 'altcoin', 'defi', 'nft', 'binance', 'coinbase', 'tether', 
               'usdt', 'stablecoin', 'mining', 'wallet', 'ledger', 'satoshi', 'dogecoin', 'doge'],
    'market_crash': ['crash', 'plunge', 'collapse', 'drop', 'fall', 'decline', 'tumble', 'sell-off'],
    'regulation': ['ban', 'illegal', 'prohibited', 'restrict', 'sanction', 'penalty', 'fine'],
}

def main():
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
    
    all_posts = []
    max_id = None
    
    # Fetch multiple pages to get more posts
    for page in range(3):  # Get 3 pages = up to 60 posts
        print(f"\nFetching page {page + 1}...")
        
        posts_url = f'https://{config.TRUTH_INSTANCE}/api/v1/accounts/{user_id}/statuses'
        params = {
            'exclude_replies': 'true',
            'exclude_reblogs': 'true',
            'limit': '20'
        }
        
        if max_id:
            params['max_id'] = max_id
        
        response = make_flaresolverr_request(posts_url, params=params, headers=headers)
        posts = response.json()
        
        if not posts:
            print("No more posts found.")
            break
        
        all_posts.extend(posts)
        max_id = posts[-1]['id']
        print(f"Got {len(posts)} posts (total: {len(all_posts)})")
    
    print(f"\n{'='*100}")
    print(f"Total posts retrieved: {len(all_posts)}")
    print(f"{'='*100}\n")
    
    found_posts = []
    
    for i, post in enumerate(all_posts, 1):
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
        
        # Search for keywords in all categories
        content_lower = cleaned_content.lower()
        matches = {}
        
        for category, keywords in SEARCH_KEYWORDS.items():
            found = [kw for kw in keywords if kw in content_lower]
            if found:
                matches[category] = found
        
        # Print all posts with indication of relevance
        indicator = ""
        if matches:
            categories = " | ".join([f"{cat.upper()}: {', '.join(kws)}" for cat, kws in matches.items()])
            indicator = f"🔶 RELEVANT - {categories}"
            found_posts.append({
                'index': i,
                'id': post_id,
                'time': time_str,
                'datetime': dt if 'dt' in locals() else None,
                'matches': matches,
                'content': cleaned_content
            })
        
        print(f"{i:3}. {time_str} {indicator}")
        if cleaned_content and len(cleaned_content) > 10:
            preview = cleaned_content[:150].replace('\n', ' ')
            print(f"     {preview}...")
        else:
            print(f"     [No text / Media only]")
        print()
    
    # Print detailed results
    if found_posts:
        print("\n" + "="*100)
        print(f"🔶 FOUND {len(found_posts)} RELEVANT POST(S):")
        print("="*100 + "\n")
        
        for fp in found_posts:
            print(f"Post #{fp['index']}")
            print(f"Time: {fp['time']}")
            for cat, kws in fp['matches'].items():
                print(f"  {cat.upper()}: {', '.join(kws)}")
            print(f"\nContent:\n{fp['content']}")
            print("\n" + "-"*100 + "\n")
        
        # Save to file
        with open('detailed_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(f"DETAILED POST ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Analyzed {len(all_posts)} posts\n")
            f.write("="*100 + "\n\n")
            for fp in found_posts:
                f.write(f"Post #{fp['index']}\n")
                f.write(f"Time: {fp['time']}\n")
                for cat, kws in fp['matches'].items():
                    f.write(f"  {cat.upper()}: {', '.join(kws)}\n")
                f.write(f"\n{fp['content']}\n")
                f.write("\n" + "="*100 + "\n\n")
        print(f"Saved detailed analysis to: detailed_analysis.txt")
    else:
        print("\n❌ No relevant posts found.")

if __name__ == "__main__":
    main()
