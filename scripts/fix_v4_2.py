# -*- coding: utf-8 -*-
from pathlib import Path
import py_compile

p = Path(r"C:\Users\scrccpa\.openclaw\workspace\scripts\generate_rongce_brochure_v4.py")
c = p.read_text('utf-8')

# Fix BGE replacement - needs quotes around hex color
c = c.replace('rgb(#FAF8F4)', 'rgb("#FAF8F4")')

# Fix OUT references 
c = c.replace('OUT.', 'OUT_DIR.')

# Fix PDF_ references
c = c.replace('PDF_PATH_', 'PDF_PATH')

# Remove any lingering str(DOCX_PATH) etc. from tail
for bad, good in [
    ('DOCX_PATH_PATH', 'DOCX_PATH'),
    ('WORK_DIR_DIR', 'WORK_DIR'),
]:
    c = c.replace(bad, good)

p.write_text(c, 'utf-8')

try:
    py_compile.compile(str(p), doraise=True)
    print('SYNTAX OK')
except py_compile.PyCompileError as e:
    print(f'ERROR: {e}')
