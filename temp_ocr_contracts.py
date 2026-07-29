"""OCR scan of first N pages of each contract PDF"""
import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\政府合同\政府合同"
output_dir = os.path.join(os.path.dirname(pdf_dir), "ocr_output")
os.makedirs(output_dir, exist_ok=True)

pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))

# Try PaddleOCR
try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(lang='ch', use_angle_cls=True, show_log=False)
    print("PaddleOCR initialized.")
except Exception as e:
    print(f"PaddleOCR failed: {e}")
    sys.exit(1)

from pdf2image import convert_from_path
import json

results = {}

for pdf_path in pdfs:
    fname = os.path.basename(pdf_path)
    print(f"\nProcessing: {fname}")
    
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=15, dpi=200)
        print(f"  Converted {len(images)} pages to images")
        
        full_text = ""
        for i, img in enumerate(images):
            img_path = os.path.join(output_dir, f"{fname}_p{i+1:03d}.png")
            img.save(img_path)
            
            ocr_result = ocr.ocr(img_path, cls=True)
            page_text = ""
            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    page_text += line[1][0] + "\n"
            
            full_text += f"\n--- Page {i+1} ---\n{page_text}"
            os.remove(img_path)  # cleanup
        
        # Save full OCR text
        txt_path = os.path.join(output_dir, fname.replace('.pdf', '.txt'))
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        results[fname] = {"chars": len(full_text), "lines": full_text.count(chr(10))}
        print(f"  Saved: {txt_path} ({len(full_text)} chars)")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results[fname] = {"error": str(e)}

# Save summary
with open(os.path.join(output_dir, "_summary.json"), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nAll done. Output: {output_dir}")
for k, v in results.items():
    print(f"  {k}: {v}")
