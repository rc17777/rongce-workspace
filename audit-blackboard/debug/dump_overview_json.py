# -*- coding: utf-8 -*-
"""Dump full overview to JSON file for review"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import openpyxl, json

path = r"C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx"
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
ws = wb["☆算法资产库总览"]
rows = list(ws.iter_rows(values_only=True))
header = rows[0]
data = [dict(zip(header, r)) for r in rows[1:] if any(r)]

out = []
for r in data:
    out.append({
        "序号": r["序号"], "编号": r["算法编号"], "名称": r["算法名称"],
        "类型": r["类型(旗舰/骨架)"], "场景": r["适用场景"],
        "风险机制": r["风险机制"], "复杂度": r["复杂度(L2/L3)"],
        "业务线": r["业务线"], "Agent映射": r["Agent映射"],
        "批次": r["来源批次"], "状态": r["状态"],
    })

with open(r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\debug\overview_v5.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", len(out))
