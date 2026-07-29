# encoding: utf-8
"""快速3页PaddleOCR测试 — 验证worker能否正常工作"""
import os, json, subprocess, sys, time

# Find books dir
BASE = r'E:\2026'
subdirs = [d for d in os.listdir(BASE) if '审计方法' in d]
BOOKS_DIR = os.path.join(BASE, subdirs[0], '审计相关书籍')

# Find smallest PDF
pdfs = []
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in files:
        if f.endswith('.pdf') and not f.startswith('~$'):
            fp = os.path.join(root, f)
            pdfs.append((fp, f, os.path.getsize(fp)))
pdfs.sort(key=lambda x: x[2])
smallest = pdfs[0]
print(f'PDF: {smallest[1]} ({smallest[2]/1024/1024:.1f}MB)', flush=True)

# But process only 3 pages for speed test
# write a 3-page only config
import fitz
doc = fitz.open(smallest[0])
total = len(doc)
pages_to_test = min(3, total)
print(f'Total pages: {total}, testing first {pages_to_test}', flush=True)

# Manual OCR test for 3 pages (in-process, no subprocess)
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)
import tempfile

t0 = time.time()
for i in range(pages_to_test):
    t_page = time.time()
    page = doc[i]
    mat = fitz.Matrix(200/72, 200/72)
    pix = page.get_pixmap(matrix=mat)
    
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp.write(pix.tobytes('png'))
    tmp.close()
    
    result = ocr.ocr(tmp.name, cls=True)
    os.unlink(tmp.name)
    
    lines = []
    confs = []
    if result and result[0]:
        for line in result[0]:
            lines.append(line[1][0])
            confs.append(line[1][1])
    text = '\n'.join(lines)
    avg_conf = sum(confs)/len(confs) if confs else 0.0
    
    elapsed = time.time() - t_page
    print(f'  Page {i+1}: {len(text)} chars, conf {avg_conf:.2%}, {elapsed:.1f}s', flush=True)
    if text:
        print(f'    Preview: {text[:100]}...', flush=True)

doc.close()
total_time = time.time() - t0
avg_per_page = total_time / pages_to_test
eta_208 = avg_per_page * 208
print(f'\nTotal: {total_time:.1f}s ({avg_per_page:.1f}s/page)', flush=True)
print(f'ETA for 208 pages: {eta_208:.0f}s ({eta_208/60:.1f}min)', flush=True)
