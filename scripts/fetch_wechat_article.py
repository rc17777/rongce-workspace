import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/uyfAK9omqxwWoU92e1EACw'
out = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\scrccpa\.openclaw\workspace\temp_wechat_article.txt'

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
})

with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8')

# Extract title
m = re.search(r'var msg_title\s*=\s*"(.*?)"', html, re.DOTALL)
title = m.group(1) if m else 'N/A'

# Extract description
m = re.search(r'var msg_desc\s*=\s*"(.*?)"', html, re.DOTALL)
desc = m.group(1) if m else 'N/A'

# Extract author
m = re.search(r'var nickname\s*=\s*"(.*?)"', html, re.DOTALL)
author = m.group(1) if m else 'N/A'

# Extract content from js_content div
m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if not m:
    # fallback: try rich_media_content
    m = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)

content_raw = m.group(1) if m else 'NOT FOUND'

# Clean HTML tags but preserve structure
content = content_raw
content = re.sub(r'<p[^>]*>', '\n', content)
content = re.sub(r'<br\s*/?>', '\n', content)
content = re.sub(r'<[^>]+>', '', content)
content = re.sub(r'&nbsp;', ' ', content)
content = re.sub(r'&lt;', '<', content)
content = re.sub(r'&gt;', '>', content)
content = re.sub(r'&amp;', '&', content)
content = re.sub(r'&quot;', '"', content)
content = re.sub(r'&#39;', "'", content)
content = re.sub(r'\n{3,}', '\n\n', content)
content = content.strip()

with open(out, 'w', encoding='utf-8') as f:
    f.write(f'标题: {title}\n')
    f.write(f'作者: {author}\n')
    f.write(f'描述: {desc}\n')
    f.write(f'---\n\n')
    f.write(content)

print(f'Title: {title}')
print(f'Author: {author}')
print(f'Content length: {len(content)} chars')
print(f'Saved to: {out}')
