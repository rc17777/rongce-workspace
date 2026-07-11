#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终验证杂志分类质量"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
base = os.path.join(vault, '杂志资料')

by_scene = {}
for root, dirs, files in os.walk(base):
    if '按类型' in root:
        continue
    for f in files:
        if not f.endswith('.md'): continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
            c = ff.read(500)
        m = re.search(r'scene:\s*["\']?([^"\'\n]+)', c)
        scene = m.group(1).strip() if m else '(无)'
        by_scene.setdefault(scene, []).append(f[:70])

for s in sorted(by_scene.keys(), key=lambda x: -len(by_scene[x])):
    items = by_scene[s]
    print(f'\n{s} ({len(items)}篇):')
    for f in items[:4]:
        print(f'  · {f}')
