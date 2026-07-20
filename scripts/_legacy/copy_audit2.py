# -*- coding: utf-8 -*-
import os, shutil

desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')

# Find all items under the audit directory
for root, dirs, files in os.walk(desktop):
    if '护理学院任中经济责任审计审计' not in root:
        continue
    
    # Report files - look for 述职
    if '述职' in root:
        dst = r'D:\openclaw-workspace\projects\护理学院任中经责审计\述职报告'
        os.makedirs(dst, exist_ok=True)
        for f in files:
            if f.startswith('~$'): continue
            shutil.copy2(os.path.join(root, f), os.path.join(dst, f))
            print(f'OK report: {f}')

    # Meeting minutes
    if '会议纪要' in root or '会议记录' in root:
        # Get relative path
        parts = root.split('递交经责审计资料')
        if len(parts) > 1:
            rel = parts[1].lstrip('\\').lstrip('/').lstrip('（第一次，20260415，李欣）').lstrip('\\').lstrip('/')
        else:
            rel = os.path.basename(root)
        dst = os.path.join(r'D:\openclaw-workspace\projects\护理学院任中经责审计\任职分析', rel)
        os.makedirs(dst, exist_ok=True)
        for f in files:
            if f.startswith('~$'): continue
            try:
                shutil.copy2(os.path.join(root, f), os.path.join(dst, f))
            except:
                pass
        print(f'OK minutes: {rel} ({len([f for f in files if not f.startswith("~$")])} files)')

    # Major decisions
    if '重大经济决策' in root or '重大决策' in root:
        parts = root.split('递交经责审计资料')
        if len(parts) > 1:
            rel = parts[1].lstrip('\\').lstrip('/').lstrip('（第一次，20260415，李欣）').lstrip('\\').lstrip('/')
        else:
            rel = os.path.basename(root)
        dst = os.path.join(r'D:\openclaw-workspace\projects\护理学院任中经责审计\任职分析', rel)
        os.makedirs(dst, exist_ok=True)
        for f in files:
            if f.startswith('~$'): continue
            try:
                shutil.copy2(os.path.join(root, f), os.path.join(dst, f))
            except:
                pass
        print(f'OK decisions: {rel} ({len([f for f in files if not f.startswith("~$")])} files)')

    # Org structure
    if '机构设置' in root or '内控制度' in root:
        parts = root.split('递交经责审计资料')
        if len(parts) > 1:
            rel = parts[1].lstrip('\\').lstrip('/').lstrip('（第一次，20260415，李欣）').lstrip('\\').lstrip('/')
        else:
            rel = os.path.basename(root)
        dst = os.path.join(r'D:\openclaw-workspace\projects\护理学院任中经责审计\任职分析', rel)
        os.makedirs(dst, exist_ok=True)
        for f in files:
            if f.startswith('~$'): continue
            try:
                shutil.copy2(os.path.join(root, f), os.path.join(dst, f))
            except:
                pass
        print(f'OK org: {rel} ({len([f for f in files if not f.startswith("~$")])} files)')

print('\nDone!')
