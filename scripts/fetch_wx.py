import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

r = requests.get(
    'https://mp.weixin.qq.com/s/DZSX7_dG_bpzG7TRh5FpNA',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
    timeout=15
)
html = r.text

# Try to find article content in rich_media_content div
match = re.search(r'<div class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<div class="rich_media_area_extra', html, re.DOTALL)
if match:
    content = match.group(1)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<p[^>]*>', '\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'&nbsp;', ' ', content)
    content = re.sub(r'&lt;', '<', content)
    content = re.sub(r'&gt;', '>', content)
    content = re.sub(r'&amp;', '&', content)
    content = re.sub(r'&quot;', '"', content)
    content = re.sub(r'\n\s*\n', '\n\n', content)
    print(content[:10000])
else:
    title = re.search(r'<title>(.*?)</title>', html)
    print('Title:', title.group(1) if title else 'Not found')
    # Find msg_title, msg_desc in var
    for field in ['msg_title', 'msg_desc', 'msg_cdn_url', 'msg_link', 'nickname']:
        m = re.search(r"var\s+" + field + r"\s*=\s*['\"](.*?)['\"]\s*;", html)
        if m:
            print(f'{field}: {m.group(1)}')
    # Try scripts
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for i, s in enumerate(scripts):
        if 'rich_media_content' in s or 'msg_title' in s:
            print(f'\nScript {i} (len={len(s)}):')
            print(s[:3000])
            break
