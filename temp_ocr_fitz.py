"""Tesseract OCR using PyMuPDF (no poppler needed)"""
import sys, os, glob, json
sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\政府合同\政府合同"
output_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\政府合同\ocr_output"
os.makedirs(output_dir, exist_ok=True)

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
results = {}

for idx, pdf_path in enumerate(pdfs):
    fname = os.path.basename(pdf_path)
    print(f"\n[{idx+1}/5] OCR: {fname}")
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        limit = min(total_pages, 18)
        print(f"  Total pages: {total_pages}, OCR first {limit}")
        
        full_text = ""
        for i in range(limit):
            page = doc[i]
            # Render at 200 DPI
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            page_text = pytesseract.image_to_string(img, lang='chi_sim')
            full_text += f"\n=== Page {i+1} ===\n{page_text}"
            
            if (i+1) % 5 == 0:
                print(f"  ... page {i+1}/{limit}")
        
        doc.close()
        
        txt_path = os.path.join(output_dir, fname.replace('.pdf', '.txt'))
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        results[fname] = {"chars": len(full_text), "pages": limit}
        print(f"  Saved: {txt_path} ({len(full_text)} chars)")

    except Exception as e:
        print(f"  ERROR: {e}")
        results[fname] = {"error": str(e)}

summary_path = os.path.join(output_dir, "_summary.json")
with open(summary_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n=== COMPLETE ===")
for k, v in results.items():
    print(f"  {k}: {v}")
