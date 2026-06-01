import urllib.request
import re
import html
import sys

sys.stdout.reconfigure(encoding='utf-8')

article_url = 'https://mp.weixin.qq.com/s/c5J0eUQhTee_yaF4nuT10Q'
api_url = f'https://down.mptext.top/api/public/v1/download?url={article_url}&format=html'

req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r = urllib.request.urlopen(req, timeout=30)
raw = r.read().decode('utf-8')

title_match = re.search(r'id="activity-name"[^>]*>(.*?)</h1>', raw, re.DOTALL)
title = ''
if title_match:
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    title = html.unescape(title)
    print('TITLE:', title)

match = re.search(r'id="js_content"[^>]*>(.*?)(?=<div class="rich_media_tool|<script)', raw, re.DOTALL)
if not match:
    match = re.search(r'id="js_content"[^>]*>(.*?)(?=</div>\s*<div class="ct_mpda_wrp|<script)', raw, re.DOTALL)

if match:
    content = match.group(1)
    content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', lambda m: '\n## ' + m.group(1).strip() + '\n', content, flags=re.DOTALL)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<p[^>]*>', '\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', lambda m: '**' + m.group(1) + '**', content, flags=re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', lambda m: '*' + m.group(1) + '*', content, flags=re.DOTALL)
    content = re.sub(r'<img[^>]+data-src="([^"]+)"[^>]*/?\s*>', lambda m: '\n[图片]\n', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = html.unescape(content)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    content = content.strip()
    
    with open(r'C:\Users\Admin\.openclaw\workspace\temp_article3.txt', 'w', encoding='utf-8') as f:
        f.write(f'TITLE: {title}\n\n{content}')
    
    print(f'Content length: {len(content)} chars')
    print('Saved to temp_article3.txt')
else:
    print('Content div not found')
