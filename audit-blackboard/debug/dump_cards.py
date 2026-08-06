# -*- coding: utf-8 -*-
"""Explore detail cards sheet structure"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import openpyxl

path = r"C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx"
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
ws = wb["☆算法详细卡片"]
rows = list(ws.iter_rows(values_only=True))
print("TOTAL ROWS:", len(rows))
# Print first 80 rows raw
for i, r in enumerate(rows[:80]):
    cells = [str(c)[:120] if c is not None else "" for c in r]
    print(f"R{i}: {cells}")
