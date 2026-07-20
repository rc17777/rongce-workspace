# -*- coding: utf-8 -*-
import os, shutil

# Walk desktop to find the audit directories
desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')

# Find 护理学院 audit directories
for root, dirs, files in os.walk(desktop):
    if '护理学院任中经济责任审计审计' not in root:
        continue
    
    # Copy 述职报告
    if '个人述职报告' in root:
        dst = r'D:\openclaw-workspace\projects\护理学院任中经责审计\述职报告'
        os.makedirs(dst, exist_ok=True)
        for f in files:
            if f.startswith('~$'): 
                continue
            src = os.path.join(root, f)
            out = os.path.join(dst, f)
            shutil.copy2(src, out)
            print(f'OK report: {f}')
    
    # Copy 制度文件
    if '国资处有关制度' in root:
        rel = root.split('国资处有关制度')[-1].lstrip('\\').lstrip('/')
        if rel:
            dst = os.path.join(r'D:\openclaw-workspace\projects\护理学院任中经责审计\制度分析', rel)
        else:
            dst = r'D:\openclaw-workspace\projects\护理学院任中经责审计\制度分析'
        os.makedirs(dst, exist_ok=True)
        for f in files:
            if f.startswith('~$'):
                continue
            src = os.path.join(root, f)
            out = os.path.join(dst, f)
            shutil.copy2(src, out)
            print(f'OK policy: {f[:60]}')

print('\nDone!')
