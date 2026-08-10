"""Quick debug: save raw HTML from search page"""
import asyncio, re, sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = 'https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&kw=%E5%AE%A1%E8%AE%A1%E6%9C%8D%E5%8A%A1&start_time=2026:07:04&end_time=2026:07:11&timeType=6&dbselect=bidx'
        print(f'Loading: {url}')
        resp = await page.goto(url, timeout=30000, wait_until='networkidle')
        print(f'Response status: {resp.status}')
        await page.wait_for_timeout(5000)  # Wait longer
        html = await page.content()
        print(f'Final URL: {page.url}')
        print(f'Title: {await page.title()}')

        with open(r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\debug_search.html', 'w', encoding='utf-8') as f:
            f.write(html)

        # Quick stats
        lis = re.findall(r'<li[^>]*>', html)
        links = re.findall(r'<a[^>]*href="([^"]+)"', html)
        titles = re.findall(r'审计', html)
        print(f'HTML: {len(html)} chars')
        print(f'<li> tags: {len(lis)}')
        print(f'<a> links: {len(links)}')
        print(f'"审计" mentions: {len(titles)}')

        # Show first few links
        for l in links[:10]:
            print(f'  {l[:100]}')

        # Check for table-based layout
        tables = re.findall(r'<table', html)
        trs = re.findall(r'<tr', html)
        print(f'Tables: {len(tables)}, TRs: {len(trs)}')

        await browser.close()

asyncio.run(main())
