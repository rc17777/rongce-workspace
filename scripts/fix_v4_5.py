# -*- coding: utf-8 -*-
from pathlib import Path
import py_compile

p = Path(r"C:\Users\scrccpa\.openclaw\workspace\scripts\generate_rongce_brochure_v4.py")
c = p.read_text('utf-8')

# Find end of ft function  
pos = c.find('def ft(d, text, x, y, font, fill, w=None, gap=6, align="left"):')
end_marker = '    return y'
e1 = c.find(end_marker, pos)
e2 = c.find('\n', e1 + len(end_marker))

# Insert wrapdraw alias after ft
insert = '\n\nwrapdraw = ft  # alias for appended code'
c = c[:e2] + insert + c[e2:]
p.write_text(c, 'utf-8')

try:
    py_compile.compile(str(p), doraise=True)
    print('SYNTAX OK')
except py_compile.PyCompileError as e:
    print(f'ERROR: {e}')
