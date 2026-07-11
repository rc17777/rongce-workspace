#!/usr/bin/env python3
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
VAULT = r'C:\Users\scrccpa\Documents\Obsidian Vault'

# 检查杂志资料中标记为其他审计的文章位置
for root, dirs, files in os.walk(os.path.join(VAULT, '杂志资料')):
    for f in files:
        if not f.endswith('.md'): continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
            c = ff.read(500)
        m = re.search(r'scene:\s*["\']?([^"\'\n]+)', c)
        s = m.group(1).strip() if m else ''
        if s == '其他审计':
            rel = os.path.relpath(root, os.path.join(VAULT, '杂志资料'))
            print(f'{rel}\\{f}')
