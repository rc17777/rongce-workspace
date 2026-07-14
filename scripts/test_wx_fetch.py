"""Test fetching a WeChat MP article with Python."""
import urllib.request
import re
import sys

url = 'http://mp.weixin.qq.com/s?__biz=MzI1NTA5NDA2MA==&mid=2648442758&idx=1&sn=34f9167ecf58f850016e5f30c4a24236'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml'
})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    title_match = re.search(r'<title>(.*?)</title>', html)
    content_match = re.search(r'id="js_content"[^>]*>(.*?)</div>', html, re.DOTALL)
    title = title_match.group(1) if title_match else 'N/A'
    text_len = len(content_match.group(1)) if content_match else 0
    print(f'Title: {title}')
    print(f'Content length: {text_len}')
    if content_match:
        text = re.sub(r'<[^>]+>', '', content_match.group(1))
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'\s+', ' ', text).strip()
        print(f'Text preview: {text[:500]}')
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
