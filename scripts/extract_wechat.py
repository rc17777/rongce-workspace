#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract WeChat article content from saved HTML."""

import re
import html
import sys
import os

html_path = os.path.expandvars(r'%TEMP%\wechat_article.html')

with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

print(f'Total HTML: {len(content)} bytes', file=sys.stderr)

# Try js_content
js_match = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', content, re.DOTALL)
if js_match and len(js_match.group(1)) > 100:
    text = js_match.group(1)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = html.unescape(text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    print(f'js_content: {len(text)} chars', file=sys.stderr)
    print(text)
    sys.exit(0)

# Try rich_media_content
rich_match = re.search(r'class="rich_media_content"[^>]*>(.*?)</div>\s*<script', content, re.DOTALL)
if rich_match:
    text = rich_match.group(1)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = html.unescape(text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    print(f'rich_media_content: {len(text)} chars', file=sys.stderr)
    print(text)
    sys.exit(0)

# Try to find any content div
print('NO CONTENT FOUND', file=sys.stderr)
# Print first 2000 chars of HTML for debugging
print(content[:2000], file=sys.stderr)