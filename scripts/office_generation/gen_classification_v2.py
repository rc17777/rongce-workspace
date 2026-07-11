#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成完整的180篇审计案例分类结果"""
import json, os

# 读取导出的数据
with open(r'D:\openclaw-workspace\for_classification.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 读取分类数据
with open(r'D:\openclaw-workspace\scripts\classification_data_inline.json', 'r', encoding='utf-8') as f:
    CLASSIFICATIONS = json.load(f)

# 构建输出
results = []
for item in data:
    fid = str(item['id'])
    cls = CLASSIFICATIONS.get(fid, {"scene": "其他审计", "findings": [], "recommendations": [], "regulations": [], "keywords": []})
    scene_dir = item['current_scene']
    results.append({
        "filepath": os.path.join(r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR', scene_dir, item['filename']),
        "filename": item['filename'],
        "scene": cls["scene"],
        "findings": cls["findings"],
        "recommendations": cls["recommendations"],
        "regulations": cls["regulations"],
        "keywords": cls["keywords"]
    })

out_path = r'D:\openclaw-workspace\scripts\classification_results.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

from collections import Counter
scenes = Counter(r['scene'] for r in results)
print(f"分类完成，共处理{len(results)}个文件")
print(f"\n各场景分布:")
for scene, count in scenes.most_common():
    print(f"  {scene}: {count}篇")
print(f"\n结果已保存至: {out_path}")
