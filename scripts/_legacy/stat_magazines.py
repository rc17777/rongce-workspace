#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计杂志资料文章分布"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
base = os.path.join(vault, '杂志资料')

total = 0
for root, dirs, files in os.walk(base):
    if '按类型' in root:
        continue
    mds = [f for f in files if f.endswith('.md')]
    if not mds:
        continue
    folder = os.path.relpath(root, base)
    cat_counts = {}
    for f in mds:
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
            c = ff.read(500)
        m = re.search(r'category:\s*["\']?([^"\'\n]+)', c)
        if m:
            cat = m.group(1).strip()
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        else:
            cat_counts['(无)'] = cat_counts.get('(无)', 0) + 1
    print(f'杂志资料/{folder}: {len(mds)}篇')
    if len(cat_counts) <= 3:
        for k, v in sorted(cat_counts.items()):
            print(f'  现有category: {k} = {v}篇')
    total += len(mds)

print(f'\n总计非分类目录文章: {total}篇')

# 检查按类型目录
print('\n按类型目录现有场景:')
type_dir = os.path.join(base, '按类型')
for d in sorted(os.listdir(type_dir)):
    sub = os.path.join(type_dir, d)
    if os.path.isdir(sub):
        n = len([f for f in os.listdir(sub) if f.endswith('.md')])
        print(f'  {d}: {n}篇')
