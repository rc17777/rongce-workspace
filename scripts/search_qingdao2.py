import urllib.request
import urllib.parse
import ssl
import re

ssl._create_default_https_context = ssl._create_unverified_context

# Search multiple queries
queries = [
    '青岛市审计局 四库四系统 大数据审计平台 建设',
    '青岛 "四库四系统" site:gov.cn',
    '青岛 审计 "四库" "四系统"',
    '青岛市审计局 大数据 平台 法规库 项目库',
]

for query in queries:
    print(f'\n=== SEARCH: {query} ===')
    url = f'https://www.sogou.com/web?query={urllib.parse.quote(query)}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
        count = 0
        for m in re.finditer(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
            href = m.group(1)
            text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            # Filter for relevant-looking results
            if len(text) > 15 and any(kw in text+href for kw in ['审计', '青岛', '四库', '大数据']):
                if 'sogou' not in href and 'passport' not in href:
                    print(f'  [{text[:80]}]')
                    print(f'  -> {href}')
                    count += 1
                    if count >= 5:
                        break
    except Exception as e:
        print(f'  Error: {e}')
