# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from paddleocr import PaddleOCR

img = r"C:\Users\scrccpa\.openclaw\workspace\_tmp_ocr\input.jpg"
ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
result = ocr.ocr(img, cls=True)

lines = []
for page in result:
    if not page:
        continue
    for box, (text, conf) in page:
        # 取文本框左上角坐标用于排序
        x = box[0][0]
        y = box[0][1]
        lines.append((y, x, text, conf))

# 按 y 排序（从上到下），近似还原阅读顺序
lines.sort(key=lambda t: (round(t[0]/15), t[1]))
for y, x, text, conf in lines:
    print(f"{int(y):5d} {int(x):5d}  {text}")
