#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量统计v2 - OCR + 杂志"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'

# OCR统计
scenes_ocr = {}
ocr_dir = os.path.join(vault, '审计案例库-OCR')
for d in os.listdir(ocr_dir):
    sub = os.path.join(ocr_dir, d)
    if os.path.isdir(sub) and not d.startswith('.'):
        mds = [f for f in os.listdir(sub) if f.endswith('.md')]
        if mds:
            scenes_ocr[d] = len(mds)

# 杂志统计
scenes_mag = {}
mag_dir = os.path.join(vault, '杂志资料')
for root, dirs, files in os.walk(mag_dir):
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
        scenes_mag[scene] = scenes_mag.get(scene, 0) + 1

all_scenes = {}
for k, v in scenes_ocr.items():
    all_scenes[k] = {'OCR': v, '杂志': 0}
for k, v in scenes_mag.items():
    if k in all_scenes:
        all_scenes[k]['杂志'] = v
    else:
        all_scenes[k] = {'OCR': 0, '杂志': v}

print('=' * 65)
print(f'{"场景":<20} {"OCR文章":>8} {"杂志文章":>8} {"合计":>8}')
print('=' * 65)
ocr_total = 0
mag_total = 0
for s in sorted(all_scenes.keys(), key=lambda x: -(all_scenes[x]['OCR'] + all_scenes[x]['杂志'])):
    d = all_scenes[s]
    ocr_total += d['OCR']
    mag_total += d['杂志']
    print(f'{s:<20} {d["OCR"]:>8} {d["杂志"]:>8} {d["OCR"]+d["杂志"]:>8}')
print('=' * 65)
print(f'{"合计":<20} {ocr_total:>8} {mag_total:>8} {ocr_total+mag_total:>8}')
print(f'\n总计: {ocr_total + mag_total}篇已分类文章')
