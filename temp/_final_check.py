import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
wb = openpyxl.load_workbook(r'C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx')
ws3 = wb['☆业务场景地图']
lines = {}
for row in ws3.iter_rows(min_row=2, values_only=True):
    if row[0] and row[3]:
        lines[row[0]] = row[3].split(chr(10))
covered = set()
for ln in sorted(lines.keys()):
    covered.update(lines[ln])
    print(f"  {ln}: {len(lines[ln])}")
print(f"\nTotal: {len(lines)} lines | Covered: {len(covered)}/135")
# Check NATRES and key cards
targets = ['NATRES-AUDIT-001','ASSET-REVIVE-001','BUDGET-006','ASSET-MATCH-001',
           'WHISTLE-FLOW-001','EINV-CROSS-001','CHK2-001']
for t in targets:
    for ln, sns in lines.items():
        if t in sns:
            print(f"  {t} → {ln}")
            break
