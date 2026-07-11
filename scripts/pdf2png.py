import fitz, os, sys
sys.stdout.reconfigure(encoding='utf-8')

pdfs = [
    r'D:\openclaw-workspace\temp\国有资产_renamed\pdf_1.pdf',
    r'D:\openclaw-workspace\temp\国有资产_renamed\pdf_2.pdf', 
    r'D:\openclaw-workspace\temp\国有资产_renamed\pdf_4.pdf',
]
names = ['四川起底式清查', '王保平_资源资产资本', '孙耀河_资产化管理']

outdir = r'D:\openclaw-workspace\temp\ocr_images'
os.makedirs(outdir, exist_ok=True)

for pdf_path, name in zip(pdfs, names):
    doc = fitz.open(pdf_path)
    print(f'\n=== {name}: {doc.page_count} pages ===')
    subdir = os.path.join(outdir, name)
    os.makedirs(subdir, exist_ok=True)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        outpath = os.path.join(subdir, f'page_{i+1:02d}.png')
        pix.save(outpath)
        print(f'  Page {i+1}/{doc.page_count} -> {outpath}')
    doc.close()
print('\nDone.')
