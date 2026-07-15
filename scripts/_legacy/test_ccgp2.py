import requests, time, re, json, hashlib
from datetime import datetime, timedelta

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
})

# First visit to get cookies
print('Getting homepage...')
r = session.get('http://www.ccgp.gov.cn/', timeout=30)
print(f'Homepage: {r.status_code}, {len(r.text)} chars, cookies: {len(session.cookies)}')
time.sleep(2)

# Try listing
print('\nGetting listing...')
r = session.get('http://www.ccgp.gov.cn/cggg/zygg/', timeout=30)
print(f'Listing: {r.status_code}, {len(r.text)} chars')
if r.status_code == 200:
    r.encoding = 'utf-8'
    text = r.text
    # Count li tags
    lis = len(re.findall(r'<li[^>]*>', text))
    print(f'<li> tags: {lis}')
    # Show sample
    idx = text.find('/cggg/')
    if idx > 0:
        print(f'Sample: ...{text[max(0,idx-50):idx+200]}...')
    # Count audit-related
    audit_count = text.count('\u5ba1\u8ba1')
    print(f'审计 mentions: {audit_count}')

time.sleep(3)
print('\nTrying search...')
r = session.get('https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&kw=%E5%AE%A1%E8%AE%A1&start_time=2026:06:11&end_time=2026:07:11&timeType=6&dbselect=bidx', timeout=30)
print(f'Search: {r.status_code}, {len(r.text)} chars')
if '频繁访问' in r.text:
    print('BLOCKED: frequent visit detected')
elif '审计' in r.text:
    print('GOT RESULTS!')
else:
    print('No results, no block')
