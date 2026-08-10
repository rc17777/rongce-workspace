# -*- coding: utf-8 -*-
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

# 检查D盘上的regulation文件
fp = r'D:\openclaw-workspace\knowledge\datasets\audit-industry\regulations_phase3_2026-07-29.json'
if os.path.exists(fp):
    data = json.load(open(fp, encoding='utf-8'))
    print(f'Entries: {len(data)}')
    if data:
        item = data[0]
        print(f'Keys: {list(item.keys())}')
        print(f'type: {item.get("type")}')
        print(f'id: {item.get("id")}')
        print(f'title: {item.get("law_name", "")[:60]}')
else:
    print(f'File not found: {fp}')
    
# 检查C盘
fp2 = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\datasets\audit-industry\regulations_phase3_2026-07-29.json'
if os.path.exists(fp2):
    data = json.load(open(fp2, encoding='utf-8'))
    print(f'\nC盘 entries: {len(data)}')
    if data:
        item = data[0]
        print(f'type: {item.get("type")}')
        print(f'id: {item.get("id")}')
        print(f'title: {item.get("law_name", "")[:60]}')
else:
    print(f'\nC盘 not found')
