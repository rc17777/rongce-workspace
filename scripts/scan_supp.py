# -*- coding: utf-8 -*-
import os

dir1 = r'C:\Users\scrccpa\Desktop\护理学院任中经济责任审计审计\国资处后续补充资料'
excel_file = r'C:\Users\scrccpa\Desktop\护理学院任中经济责任审计审计\周贤伟-四川护理职业学院中层领导干部经济责任审计问题清单-(1).xlsx'

print('===== 后续补充资料 =====')
for root, dirs, files in os.walk(dir1):
    for f in files:
        if f.startswith('~$'): continue
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        print(f'  {f} ({size/1024:.0f}KB)')

print(f'\n===== 问题清单 =====')
print(f'  {os.path.basename(excel_file)} ({os.path.getsize(excel_file)/1024:.0f}KB)')
