#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OCR处理进度"""
import os, sys, io, datetime, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base_dir = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
source_dirs = [
    r'C:\Users\scrccpa\Desktop\审计观察',
    r'C:\Users\scrccpa\Desktop\经济责任审计'
]

# 统计输出目录
processed = 0
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.md') and not f.startswith('00-'):
            processed += 1

# 统计源PDF
total_pdfs = 0
for d in source_dirs:
    if os.path.exists(d):
        for root, dirs, files in os.walk(d):
            for f in files:
                if f.endswith('.pdf'):
                    total_pdfs += 1

remaining = total_pdfs - processed
pct = processed / total_pdfs * 100 if total_pdfs > 0 else 0

print('OCR 进度报告')
print('=' * 40)
print(f'  总PDF数: {total_pdfs}')
print(f'  已处理:  {processed}')
print(f'  剩余:    {remaining}')
print(f'  完成度:  {pct:.1f}%')
print('-' * 40)

# 检查进程
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
python_count = result.stdout.count('python.exe')
if python_count > 0:
    print(f'  状态:    Python进程运行中')
else:
    print(f'  状态:    Python进程已结束')
print('-' * 40)

# 最近处理的文件
print()
print('最近处理的5个文件:')
recent = []
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.md') and not f.startswith('00-'):
            path = os.path.join(root, f)
            mtime = os.path.getmtime(path)
            scene = os.path.basename(root) if root != base_dir else '根目录'
            recent.append((mtime, f, scene))
recent.sort(reverse=True)
for mtime, name, scene in recent[:5]:
    dt = datetime.datetime.fromtimestamp(mtime)
    t = dt.strftime('%H:%M')
    print(f'  [{t}] {scene}/{name[:45]}')
