# -*- coding: utf-8 -*-
"""提取结算清单xlsx"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl

path = r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\3、鼎函九筹会议公司资料\制造业数字化转型促进中心“深度行”四川站活动暨“智改数转”供需对接会活动结算清单（604）.xlsx'
wb = openpyxl.load_workbook(path, data_only=True)
out = []
for ws in wb.worksheets:
    out.append(f'=== Sheet: {ws.title} (dims: {ws.dimensions}) ===')
    for row in ws.iter_rows(values_only=True):
        vals = ['' if v is None else str(v) for v in row]
        if any(v.strip() for v in vals):
            out.append(' | '.join(vals))
text = '\n'.join(out)
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp_review\settlement_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print(f'提取完成，共 {len(text)} 字符')
