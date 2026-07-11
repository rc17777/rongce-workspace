import requests, re, html, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('url', nargs='?', default='https://mp.weixin.qq.com/s/HpHh5bpELcpEqmLtDsoQNg')
args = parser.parse_args()

r = requests.get(args.url, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=30)

# Get title - try multiple patterns
title = None
for pat in [
    r'var\s+msg_title\s*=\s*[\'"](.+?)[\'"]',
    r'property="og:title"\s+content="(.+?)"',
    r'<title>(.+?)</title>',
    r'var\s+msg_title\s*=\s*htmlDecode\("(.+?)"\)',
]:
    m = re.search(pat, r.text)
    if m:
        title = html.unescape(m.group(1))
        break

print(f'标题: {title}')
print('='*60)

# Extract js_content - try multiple ending patterns
content = None
for end_pat in [
    r'</div>\s*<script\s+nonce=',
    r'</div>\s*</div>\s*<script',
    r'</div>\s*<div\s+id="js_pc_qr_code"',
    r'</div>\s*<div\s+class="rich_media_area_extra"',
]:
    content = re.search(r'id="js_content"[^>]*>(.+?)' + end_pat, r.text, re.DOTALL)
    if content:
        break

if content:
    raw = content.group(1)
    # Basic cleaning
    raw = re.sub(r'<br\s*/?>', '\n', raw)
    raw = re.sub(r'<p[^>]*>', '\n', raw)
    raw = re.sub(r'</p>', '', raw)
    raw = re.sub(r'<section[^>]*>', '\n', raw)
    raw = re.sub(r'</section>', '\n', raw)
    raw = re.sub(r'<[^>]+>', '', raw)
    raw = re.sub(r'&nbsp;', ' ', raw)
    raw = html.unescape(raw)
    raw = re.sub(r'[ \t]+', ' ', raw)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    raw = raw.strip()
    print(raw[:30000])
else:
    print("未能提取js_content")
    # Fallback: try to get content from og:description or snippet
    m = re.search(r'name="description"\s+content="(.+?)"', r.text)
    if m:
        print('描述:', m.group(1)[:2000])
