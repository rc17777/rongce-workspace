import urllib.request
import urllib.parse
import ssl
import re

ssl._create_default_https_context = ssl._create_unverified_context

# Use Sogou WeChat search specifically
query = '财政部青岛监管局 聚焦数智赋能 四库四系统'
url = f'https://weixin.sogou.com/weixin?type=2&query={urllib.parse.quote(query)}'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cookie': 'SNUID=1234567890ABCDEF',
})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    
    # Find all links
    found_links = []
    for m in re.finditer(r'href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
        href = m.group(1)
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if 'mp.weixin.qq.com' in href or '四库' in text:
            found_links.append((text[:100], href))
    
    if found_links:
        for text, href in found_links[:10]:
            print(f'[{text}]')
            print(f'-> {href}')
            print('---')
    else:
        print('No relevant links found. Keywords search:')
        # Just search for weixin URLs
        for m in re.finditer(r'(https?://mp\.weixin\.qq\.com[^"\'<>\s]+)', html):
            print(m.group(1))
except Exception as e:
    print(f'Error: {e}')
