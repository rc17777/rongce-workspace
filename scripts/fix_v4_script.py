# -*- coding: utf-8 -*-
"""Fix v4 script: replace broken make_digital, rename page*_ functions"""
from pathlib import Path
import py_compile

p = Path(r"C:\Users\scrccpa\.openclaw\workspace\scripts\generate_rongce_brochure_v4.py")
content = p.read_text('utf-8')

# The broken make_digital starts with this exact text (Unicode-escaped):
old = 'def make_digital():\n    return make_service_page(\n        "\\u6570\\u5b57\\u5316\\u5ba1\\u8ba1\\u80fd\\u529b", "DIGITAL AUDIT CAPABILITIES",\n        "\\u7528\\u6570\\u636e\\u6269\\u5927\\u8986\\u76d6\\u9762\\u3001\\u63d0\\u9ad8\\u53d1\\u73b0\\u7387\\u3001\\u589e\\u5f3a\\u8bc1\\u636e\\u8d28\\u91cf\\u2014\\u2014\\u628a\\u5ba1\\u8ba1\\u7ecf\\u9a8c\\u6c89\\u6dc0\\u4e3a\\u53ef\\u590d\\u7528\\u7684\\u6570\\u636e\\u5de5\\u5177\\u3002",\n        [("\\u6570\\u636e\\u6807\\u51c6", ["\\u8d22\\u52a1\\u3001\\u9884\\u7b97\\u3001\\u652f\\u4ed8\\u3001\\u5408\\u540c", "\\u91c7\\u8d2d\\u3001\\u8d44\\u4ea7\\u3001\\u5de5\\u7a0b\\u9879\\u76ee\\u5b57\\u6bb5\\u6574\\u7406"]),\n         ("\\u89c4\\u5219\\u6a21\\u578b", ["\\u91cd\\u590d\\u652f\\u4ed8\\u3001\\u8d85\\u9884\\u7b97\\u6267\\u884c\\u8bc6\\u522b", "\\u4f9b\\u5e94\\u5546\\u5f02\\u5e38\\u3001\\u8d44\\u91d1\\u6c89\\u6dc0\\u68c0\\u6d4b"]),\n         ("\\u7a7f\\u900f\\u6838\\u67e5", ["\\u7591\\u70b9\\u6765\\u6e90\\u3001\\u6838\\u67e5\\u8def\\u5f84", "\\u4f50\\u8bc1\\u6750\\u6599\\u3001\\u5f71\\u54cd\\u91d1\\u989d\\u3001\\u6574\\u6539\\u5efa\\u8bae"]),\n         ("\\u62a5\\u544a\\u590d\\u6838", ["\\u91d1\\u989d\\u6c47\\u603b\\u6821\\u9a8c\\u3001\\u53e3\\u5f84\\u4e00\\u81f4\\u6027", "\\u9644\\u8868\\u'

# The fix: replace with properly closed make_digital that matches the Unicode-escaped style
new = 'def make_digital():\n    return make_service_page(\n        "\\u6570\\u5b57\\u5316\\u5ba1\\u8ba1\\u80fd\\u529b", "DIGITAL AUDIT CAPABILITIES",\n        "\\u7528\\u6570\\u636e\\u6269\\u5927\\u8986\\u76d6\\u9762\\u3001\\u63d0\\u9ad8\\u53d1\\u73b0\\u7387\\u3001\\u589e\\u5f3a\\u8bc1\\u636e\\u8d28\\u91cf\\u2014\\u2014\\u628a\\u5ba1\\u8ba1\\u7ecf\\u9a8c\\u6c89\\u6dc0\\u4e3a\\u53ef\\u590d\\u7528\\u7684\\u6570\\u636e\\u5de5\\u5177\\u3002",\n        [("\\u6570\\u636e\\u6807\\u51c6", ["\\u8d22\\u52a1\\u3001\\u9884\\u7b97\\u3001\\u652f\\u4ed8\\u3001\\u5408\\u540c", "\\u91c7\\u8d2d\\u3001\\u8d44\\u4ea7\\u3001\\u5de5\\u7a0b\\u9879\\u76ee\\u5b57\\u6bb5\\u6574\\u7406"]),\n         ("\\u89c4\\u5219\\u6a21\\u578b", ["\\u91cd\\u590d\\u652f\\u4ed8\\u3001\\u8d85\\u9884\\u7b97\\u6267\\u884c\\u8bc6\\u522b", "\\u4f9b\\u5e94\\u5546\\u5f02\\u5e38\\u3001\\u8d44\\u91d1\\u6c89\\u6dc0\\u68c0\\u6d4b"]),\n         ("\\u7a7f\\u900f\\u6838\\u67e5", ["\\u7591\\u70b9\\u6765\\u6e90\\u3001\\u6838\\u67e5\\u8def\\u5f84", "\\u4f50\\u8bc1\\u6750\\u6599\\u3001\\u5f71\\u54cd\\u91d1\\u989d\\u3001\\u6574\\u6539\\u5efa\\u8bae"]),\n         ("\\u62a5\\u544a\\u590d\\u6838", ["\\u91d1\\u989d\\u6c47\\u603b\\u6821\\u9a8c\\u3001\\u53e3\\u5f84\\u4e00\\u81f4\\u6027", "\\u9644\\u8868\\u95ed\\u73af\\u3001\\u7ed3\\u8bba\\u4f9d\\u636e\\u53ef\\u8ffd\\u6eaf"])], 5)'

if old in content:
    content = content.replace(old, new)
    print("Replaced broken make_digital (unicode-escaped version)")
else:
    print("Exact pattern not found; checking alternative matches...")
    # Try to find by function name
    idx = content.find('def make_digital():')
    if idx >= 0:
        # Find the next 'def ' after this one
        next_def = content.find('\ndef ', idx + 20)
        if next_def < 0:
            next_def = len(content)
        print(f"  make_digital at {idx}, next def at {next_def}")
    else:
        print("  No make_digital found at all")

# Replace page*_ function names (these have plain Chinese, no Unicode escapes)
# These pages have plain Chinese text in the appended tail

replacements = [
    # Fix service_page -> make_service_page calls in the tail
    ("    return service_page(", "    return make_service_page("),
    # Fix page*_ names
    ("def page8_digital():", "def _make_digital_v2():"),
    ("def page9_experience():", "def make_experience():"),
    ("def page10_contact():", "def make_contact():"),
    # Fix main() references
    ("page1_cover, page2_about, page3_method, page4_services",
     "make_cover, make_about, make_method, make_services_overview"),
    ("page5_gov, page6_perf, page7_eng, page8_digital",
     "make_gov_audit, make_performance, make_engineering, make_digital"),
    ("page9_experience, page10_contact",
     "make_experience, make_contact"),
    # Fix missing variable references in appended code
    ("DOCX", "DOCX_PATH"),
    ("PDF_", "PDF_PATH"),
    ("WK", "WORK_DIR"),
]

for old_r, new_r in replacements:
    if old_r in content:
        content = content.replace(old_r, new_r)
        print(f"  Replaced: {old_r[:50]}...")

p.write_text(content, 'utf-8')
print(f"Fixed. Final size: {p.stat().st_size} bytes")

# Syntax check
try:
    py_compile.compile(str(p), doraise=True)
    print("SYNTAX OK - script is valid Python")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    # Show lines around the error
    lines = content.splitlines()
    err_line = int(str(e).split('line ')[1].split('\n')[0])
    for i in range(max(0, err_line-3), min(len(lines), err_line+2)):
        mark = '>>>' if i == err_line-1 else '   '
        print(f'{mark}{i+1}: {lines[i][:120]}')
