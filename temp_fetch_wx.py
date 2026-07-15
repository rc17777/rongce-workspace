import requests
import re
import sys
from html import unescape

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://mp.weixin.qq.com/s/DbZfZbD6WIoD8pL9pxY_BQ'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
}
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
html = r.text

# Extract metadata - try both quote styles
title_m = re.search(r'var msg_title\s*=\s*[\'"](.+?)[\'"]', html)
desc_m = re.search(r'var msg_desc\s*=\s*[\'"](.+?)[\'"]', html)
print('TITLE:', title_m.group(1) if title_m else 'NOT FOUND')
print('DESC:', desc_m.group(1) if desc_m else 'NOT FOUND')
print('---CONTENT---')

# Try to extract rich_media_content
content_m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if not content_m:
    content_m = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
if content_m:
    text = content_m.group(1)
    # Handle <section>, <p>, <span>, <br> etc
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'</section>', '\n', text)
    text = re.sub(r'</div>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove leading/trailing whitespace per line but preserve paragraphs
    lines = [l.strip() for l in text.split('\n')]
    text = '\n'.join(lines)
    # Remove empty line blocks
    text = re.sub(r'\n{3,}', '\n\n', text)
    print(text[:30000])
else:
    print('CONTENT NOT FOUND - saving HTML for debug')
    with open(r'D:\openclaw-workspace\temp_wx_article.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Saved full HTML, length:', len(html))
