import urllib.request
import urllib.parse
import ssl
import re

ssl._create_default_https_context = ssl._create_unverified_context

# Search for the full article title on non-WeChat platforms
queries = [
    '聚焦数智赋能建成四库四系统实现核心业务数字化转型',
    '财政部青岛监管局 四库 法规库 项目库 指标库 方法库',
    '青岛监管局 数字化转型 四库 四系统',
    '财政部青岛监管局 大数据 平台 数据库 系统建设',
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
                if 'sogou' not in href and 'passport' not in href and 'mp.weixin.qq.com' not in href:
                    keywords = ['四库', '四系统', '青岛', '监管局', '数智', '财政', '数字化']
                    if any(kw in text+href for kw in keywords):
                        print(f'  [{text[:100]}]')
                        print(f'  -> {href}')
                        count += 1
                        if count >= 3:
                            break
    except Exception as e:
        print(f'  Error: {e}')
