"""Fix Chinese-looking double quotes inside Python double-quoted strings"""
import re

path = r'C:\Users\scrccpa\.openclaw\workspace\temp_contract_xlsx.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace patterns like: "原为"工程完成审计后三个月内""
# The inner quotes are actual ASCII " (U+0022) being used as Chinese quotes
# We need to find them and replace with actual Chinese quotes \u201c \u201d

# Strategy: find Python string literals that contain inner double quotes
# that look like they're meant to be Chinese quotation marks
# Pattern: Chinese text followed by " (before another Chinese char)

# Specific known problematic strings and their fixes
fixes = [
    ('"2021年改为"交付满一年后"支付首次，实际是否已开始付费、付费金额是否合规、有无滞纳金"',
     "'2021年改为\\u201c交付满一年后\\u201d支付首次，实际是否已开始付费、付费金额是否合规、有无滞纳金'"),
]

for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed: {old[:50]}...")
    else:
        print(f"NOT FOUND: {old[:50]}...")

# Also do a more general fix: find "ChineseText" patterns inside Python strings
# Simple approach: find all remaining problematic double quotes
# Scan line by line
lines = content.split('\n')
fixed_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    # Check if this looks like a list element with double-quoted strings
    # having inner double quotes that break Python parsing
    if stripped.count('"') > 6 and ('[' in stripped or stripped.startswith('"')):
        # Count double quotes - if odd or clearly too many, flag it
        print(f"Line {i+1} has {stripped.count(chr(34))} double quotes: {stripped[:120]}...")
    fixed_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
