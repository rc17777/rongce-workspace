# -*- coding: utf-8 -*-
"""Dump overview sheet"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import openpyxl

path = r"C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx"
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

ws = wb["☆算法资产库总览"]
rows = list(ws.iter_rows(values_only=True))
print("TOTAL ROWS:", len(rows))
for i, r in enumerate(rows[:5]):
    print(f"\n--- Row {i} ---")
    for j, cell in enumerate(r):
        print(f"  col{j}: {repr(cell)[:300]}")
