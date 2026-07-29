"""OCR scan of contract PDFs using PyMuPDF + pytesseract (fast)"""
import sys, os, glob, json, gc, io
sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\政府合同\政府合同"
output_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\政府合同\ocr_output"
os.makedirs(output_dir, exist_ok=True)

pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
print(f"Found {len(pdfs)} PDFs in {pdf_dir}")
for p in pdfs:
    print(f"  {os.path.basename(p)} ({os.path.getsize(p)//1024} KB)")

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Config
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
LANG = 'chi_sim+eng'
DPI = 250

# Max pages per file
PAGE_LIMITS = {
    "1.恩阳医养园PPP项目协议.pdf": 30,
    "2.恩阳医养园PPP项目合同.pdf": 30,
    "3.恩阳医养园PPP项目合同之补充合同（2017年）.pdf": 10,
    "4.恩阳医养园PPP项目合同之补充合同（2018年）.pdf": 10,
    "5.恩阳医养园PPP项目合同之补充合同（2021年）.pdf": 10,
}

results = {}

for pdf_path in pdfs:
    fname = os.path.basename(pdf_path)
    max_pages = PAGE_LIMITS.get(fname, 15)
    
    print(f"\n{'='*60}")
    print(f"Processing: {fname} (first {max_pages} pages)")
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_to_ocr = min(max_pages, total_pages)
        print(f"  PDF has {total_pages} pages, OCRing {pages_to_ocr}")
        
        full_text = ""
        for i in range(pages_to_ocr):
            print(f"  Page {i+1}/{pages_to_ocr}...", end=" ", flush=True)
            
            # Render page to image
            page = doc[i]
            mat = fitz.Matrix(DPI/72, DPI/72)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            # OCR with Tesseract
            page_text = pytesseract.image_to_string(img, lang=LANG)
            
            full_text += f"\n--- Page {i+1} ---\n{page_text}"
            print(f"({len(page_text)} chars)")
            
            del page, pix, img, img_bytes
            gc.collect()
        
        doc.close()
        
        # Save OCR text
        txt_name = fname.replace('.pdf', '.txt')
        txt_path = os.path.join(output_dir, txt_name)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        char_count = len(full_text)
        line_count = full_text.count('\n')
        results[fname] = {"chars": char_count, "lines": line_count, "pages": pages_to_ocr}
        print(f"  ✓ Saved: {txt_name}")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results[fname] = {"error": str(e)}
    
    gc.collect()

summary_path = os.path.join(output_dir, "_summary.json")
with open(summary_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"All done! Results:")
for k, v in results.items():
    status = "✓" if "chars" in v else f"✗"
    detail = f"({v['chars']} chars, {v['lines']} lines, {v.get('pages','?')} pages)" if "chars" in v else f"ERROR: {v.get('error','?')}"
    print(f"  {status} {k}: {detail}")
