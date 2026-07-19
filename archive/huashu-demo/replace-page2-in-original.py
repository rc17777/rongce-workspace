from pathlib import Path
from pypdf import PdfReader, PdfWriter
import shutil

original = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10.pdf')
new_page2 = Path(__file__).resolve().parent / 'output' / 'page-02.pdf'
out_pdf = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10-仅替换第二页版.pdf')

reader = PdfReader(str(original))
replacement = PdfReader(str(new_page2))
writer = PdfWriter()
for i, page in enumerate(reader.pages):
    if i == 1:
        writer.add_page(replacement.pages[0])
    else:
        writer.add_page(page)
with out_pdf.open('wb') as f:
    writer.write(f)

preview = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10-第二页修改版预览.png')
shutil.copy2(Path(__file__).resolve().parent / 'output' / 'page-02.png', preview)
print(out_pdf)
print(preview)
print(f'pages={len(PdfReader(str(out_pdf)).pages)} size_mb={out_pdf.stat().st_size/1024/1024:.1f}')
