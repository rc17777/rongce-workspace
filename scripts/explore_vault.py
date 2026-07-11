#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
print('=== Obsidian Vault 目录结构 ===')
for root, dirs, files in os.walk(vault):
    if '.obsidian' in root.split(os.sep):
        continue
    depth = root.replace(vault, '').count(os.sep)
    if depth > 2:
        continue
    indent = '  ' * depth
    folder = os.path.basename(root) if depth > 0 else 'Obsidian Vault'
    md_count = len([f for f in files if f.endswith('.md')])
    print(f'{indent}{folder}/ ({md_count}个文件)')
print()
print('=== 杂志文章目录详情 ===')
for d in sorted(os.listdir(vault)):
    fp = os.path.join(vault, d)
    if os.path.isdir(fp) and not d.startswith('.'):
        md = [f for f in os.listdir(fp) if f.endswith('.md')]
        if md:
            print(f'  {d}/: {len(md)}篇')
