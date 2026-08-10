# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\scrccpa\.openclaw\workspace\scripts\rag_rebuild.py'
with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

# 找文件扩展名过滤逻辑
print("=== 文件扩展名相关代码 ===")
for i, line in enumerate(content.split('\n'), 1):
    if any(k in line.lower() for k in ['.md', '.txt', '.json', 'glob', 'endswith', 'suffix', 'extend']):
        print(f"  L{i}: {line.strip()[:120]}")

# 找索引函数
print("\n=== 索引函数定义 ===")
for i, line in enumerate(content.split('\n'), 1):
    if line.strip().startswith('def '):
        print(f"  L{i}: {line.strip()[:100]}")

# 确认knowledge目录路径
print("\n=== 数据源路径 ===")
for i, line in enumerate(content.split('\n'), 1):
    if 'knowledge' in line and ('path' in line.lower() or 'dir' in line.lower() or 'folder' in line.lower() or 'source' in line.lower()):
        print(f"  L{i}: {line.strip()[:150]}")
