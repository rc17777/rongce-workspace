"""
Step 1: Convert first 2 pages of each contract PDF to images
"""
import os
import json
from pdf2image import convert_from_path

BASE = r"C:\Users\scrccpa\Desktop\成都轨道资源资料\业主发送资料\天府广场项目2026年专项审计资料清单（第一批）\1合同协议"
OUT = r"D:\openclaw-workspace\data\contract_images"

os.makedirs(OUT, exist_ok=True)

# Collect all PDFs
pdfs = []
for root, dirs, files in os.walk(BASE):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdfs.append(os.path.join(root, f))

manifest = []

for pdf_path in pdfs:
    rel = os.path.relpath(pdf_path, BASE)
    fname = os.path.splitext(os.path.basename(pdf_path))[0]
    safe_name = fname[:60].replace('\\', '_').replace('/', '_').replace(':', '_')
    print(f"Processing: {rel}")
    
    try:
        # Convert first 2 pages at 250 DPI
        images = convert_from_path(pdf_path, first_page=1, last_page=2, dpi=250)
        
        page_files = []
        for idx, img in enumerate(images):
            page_file = f"{safe_name}_p{idx+1}.png"
            page_path = os.path.join(OUT, page_file)
            img.save(page_path, "PNG")
            page_files.append(page_path)
        
        manifest.append({
            "pdf": rel,
            "pdf_path": pdf_path,
            "pages": len(images),
            "images": page_files
        })
        print(f"  -> {len(images)} pages saved")
    except Exception as e:
        print(f"  ERROR: {e}")
        manifest.append({
            "pdf": rel,
            "pdf_path": pdf_path,
            "pages": 0,
            "error": str(e)
        })

# Save manifest
manifest_path = os.path.join(OUT, "manifest.json")
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\nTotal: {len(pdfs)} PDFs processed")
print(f"Manifest saved to: {manifest_path}")
