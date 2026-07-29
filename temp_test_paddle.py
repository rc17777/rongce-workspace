# encoding: utf-8
import fitz, sys, os
sys.stdout.reconfigure(encoding='utf-8')

# Render first page of test PDF
pdf_path = r'E:\2026\审计方法&政策文件\审计相关书籍\经济责任审计实务.pdf'
doc = fitz.open(pdf_path)
page = doc[0]
mat = fitz.Matrix(200/72, 200/72)
pix = page.get_pixmap(matrix=mat)
png_path = r'C:\Users\scrccpa\.openclaw\workspace\temp_test_page.png'
with open(png_path, 'wb') as f:
    f.write(pix.tobytes('png'))
doc.close()
print(f'Page 0 rendered: {pix.width}x{pix.height} -> {png_path}')

# Now test PaddleOCR on it
from paddleocr import PaddleOCR
import json
ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)
result = ocr.ocr(png_path, cls=True)

lines = []
confs = []
if result and result[0]:
    for line in result[0]:
        lines.append(line[1][0])
        confs.append(line[1][1])

text = '\n'.join(lines)
avg_conf = sum(confs) / len(confs) if confs else 0.0
print(f'OCR: {len(text)} chars, confidence: {avg_conf:.4f}')
print(f'First 200 chars: {text[:200]}')
