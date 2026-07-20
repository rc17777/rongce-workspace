# -*- coding: utf-8 -*-
"""Fetch WeChat articles with mobile User-Agent and extract content."""
import urllib.request
import re
import json
import os
import sys
import socket

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    'https://mp.weixin.qq.com/s/W-_MRS1jegzeav7lRIyTiQ',
    'https://mp.weixin.qq.com/s/YHMRZsauuPWcpEX0VhbB_w',
    'https://mp.weixin.qq.com/s/6db7tfQF9J2L1PdUnzCW_Q',
    'https://mp.weixin.qq.com/s/_Z2C7zOY7tqlZ3MIgeRYkw',
    'https://mp.weixin.qq.com/s/khYxUJa9dOMedCkz10R2ew',
]

UA = ('Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 '
      'MicroMessenger/8.0.47')

outdir = os.path.join('knowledge', 'laws', '_incoming')
os.makedirs(outdir, exist_ok=True)


def strip_html(raw):
    """Strip HTML tags from content."""
    text = re.sub(r'<br\s*/?>', '\n', raw)
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'</p>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def fetch_url(url, timeout=60):
    """Fetch URL with large buffer support."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    # Use a much larger timeout and read in chunks
    socket.setdefaulttimeout(timeout)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        chunks = []
        while True:
            chunk = resp.read(65536)  # 64KB chunks
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks).decode('utf-8', errors='replace')


results = []
for i, url in enumerate(urls):
    print(f'Fetching [{i+1}/5]: {url[:50]}...', file=sys.stderr)
    try:
        html = fetch_url(url, timeout=60)
        print(f'  Got {len(html)} bytes', file=sys.stderr)
    except Exception as e:
        print(f'  ERROR: {e}', file=sys.stderr)
        results.append({
            'index': i + 1, 'url': url,
            'error': str(e), 'title': '', 'len': 0, 'file': ''
        })
        continue

    # Extract title
    title_m = re.search(r'var msg_title\s*=\s*"(.*?)"', html)
    if not title_m:
        title_m = re.search(r'var msg_title\s*=\s*\'(.*?)\'', html)
    title = title_m.group(1) if title_m else '(no title)'

    # Extract description
    desc_m = re.search(r'var msg_desc\s*=\s*"(.*?)"', html)
    if not desc_m:
        desc_m = re.search(r'var msg_desc\s*=\s*\'(.*?)\'', html)
    desc = desc_m.group(1) if desc_m else ''

    # Extract content
    raw = ''
    # Try js_content
    cm = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
    if cm:
        raw = cm.group(1)
    else:
        cm = re.search(r'id="js_content"[^>]*>(.*?)</div>', html, re.DOTALL)
        if cm:
            raw = cm.group(1)
    if not raw:
        cm = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
        if cm:
            raw = cm.group(1)
    if not raw:
        cm = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        if cm:
            raw = cm.group(1)

    text = strip_html(raw) if raw else ''
    print(f'  Title: {title}, Content: {len(text)} chars', file=sys.stderr)

    # Save to file
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:80]
    fname = os.path.join(outdir, f'wx_{i+1:02d}_{safe_title}.md')
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(f'# {title}\n\n')
        f.write(f'> 来源: {url}\n')
        if desc:
            f.write(f'> 摘要: {desc}\n')
        f.write('\n')
        f.write(text)

    results.append({
        'index': i + 1,
        'url': url,
        'title': title,
        'desc': desc,
        'file': fname,
        'len': len(text),
    })

print(json.dumps(results, ensure_ascii=False, indent=2))
