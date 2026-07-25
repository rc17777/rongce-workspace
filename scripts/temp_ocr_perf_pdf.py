"""OCR scanned PDFs using PyMuPDF + PaddleOCR"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

FILES = [
    r"C:\Users\scrccpa\Desktop\报告\绩效政策文件\四川省制度办法\20241122 四川省财政厅关于印发财政绩效监督"三管三必须"工作流程的通知（川财办[2024]39号）.pdf",
    r"C:\Users\scrccpa\Desktop\报告\绩效政策文件\四川省制度办法\20250924四川省财政厅关于印发《四川省部门预算绩效运行监控管理办法》的通知.pdf",
    r"C:\Users\scrccpa\Desktop\报告\绩效政策文件\四川省制度办法\20250924四川省财政厅关于印发《四川省预算绩效目标管理办法》的通知.pdf",
    r"C:\Users\scrccpa\Desktop\报告\绩效政策文件\四川省制度办法\20250924四川省财政厅关于印发《四川省预算绩效结果应用管理办法》的通知.pdf",
    r"C:\Users\scrccpa\Desktop\报告\绩效政策文件\四川省制度办法\20251218四川省财政厅关于印发《四川省预算绩效评估管理办法》的通知.pdf",
    r"C:\Users\scrccpa\Desktop\报告\绩效政策文件\四川省制度办法\（川财绩〔2025〕8号）20250903 四川省财政厅关于加强2026年度省级预算绩效目标管理和事前绩效评估等工作的通知\四川省财政厅关于加强2026年度省级预算绩效目标管理和事前绩效评估等工作的通知.pdf",
]

OUT_DIR = r"C:\Users\scrccpa\.openclaw\workspace\temp\perf_policy_texts"

import fitz
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import io

ocr = PaddleOCR(lang='ch', use_angle_cls=True, show_log=False)

for fpath in FILES:
    if not os.path.exists(fpath):
        print(f"NOT FOUND: {fpath}")
        continue
    
    basename = os.path.splitext(os.path.basename(fpath))[0]
    out_path = os.path.join(OUT_DIR, f"OCR_四川省制度办法__{basename}.txt")
    
    print(f"\nOCR: {basename} ...")
    
    try:
        doc = fitz.open(fpath)
        all_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image
            pix = page.get_pixmap(dpi=200)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img_np = np.array(img)
            
            result = ocr.ocr(img_np, cls=True)
            page_text = []
            if result and result[0]:
                for line in result[0]:
                    page_text.append(line[1][0])
            all_text.append(f"--- Page {page_num+1} ---\n" + "\n".join(page_text))
            print(f"  Page {page_num+1}/{len(doc)}: {len(page_text)} lines")
        
        full_text = "\n\n".join(all_text)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"  -> Saved {len(full_text)} chars to {out_path}")
        doc.close()
    except Exception as e:
        print(f"  ERROR: {e}")
