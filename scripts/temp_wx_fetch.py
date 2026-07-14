import requests
import re
import sys
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://mp.weixin.qq.com/s/EIRLPYvwC4nVuEFIKmSAow'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
}
resp = requests.get(url, headers=headers, timeout=15)
resp.encoding = 'utf-8'
html = resp.text

# Extract meta
title_m = re.search(r'var msg_title\s*=\s*"(.*?)"', html)
desc_m = re.search(r'var msg_desc\s*=\s*"(.*?)"', html)
ct_m = re.search(r'var ct\s*=\s*"(.*?)"', html)
print('TITLE:', title_m.group(1) if title_m else 'N/A')
print('DESC:', desc_m.group(1) if desc_m else 'N/A')
print('CT:', ct_m.group(1) if ct_m else 'N/A')

# Extract author
author_m = re.search(r'var nickname_name\s*=\s*"(.*?)"', html)
print('AUTHOR:', author_m.group(1) if author_m else 'N/A')

# Extract content
content_m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if not content_m:
    content_m = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)

if content_m:
    class Stripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
            self.skip = False
        def handle_starttag(self, tag, attrs):
            if tag in ('script','style'):
                self.skip = True
        def handle_endtag(self, tag):
            if tag in ('script','style'):
                self.skip = False
            if tag in ('p','br','div','h1','h2','h3','h4','li','section','tr'):
                self.text.append('\n')
        def handle_data(self, data):
            if not self.skip:
                self.text.append(data)
    s = Stripper()
    s.feed(content_m.group(1))
    text = ''.join(s.text)
    # Clean excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    # Save full text
    with open('scripts/wx_article_temp.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    
    print('---CONTENT (first 8000 chars)---')
    print(text[:8000])
    print('---TOTAL CHARS:', len(text))
else:
    print('CONTENT NOT FOUND')
