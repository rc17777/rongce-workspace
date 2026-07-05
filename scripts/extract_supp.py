# -*- coding: utf-8 -*-
"""Extract key data from supplementary materials"""
import os, openpyxl

base = r'D:\openclaw-workspace\projects\护理学院任中经责审计\补充资料'

# 1. Staff assignments
from docx import Document
staff_file = os.path.join(base, '国资处人员分工定稿.docx')
doc = Document(staff_file)
print("===== 国资处人员分工 =====")
for p in doc.paragraphs:
    if p.text.strip():
        print(p.text)

# 2. Procurement ledgers - count projects and total amounts
print("\n===== 采购台账统计 =====")
for f in sorted(os.listdir(base)):
    if '采购' not in f or '台账' not in f:
        continue
    path = os.path.join(base, f)
    if not f.endswith('.xlsx'):
        continue
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
        for sn in wb.sheetnames:
            ws = wb[sn]
            rows = ws.max_row
            cols = ws.max_column
            print(f'\n{f} / {sn}: {rows}行 x {cols}列')
            # Print header
            header = [ws.cell(1, c).value for c in range(1, cols+1)]
            print(f'  表头: {header}')
            # Print first 3 data rows
            for r in range(2, min(5, rows+1)):
                row_data = [ws.cell(r, c).value for c in range(1, cols+1)]
                print(f'  Row{r}: {row_data}')
    except Exception as e:
        print(f'  ERROR: {e}')

# 3. Land/building asset summary
print("\n===== 土地房屋资产 =====")
land_file = os.path.join(base, '两校区土地、房屋资产明细表.xlsx')
try:
    wb = openpyxl.load_workbook(land_file, data_only=True)
    for sn in wb.sheetnames:
        ws = wb[sn]
        print(f'\nSheet: {sn} ({ws.max_row}行 x {ws.max_column}列)')
        for r in range(1, min(ws.max_row+1, 15)):
            row_data = [ws.cell(r, c).value for c in range(1, ws.max_column+1)]
            if any(v is not None for v in row_data):
                print(f'  R{r}: {row_data}')
except Exception as e:
    print(f'  ERROR: {e}')
