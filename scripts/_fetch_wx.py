import urllib.request, re, html as hlib, sys

url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/kDQDk_9y9hZF4dMF3m4RIg'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8')

m = re.search(r'var msg_title\s*=\s*"(.*?)"', html)
title = m.group(1) if m else 'N/A'
m = re.search(r'var msg_desc\s*=\s*"(.*?)"', html)
desc = m.group(1) if m else 'N/A'

m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
content = m.group(1) if m else 'NOT FOUND'
content = hlib.unescape(content)
content = re.sub(r'<br\s*/?>', '\n', content)
content = re.sub(r'<p[^>]*>', '\n', content)
content = re.sub(r'</p>', '', content)
content = re.sub(r'<section[^>]*>', '', content)
content = re.sub(r'</section>', '', content)
content = re.sub(r'<span[^>]*>', '', content)
content = re.sub(r'</span>', '', content)
content = re.sub(r'<strong[^>]*>', '**', content)
content = re.sub(r'</strong>', '**', content)
content = re.sub(r'<em[^>]*>', '*', content)
content = re.sub(r'</em>', '*', content)
content = re.sub(r'<[^>]+>', '', content)
content = re.sub(r'\n{3,}', '\n\n', content)
content = content.strip()

print(f'TITLE: {title}')
print(f'DESC: {desc}')
print(f'---CONTENT---')
print(content[:10000])
