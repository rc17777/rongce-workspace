# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from paddleocr import PaddleOCR

src = r"C:\Users\scrccpa\.openclaw\workspace\_tmp_ocr\input.jpg"
im = Image.open(src)
# 只裁收入列的最后两行(兴鸿+合计)
crop = im.crop((2950, 2420, 3850, 2700))
cw, ch = crop.size
crop = crop.resize((cw*4, ch*4), Image.LANCZOS)
tmp = r"C:\Users\scrccpa\.openclaw\workspace\_tmp_ocr\income_bottom.png"
crop.save(tmp)
ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
result = ocr.ocr(tmp, cls=True)
found = False
for page in result:
    if not page:
        continue
    for box, (text, conf) in page:
        y = 2420 + box[0][1]/4
        x = 2950 + box[0][0]/4
        print(f"{int(y):5d} {int(x):5d}  {text}  ({conf:.2f})")
        found = True
if not found:
    print("NO_TEXT_IN_INCOME_COLUMN_BOTTOM")
