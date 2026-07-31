#!/usr/bin/env python3
# encoding: utf-8
import sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

FPATH = r"C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）\古英=2024-2025门诊、住院、个人账户、基金拨付明细\2025.xlsx"

import openpyxl
wb = openpyxl.load_workbook(FPATH, read_only=True, data_only=True)
ws = wb['总表']

col29 = Counter()
jz_col29 = []
first_20_data = []

for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0:
        # Print header Col28-30 for context
        h28 = row[28] if len(row)>28 else ""
        h29 = row[29] if len(row)>29 else ""
        h30 = row[30] if len(row)>30 else ""
        print(f"Headers: Col28={h28}, Col29={h29}, Col30={h30}")
        continue
    
    if len(row) > 29 and row[29]:
        v = str(row[29]).strip()
        col29[v] += 1
        if '降扎' in v:
            jz_col29.append(v)
    
    if i <= 10:
        rlist = [str(c)[:30] if c else "" for c in row[:50]]
        first_20_data.append(rlist)

    if i % 50000 == 0 and i > 0:
        print(f"  scanned {i} rows...")

wb.close()

print(f"\n=== 降扎 in Col29 ===")
if jz_col29:
    for v in set(jz_col29):
        print(f"  '{v}': {col29[v]} rows")
else:
    print("  None found!")
    # Show institutions from 若尔盖 area
    ruoergai = [(k,v) for k,v in col29.items() if '若尔盖' in k or '降扎' in k]
    if ruoergai:
        print("  若尔盖 related:")
        for k,v in sorted(ruoergai, key=lambda x:-x[1]):
            print(f"    '{k}': {v} rows")

print(f"\n=== Top 50 institutions ===")
for inst, cnt in col29.most_common(50):
    print(f"  '{inst}': {cnt} rows")

print(f"\n=== First few data rows (Cols 0-49) ===")
for idx, row_data in enumerate(first_20_data[:5]):
    print(f"  Row {idx+2}:")
    for j, val in enumerate(row_data):
        if val:
            print(f"    Col{j}: {val}")
