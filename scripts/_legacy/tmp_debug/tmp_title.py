# -*- coding: utf-8 -*-
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://mp.weixin.qq.com/s/kk3VIS4FB6UYlshkN1zJkg'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.get(url, headers=headers, timeout=15)
r.encoding = r.apparent_encoding
html = r.text

print("ENCODING:", r.apparent_encoding)
print("HAS msg_title:", 'msg_title' in html)

# Search for title with different patterns
for pattern in [
    r'var msg_title = "([^"]*)"',
    r"var msg_title = '([^']*)'",
    r'msg_title\s*=\s*"([^"]*)"',
    r'<title>([^<]*)</title>',
]:
    m = re.search(pattern, html)
    if m:
        print(f"MATCH: {m.group(1)}")
        break

# Also try nickname/source
for pattern in [
    r'var nickname = "([^"]*)"',
    r"var nickname = '([^']*)'",
    r'id="js_name">([^<]*)<',
    r'js_name[^>]*>([^<]*)<',
]:
    m = re.search(pattern, html)
    if m:
        print(f"SOURCE: {m.group(1)}")
        break
