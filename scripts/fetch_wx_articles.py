import requests
import re
import sys
import os

urls = [
    'https://mp.weixin.qq.com/s/3htnluYqU0QieX3rwl3BDQ',
    'https://mp.weixin.qq.com/s/9rsfU9xIuSSCF575MEt-tw',
    'https://mp.weixin.qq.com/s/_rh1vAWS7hC8Eaz0P7-YsQ',
    'https://mp.weixin.qq.com/s/5G3ACSpI4jIVyRG2D5fpuA',
    'https://mp.weixin.qq.com/s/KCf38O40h61MUjy0CTPejg',
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
}

outdir = os.path.expanduser(r'~\.openclaw\workspace\knowledge\taxonomy\wx_articles')
os.makedirs(outdir, exist_ok=True)

for i, url in enumerate(urls):
    filename = os.path.join(outdir, f'article_{i+1}.txt')
    print(f'\n[Article {i+1}] {url}')
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        html = r.text
        
        # Extract title
        m = re.search(r'var msg_title\s*=\s*"(.+?)"', html)
        title = m.group(1) if m else 'Unknown'
        
        # Extract description
        m = re.search(r'var msg_desc\s*=\s*"(.+?)"', html)
        desc = m.group(1) if m else ''
        
        # Extract content
        m = re.search(r'<div class="rich_media_content[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
        if not m:
            m = re.search(r'id="js_content">(.*?)</div>', html, re.DOTALL)
        
        content = ''
        if m:
            content = m.group(1)
            content = re.sub(r'<br\s*/?>', '\n', content)
            content = re.sub(r'</p>', '\n', content)
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'&nbsp;', ' ', content)
            content = re.sub(r'&amp;', '&', content)
            content = re.sub(r'&lt;', '<', content)
            content = re.sub(r'&gt;', '>', content)
            content = re.sub(r'&quot;', '"', content)
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
            content = content.strip()
        
        print(f'Title: {title}')
        print(f'Content: {len(content)} chars')
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f'URL: {url}\n')
            f.write(f'Title: {title}\n')
            f.write(f'Desc: {desc}\n')
            f.write(f'---\n\n')
            f.write(content)
        
        # Print first 2500 chars
        print(content[:2500])
        if len(content) > 2500:
            print(f'\n... [truncated, full text saved to {filename}]')
        
    except Exception as e:
        print(f'ERROR: {e}')
