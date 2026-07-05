#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按场景生成详细案例清单"""
import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')

VAULT = r'C:\Users\scrccpa\Documents\Obsidian Vault'
INDEX = os.path.join(VAULT, '审计资料清单.json')

with open(INDEX, 'r', encoding='utf-8') as f:
    articles = json.load(f)

# 读取分类详细数据
results_path = r'D:\openclaw-workspace\scripts\classification_results.json'
detailed = {}
if os.path.exists(results_path):
    with open(results_path, 'r', encoding='utf-8') as f:
        for item in json.load(f):
            fname = os.path.basename(item['filepath']).replace('.md', '')
            detailed[fname] = item

# 按场景分组
by_scene = {}
for a in articles:
    s = a['scene']
    if not s or s == '(未分类)':
        continue
    by_scene.setdefault(s, []).append(a)

# 场景排序（按数量降序）
ordered = sorted(by_scene.items(), key=lambda x: -len(x[1]))

md = '''---
created: 2026-06-24
tags: [案例清单, MOC]
description: 按审计场景分类的详细案例清单
---

# 📋 审计案例详细清单

> **总计 {total}篇案例** | 覆盖14个审计场景
> 包含：审计案例库（OCR全文版）+ 杂志资料

---

'''.format(total=len(articles))

# 顶部导航
md += '## 快速导航\n\n'
for i, (scene, items) in enumerate(ordered, 1):
    md += f'1. [[#{scene}|{scene}]] — {len(items)}篇案例\n'
md += '\n---\n\n'

# 按场景详细列出
for scene, items in ordered:
    # 分出OCR版和杂志版
    ocr_items = [a for a in items if '审计案例库-OCR' in a['path']]
    legacy_items = [a for a in items if '审计案例库' in a['path'] and 'OCR' not in a['path'] and '杂志' not in a['path']]
    mag_items = [a for a in items if '杂志资料' in a['path']]
    
    md += f'## {scene}\n\n'
    md += f'> **共{len(items)}篇**'
    if ocr_items:
        md += f' | OCR全文版({len(ocr_items)}篇)'
    if mag_items:
        md += f' | 杂志({len(mag_items)}篇)'
    if legacy_items:
        md += f' | 旧版({len(legacy_items)}篇)'
    md += '\n\n'
    
    # OCR版（最详细）
    if ocr_items:
        md += '### 📄 OCR全文版\n\n'
        md += '| # | 文件名 | 审计发现 | 审计建议 | 法规依据 | 关键词 |\n'
        md += '|---|------|---------|---------|---------|-------|\n'
        for idx, a in enumerate(ocr_items, 1):
            fname = a['filename'].replace('.md', '')
            det = detailed.get(fname, {})
            findings = det.get('findings', [])
            recs = det.get('recommendations', [])
            regs = det.get('regulations', [])
            kws = det.get('keywords', [])
            
            f_text = ' | '.join(findings[:2]) if findings else '—'
            r_text = ' | '.join(recs[:2]) if recs else '—'
            g_text = ' | '.join(regs[:2]) if regs else '—'
            k_text = '、'.join(kws[:4]) if kws else '—'
            
            # 转义表格中的竖线
            f_text = f_text.replace('|', '/')
            r_text = r_text.replace('|', '/')
            
            title_display = fname[:60]
            md += f'| {idx} | {title_display} | {f_text[:60]} | {r_text[:60]} | {g_text[:40]} | {k_text[:40]} |\n'
        md += '\n'
    
    # 杂志版
    if mag_items:
        md += '### 📰 杂志文章\n\n'
        md += '| # | 文件名 | 来源 |\n'
        md += '|---|------|------|\n'
        for idx, a in enumerate(mag_items, 1):
            fname = a['filename'].replace('.md', '')
            src = a['path'].split('\\')
            source = src[2] if len(src) > 2 else ''
            if len(src) > 3:
                source += '/' + src[3]
            md += f'| {idx} | {fname[:70]} | {source} |\n'
        md += '\n'
    
    md += '---\n\n'

# 附录
md += '## 附录\n\n'
md += '### 各场景文章数汇总\n\n'
md += '| 场景 | OCR全文 | 杂志 | 旧版 | 合计 |\n'
md += '|:----|:-------:|:----:|:----:|:---:|\n'
for scene, items in ordered:
    ocr_cnt = len([a for a in items if '审计案例库-OCR' in a['path']])
    legacy_cnt = len([a for a in items if '审计案例库' in a['path'] and 'OCR' not in a['path'] and '杂志' not in a['path']])
    mag_cnt = len([a for a in items if '杂志资料' in a['path']])
    total = len(items)
    md += f'| {scene} | {ocr_cnt} | {mag_cnt} | {legacy_cnt} | {total} |\n'

md += '\n### Dataview查询示例\n\n'
md += '''```dataview
TABLE title as "名称", scene as "场景", file.tags as "标签"
FROM "审计案例库-OCR" OR "杂志资料"
WHERE scene = "经济责任审计"
SORT file.name
```
'''

md += '\n---\n\n*自动生成: 2026-06-24*\n'

output = os.path.join(VAULT, '审计案例详细清单.md')
with open(output, 'w', encoding='utf-8') as f:
    f.write(md)
print(f'已生成: {output}')
print(f'共 {len(articles)} 篇案例, 按 {len(ordered)} 个场景列出')
print(f'文件大小: {len(md)/1024:.1f}KB')
