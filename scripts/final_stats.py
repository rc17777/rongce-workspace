#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量统计 - 所有已分类文章的汇总"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'

# 统计两个目录
scenes_ocr = {}
scenes_mag = {}
total = 0

for root, dirs, files in os.walk(vault):
    rel = os.path.relpath(root, vault)
    if rel.startswith('审计案例库-OCR') and '\\' in rel[15:]:
        scene = rel[15:]  # 取子目录名
        mds = [f for f in files if f.endswith('.md')]
        if mds:
            scenes_ocr[scene] = scenes_ocr.get(scene, 0) + len(mds)
            total += len(mds)
    elif rel.startswith('杂志资料'):
        if '按类型' in rel:
            continue
        for f in files:
            if not f.endswith('.md'): continue
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
                c = ff.read(500)
            m = re.search(r'scene:\s*["\']?([^"\'\n]+)', c)
            scene = m.group(1).strip() if m else '(无)'
            scenes_mag[scene] = scenes_mag.get(scene, 0) + 1
            total += 1

# 合并
all_scenes = {}
for k, v in scenes_ocr.items():
    all_scenes[k] = {'OCR': v, '杂志': 0}
for k, v in scenes_mag.items():
    if k in all_scenes:
        all_scenes[k]['杂志'] = v
    else:
        all_scenes[k] = {'OCR': 0, '杂志': v}

print('=' * 65)
print(f'{"场景":<18} {"OCR文章":>8} {"杂志文章":>8} {"合计":>8}')
print('=' * 65)
ocr_total = sum(s['OCR'] for s in all_scenes.values())
mag_total = sum(s['杂志'] for s in all_scenes.values())
for s in sorted(all_scenes.keys(), key=lambda x: -(all_scenes[x]['OCR'] + all_scenes[x]['杂志'])):
    d = all_scenes[s]
    print(f'{s:<18} {d["OCR"]:>8} {d["杂志"]:>8} {d["OCR"]+d["杂志"]:>8}')
print('=' * 65)
print(f'{"合计":<18} {ocr_total:>8} {mag_total:>8} {ocr_total+mag_total:>8}')
print(f'\n总计: {ocr_total + mag_total}篇已分类文章')
