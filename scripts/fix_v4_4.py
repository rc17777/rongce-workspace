# -*- coding: utf-8 -*-
from pathlib import Path
import py_compile

p = Path(r"C:\Users\scrccpa\.openclaw\workspace\scripts\generate_rongce_brochure_v4.py")
c = p.read_text('utf-8')

# Replace ft function with version that handles \n in text
# Find the ft function definition
idx = c.find('def ft(d, text, x, y, font, fill, w=None, gap=6, align="left"):')
if idx < 0:
    print("ft function not found")
else:
    # Find the end of the function - look for next 'def ' or blank line followed by def
    rest = c[idx:]
    # The function ends after line processing loop - find the 'for line in lines:' loop
    end_of_loop = rest.find('\n    return y')
    if end_of_loop < 0:
        print("Could not find end of ft function")
    else:
        # Replace the entire function
        old_ft = rest[:end_of_loop + len('\n    return y')]
        new_ft = """def ft(d, text, x, y, font, fill, w=None, gap=6, align="left"):
    maxw = w or 9999
    lines = []
    for para in text.split('\\n'):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=font) <= maxw:
                cur += ch
            else:
                if cur: lines.append(cur)
                cur = ch
        if cur: lines.append(cur)
    for line in lines:
        xx = x
        if align == "center" and w:
            xx = x + (w - d.textlength(line, font=font)) // 2
        d.text((xx, y), line, font=font, fill=fill)
        y += font.size + gap
    return y"""
        c = c.replace(old_ft, new_ft)
        print("Replaced ft() to handle newlines")

# Same for wrapdraw function
idx = c.find('def wrapdraw(d, text, x, y, f, fill, w=None, gap=6, align="left"):')
if idx < 0:
    print("wrapdraw function not found")
else:
    rest = c[idx:]
    end_of_f = rest.find('\n    return y')
    if end_of_f >= 0:
        old_wd = rest[:end_of_f + len('\n    return y')]
        new_wd = """def wrapdraw(d, text, x, y, f, fill, w=None, gap=6, align="left"):
    maxw = w or 9999
    lines = []
    for para in text.split('\\n'):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=f) <= maxw:
                cur += ch
            else:
                if cur: lines.append(cur)
                cur = ch
        if cur: lines.append(cur)
    for line in lines:
        xx = x
        if align == "center" and w:
            xx = x + (w - d.textlength(line, font=f)) // 2
        d.text((xx, y), line, font=f, fill=fill)
        y += f.size + gap
    return y"""
        c = c.replace(old_wd, new_wd)
        print("Replaced wrapdraw() to handle newlines")

p.write_text(c, 'utf-8')

try:
    py_compile.compile(str(p), doraise=True)
    print('SYNTAX OK')
except py_compile.PyCompileError as e:
    print(f'ERROR: {e}')
