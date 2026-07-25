#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch WeChat article and save to knowledge base."""

import requests
import re
import html
import os
from datetime import datetime

url = 'https://mp.weixin.qq.com/s/56gBkUbjeDssNBhpf41LIw'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47',
}
r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)

# Extract title
title_match = re.search(r'var msg_title\s*=\s*[\'"](.+?)[\'"]\s*;', r.text)
if title_match:
    title = html.unescape(title_match.group(1).strip())
else:
    title = '撰写审计报告应重点关注的10项内容'

# Extract description
desc_match = re.search(r'var msg_desc\s*=\s*[\'"](.+?)[\'"]\s*;', r.text)
desc = html.unescape(desc_match.group(1).strip()) if desc_match else ''

# Extract article content
js_match = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', r.text, re.DOTALL)
if js_match:
    text = js_match.group(1)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = html.unescape(text)
    text = re.sub(r'\n[ \t]*\n', '\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
else:
    text = ''

# Build markdown file
today = datetime.now().strftime('%Y-%m-%d')
md = f"""---
title: "{title}"
source: "广州市内部审计协会"
url: "{url}"
date: "{today}"
tags: [审计报告, 质量控制, 审计复核, 审盾]
scene: [审计报告复核, 审计质量控制]
---

# {title}

> 来源：广州市内部审计协会 | 采集日期：{today}

{text}

---

## 审盾整合建议

本文10项内容可与审盾一期绩效评价报告AI复核检查清单整合：
1. 审计评价恰当性 → 复核清单"评价维度"
2. 问题定性准确性 → 复核清单"定性维度"
3. 事实表述清晰性 → 复核清单"事实维度"
4. 依据引用合理性 → 复核清单"依据维度"
5. 处理处罚合法性 → 复核清单"处理维度"
6. 责任界定科学性 → 复核清单"责任维度"
7. 审计建议操作性 → 复核清单"建议维度"
8. 采纳意见合理性 → 复核清单"采纳维度"
9. 同类问题一致性 → 复核清单"一致维度"
10. 报告格式规范性 → 复核清单"格式维度"
"""

# Save to knowledge base
kb_path = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\audit\审计报告10项重点关注-广州市内部审计协会.md'
os.makedirs(os.path.dirname(kb_path), exist_ok=True)
with open(kb_path, 'w', encoding='utf-8') as f:
    f.write(md)

print(f'SAVED: {kb_path}')
print(f'Title: {title}')
print(f'Content length: {len(text)} chars')