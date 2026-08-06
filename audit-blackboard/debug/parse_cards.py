# -*- coding: utf-8 -*-
"""Parse all cards from detail sheet, dump to JSON"""
import sys, re, json
sys.stdout.reconfigure(encoding="utf-8")
import openpyxl

path = r"C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx"
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
ws = wb["☆算法详细卡片"]

cards = {}
order = []
cur = None
for row in ws.iter_rows(values_only=True):
    a = str(row[0]).strip() if row[0] else ""
    b = str(row[1]).strip() if row[1] else ""
    c = str(row[2]).strip() if row[2] else ""
    m = re.match(r"^算法卡[:：]\s*([A-Z0-9\-]+)", a)
    if m:
        cur = m.group(1)
        cards[cur] = {}
        order.append(cur)
    elif cur and a and a != "要素名称":
        cards[cur][a] = c

print("Cards found:", len(cards))
print("Order count:", len(order))
# element count distribution
from collections import Counter
cnt = Counter(len(v) for v in cards.values())
print("Elements per card dist:", dict(cnt))

# Show one skeleton card fully (BUDGET-001)
print("\n=== BUDGET-001 card ===")
for k, v in cards.get("BUDGET-001", {}).items():
    print(f"  [{k}] {v[:200] if v else ''}")

# Show one batch4 skeleton (EINV-CROSS-001)
print("\n=== EINV-CROSS-001 card ===")
for k, v in cards.get("EINV-CROSS-001", {}).items():
    print(f"  [{k}] {v[:200] if v else ''}")

# Which overview SNs missing from cards?
ov = [r["编号"] for r in json.load(open(r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\debug\overview_v5.json", encoding="utf-8"))]
missing = [s for s in ov if s not in cards]
extra = [s for s in cards if s not in ov]
print("\nMissing from cards:", missing)
print("Extra in cards:", extra)

with open(r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\debug\cards_v5.json", "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=1)
print("cards_v5.json written")
