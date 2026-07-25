"""Fetch WeChat public account article with mobile UA."""
import requests, re, html, sys

url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/VwtWqynnEMJmGDVIYY9omQ'

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'

# Extract title
m = re.search(r'var msg_title\s*=\s*"(.+?)"', r.text)
title = m.group(1) if m else '未找到标题'

# Extract description
m = re.search(r'var msg_desc\s*=\s*"(.+?)"', r.text)
desc = html.unescape(m.group(1)) if m else ''

# Extract content from js_content
m = re.search(r'id="js_content"[^>]*>(.+?)</div>\s*<script', r.text, re.DOTALL)
if m:
    content = m.group(1)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = content.replace('<br/>', '\n').replace('<br>', '\n')
    content = re.sub(r'<section[^>]*>', '\n', content)
    content = re.sub(r'</section>', '\n', content)
    content = re.sub(r'<p[^>]*>', '\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = html.unescape(content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()
else:
    content = '未找到正文内容'

print(f'# {title}')
if desc:
    print(f'> {desc}')
print()
print(content)