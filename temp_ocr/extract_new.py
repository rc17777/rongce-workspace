"""Extract first 2 pages from new scanned PDFs for content sampling."""
import fitz, os, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'
out_root = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\pages_new'
os.makedirs(out_root, exist_ok=True)

# New files (not previously OCR'd)
new_files = {
    r'DRG支付\2024DRG支付文件2.pdf': 'DRG支付2024',
    r'DRG支付\2025DRG支付.pdf': 'DRG支付2025',
    r'委托支付协议\集中采购协议.pdf': '集中采购协议',
    r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查4.pdf': '稽查4',
    r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查6.pdf': '稽查6',
    r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查8.pdf': '稽查8',
    r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件.pdf': '稽查文件',
    r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件2.pdf': '稽查文件2',
    r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件3.pdf': '稽查文件3',
}

for rel_path, label in new_files.items():
    fp = os.path.join(base, rel_path)
    if not os.path.exists(fp):
        print(f'SKIP: {rel_path}')
        continue
    doc = fitz.open(fp)
    doc_out = os.path.join(out_root, label)
    os.makedirs(doc_out, exist_ok=True)
    total = doc.page_count
    for i in range(min(2, total)):
        mat = fitz.Matrix(1.5, 1.5)
        pix = doc[i].get_pixmap(matrix=mat)
        png_path = os.path.join(doc_out, f'p{i+1:02d}.png')
        pix.save(png_path)
    doc.close()
    print(f'{label}: {total} pages, extracted p01-p02')

print(f'\nDone. Output: {out_root}')
