#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查所有已分类文章的YAML格式一致性"""
import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'

# 构建完整索引
index = []
incomplete = 0
total = 0

for root, dirs, files in os.walk(vault):
    if '.obsidian' in root or 'node_modules' in root or '.venv' in root:
        continue
    for f in files:
        if not f.endswith('.md'): 
            continue
        fp = os.path.join(root, f)
        
        # 跳过非案例目录
        rel = os.path.relpath(root, vault)
        if not rel.startswith(('审计案例库', '杂志资料', '审计案例库-OCR')):
            continue
        if '按类型' in rel:
            continue
        if rel.startswith('审计案例库') and '\\' not in rel[5:]:
            continue  # 根目录文件跳过
        
        with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
            content = ff.read(2000)
        
        if not content.startswith('---'):
            continue
        
        end = content.find('---', 3)
        if end < 0:
            continue
        head = content[3:end]
        
        # 提取字段
        scene = ''
        title = ''
        keywords = ''
        findings = ''
        
        m = re.search(r'scene:\s*["\']?([^"\'\n]+)', head)
        if m: scene = m.group(1).strip()
        
        m = re.search(r'title:\s*["\']?([^"\'\n]+)', head)
        if m: title = m.group(1).strip()
        
        m = re.search(r'keywords:\s*\[(.*?)\]', head)
        if m: keywords = m.group(1)
        
        has_findings = 'findings:' in head
        
        rel_path = os.path.relpath(fp, vault)
        index.append({
            'path': rel_path,
            'filename': f,
            'scene': scene,
            'title': title or f,
            'has_keywords': bool(keywords),
            'has_findings': has_findings,
        })
        total += 1
        if not scene:
            incomplete += 1

print(f'总扫描: {total}篇\n')
print(f'缺少scene字段: {incomplete}篇\n')

# 输出统计
by_scene = {}
for item in index:
    s = item['scene'] or '(无)'
    by_scene.setdefault(s, []).append(item)

for s, items in sorted(by_scene.items(), key=lambda x: -len(x[1])):
    with_findings = sum(1 for i in items if i['has_findings'])
    print(f'{s}: {len(items)}篇 (含完整标签: {with_findings}篇)')

# 输出JSON索引
output = os.path.join(vault, '审计资料清单.json')
with open(output, 'w', encoding='utf-8') as f:
    json.dump(index, f, ensure_ascii=False, indent=2)
print(f'\nJSON索引已写入: {output} ({len(index)}条)')
