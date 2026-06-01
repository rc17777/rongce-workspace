import urllib.request, sys, re
sys.stdout.reconfigure(encoding='utf-8')
url = 'https://down.mptext.top/api/public/v1/download?url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%2FAXrQsJSVeR-Q9-PaHts5uA&format=html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req, timeout=30)
raw = r.read().decode('utf-8', errors='replace')
print('LEN:', len(raw))
t = re.search('"msg_title"\s*:\s*"(.*?)"', raw)
if t: print('TITLE:', t.group(1))
idx = raw.find('js_content')
print('js_content at:', idx)
if idx < 0:
    with open(r'C:\Users\Admin\.openclaw\workspace\_debug_raw.txt', 'w', encoding='utf-8') as f:
        f.write(raw[:20000])
    print('Saved debug')