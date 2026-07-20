#!/usr/bin/env python3
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例详细清单.md', 'r', encoding='utf-8') as f:
    c = f.read()
sections = c.split('## ')
for s in sections:
    if not s.strip():
        continue
    lines = s.split('\n')
    scene = lines[0].strip()
    table_rows = [l for l in lines if l.startswith('| ') and not l.startswith('| -') and not l.startswith('| #')]
    if table_rows:
        print(f'{scene}: {len(table_rows)}行')
