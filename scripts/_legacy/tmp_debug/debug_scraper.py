"""Debug ccgp.gov.cn search page HTML"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&kw=审计服务&start_time=2026:07:04&end_time=2026:07:11&timeType=6&dbselect=bidx'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
r.encoding = 'utf-8'
html = r.text

print(f'HTML length: {len(html)}')

# Find the search results section
# The results are in a <ul class="..." > section
ul_start = html.find('<ul')
if ul_start > 0:
    sample = html[ul_start:ul_start+3000]
    print('\n--- First UL block (3000 chars) ---')
    print(sample[:3000])
else:
    # Show areas with "审计" in them
    print('\n--- Searching for 审计 in HTML ---')
    positions = [m.start() for m in re.finditer('审计', html)]
    for pos in positions[:3]:
        snippet = html[max(0,pos-200):min(len(html),pos+400)]
        print(f'\nAt position {pos}:')
        print(snippet.replace('\n','\\n'))
