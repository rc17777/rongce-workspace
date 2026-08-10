# fix v7 walrus operator
from pathlib import Path
p = Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v7.py')
text = p.read_text('utf-8')
lines = text.split('\n')
new_lines = []
seen_yy_init = False
for line in lines:
    # Skip walrus operator line
    if "y := (y if 'y' in dir()" in line:
        continue
    # Keep only one yy_dt init
    if 'yy_dt = 710' in line:
        if seen_yy_init:
            continue
        seen_yy_init = True
    new_lines.append(line)
text = '\n'.join(new_lines)
p.write_text(text, 'utf-8')
# Verify
import py_compile
try:
    py_compile.compile(str(p), doraise=True)
    print('OK')
except py_compile.PyCompileError as e:
    print('FAIL:', e)
    # Show context around error
    err_line = int(str(e).split('line ')[1].split('\n')[0]) if 'line ' in str(e) else 0
    if err_line:
        print(f'Line {err_line-1}: {lines[err_line-2]}')
        print(f'Line {err_line}: {lines[err_line-1]}')
        print(f'Line {err_line+1}: {lines[err_line]}')
