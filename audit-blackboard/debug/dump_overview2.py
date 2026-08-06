# -*- coding: utf-8 -*-
"""Dump full overview sheet to JSON for inspection"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import openpyxl, json

path = r"C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx"
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
ws = wb["☆算法资产库总览"]
rows = list(ws.iter_rows(values_only=True))
header = rows[0]
data = [dict(zip(header, r)) for r in rows[1:] if any(r)]
print("Data rows:", len(data))

# Check last rows
for r in data[-3:]:
    print(json.dumps(r, ensure_ascii=False)[:400])

# List all IDs
ids = [r["算法编号"] for r in data]
print("\nTotal IDs:", len(ids))
print("Unique IDs:", len(set(ids)))
print("\nAll IDs:")
for i in range(0, len(ids), 10):
    print("  " + ", ".join(str(x) for x in ids[i:i+10]))

# Type distribution
from collections import Counter
print("\nType dist:", Counter(str(r["类型(旗舰/骨架)"]) for r in data))
print("Complexity dist:", Counter(str(r["复杂度(L2/L3)"]) for r in data))
print("Agent映射 dist:")
for k, v in Counter(str(r["Agent映射"]) for r in data).most_common():
    print(f"  {k}: {v}")
