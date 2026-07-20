# -*- coding: utf-8 -*-
"""Extract text from org structure and meeting minutes docx files"""
import os
from docx import Document

base = r'D:\openclaw-workspace\projects\护理学院任中经责审计\任职分析'

# Find all docx files
for root, dirs, files in os.walk(base):
    for f in files:
        if not f.endswith('.docx') or f.startswith('~$'):
            continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, base)
        print(f'\n{"="*60}')
        print(f'FILE: {rel}')
        print('='*60)
        try:
            doc = Document(path)
            text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
            if len(text) > 2000:
                print(text[:2000])
                print(f'\n... [{len(text)} chars total]')
            else:
                print(text)
        except Exception as e:
            print(f'ERROR: {e}')
