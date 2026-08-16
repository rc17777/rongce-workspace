import urllib.request
import urllib.parse
import ssl
import re

ssl._create_default_https_context = ssl._create_unverified_context

queries = [
    '财政部青岛监管局 四库四系统 数智赋能',
    '青岛监管局 "四库" "四系统"',
    '青岛 四库四系统 财政监管',
    '"四库四系统" 财政部 青岛',
    '聚焦数智赋能 建成四库四系统',
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
            if len(text) > 15:
                # Look for relevant results
                keywords = ['四库', '四系统', '青岛', '监管局', '数智', '财政']
                if any(kw in text+href for kw in keywords):
                    if 'sogou' not in href and 'passport' not in href:
                        print(f'  [{text[:100]}]')
                        print(f'  -> {href}')
                        count += 1
                        if count >= 5:
                            break
    except Exception as e:
        print(f'  Error: {e}')
