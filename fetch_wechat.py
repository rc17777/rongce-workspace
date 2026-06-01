import urllib.request
import re
import html

url = 'https://down.mptext.top/api/public/v1/download?url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%2FCIw8rUtqmGtJRTXRgWi0ng&format=html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r = urllib.request.urlopen(req, timeout=30)
raw = r.read().decode('utf-8')

# Extract title
title_match = re.search(r'id="activity-name"[^>]*>(.*?)</h1>', raw, re.DOTALL)
title = ''
if title_match:
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    title = html.unescape(title)
    print(f'TITLE: {title}\n')

# Extract content from js_content div
match = re.search(r'id="js_content"[^>]*>(.*?)(?=<div class="rich_media_tool|<script)', raw, re.DOTALL)
if match:
    content = match.group(1)
    # Convert section headers
    content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n## \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<p[^>]*>', '\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
    content = re.sub(r'<img[^>]+data-src="([^"]+)"[^>]*/?\s*>', r'\n[图片: \1]\n', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = html.unescape(content)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    content = content.strip()
    
    with open(r'C:\Users\Admin\.openclaw\workspace\temp_article.txt', 'w', encoding='utf-8') as f:
        f.write(f'TITLE: {title}\n\n{content}')
    
    print(f'Content length: {len(content)} chars')
    print(f'Saved to temp_article.txt')
    print('\n--- PREVIEW (first 3000 chars) ---\n')
    print(content[:3000])
else:
    print('Could not find js_content div')
    # Find content area
    idx = raw.find('js_content')
    print(f'js_content at position: {idx}')
    if idx > 0:
        print(repr(raw[idx:idx+200]))
