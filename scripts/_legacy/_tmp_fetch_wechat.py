# -*- coding: utf-8 -*-
"""Try to extract WeChat article content from raw HTML."""
import sys, re, urllib.request

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://mp.weixin.qq.com/s/bzFVFqV4qTeqX3ljrjN0OA'

try:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='replace')
    
    print(f'HTML size: {len(html)} bytes')
    
    # Look for js_content (WeChat article body)
    idx = html.find('js_content')
    if idx >= 0:
        print(f'Found js_content at offset {idx}')
        # Try to extract the div contents
        start = html.find('>', idx) + 1
        end_tag = '</div>'
        end = html.find(end_tag, start)
        if end > start:
            content = html[start:end]
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', '', content)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 100:
                print(f'EXTRACTED CONTENT ({len(text)} chars):')
                print(text[:3000])
                print('...')
                if len(text) > 3000:
                    print(text[3000:6000])
            else:
                print(f'Content too short ({len(text)} chars): {text[:200]}')
    else:
        print('No js_content found')
    
    # Also look for rich_media_content
    idx2 = html.find('rich_media_content')
    if idx2 >= 0:
        print(f'\nFound rich_media_content at offset {idx2}')
    
    # Try to find title
    import json
    title_match = re.search(r'var\s+msg_title\s*=\s*[\'"]([^\'"]+)[\'"]', html)
    if title_match:
        print(f'\nTitle from var: {title_match.group(1)}')
    
    # Try to find any JSON-embedded content
    json_match = re.search(r'var\s+content\s*=\s*[\'"]([^\'"]{500,})[\'"]', html)
    if json_match:
        raw = json_match.group(1)
        print(f'\nFound var content ({len(raw)} chars)')
        # Try URL decode
        from urllib.parse import unquote
        decoded = unquote(raw)
        print(f'Decoded: {decoded[:500]}')

except Exception as e:
    print(f'Error: {e}')
