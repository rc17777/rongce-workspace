import urllib.request, ssl, re, html, sys
sys.stdout.reconfigure(encoding='utf-8')
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://down.mptext.top/api/public/v1/download?url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%2FAXrQsJSVeR-Q9-PaHts5uA&format=html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req, timeout=30, context=ctx)
raw = r.read().decode('utf-8', errors='replace')
t = re.search(r'id="activity-name"[^>]*>(.*?)</h1>', raw, re.DOTALL)
if t: print('TITLE:', re.sub(r'<[^>]+>', '', t.group(1)).strip())
m = re.search(r'id="js_content"[^>]*>(.*?)(?=<div class="rich_media_tool"|<script)', raw, re.DOTALL)
if m:
    c = m.group(1)
    c = re.sub(r'<br\s*/?>', '\n', c)
    c = re.sub(r'<p[^>]*>', '\n', c)
    c = re.sub(r'</p>', '', c)
    c = re.sub(r'<strong[^>]*>(.*?)</strong>', lambda m: '**' + m.group(1) + '**', c, flags=re.DOTALL)
    c = re.sub(r'<[^>]+>', '', c)
    c = html.unescape(c)
    c = re.sub(r'\n\s*\n\s*\n+', '\n\n', c).strip()
    with open(r'C:\Users\Admin\.openclaw\workspace\temp_article4.txt', 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK:', len(c), 'chars')
    print(c[:2000])
else:
    print('Not found')
    i = raw.find('js_content')
    print('at', i, repr(raw[i:i+300]))
