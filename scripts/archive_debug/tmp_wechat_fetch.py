import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
url = 'https://mp.weixin.qq.com/s/5Hwn3et9k-XtEATC-SDR6A'
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'

# Extract title
title_m = re.search(r'<title>(.*?)</title>', r.text)
title = title_m.group(1) if title_m else 'unknown'
print(f'TITLE: {title}')

# Extract author and date
author_m = re.search(r'var nickname\s*=\s*"(.*?)"', r.text)
date_m = re.search(r'var publish_time\s*=\s*"(.*?)"', r.text)
if author_m:
    print(f'AUTHOR: {author_m.group(1)}')
if date_m:
    print(f'DATE: {date_m.group(1)}')

# Extract js_content
if 'js_content' in r.text:
    content_m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', r.text, re.DOTALL)
    if content_m:
        text = content_m.group(1)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        # Save to file
        outpath = r'C:\Users\scrccpa\.openclaw\workspace\tmp_wechat_article.txt'
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(f'TITLE: {title}\n')
            if author_m:
                f.write(f'AUTHOR: {author_m.group(1)}\n')
            if date_m:
                f.write(f'DATE: {date_m.group(1)}\n')
            f.write(f'---\n\n')
            f.write(text)
        print(f'Saved to {outpath}')
        print(f'Length: {len(text)} chars')
        print(f'\nFirst 3000 chars:\n{text[:3000]}')
    else:
        print('js_content found but regex did not match')
else:
    print('js_content NOT found in page')
    # Check for alternative content patterns
    print(f'Page length: {len(r.text)}')
    # Look for rich_media_content
    if 'rich_media_content' in r.text:
        print('rich_media_content found')
    if 'js_article' in r.text:
        print('js_article found')
