# -*- coding: utf-8 -*-
"""Batch extract key remaining policy PDFs and save as text"""
import os, pdfplumber, json

base = r'D:\openclaw-workspace\projects\护理学院任中经责审计\制度分析'
out_dir = r'D:\openclaw-workspace\projects\护理学院任中经责审计\制度分析\_extracted'
os.makedirs(out_dir, exist_ok=True)

# All PDF files
for root, dirs, files in os.walk(base):
    for f in files:
        if not f.endswith('.pdf'):
            continue
        path = os.path.join(root, f)
        rel_dir = os.path.relpath(root, base)
        safe_name = f.replace('/', '_')[:80]
        out_path = os.path.join(out_dir, f'{rel_dir}__{safe_name}.txt'.replace('\\','_'))
        
        print(f'Extracting: {f[:60]}...')
        try:
            with pdfplumber.open(path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                full = '\n\n'.join(pages_text)
                with open(out_path, 'w', encoding='utf-8') as out:
                    out.write(full)
                print(f'  -> {len(pdf.pages)} pages, {len(full)} chars OK')
        except Exception as e:
            print(f'  -> ERROR: {e}')

print('\nAll done!')
