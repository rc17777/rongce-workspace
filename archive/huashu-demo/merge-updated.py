from pathlib import Path
from pypdf import PdfReader, PdfWriter
import shutil

root = Path(__file__).resolve().parent
out_dir = root / 'output'
pages = sorted(out_dir.glob('page-*.pdf'))
writer = PdfWriter()
for p in pages:
    reader = PdfReader(str(p))
    writer.add_page(reader.pages[0])

out_pdf = out_dir / '融策-政府审计宣传册-第二页修改版.pdf'
with out_pdf.open('wb') as f:
    writer.write(f)

desktop_pdf = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10-第二页修改版.pdf')
shutil.copy2(out_pdf, desktop_pdf)

desktop_png = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10-第二页修改版预览.png')
shutil.copy2(out_dir / 'page-02.png', desktop_png)

print(out_pdf)
print(desktop_pdf)
print(desktop_png)
print(f'pages={len(pages)} size_mb={desktop_pdf.stat().st_size/1024/1024:.1f}')
