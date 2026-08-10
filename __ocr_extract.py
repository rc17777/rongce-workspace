# -*- coding: utf-8 -*-
import fitz, os, pytesseract
from PIL import Image

# ========== 配置 ==========
BASE = r'C:\Users\15528\Desktop\四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务响应文件'
OUT_DIR = os.path.join(BASE, '__ocr_text')
os.makedirs(OUT_DIR, exist_ok=True)

# 设置tesseract路径和TESSDATA_PREFIX
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = 'C:\\Users\\15528\\.openclaw\\workspace'

# ========== 提取文本 ==========
for fname in os.listdir(BASE):
    if not fname.endswith('.pdf'):
        continue
    path = os.path.join(BASE, fname)
    doc = fitz.open(path)
    print('\n=== ' + fname + ' ===')
    
    # 提取前3页的文本
    for pnum in range(min(3, doc.page_count)):
        page = doc[pnum]
        mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
        clip = page.rect
        try:
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes('png')
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            
            # 使用pytesseract做OCR
            text = pytesseract.image_to_string(tmp_path, lang='chi_sim')
            os.unlink(tmp_path)
            
            # 保存结果
            out_path = os.path.join(OUT_DIR, fname + '_p' + str(pnum+1) + '.txt')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f'  第{pnum+1}页OCR成功，字符数: {len(text)}')
            if text.strip():
                print(f'  文本预览: {text[:200]}...')
        except Exception as e:
            print(f'  第{pnum+1}页OCR失败: {e}')
    doc.close()
