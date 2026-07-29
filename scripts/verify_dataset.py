# -*- coding: utf-8 -*-
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\datasets'
grand = 0
entries_by_type = {}

for root, dirs, files in os.walk(base):
    for f in files:
        if not f.endswith('.json') or 'catalog' in f or 'schema' in f:
            continue
        fp = os.path.join(root, f)
        rel = os.path.relpath(root, base)
        with open(fp, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        count = len(data) if isinstance(data, list) else 1
        grand += count
        
        # count by type
        for item in (data if isinstance(data, list) else [data]):
            t = item.get('type', 'unknown')
            entries_by_type[t] = entries_by_type.get(t, 0) + 1
        
        print(f'  [{rel}] {f}: {count} entries')

print(f'\n{"="*50}')
print(f'  数据集验证报告')
print(f'{"="*50}')
print(f'  JSON文件数: {sum(1 for r,ds,fs in os.walk(base) for f in fs if f.endswith(".json") and "catalog" not in f and "schema" not in f)}')
print(f'  总条目数:   {grand}')
print()
for t, c in sorted(entries_by_type.items()):
    print(f'  {t}: {c}')
print()
print(f'  目录结构:')
for r, ds, fs in os.walk(base):
    level = r.replace(base, '').count(os.sep)
    indent = '  ' * level
    dname = os.path.basename(r) or 'datasets'
    print(f'{indent}{dname}/')
    for f in sorted(fs):
        if f.endswith('.json') or f.endswith('.md'):
            fsize = os.path.getsize(os.path.join(r, f))
            print(f'{indent}  {f} ({fsize/1024:.0f}KB)')
