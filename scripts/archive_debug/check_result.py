#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\openclaw-workspace\scripts\classification_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
from collections import Counter
sc = Counter(r['scene'] for r in data)
print('分类完成，共处理%d个文件' % len(data))
print()
for s, c in sc.most_common():
    print('  %s: %d篇' % (s, c))
print()
print('前5条验证:')
for r in data[:5]:
    print('  [%s] -> %s  关键词:%s' % (r['filename'][:30], r['scene'], r['keywords']))
