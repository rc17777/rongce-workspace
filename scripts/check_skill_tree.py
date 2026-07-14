#!/usr/bin/env python3
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
fp = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计技能树.md'
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()
scenes = [l for l in c.split('\n') if l.startswith('## ') and not l.startswith('## 导') and not l.startswith('## 跨') and not l.startswith('## 数')]
methods = [l for l in c.split('\n') if l.startswith('#### ')]
cases = [l for l in c.split('\n') if l.startswith('- `')]
print(f'技能树概览:')
print(f'  场景数: {len(scenes)}')
print(f'  方法数: {len(methods)}')
print(f'  案例引用: {len(cases)}条')
print(f'  文件大小: {len(c)/1024:.0f}KB')
print()
for s in scenes:
    print(f'  {s.replace("## ","")}')
