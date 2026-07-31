#!/usr/bin/env python3
# encoding: utf-8
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

FPATH = r"C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）\古英=2024-2025门诊、住院、个人账户、基金拨付明细\2025.xlsx"

import openpyxl
wb = openpyxl.load_workbook(FPATH, read_only=True, data_only=True)
ws = wb['总表']

# Quick strategy: collect unique Col29 + count, but check if 降扎 appears in Col29
# Also collect Col28 (institution code) for 若尔盖-related codes
col29_vals = {}
col28_vals = {}
ruoergai_col29 = []
any_jiangzha = False
row_idx = 0

for row in ws.iter_rows(values_only=True):
    row_idx += 1
    if row_idx % 50000 == 0:
        print(f"  scanned {row_idx} rows...")
    
    if len(row) > 29 and row[29]:
        v29 = str(row[29]).strip()
        if v29 not in col29_vals:
            col29_vals[v29] = 0
        col29_vals[v29] += 1
        if '降扎' in v29:
            any_jiangzha = True
            print(f"  FOUND 降扎 in Col29: '{v29}' at row {row_idx}")
        if '若尔盖' in v29:
            ruoergai_col29.append(v29)
    
    if len(row) > 28 and row[28]:
        v28 = str(row[28]).strip()
        if v28 not in col28_vals:
            col28_vals[v28] = 0
        col28_vals[v28] += 1

wb.close()
print(f"\nTotal rows scanned: {row_idx}")

if any_jiangzha:
    print("降扎 found in Col29!")
else:
    print("降扎 NOT found in Col29")
    
print(f"\n若尔盖-related institutions in Col29:")
ruoergai_set = set(ruoergai_col29)
for v in ruoergai_set:
    print(f"  '{v}': {col29_vals.get(v, 0)} rows")

# Check for codes that might be 降扎乡卫生院
print(f"\nInstitutions with codes starting with H513232 or P513232:")
for code, cnt in sorted(col28_vals.items(), key=lambda x:-x[1]):
    if '513232' in code[:15]:
        print(f"  '{code}': {cnt} rows (Col29 name: {[k for k,v in col29_vals.items() if k.startswith(code[:6]) or code[:6] in k][:3]})")
    if sum(1 for c in [code] if '513232' in c) == 0:
        continue
