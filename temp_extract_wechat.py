import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Users/scrccpa/.openclaw/workspace/temp_wechat_article.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract metadata
title_m = re.search(r'var msg_title\s*=\s*"(.*?)"', html)
desc_m = re.search(r'var msg_desc\s*=\s*"(.*?)"', html)
author_m = re.search(r'var nickname\s*=\s*"(.*?)"', html)

title = title_m.group(1) if title_m else 'Unknown'
desc = desc_m.group(1) if desc_m else ''
author = author_m.group(1) if author_m else 'Unknown'

print(f'Title: {title}')
print(f'Author: {author}')
print(f'Desc: {desc}')
print('='*60)

# Extract content
content_m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if not content_m:
    content_m = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)

if content_m:
    content = content_m.group(1)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<p[^>]*>', '\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<section[^>]*>', '', content)
    content = re.sub(r'</section>', '', content)
    content = re.sub(r'<span[^>]*>', '', content)
    content = re.sub(r'</span>', '', content)
    content = re.sub(r'<strong>', '**', content)
    content = re.sub(r'</strong>', '**', content)
    content = re.sub(r'<em>', '*', content)
    content = re.sub(r'</em>', '*', content)
    content = re.sub(r'<img[^>]*?data-src="([^"]+)"[^>]*?>', r'\n[IMG: \1]\n', content)
    content = re.sub(r'<img[^>]*?src="([^"]+)"[^>]*?>', r'\n[IMG: \1]\n', content)
    content = re.sub(r'<blockquote[^>]*?>', '\n> ', content)
    content = re.sub(r'</blockquote>', '\n', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'&nbsp;', ' ', content)
    content = re.sub(r'&amp;', '&', content)
    content = re.sub(r'&lt;', '<', content)
    content = re.sub(r'&gt;', '>', content)
    content = re.sub(r'&quot;', '"', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()
    
    # Save clean version
    with open('C:/Users/scrccpa/.openclaw/workspace/temp_wechat_article.txt', 'w', encoding='utf-8') as out:
        out.write(f'# {title}\n\n')
        out.write(f'**来源**: {author}\n\n')
        out.write(content)
    
    print(content[:6000])
else:
    print('Content not found')
