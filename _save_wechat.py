import requests, re, os
from html.parser import HTMLParser

url = 'https://mp.weixin.qq.com/s/hcql_HJrsvAB_r_ttKNVLg'
headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'}
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
html = r.text

# WeChat uses single quotes for msg_title
title_m = re.search(r"var msg_title\s*=\s*'(.*?)'", html)
desc_m = re.search(r"var msg_desc\s*=\s*'(.*?)'", html)
title = title_m.group(1) if title_m else 'unknown-title'
desc = desc_m.group(1) if desc_m else ''

# Find js_content div and track nesting
start = html.find('id="js_content"')
tag_start = html.find('>', start) + 1

depth = 1
pos = tag_start
while depth > 0 and pos < len(html):
    next_open = html.find('<div', pos)
    next_close = html.find('</div>', pos)
    if next_close == -1:
        break
    if next_open != -1 and next_open < next_close:
        depth += 1
        pos = next_open + 4
    else:
        depth -= 1
        if depth == 0:
            content_end = next_close
            break
        pos = next_close + 6

raw_content = html[tag_start:content_end]

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    def handle_data(self, d):
        self.text.append(d)
    def get_data(self):
        return ''.join(self.text)

s = MLStripper()
s.feed(raw_content)
text = s.get_data()
text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text).strip()

safe_name = re.sub(r'[\\/:*?"<>|]', '_', title)[:80]
outdir = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\_incoming'
os.makedirs(outdir, exist_ok=True)
path = os.path.join(outdir, f'{safe_name}.md')

md_content = f"""---
title: "{title}"
source: "{url}"
author: "Sanmist / Lab"
date: 2026-07-15
tags: [AI Agent, knowledge-graph, memory, Cognee, RAG, open-source, graph-database]
scene: tech-research
category: ai-tools
status: ingested
---

# {title}

> Source: {url}
> Author: Sanmist / Lab | Ingested: 2026-07-15

{text}
"""

with open(path, 'w', encoding='utf-8') as f:
    f.write(md_content)
print(f'Title: {title}')
print(f'OK: {path}')
print(f'Size: {len(md_content)} chars')

# Remove the old unknown-title.md if it exists
old = os.path.join(outdir, 'unknown-title.md')
if os.path.exists(old):
    os.remove(old)
    print(f'Removed old: {old}')
