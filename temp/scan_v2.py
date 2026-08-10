# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
lines = open('build_algorithm_lib_v2.py', encoding='utf-8').readlines()
in_alg = False
for i, l in enumerate(lines, 1):
    s = l.strip()
    if s.startswith("'sn':"):
        print(i, 'SN:', s)
    elif s.startswith("'name':"):
        print(i, 'NAME:', s[:110])
    elif s.startswith('# ====='):
        print(i, 'SEP:', s[:80])
    elif s.startswith('def '):
        print(i, 'DEF:', s[:80])
    elif s.startswith('if __name__'):
        print(i, 'MAIN:', s[:80])
