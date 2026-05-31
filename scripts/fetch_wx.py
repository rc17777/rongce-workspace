import requests, re, sys

url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/h4tKxobmuvsi8VX3QP2XfA'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.get(url, headers=headers, timeout=15)

m = re.search(r'id="js_content"[^>]*>(.*?)</div>', r.text, re.DOTALL)
if m:
    content = m.group(1)
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'&nbsp;', ' ', content)
    content = re.sub(r'&amp;', '&', content)
    content = re.sub(r'&lt;', '<', content)
    content = re.sub(r'&gt;', '>', content)
    content = re.sub(r'&quot;', '"', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    print(content[:5000])
else:
    print('js_content not found')
    # Try extract title at least
    tm = re.search(r'<title>(.*?)</title>', r.text)
    if tm: print('Title:', tm.group(1))
