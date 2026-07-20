# -*- coding: utf-8 -*-
"""全过程控制招标资料+合同 OCR（扫描件）"""
import os, sys, time
sys.stdout.reconfigure(encoding='utf-8')
import fitz
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

BASE = r'C:\Users\scrccpa\.openclaw\workspace\projects\新建文件夹审核'
RAW = os.path.join(BASE, 'raw_data')
OUT = os.path.join(BASE, 'ocr_out')
os.makedirs(OUT, exist_ok=True)

FILES = ['全过程控制合同.pdf', '全过程控制的招标资料(1).pdf']

ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

for fname in FILES:
    src = os.path.join(RAW, fname)
    dst = os.path.join(OUT, fname.replace('.pdf', '.txt'))
    doc = fitz.open(src)
    n = len(doc)
    print(f'=== {fname}: {n} pages ===', flush=True)
    with open(dst, 'w', encoding='utf-8') as f:
        for i in range(n):
            t0 = time.time()
            page = doc[i]
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
            arr = np.array(img)
            try:
                res = ocr.ocr(arr, cls=True)
                lines = []
                if res and res[0]:
                    for line in res[0]:
                        lines.append(line[1][0])
                text = '\n'.join(lines)
            except Exception as e:
                text = f'[OCR_ERROR] {e}'
            f.write(f'\n===== PAGE {i+1}/{n} =====\n{text}\n')
            f.flush()
            print(f'  p{i+1}/{n} {time.time()-t0:.1f}s chars={len(text)}', flush=True)
    doc.close()
print('ALL DONE', flush=True)
