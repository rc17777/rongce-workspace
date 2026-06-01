import urllib.request, re, html, sys, time
sys.stdout.reconfigure(encoding='utf-8')
url = 'https://down.mptext.top/api/public/v1/download?url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%2Fyt37MGcoSt46-02teb6XgQ&format=html'
# Try multiple times
for attempt in range(3):
    try:
        time.sleep(2)
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        })
        r = urllib.request.urlopen(req, timeout=30)
        raw = r.read().decode('utf-8', errors='replace')
        print(f'Attempt {attempt+1} OK, len={len(raw)}')
        break
    except Exception as e:
        print(f'Attempt {attempt+1} failed: {e}')
        if attempt == 2: sys.exit(1)

t = re.search(r'id="activity-name"[^>]*>(.*?)</h1>', raw, re.DOTALL)
if t: print('TITLE:', re.sub(r'<[^>]+>', '', t.group(1)).strip())
m = re.search(r'id="js_content"[^>]*>(.*?)(?=<div class="rich_media_tool"|<script)', raw, re.DOTALL)
if m:
    c = m.group(1)
    c = re.sub(r'<br\s*/?>', '\n', c)
    c = re.sub(r'<p[^>]*>', '\n', c)
    c = re.sub(r'</p>', '', c)
    c = re.sub(r'<strong[^>]*>(.*?)</strong>', lambda m1: '**' + m1.group(1) + '**', c, flags=re.DOTALL)
    c = re.sub(r'<[^>]+>', '', c)
    c = html.unescape(c)
    c = re.sub(r'\n\s*\n\s*\n+', '\n\n', c).strip()
    with open(r'C:\Users\Admin\.openclaw\workspace\temp_art5.txt', 'w', encoding='utf-8') as f: f.write(c)
    print('OK:', len(c), 'chars')
    print(c[:2000])
else:
    print('Not found')
    i = raw.find('js_content')
    if i > 0: print(repr(raw[i:i+300]))
    else: print('js_content not in HTML')