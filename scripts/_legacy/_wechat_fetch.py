import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/0wDBqHo2uWFvAaR2L0Hv0Q'

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
}
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
html = r.text

# Extract metadata
title_m = re.search(r'var msg_title\s*=\s*"(.+?)"', html)
if not title_m:
    title_m = re.search(r"var msg_title\s*=\s*'(.+?)'", html)

desc_m = re.search(r'var msg_desc\s*=\s*"(.*?)"', html, re.DOTALL)
if not desc_m:
    desc_m = re.search(r"var msg_desc\s*=\s*'(.*?)'", html, re.DOTALL)

author_m = re.search(r'var nickname\s*=\s*"(.+?)"', html)
if not author_m:
    author_m = re.search(r"var nickname\s*=\s*'(.+?)'", html)

title = title_m.group(1) if title_m else '(not found)'
desc = desc_m.group(1) if desc_m else ''
author = author_m.group(1) if author_m else ''

# HTML entity decode
import html as htmlmod
title = htmlmod.unescape(title)
desc = htmlmod.unescape(desc)
author = htmlmod.unescape(author)

print(f'title: {title}')
print(f'author: {author}')
print(f'===CONTENT_START===')

# Extract content
content_m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if not content_m:
    content_m = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)

if content_m:
    content = content_m.group(1)
    # Strip HTML tags
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<p[^>]*>', '', content)
    content = re.sub(r'</p>', '\n', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = htmlmod.unescape(content)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    content = content.strip()
    print(content)
else:
    print('ERROR: content not found')
    print(f'HTML length: {len(html)}')
    # try to find any div with rich_media
    for m in re.finditer(r'<div[^>]*class="[^"]*rich_media[^"]*"[^>]*>', html):
        print(f'Found div: {m.group()[:200]}')
