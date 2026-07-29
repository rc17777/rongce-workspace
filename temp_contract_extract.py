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
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        total = len(reader.pages)
        # Extract first 60 pages max (contract key terms are front-loaded)
        limit = min(total, 60)
        text = ""
        for i in range(limit):
            try:
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"
            except:
                pass
        
        # Print first 15000 chars per file
        print(text[:15000])
        if len(text) > 15000:
            print(f"\n... [truncated, total extracted {len(text)} chars from {limit}/{total} pages]")
    except Exception as e:
        print(f"ERROR: {e}")
