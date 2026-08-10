# -*- coding: utf-8 -*-
"""Merge rongce_v5_part1.py + part2.py into rongce_v5.py"""
from pathlib import Path
p1 = Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v5_part1.py').read_text('utf-8')
p2 = Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v5_part2.py').read_text('utf-8')
marker = "def p7_eng():"
idx = p2.find(marker)
p2_tail = p2[idx:] if idx > 0 else p2
merged = p1.rstrip() + '\n\n\n' + p2_tail
out = Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v5.py')
out.write_text(merged, 'utf-8')
import py_compile
try:
    py_compile.compile(str(out), doraise=True)
    print('OK', len(merged), 'bytes')
except py_compile.PyCompileError as e:
    print('FAIL:', e)