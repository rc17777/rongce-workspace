"""Check the structure of WeChat MP article HTML."""
import urllib.request
import re

url = 'https://mp.weixin.qq.com/s?__biz=MzI1NTA5NDA2MA==&mid=2648442758&idx=1&sn=34f9167ecf58f850016e5f30c4a24236'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
})
resp = urllib.request.urlopen(req, timeout=15)
html = resp.read().decode('utf-8', errors='ignore')
print(f'HTML length: {len(html)}')
print(f'js_content present: {"js_content" in html}')
print(f'rich_media_content present: {"rich_media_content" in html}')
print(f'Script tags: {html.count("<script")}')

# Check for content in various divs
for div_id in ['js_content', 'js_article', 'img-content', 'rich_media_content']:
    m = re.search(rf'id="{div_id}"[^>]*>', html)
    if m:
        # Find the matching end
        start = m.end()
        # Simple approach - grab next 500 chars
        print(f'\n--- {div_id} found at {m.start()}, next 300 chars:')
        print(html[start:start+300])
        print('...')

# Check for common patterns
patterns = ['var msg_title', 'var msg_desc', 'var msg_cdn_url', 'ct=var', 'nickname']
for p in patterns:
    idx = html.find(p)
    if idx >= 0:
        print(f'\n--- {p} found at {idx}')
        print(html[idx:idx+200])
