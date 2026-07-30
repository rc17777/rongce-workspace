import re, os, html as html_mod, sys

for i, name in [(1, 'wechat_article_1.html'), (2, 'wechat_article_2.html')]:
    path = os.environ['TEMP'] + '\\' + name
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title
    title_m = re.search(r'var\s+msg_title\s*=\s*"(.+?)"', content)
    title = html_mod.unescape(title_m.group(1)) if title_m else 'N/A'
    
    # Extract description  
    desc_m = re.search(r'var\s+msg_desc\s*=\s*"(.+?)"', content)
    desc = html_mod.unescape(desc_m.group(1)) if desc_m else 'N/A'
    
    # Extract author/source
    author_m = re.search(r'var\s+nickname\s*=\s*"(.+?)"', content)
    author = html_mod.unescape(author_m.group(1)) if author_m else 'N/A'
    
    print(f'=== ARTICLE {i} ===')
    print(f'Title: {title}')
    print(f'Author: {author}')
    print(f'Desc: {desc}')
    
    # Extract js_content
    content_m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', content, re.DOTALL)
    if not content_m:
        content_m = re.search(r'id="js_content"[^>]*>(.*?)</div>', content, re.DOTALL)
    
    if content_m:
        text = content_m.group(1)
        # Remove HTML tags but keep structure
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<p[^>]*>', '\n', text)
        text = re.sub(r'</p>', '\n', text)
        text = re.sub(r'</?section[^>]*>', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = html_mod.unescape(text)
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        print(f'Content ({len(text)} chars):')
        print(text[:5000])
        if len(text) > 5000:
            print(f'\n... [truncated, total {len(text)} chars]')
    
    print()
