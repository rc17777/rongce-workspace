#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search for city property prices via web scraping"""
import urllib.request, re, sys, json, ssl
sys.stdout.reconfigure(encoding='utf-8-sig')
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Try to get data from gotohui.com which has a simpler API
targets = [
    ('马尔康', 'https://www.gotohui.com/price/280000'),
    ('都江堰', 'https://www.gotohui.com/price/510181'),
    ('广汉', 'https://www.gotohui.com/price/510681'),
    ('金牛区', 'https://www.gotohui.com/price/510106'),
    ('金堂', 'https://www.gotohui.com/price/510121'),
    ('北海', 'https://www.gotohui.com/price/450500'),
    ('红原', 'https://www.gotohui.com/price/513233'),
]
for name, url in targets:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = r.read().decode('utf-8', errors='ignore')
            # find price data
            nums = re.findall(r'[\d,]+\.?\d*', data)
            print(f'{name}: {len(data)} bytes, first 200 chars: {data[:200]}')
    except Exception as e:
        print(f'{name}: {e}')