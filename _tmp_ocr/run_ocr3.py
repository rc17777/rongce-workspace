# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from paddleocr import PaddleOCR

src = r"C:\Users\scrccpa\.openclaw\workspace\_tmp_ocr\input.jpg"
im = Image.open(src)
W, H = im.size

# 裁剪底部两行(兴鸿公司行 + 合计行)整行，放大3倍
crop = im.crop((250, 2400, 3900, 2720))
cw, ch = crop.size
crop = crop.resize((cw*3, ch*3), Image.LANCZOS)
tmp = r"C:\Users\scrccpa\.openclaw\workspace\_tmp_ocr\bottom.png"
crop.save(tmp)

ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
result = ocr.ocr(tmp, cls=True)
lines = []
for page in result:
    if not page:
        continue
    for box, (text, conf) in page:
        x = 250 + box[0][0]/3
        y = 2400 + box[0][1]/3
        lines.append((y, x, text, conf))
lines.sort(key=lambda t: (round(t[0]/15), t[1]))
for y, x, text, conf in lines:
    print(f"{int(y):5d} {int(x):5d}  {text}  ({conf:.2f})")
