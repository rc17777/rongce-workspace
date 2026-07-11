#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出180篇审计案例用于AI分类"""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
out_path = r'D:\openclaw-workspace\for_classification.json'

files_data = []
for root, dirs, files in os.walk(base):
    scene = os.path.basename(root)
    if scene in ('word', '_temp_images', 'ocr_text', 'test_abbyy', 'raw_text', 'test_output'):
        continue
    for f in sorted(files):
        if not f.endswith('.md') or f.startswith('00-'):
            continue
        fp = os.path.join(root, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
        except:
            continue
        
        # 提取正文
        body = content
        if body.startswith('---'):
            idx = body.find('---', 3)
            if idx > 0:
                body = body[idx+3:]
        
        preview = body.strip()[:600]
        
        files_data.append({
            'id': len(files_data) + 1,
            'filename': f,
            'current_scene': scene,
            'preview': preview
        })

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(files_data, f, ensure_ascii=False, indent=1)

print(f'Exported {len(files_data)} files to {out_path}')
