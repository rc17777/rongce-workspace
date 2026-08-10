# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR\工程审计\“先种后铲”的绿化闹剧.md'
with open(f, encoding='utf-8') as fh:
    lines = fh.readlines()
print('TOTAL:', len(lines))
for i, l in enumerate(lines[:150], 1):
    print(i, l.rstrip())
