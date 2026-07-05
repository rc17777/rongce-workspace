import urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://mp.weixin.qq.com/s/PEc6d-5LaLlAkClGfQvCYg'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})
html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
print(f"HTML size: {len(html)} bytes")

# Extract content between id="js_content" and the next major </div>
m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if m:
    from html import unescape
    content = m.group(1)
    clean = re.sub(r'<[^>]+>', '\n', content)
    clean = unescape(clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'[ \t]+', ' ', clean)
    
    outpath = 'output/wechat_article_python_audit.txt'
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(clean)
    print(f"Saved {len(clean)} chars to {outpath}")
    print(f"=== First 200 chars ===")
    print(clean[:200])
else:
    print("js_content not found with regex")
    # fallback
    idx = html.find('js_content')
    if idx > -1:
        chunk = html[idx:idx+500]
        print(f"js_content area: {chunk[:300]}")
