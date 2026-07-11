# -*- coding: utf-8 -*-
"""Extract text from audit docx files"""
import os

# Extract all 述职报告
report_dir = r'D:\openclaw-workspace\projects\护理学院任中经责审计\述职报告'

try:
    from docx import Document
except ImportError:
    print("Need python-docx: pip install python-docx")
    exit(1)

for f in sorted(os.listdir(report_dir)):
    if f.startswith('~$'):
        continue
    path = os.path.join(report_dir, f)
    print(f"\n{'='*60}")
    print(f"FILE: {f}")
    print('='*60)
    try:
        doc = Document(path)
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                print(text)
    except Exception as e:
        print(f"ERROR: {e}")
