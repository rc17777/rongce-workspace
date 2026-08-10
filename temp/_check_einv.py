import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
wb = openpyxl.load_workbook(r'C:\Users\scrccpa\Desktop\算法\政府审计算法资产库_v5.xlsx')
ws1 = wb['☆算法资产库总览']
for r in ws1.iter_rows(min_row=2, values_only=True):
    if r[1] == 'EINV-CROSS-001':
        print('EINV-CROSS-001:')
        print('  name:', r[2])
        print('  scene:', r[4])
        print('  biz_line:', r[7])
        text = ' '.join([str(r[2] or ''), str(r[4] or ''), str(r[7] or '')])
        print('  full text:', text[:300])
        caikuai_kws = ['财会', '举报', '受理']
        print('  财会 kws hit:', [k for k in caikuai_kws if k in text])
        break
