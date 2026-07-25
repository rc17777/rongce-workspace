#!/usr/bin/env python
"""Extract text from PDF files."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

try:
    import fitz  # PyMuPDF
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyMuPDF', '-q'])
    import fitz

desktop = r'C:\Users\scrccpa\Desktop'
files = [f for f in os.listdir(desktop) if '十五五' in f or '注册会计师' in f]

for fname in files:
    fpath = os.path.join(desktop, fname)
    print(f"\n{'='*80}")
    print(f"FILE: {fname}")
    print(f"{'='*80}")
    try:
        doc = fitz.open(fpath)
        print(f"Pages: {len(doc)}")
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                print(f"\n--- Page {i+1} ---")
                print(text)
    except Exception as e:
        print(f"ERROR: {e}")
