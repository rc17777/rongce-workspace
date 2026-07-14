# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from paddleocr import PaddleOCR

src = r"C:\Users\scrccpa\.openclaw\workspace\_tmp_ocr\input.jpg"
im = Image.open(src)
W, H = im.size
print("SIZE", W, H)

ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

# 放大2倍整体重识别，重点看收入列(右侧)和底部合计
im2 = im.resize((W*2, H*2), Image.LANCZOS)
tmp = r"C:\Users\scrccpa\.openclaw\workspace\_tmp_ocr\input_2x.png"
im2.save(tmp)

result = ocr.ocr(tmp, cls=True)
lines = []
for page in result:
    if not page:
        continue
    for box, (text, conf) in page:
        x = box[0][0]/2
        y = box[0][1]/2
        lines.append((y, x, text, conf))

lines.sort(key=lambda t: (round(t[0]/15), t[1]))
for y, x, text, conf in lines:
    # 只打印右侧收入列 + 底部区域，减少噪音
    if x > 2900 or y > 2500:
        print(f"{int(y):5d} {int(x):5d}  {text}  ({conf:.2f})")
