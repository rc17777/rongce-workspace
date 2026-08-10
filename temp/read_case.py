# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
def show(sub, kw, limit=120):
    p = os.path.join(base, sub)
    for f in os.listdir(p):
        if kw in f:
            full = os.path.join(p, f)
            print('='*90)
            print(f'FILE: [{sub}] {f}')
            print('='*90)
            with open(full, encoding='utf-8', errors='replace') as fh:
                lines = fh.readlines()
            for l in lines[:limit]:
                print(l.rstrip())
            if len(lines) > limit:
                print(f'... ({len(lines)-limit} more lines)')
            return
show('国企审计', '影子', 100)
