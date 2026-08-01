#!/usr/bin/env python3
"""Fetch WeChat MP article with mobile UA and extract content + images."""
import sys
import re
import json
import os
import urllib.request
import urllib.parse
from html import unescape

sys.stdout.reconfigure(encoding='utf-8')

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/xuKkXxOAA7uo8ozUdK79kw'
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\scrccpa\.openclaw\workspace\wechat_articles\agent_optimization_20260801'

os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
}
req = urllib.request.Request(URL, headers=headers)
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode('utf-8')

# Extract metadata
title_m = re.search(r'var msg_title\s*=\s*[\'"](.*?)[\'"]', html)
desc_m = re.search(r'var msg_desc\s*=\s*[\'"](.*?)[\'"]', html)
author_m = re.search(r'var nickname\s*=\s*[\'"](.*?)[\'"]', html)
ctime_m = re.search(r'var ct\s*=\s*[\'"](.*?)[\'"]', html)

title = unescape(title_m.group(1)) if title_m else '未知标题'
desc = unescape(desc_m.group(1)) if desc_m else ''
author = unescape(author_m.group(1)) if author_m else '未知作者'
ctime = ctime_m.group(1) if ctime_m else ''

print(f'标题: {title}')
print(f'作者: {author}')
print(f'描述: {desc}')
print(f'时间戳: {ctime}')

# Extract article content from rich_media_content div
content_match = re.search(r'<div[^>]*class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<div[^>]*class="rich_media_area_extra', html, re.DOTALL)
if not content_match:
    content_match = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<div[^>]*class="rich_media_area_extra', html, re.DOTALL)
if not content_match:
    content_match = re.search(r'<div[^>]*class="rich_media_content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)

if not content_match:
    print('ERROR: Could not find article content div')
    sys.exit(1)

raw_content = content_match.group(1)

# Extract all image URLs
img_pattern = re.compile(r'<img[^>]+data-src="([^"]+)"', re.IGNORECASE)
img_urls = img_pattern.findall(raw_content)
# Also check src attribute
img_pattern2 = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)
img_urls2 = img_pattern2.findall(raw_content)
all_img_urls = list(set(img_urls + img_urls2))
print(f'\n发现 {len(all_img_urls)} 张图片')

# Download images
img_dir = os.path.join(OUT_DIR, 'images')
os.makedirs(img_dir, exist_ok=True)
downloaded = []
for i, img_url in enumerate(all_img_urls):
    if img_url.startswith('//'):
        img_url = 'https:' + img_url
    if 'mmbiz.qpic.cn' in img_url or 'mmbiz_jpg' in img_url or 'mmbiz_png' in img_url:
        try:
            img_name = f'img_{i+1:03d}.{img_url.split(".")[-1].split("?")[0] if "." in img_url.split("?")[0] else "jpg"}'
            # Try wx_fmt=jpeg
            fmt_match = re.search(r'wx_fmt=(\w+)', img_url)
            if fmt_match:
                fmt = fmt_match.group(1)
                if fmt == 'jpeg':
                    fmt = 'jpg'
                img_name = f'img_{i+1:03d}.{fmt}'
            
            img_path = os.path.join(img_dir, img_name)
            if 'wx_fmt=jpeg' in img_url or True:  # always try to download
                req2 = urllib.request.Request(img_url, headers={'User-Agent': headers['User-Agent'], 'Referer': URL})
                img_data = urllib.request.urlopen(req2, timeout=15).read()
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                print(f'  [{i+1}/{len(all_img_urls)}] 已下载: {img_name} ({len(img_data)} bytes)')
                downloaded.append(img_name)
        except Exception as e:
            print(f'  [{i+1}/{len(all_img_urls)}] 下载失败: {e}')

# Strip HTML tags for text content
def strip_tags(html_text):
    # Replace common block tags with newlines
    for tag in ['</p>', '</div>', '</section>', '<br/>', '<br />', '<br>', '</h1>', '</h2>', '</h3>', '</h4>', '</h5>', '</h6>', '</li>', '</tr>']:
        html_text = html_text.replace(tag, '\n')
    # Remove all remaining HTML tags
    clean = re.sub(r'<[^>]+>', '', html_text)
    # Decode HTML entities
    clean = unescape(clean)
    # Remove empty lines and collapse whitespace
    lines = [line.strip() for line in clean.split('\n')]
    lines = [line for line in lines if line]
    return '\n'.join(lines)

clean_content = strip_tags(raw_content)

# Save markdown
md_path = os.path.join(OUT_DIR, 'article.md')
md_content = f"""# {title}

**来源**: {author}  
**原文链接**: {URL}  
**爬取时间**: 2026-08-01

---

{clean_content}

---

## 图片列表

共 {len(downloaded)} 张图片已下载至 `images/` 目录：

"""
for img in downloaded:
    md_content += f'- ![](images/{img})\n'

with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

print(f'\n✅ 文章保存至: {md_path}')
print(f'✅ 图片保存至: {img_dir} ({len(downloaded)} 张)')
print(f'✅ 正文长度: {len(clean_content)} 字符')
