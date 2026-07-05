#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取微信文章中的图片"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\openclaw-workspace\temp\wx_article.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

print(f"HTML大小: {len(content)} 字符")

# 提取标题
title_match = re.search(r'<title>(.*?)</title>', content)
if title_match:
    print(f"标题: {title_match.group(1)}")

# 提取所有图片URL
imgs = re.findall(r'data-src="(https?://[^"]+)"', content)
print(f"找到 {len(imgs)} 张图片:")
for i, url in enumerate(imgs[:10]):
    # 微信图片URL通常很长, 截取
    short = url[:80]
    print(f"  [{i+1}] {short}...")
    print(f"      后缀: {url.split('.')[-1].split('?')[0]}")

# 尝试下载前几张图片到本地
import urllib.request
import os

os.makedirs(r'D:\openclaw-workspace\temp\wx_images', exist_ok=True)
for i, url in enumerate(imgs[:5]):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=10).read()
        ext = url.split('.')[-1].split('?')[0]
        if ext not in ['jpg','jpeg','png','gif','webp']:
            ext = 'jpg'
        fp = rf'D:\openclaw-workspace\temp\wx_images\img_{i+1}.{ext}'
        with open(fp, 'wb') as f:
            f.write(data)
        print(f"  ✅ 下载: {fp} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"  ❌ 图片{i+1}下载失败: {e}")

# 提取文章正文
print(f"\n{'='*50}")
print("文章正文:")
idx = content.find('js_content')
if idx > 0:
    # 找最近的div
    div_start = content.find('<section', idx)
    if div_start < 0 or div_start - idx > 500:
        div_start = content.find('<div', idx)
    div_end = content.find('</div>', div_start)
    if div_start > 0 and div_end > 0:
        body = content[div_start:div_end+6]
        # 简化HTML
        text = re.sub(r'<[^>]+>', '\n', body)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        print(text[:2000])
