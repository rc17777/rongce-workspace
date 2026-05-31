# -*- coding: utf-8 -*-
"""Extract text from key policy PDFs using pdfplumber"""
import os, pdfplumber

base = r'D:\openclaw-workspace\projects\护理学院任中经责审计\制度分析'

# Key policy files to extract
key_files = [
    # 国有资产管理
    os.path.join('国有资产管理制度', '川护职院发〔2022〕56号关于印发《四川护理职业学院国有资产管理办法》的通知.pdf'),
    os.path.join('新增制度', '川护职院发〔2025〕78号《四川护理职业学院国有资产管理办法》.pdf'),
    # 采购管理
    os.path.join('招标采购制度', '川护职院发〔2023〕150号关于印发《四川护理职业学院采购管理办法》的通知.pdf'),
    os.path.join('新增制度', '川护职院发〔2025〕2号关于印发《四川护理职业学院采购管理办法（修订）》的通知.pdf'),
    # 招标
    os.path.join('新增制度', '川护职院发〔2025〕1号四川护理职业学院基本建设工程招标管理办法.pdf'),
    # 验收
    os.path.join('新增制度', '川护职院发〔2025〕81号四川护理职业学院货物和服务履约验收实施细则.pdf'),
    # 绩效
    os.path.join('新增制度', '川护职院发〔2025〕79号四川护理职业学院国有资产管理绩效评价办法（试行）.pdf'),
]

for fname in key_files:
    path = os.path.join(base, fname)
    if not os.path.exists(path):
        print(f'\n!! NOT FOUND: {fname}')
        continue
    print(f'\n{"="*60}')
    print(f'FILE: {os.path.basename(fname)}')
    print('='*60)
    try:
        with pdfplumber.open(path) as pdf:
            text = ''
            for page in pdf.pages[:8]:  # first 8 pages
                t = page.extract_text()
                if t:
                    text += t + '\n'
            # Print first 3000 chars
            if len(text) > 3000:
                print(text[:3000] + '\n... [TRUNCATED]')
            else:
                print(text)
            print(f'\n[Total pages: {len(pdf.pages)}, extracted: {len(text)} chars]')
    except Exception as e:
        print(f'ERROR: {e}')
