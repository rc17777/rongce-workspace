#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查审计案例库(非OCR)的文件格式"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
base = os.path.join(vault, '审计案例库')

for d in sorted(os.listdir(base)):
    sub = os.path.join(base, d)
    if not os.path.isdir(sub) or d.startswith('.'):
        continue
    mds = [f for f in os.listdir(sub) if f.endswith('.md')]
    if not mds: continue
    # 看第一篇的头部
    fp = os.path.join(sub, mds[0])
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(800)
    has_yaml = content.startswith('---')
    has_scene = bool(re.search(r'scene:', content[:500]))
    print(f'{d}/ ({len(mds)}篇): YAML={has_yaml}, scene={has_scene}')
    if has_yaml:
        end = content.find('---', 3)
        if end > 0:
            print(f'  YAML头: {content[3:end][:200]}')
    else:
        print(f'  开头: {content[:100]}')
    print()
