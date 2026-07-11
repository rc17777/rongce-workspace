#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出其他审计所有文章"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

VAULT = r'C:\Users\scrccpa\Documents\Obsidian Vault'
INDEX = os.path.join(VAULT, '审计资料清单.json')

with open(INDEX, 'r', encoding='utf-8') as f:
    articles = json.load(f)

others = [a for a in articles if a['scene'] == '其他审计']

ocr = [a for a in others if '审计案例库-OCR' in a['path']]
mag = [a for a in others if '杂志资料' in a['path']]
legacy = [a for a in others if '审计案例库' in a['path'] and 'OCR' not in a['path'] and '杂志' not in a['path']]

print(f'其他审计 共{len(others)}篇\n')

if ocr:
    print(f'=== OCR全文版 ({len(ocr)}篇) ===')
    for i, a in enumerate(ocr, 1):
        print(f'  {i:2d}. {a["filename"].replace(".md","")}')
    print()

if mag:
    print(f'=== 杂志文章 ({len(mag)}篇) ===')
    for i, a in enumerate(mag, 1):
        src = a['path'].split('\\')
        source = '/'.join(src[2:4]) if len(src) > 3 else '/'.join(src[2:3])
        print(f'  {i:2d}. [{source}] {a["filename"].replace(".md","")}')
    print()

if legacy:
    print(f'=== 旧案例库 ({len(legacy)}篇) ===')
    for i, a in enumerate(legacy, 1):
        print(f'  {i:2d}. {a["filename"].replace(".md","")}')
