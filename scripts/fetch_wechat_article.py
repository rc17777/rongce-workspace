#!/usr/bin/env python3
"""微信文章抓取"""
import urllib.request, re, sys

url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/n9E5QU4EaRy1vL7e3HISHw'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
})
html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')

# 提取元信息
title_match = re.search(r'var msg_title\s*=\s*"(.*?)"', html)
desc_match = re.search(r'var msg_desc\s*=\s*"(.*?)"', html)
title = title_match.group(1) if title_match else '未知标题'
desc = desc_match.group(1) if desc_match else ''

# 提取正文
content_match = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if content_match:
    content = content_match.group(1)
    # 去HTML标签
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'&nbsp;', ' ', content)
    content = re.sub(r'&amp;', '&', content)
    content = re.sub(r'&lt;', '<', content)
    content = re.sub(r'&gt;', '>', content)
    content = re.sub(r'&quot;', '"', content)
    content = re.sub(r"&#39;", "'", content)
    content = re.sub(r'\s+', ' ', content).strip()
else:
    content = '正文提取失败'

print(f'TITLE: {title}')
print(f'DESC: {desc}')
print(f'LEN: {len(content)} chars')
print('---CONTENT---')
print(content[:20000])
if len(content) > 20000:
    print(f'... [截断, 共{len(content)}字]')
