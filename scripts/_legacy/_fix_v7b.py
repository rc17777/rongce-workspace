from pathlib import Path
p = Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v7.py')
lines = p.read_text('utf-8').split('\n')
# Add yy_dt init before the for loop and the draw line as body
# Find the for loop (line 287) and insert yy_dt=710 before it
fixed = []
for i, line in enumerate(lines):
    fixed.append(line)
    if "for item in [" in line and "事前评估" in line:
        # Insert yy_dt init before this line (replace previous line if needed)
        # Actually check if we already have yy_dt
        prev = fixed[-2] if len(fixed) >= 2 else ""
        if 'yy_dt' not in prev:
            # Insert before the for line
            fixed.insert(-1, '    yy_dt = 710')
    if line.strip().startswith('for item in') and '事前评估' in line:
        # The next line should be the body
        pass  # We'll handle it below
# Second pass: add the for loop body
result = []
skip_next = False
for i, line in enumerate(fixed):
    if skip_next:
        skip_next = False
    result.append(line)
    # After the second item line in the for loop, add the draw body
    if "每个环节交付" in line and "for item" in fixed[i-1]:
        result.append('        yy_dt = draw(d, item, M+40, yy_dt+14, font(24), IK, 1200, 6)')

text = '\n'.join(result)
p.write_text(text, 'utf-8')
# Verify
import py_compile
try:
    py_compile.compile(str(p), doraise=True)
    print('OK')
except py_compile.PyCompileError as e:
    print('FAIL:', e)
