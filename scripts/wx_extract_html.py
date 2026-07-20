# -*- coding: utf-8 -*-
"""Extract WeChat article content from downloaded HTML files."""
import re, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

files = [
    ('knowledge/laws/_incoming/wx_01_raw.html', 'https://mp.weixin.qq.com/s/W-_MRS1jegzeav7lRIyTiQ', 1),
    ('knowledge/laws/_incoming/wx_02_raw.html', 'https://mp.weixin.qq.com/s/YHMRZsauuPWcpEX0VhbB_w', 2),
]

results = []
for fpath, url, idx in files:
    if not os.path.exists(fpath):
        results.append({'index': idx, 'error': 'file missing', 'title': '', 'len': 0})
        continue
    size = os.path.getsize(fpath)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    print(f'  [{idx}] {fpath}: {len(html)} bytes from {size} file', file=sys.stderr)

    # Title
    tm = re.search(r'var msg_title\s*=\s*"(.*?)"', html)
    if not tm:
        tm = re.search(r"var msg_title\s*=\s*'(.*?)'", html)
    title = tm.group(1) if tm else '(no title)'

    # Also try <title> tag
    if title == '(no title)':
        tm2 = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if tm2:
            title = tm2.group(1).strip()

    # Content
    raw = ''
    for pattern in [
        r'id="js_content"[^>]*>(.*?)</div>\s*<script',
        r'id="js_content"[^>]*>(.*?)</div>',
        r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script',
        r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>',
    ]:
        cm = re.search(pattern, html, re.DOTALL)
        if cm:
            raw = cm.group(1)
            break

    text = re.sub(r'<br\s*/?>', '\n', raw)
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'</p>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\u00a0', ' ').replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:80]
    out = f'knowledge/laws/_incoming/wx_{idx:02d}_{safe_title}.md'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(f'# {title}\n\n')
        f.write(f'> 来源: {url}\n\n')
        f.write(text)

    results.append({'index': idx, 'title': title, 'file': out, 'len': len(text)})
    print(f'    Title: {title}, Content: {len(text)} chars', file=sys.stderr)

print(json.dumps(results, ensure_ascii=False, indent=2))
