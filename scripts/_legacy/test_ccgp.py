import requests
r = requests.get('http://www.ccgp.gov.cn/cggg/zygg/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
print(f'Status: {r.status_code}, Len: {len(r.text)}')
print(f'Has shenji: {"shenji" in r.text}')
print(f'First 500: {r.text[:500]}')
