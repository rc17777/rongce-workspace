# -*- coding: utf-8 -*-
import os, re

base = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
dirs = sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))])
for i, d in enumerate(dirs):
    full = os.path.join(base, d)
    files = [f for f in os.listdir(full) if f.endswith('.md')]
    if not files: continue
    try:
        with open(os.path.join(full, files[0]), 'r', encoding='utf-8') as f:
            content = f.read()[:500]
            m = re.search(r'scene:\s*"([^"]*)"', content)
            if not m:
                m = re.search(r'scene:\s*(\S+)', content)
            scene = m.group(1) if m else '?'
            if any(kw in scene for kw in ['补贴', '补助', '专项']):
                print('DIR[{}] {} ({}f) scene={}'.format(i, d, len(files), scene))
    except Exception as e:
        pass
