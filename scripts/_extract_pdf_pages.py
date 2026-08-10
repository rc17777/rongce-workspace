"""Extract brochure pages as images"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import fitz

pdf_path = r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10.pdf'
out_dir = r'C:\Users\scrccpa\Desktop\brochure_pages'
os.makedirs(out_dir, exist_ok=True)

doc = fitz.open(pdf_path)
print(f'Total pages: {len(doc)}')
print(f'Metadata: {doc.metadata}')

for i in range(len(doc)):
    page = doc[i]
    # Render at 200 DPI for readability
    pix = page.get_pixmap(dpi=200)
    out = os.path.join(out_dir, f'page_{i+1:02d}.png')
    pix.save(out)
    print(f'Page {i+1}: saved ({pix.width}x{pix.height})')

doc.close()
print(f'\nAll pages saved to: {out_dir}')