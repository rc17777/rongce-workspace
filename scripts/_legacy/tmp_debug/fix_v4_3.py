# -*- coding: utf-8 -*-
from pathlib import Path
import py_compile

p = Path(r"C:\Users\scrccpa\.openclaw\workspace\scripts\generate_rongce_brochure_v4.py")
c = p.read_text('utf-8')

old = 'def ft(d, text, x, y, f, fill, w=None, gap=6, align="left"):\n    """自动换行绘制"""\n    maxw = w or 9999\n    lines, cur = [], ""\n    for ch in text:\n        if d.textlength(cur + ch, font=f) <= maxw:\n            cur += ch\n        else:\n            if cur: lines.append(cur)\n            cur = ch\n    if cur: lines.append(cur)'

new = 'def ft(d, text, x, y, f, fill, w=None, gap=6, align="left"):\n    """自动换行绘制"""\n    maxw = w or 9999\n    lines = []\n    for para in text.split("\\n"):\n        cur = ""\n        for ch in para:\n            if d.textlength(cur + ch, font=f) <= maxw:\n                cur += ch\n            else:\n                if cur: lines.append(cur)\n                cur = ch\n        if cur: lines.append(cur)'

if old in c:
    c = c.replace(old, new)
    p.write_text(c, 'utf-8')
    print("Fixed ft() to handle newlines")
else:
    print("Pattern not found")

try:
    py_compile.compile(str(p), doraise=True)
    print('SYNTAX OK')
except py_compile.PyCompileError as e:
    print(f'ERROR: {e}')
