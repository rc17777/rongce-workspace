import urllib.request
import urllib.parse
import ssl
import re

ssl._create_default_https_context = ssl._create_unverified_context

query = '青岛 四库四系统 审计 大数据'
url = f'https://www.sogou.com/web?query={urllib.parse.quote(query)}'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    for m in re.finditer(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        href = m.group(1)
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if len(text) > 15 and 'sogou' not in href and 'passport' not in href:
            print(f'TITLE: {text[:120]}')
            print(f'URL: {href}')
            print('---')
except Exception as e:
    print(f'Error: {e}')
