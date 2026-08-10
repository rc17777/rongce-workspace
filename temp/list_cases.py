# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
for d in sorted(os.listdir(base)):
    p = os.path.join(base, d)
    if os.path.isdir(p):
        files = os.listdir(p)
        print(f'[{d}] ({len(files)} files)')
        for f in files[:40]:
            print('   ', f)
