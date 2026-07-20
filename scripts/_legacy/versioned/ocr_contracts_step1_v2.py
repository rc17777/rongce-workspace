"""
Step 1: Convert PDF first 2 pages to images using pypdfium2 (no poppler needed)
"""
import os, json, pypdfium2 as pdfium

PDF_DIR = r"D:\openclaw-workspace\data\contracts_pdf"
IMG_DIR = r"D:\openclaw-workspace\data\contract_images"

os.makedirs(IMG_DIR, exist_ok=True)

pdfs = []
for root, dirs, files in os.walk(PDF_DIR):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdfs.append(os.path.join(root, f))

manifest = []
for pdf_path in sorted(pdfs):
    rel = os.path.relpath(pdf_path, PDF_DIR)
    fname = os.path.splitext(os.path.basename(pdf_path))[0][:60]
    safe_name = fname.replace('\\', '_').replace('/', '_').replace(':', '_').replace(' ', '_')
    print(f"Rendering: {rel}")
    
    try:
        doc = pdfium.PdfDocument(pdf_path)
        n_pages = len(doc)
        # Render first 2 pages at 250 DPI
        page_files = []
        for i in range(min(2, n_pages)):
            page = doc[i]
            bitmap = page.render(scale=250/72)  # 72 DPI base, scale to 250
            pil_img = bitmap.to_pil()
            page_file = f"{safe_name}_p{i+1}.png"
            page_path = os.path.join(IMG_DIR, page_file)
            pil_img.save(page_path, "PNG")
            page_files.append(page_path)
            print(f"  Page {i+1}/{n_pages} -> {page_file}")
        
        manifest.append({
            "pdf": rel,
            "pdf_path": pdf_path,
            "total_pages": n_pages,
            "images": page_files
        })
        doc.close()
    except Exception as e:
        print(f"  ERROR: {e}")
        manifest.append({"pdf": rel, "pdf_path": pdf_path, "error": str(e)})

manifest_path = os.path.join(IMG_DIR, "manifest.json")
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\nDone: {len(pdfs)} PDFs, {sum(1 for m in manifest if 'images' in m)} successful")
print(f"Manifest: {manifest_path}")
