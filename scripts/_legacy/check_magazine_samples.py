#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证杂志分类质量"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
base = os.path.join(vault, '杂志资料')

by_scene = {}
for root, dirs, files in os.walk(base):
    if '按类型' in root:
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
            c = ff.read(500)
        m = re.search(r'scene:\s*["\']?([^"\'\n]+)', c)
        scene = m.group(1).strip() if m else '(无)'
        by_scene.setdefault(scene, []).append(f[:60])

print('分类抽样验证:\n')
for scene in ['预算执行审计', '其他审计', '绩效审计', '社保民生审计', '内部审计', '经济责任审计', '工程审计', '农业农村审计']:
    items = by_scene.get(scene, [])
    print(f'=== {scene} ({len(items)}篇) ===')
    for fname in items[:4]:
        print(f'  {fname}')
    print()
