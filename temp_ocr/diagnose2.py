#!/usr/bin/env python3
# encoding: utf-8
import sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

FPATH = r"C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）\古英=2024-2025门诊、住院、个人账户、基金拨付明细\2025.xlsx"

import openpyxl
wb = openpyxl.load_workbook(FPATH, read_only=True, data_only=True)
ws = wb['总表']

# Collect Col29 values and also check if '降扎' appears anywhere
col29_vals = set()
col29_counter = Counter()
jz_in_any_col = 0

for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0: continue
    
    # Check if '降扎' in col29
    c29 = str(row[29]).strip() if len(row)>29 and row[29] else ""
    if c29:
        col29_counter[c29] += 1
        if len(col29_vals) < 100:
            col29_vals.add(c29)
        if '降扎' in c29:
            jz_in_any_col += 1
    
    if i % 50000 == 0:
        print(f"  scanned {i} rows...")

wb.close()

print("\n=== Col29 (医药机构名称) analysis ===")
print(f"Total unique institutions found (sampled): {len(col29_vals)}")

# Find all 降扎-related institutions
jz_institutions = [v for v in col29_counter if '降扎' in str(v)]
print(f"\nInstitutions with '降扎': {jz_institutions}")
for inst in jz_institutions:
    print(f"  {inst}: {col29_counter[inst]} rows")

# Also show top 30 institutions overall
print("\nTop 30 institutions in Col29:")
for inst, cnt in col29_counter.most_common(30):
    print(f"  {inst}: {cnt} rows")

# Show institutions with 降扎 in their codes
print("\nInstitutions whose code starts with 513232 (若尔盖 codes):")
for inst, cnt in col29_counter.most_common():
    if inst.startswith('H513232') or inst.startswith('P513232') or inst.startswith('513232'):
        print(f"  {inst}: {cnt} rows")
    if len([1 for i in [inst] if i.startswith(('H513232','P513232','513232'))]) == 0:
        continue

# Show ALL unique institution names
print(f"\n=== ALL {len(col29_counter)} unique institution names ===")
for inst, cnt in sorted(col29_counter.items(), key=lambda x: -x[1]):
    print(f"  '{inst}': {cnt} rows")
