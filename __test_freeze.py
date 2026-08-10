# -*- coding: utf-8 -*-
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
print('freeze_panes available:', hasattr(ws, 'freeze_panes'))
if hasattr(ws, 'freeze_panes'):
    ws.freeze_panes(2)
    print('freeze_panes called successfully')
else:
    print('freeze_panes not available')
wb.save('test.xlsx')