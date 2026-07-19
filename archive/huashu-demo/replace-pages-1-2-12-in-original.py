from pathlib import Path
from pypdf import PdfReader, PdfWriter
import shutil

root = Path(__file__).resolve().parent
original = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10.pdf')
output_dir = root / 'output'
replacements = {
    0: output_dir / 'page-01.pdf',
    1: output_dir / 'page-02.pdf',
    11: output_dir / 'page-14.pdf',
}
out_pdf = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10-封面第二页第十二页修改版.pdf')

reader = PdfReader(str(original))
writer = PdfWriter()
for i, page in enumerate(reader.pages):
    if i in replacements:
        repl = PdfReader(str(replacements[i]))
        writer.add_page(repl.pages[0])
    else:
        writer.add_page(page)

with out_pdf.open('wb') as f:
    writer.write(f)

preview_map = {
    '融策-政府审计简介7.10-封面修改版预览.png': output_dir / 'page-01.png',
    '融策-政府审计简介7.10-第二页修改版预览.png': output_dir / 'page-02.png',
    '融策-政府审计简介7.10-第十二页修改版预览.png': output_dir / 'page-14.png',
}
for name, src in preview_map.items():
    shutil.copy2(src, Path(r'C:\Users\scrccpa\Desktop') / name)

print(out_pdf)
print(f'pages={len(PdfReader(str(out_pdf)).pages)} size_mb={out_pdf.stat().st_size/1024/1024:.1f}')
