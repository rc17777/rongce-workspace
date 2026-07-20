# -*- coding: utf-8 -*-
import re, sys, html, os

sys.stdout.reconfigure(encoding='utf-8')

path = os.path.join(os.environ['TEMP'], 'wx_article.html')
raw = open(path, 'r', encoding='utf-8', errors='ignore').read()

# Title
m = re.search(r"var msg_title = '([^']*)'", raw)
title = m.group(1) if m else ''
m = re.search(r"var msg_desc = '([^']*)'", raw)
desc = m.group(1) if m else ''
m = re.search(r"var nickname = '([^']*)'", raw)
nick = m.group(1) if m else ''
m = re.search(r"var createTime = '([^']*)'", raw)
ctime = m.group(1) if m else ''

print(f"标题: {html.unescape(title)}")
print(f"公众号: {html.unescape(nick)}")
print(f"时间: {ctime}")
print(f"摘要: {html.unescape(desc)}")
print("=" * 60)

# Content
m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<!--', raw, re.S)
if not m:
    m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*)', raw, re.S)
content = m.group(1) if m else ''

# strip tags but keep structure
content = re.sub(r'<script.*?</script>', '', content, flags=re.S)
content = re.sub(r'<style.*?</style>', '', content, flags=re.S)
content = re.sub(r'</(p|section|h[1-6]|li|blockquote|tr)>', '\n', content)
content = re.sub(r'<br[^>]*>', '\n', content)
content = re.sub(r'<[^>]+>', '', content)
content = html.unescape(content)
content = re.sub(r'[ \t\u00a0]+', ' ', content)
content = re.sub(r'\n\s*\n+', '\n\n', content).strip()

print(content[:12000])
print(f"\n\n[正文总长: {len(content)} 字符]")
