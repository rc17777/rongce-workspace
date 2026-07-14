"""NCPSSD 采集测试 - 直接用 requests + BeautifulSoup"""
import requests, sys, json, re, time
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# NCPSSD 搜索 API
# 国家哲学社会科学文献中心搜索接口
search_url = "https://www.ncpssd.cn/api/search"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.ncpssd.cn/',
}

# 尝试各种可能的搜索接口
endpoints = [
    ("GET", "https://www.ncpssd.cn/api/search?keyword=%E7%BB%8F%E6%B5%8E%E8%B4%A3%E4%BB%BB%E5%AE%A1%E8%AE%A1&page=1&size=5"),
    ("GET", "https://www.ncpssd.cn/search?keyword=%E7%BB%8F%E6%B5%8E%E8%B4%A3%E4%BB%BB%E5%AE%A1%E8%AE%A1"),
    ("POST", "https://www.ncpssd.cn/api/search", {"keyword": "经济责任审计", "pageNo": 1, "pageSize": 5}),
    ("GET", "https://www.ncpssd.cn/literature/search?keyword=%E7%BB%8F%E6%B5%8E%E8%B4%A3%E4%BB%BB%E5%AE%A1%E8%AE%A1"),
]

for method, url, *rest in endpoints + []:
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        else:
            data = rest[0] if rest else None
            resp = requests.post(url, json=data, headers=headers, timeout=15)
        
        print(f"\n{'='*60}")
        print(f"{method} {url[:80]}...")
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type', 'Unknown')}")
        
        # 尝试解析为 JSON
        try:
            data = resp.json()
            print(f"JSON keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
            if isinstance(data, dict) and 'data' in data:
                items = data['data'] if isinstance(data['data'], list) else data['data'].get('records', [])
                print(f"Found {len(items)} items")
                for i, item in enumerate(items[:3]):
                    title = item.get('title', item.get('name', str(item)[:100]))
                    print(f"  [{i}] {title}")
        except:
            # 不是 JSON，看文本
            text = resp.text[:1000]
            if '<html' in text.lower():
                # 提取标题
                titles = re.findall(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)', text)
                if not titles:
                    titles = re.findall(r'title="([^"]{10,})"', text)
                print(f"HTML, found {len(titles)} titles")
                for t in titles[:5]:
                    print(f"  - {t.strip()}")
            else:
                print(f"Text: {text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(1)