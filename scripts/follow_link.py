import urllib.request
import urllib.parse
import ssl
import re

ssl._create_default_https_context = ssl._create_unverified_context

# Follow the Sogou link to get the actual WeChat URL
sogou_link = '/link?url=dn9a_-gY295K0Rci_xozVXfdMkSQTLW6cwJThYulHEtVjXrGTiVgS3GR0sbpHfv3u4jWNKZRc6O6y_AUI-O3PFqXa8Fplpd9Hl8UoPB6fdzonx31UDCZjTw7D9I6bkE-_ajN0f4xCRsn19TC_d3E8wZsXKrT0zpnIFEBxH9nYANB6-sheR_yD-SZXwnAP_hGmu3Xh4xULGlDWNfkWRm_J01xSVQG6QqiLeta82Zc2Pwgw8hL7Hz6EgHErl7JHiyXsTFXUqybkrUCn9lOoZLP2Q..'
url = f'https://weixin.sogou.com{sogou_link}'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://weixin.sogou.com/',
})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    final_url = resp.geturl()
    print(f'Final URL: {final_url}')
    
    html = resp.read().decode('utf-8', errors='ignore')
    
    # Look for the WeChat article URL in the page
    for m in re.finditer(r'(https?://mp\.weixin\.qq\.com[^"\'<>\s]+)', html):
        url = m.group(1).replace('&amp;', '&')
        print(f'WeChat URL: {url}')
    
    # Also look for redirect or script URLs
    for m in re.finditer(r'var\s+url\s*=\s*["\']([^"\']+mp\.weixin[^"\']*)', html):
        print(f'JS URL: {m.group(1)}')
    
    # If no direct URL found, look for the snippet
    for m in re.finditer(r'window\.location[^;]*["\']([^"\']+)["\']', html):
        print(f'Location URL: {m.group(1)}')
    
    # Print any URL containing 'weixin'
    for m in re.finditer(r'(https?://[^"\'<>\s]*weixin[^"\'<>\s]*)', html):
        print(f'Other weixin URL: {m.group(1)}')
        
except Exception as e:
    print(f'Error: {e}')
