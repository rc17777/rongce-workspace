#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新OCR文件的YAML头, 按分类结果调整目录"""
import sys, os, json, shutil
sys.stdout.reconfigure(encoding='utf-8')

vault_ocr = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'

# 读取分类结果
with open(r'D:\openclaw-workspace\scripts\classification_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

moved = 0
updated = 0
errors = 0

for item in results:
    old_path = item['filepath']
    if not os.path.exists(old_path):
        errors += 1
        continue
    
    # 读取原文件
    with open(old_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # 构建YAML头
    scene = item['scene']
    findings = item.get('findings', [])
    recs = item.get('recommendations', [])
    regs = item.get('regulations', [])
    kws = item.get('keywords', [])
    
    yaml_lines = ['---']
    yaml_lines.append(f'scene: "{scene}"')
    if findings:
        yaml_lines.append('findings:')
        for f_ in findings:
            yaml_lines.append(f'  - "{f_}"')
    if recs:
        yaml_lines.append('recommendations:')
        for r_ in recs:
            yaml_lines.append(f'  - "{r_}"')
    if regs:
        yaml_lines.append('regulations:')
        for r_ in regs:
            yaml_lines.append(f'  - "{r_}"')
    if kws:
        yaml_lines.append(f'keywords: [{", ".join(kws)}]')
    yaml_lines.append('---')
    yaml_head = '\n'.join(yaml_lines) + '\n'
    
    # 移除原有的YAML头（如果有）
    body = content
    if body.startswith('---'):
        idx = body.find('---', 3)
        if idx > 0:
            body = body[idx+3:].strip()
    
    # 新内容
    new_content = yaml_head + '\n' + body
    
    # 确定新路径（如果场景变了就移动目录）
    old_dir = os.path.dirname(old_path)
    new_dir = os.path.join(vault_ocr, scene)
    new_path = os.path.join(new_dir, os.path.basename(old_path))
    
    os.makedirs(new_dir, exist_ok=True)
    
    if new_path != old_path:
        # 需要移动
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        os.remove(old_path)
        moved += 1
    else:
        # 原地更新
        with open(old_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated += 1

print(f'更新完成: {updated}篇原地更新, {moved}篇移动目录, {errors}个错误')
print()

# 最后统计各场景文件数
print('当前 审计案例库-OCR 场景分布:')
for root, dirs, files in os.walk(vault_ocr):
    if root == vault_ocr:
        continue
    scene = os.path.basename(root)
    mds = [f for f in files if f.endswith('.md')]
    if mds:
        print(f'  {scene}: {len(mds)}篇')
