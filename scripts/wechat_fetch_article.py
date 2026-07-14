# -*- coding: utf-8 -*-
import requests, re, html, sys, json

url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/KSIjTUXcC6pGnk95hkuMJA'

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
}
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'

# Title
title_match = re.search(r'var msg_title\s*=\s*"(.*?)"', r.text)
title = title_match.group(1) if title_match else '未知标题'

# Description
desc_match = re.search(r'var msg_desc\s*=\s*"(.*?)"', r.text)
desc = desc_match.group(1) if desc_match else ''

# Author
author_match = re.search(r'var msg_copyright\s*=\s*"(.*?)"', r.text)
author = ''

# 发布日期
date_match = re.search(r'var create_date\s*=\s*"(.*?)"', r.text)
pub_date = date_match.group(1) if date_match else ''

# Content from rich_media_content
content_match = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', r.text, re.DOTALL)
if not content_match:
    content_match = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script', r.text, re.DOTALL)

if content_match:
    raw_content = content_match.group(1)
    raw_content = re.sub(r'<style[^>]*>.*?</style>', '', raw_content, flags=re.DOTALL)
    raw_content = re.sub(r'<script[^>]*>.*?</script>', '', raw_content, flags=re.DOTALL)
    raw_content = re.sub(r'<br\s*/?>', '\n', raw_content)
    raw_content = re.sub(r'<[^>]+>', '', raw_content)
    raw_content = html.unescape(raw_content)
    raw_content = re.sub(r'\n\s*\n\s*\n', '\n\n', raw_content)
    raw_content = raw_content.strip()
else:
    raw_content = '（内容未提取到）'

print(f'标题: {title}')
print(f'作者: {author}')
print(f'发布日期: {pub_date}')
print(f'描述: {desc}')
print()
print('=== 正文 ===')
print(raw_content)
print('=== 正文结束 ===')
print(f'\n正文长度: {len(raw_content)} 字')