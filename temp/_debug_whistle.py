import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Load batch4
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp\batch_algorithms_batch4.json', encoding='utf-8') as f:
    batch4 = json.load(f)

# Find WHISTLE-FLOW-001
for c in batch4:
    if c.get('sn') == 'WHISTLE-FLOW-001' or 'WHISTLE' in c.get('sn',''):
        name = c.get('name','')
        scene = c.get('scene','')
        biz = c.get('agent_map','')
        print("NAME:", repr(name[:200]))
        print("SCENE:", repr(scene[:200]))
        print("BIZ:", repr(biz[:100]))
        text = ' '.join([name, scene, biz])
        print()
        # Check against tax line kws
        tax_kws = ['税务','税','虚开','发票','货运','逃逸','注销','税源','开票']
        caikuai_kws = ['财会','监督','举报','受理','内控','报销']
        print("Tax kws hit:", [k for k in tax_kws if k in text])
        print("Caikuai kws hit:", [k for k in caikuai_kws if k in text])
        break

# Also check what card is in 财会监督
import openpyxl
wb = openpyxl.load_workbook(r'C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx')
ws3 = wb['☆业务场景地图']
for row in ws3.iter_rows(min_row=2, values_only=True):
    if row[0] and '财会' in str(row[0]):
        sns = str(row[3]) if row[3] else ''
        print(f"\nIn 财会监督: {sns[:200]}")
