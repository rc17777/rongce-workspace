import sys, requests, re, html as htmlmod
sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47'
url = 'https://mp.weixin.qq.com/s/0qOiKvRkYJR5-8O3qCFZKQ'
resp = requests.get(url, headers={'User-Agent': UA}, timeout=120, stream=True)
chunks = []
for chunk in resp.iter_content(chunk_size=65536, decode_unicode=True):
    chunks.append(chunk)
s = ''.join(chunks)
print('FULL_SIZE:', len(s))

for p in [r'var msg_title = htmlDecode\("(.*?)"\)', r'var msg_title = "(.*?)";',
          r'<h1[^>]*id="activity-name"[^>]*>(.*?)</h1>', r'rich_media_title[^>]*>(.*?)</h1>']:
    m = re.search(p, s, re.S)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        print('TITLE:', htmlmod.unescape(t)[:160])
        break
for p in [r'var nickname = htmlDecode\("(.*?)"\)', r'id="js_name"[^>]*>\s*(.*?)\s*<']:
    m = re.search(p, s, re.S)
    if m:
        print('ACCOUNT:', htmlmod.unescape(m.group(1)).strip()[:60])
        break
m = re.search(r'var createTime = ["\'](\d{4}-\d{2}-\d{2})', s) or re.search(r'ct = "(\d{10})"', s)
if m:
    v = m.group(1)
    if v.isdigit():
        import datetime; v = datetime.datetime.fromtimestamp(int(v)).strftime('%Y-%m-%d')
    print('DATE:', v)

m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<script', s, re.S)
if not m:
    m = re.search(r'<div[^>]*class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*</div>\s*<div class="rich_media_tool', s, re.S)
if m:
    body = m.group(1)
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S)
    body = re.sub(r'<br[^>]*>', '\n', body)
    body = re.sub(r'</p>|</section>|</h\d>|</li>', '\n', body)
    body = re.sub(r'<[^>]+>', '', body)
    body = htmlmod.unescape(body)
    body = re.sub(r'\n\s*\n+', '\n\n', body)
    print('BODY_LEN:', len(body.strip()))
    lines = [l.strip() for l in body.strip().split('\n') if l.strip()]
    for l in lines[:50]:
        print(l[:200])
    with open('_wx_article.txt', 'w', encoding='utf-8') as f:
        f.write(body.strip())
else:
    print('BODY: NOT FOUND<br>')