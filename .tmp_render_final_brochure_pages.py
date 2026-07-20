from pathlib import Path
import fitz
pdf_path = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10-封面第二页第十二页修改版.pdf')
out_dir = Path(r'C:\Users\scrccpa\.openclaw\workspace\output\brochure_final_check')
out_dir.mkdir(parents=True, exist_ok=True)
doc = fitz.open(str(pdf_path))
for page_no in [1,2,12]:
    pix = doc[page_no-1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    out = out_dir / f'final_page_{page_no:02d}.png'
    pix.save(str(out))
    print(out)
