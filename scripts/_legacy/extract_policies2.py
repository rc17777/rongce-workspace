# -*- coding: utf-8 -*-
import os, pdfplumber

base = r'D:\openclaw-workspace\projects\护理学院任中经责审计\制度分析'

# Use os.walk to find files by pattern
targets = {
    '资产(2022旧)': '56号',
    '资产(2025新)': '2025]78号',
    '采购(2023旧)': '2023]150号',
    '采购(2025新)': '2025]2号',
    '工程招标(2025)': '2025]1号',
    '验收(2025)': '2025]81号',
    '绩效评价(2025)': '2025]79号',
    '采购内控(2021)': '2021]179号',
}

found = {}
for root, dirs, files in os.walk(base):
    for f in files:
        for label, keyword in targets.items():
            if keyword in f and label not in found:
                found[label] = os.path.join(root, f)

for label, path in found.items():
    print(f'\n{"="*60}')
    print(f'{label}: {os.path.basename(path)}')
    print('='*60)
    try:
        with pdfplumber.open(path) as pdf:
            text = ''
            for page in pdf.pages[:6]:
                t = page.extract_text()
                if t:
                    text += t + '\n'
            text = text.strip()
            if len(text) > 2500:
                print(text[:2500])
                print(f'\n... [{len(text)} chars total, {len(pdf.pages)} pages]')
            else:
                print(text)
                print(f'\n[{len(pdf.pages)} pages]')
    except Exception as e:
        print(f'ERROR: {e}')
