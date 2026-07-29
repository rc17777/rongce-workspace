import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\政府合同\政府合同"
pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))

for pdf_path in pdfs:
    fname = os.path.basename(pdf_path)
    print(f"\n{'='*80}")
    print(f"FILE: {fname}")
    print(f"{'='*80}")
    
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            limit = min(total, 50)
            text = ""
            for i in range(limit):
                try:
                    page = pdf.pages[i]
                    pt = page.extract_text()
                    if pt:
                        text += pt + "\n"
                except:
                    pass
            if text.strip():
                print(text[:12000])
                if len(text) > 12000:
                    print(f"\n... [truncated, {len(text)} chars from {limit}/{total} pages]")
            else:
                # Check if image-based
                page0 = pdf.pages[0]
                imgs = page0.images if hasattr(page0, 'images') else []
                print(f"[No text extractable, page has {len(imgs)} images - likely scanned PDF]")
    except Exception as e:
        print(f"ERROR: {e}")
