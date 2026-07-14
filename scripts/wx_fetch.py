import urllib.request
import re
import html as html_mod
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://mp.weixin.qq.com/s/MVXHToWtNVT_b68zxr7fSA'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})
resp = urllib.request.urlopen(req, timeout=15)
html = resp.read().decode('utf-8')

# Extract title
title_m = re.search(r'<title>(.+?)</title>', html)
title = title_m.group(1).strip() if title_m else 'No title'
print(f'Title: {title}')

# Extract msg metadata
for key in ['msg_title', 'msg_desc', 'msg_cdn_url', 'msg_source_url']:
    m = re.search(r'var ' + key + r'\s*=\s*"(.+?)"', html)
    if m:
        print(f'{key}: {m.group(1)}')

# Extract article content
content_m = re.search(r'id="js_content"[^>]*>(.+?)</div>\s*<script', html, re.DOTALL)
if content_m:
    text = content_m.group(1)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = html_mod.unescape(text)
    text = text.strip()
    print(f'\n--- ARTICLE ({len(text)} chars) ---')
    print(text[:6000])
else:
    print('\nFailed to extract content')
    # Save HTML for debugging
    with open(r'C:\Users\scrccpa\AppData\Local\Temp\wx_debug.html', 'w', encoding='utf-8') as f:
        f.write(html[:50000])
    print('Saved HTML to %TEMP%\\wx_debug.html')
