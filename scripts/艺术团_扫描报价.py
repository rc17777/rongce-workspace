"""Scan PDF for pricing pages"""
import fitz, pytesseract, re
from PIL import Image

path = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目\供应商投标文件\四川胤皓文化传媒有限公司.pdf"
doc = fitz.open(path)
print('Scanning %d pages...' % len(doc))

price_kws = ['报价','总价','最后','磋商','金额','大写','小写','响应报价','最终报价','费用']

for pg_idx in range(len(doc)):
    page = doc[pg_idx]
    text = page.get_text()
    
    # Try embedded text first
    if text.strip():
        if any(kw in text for kw in price_kws):
            print('Page %d [EMBEDDED]: %s' % (pg_idx+1, text[:200]))
        continue
    
    # Quick OCR
    pix = page.get_pixmap(dpi=100)
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img, lang='chi_sim', config='--psm 6')
    
    if any(kw in text for kw in price_kws):
        print('\n>>> Page %d: PRICE KEYWORD!' % (pg_idx+1))
        print('    OCR: %s' % text[:300].replace('\n',' '))
        
        # High-quality OCR
        pix2 = page.get_pixmap(dpi=200)
        img2 = Image.frombytes('RGB', [pix2.width, pix2.height], pix2.samples)
        text2 = pytesseract.image_to_string(img2, lang='chi_sim', config='--psm 6')
        prices = re.findall(r'(\d[\d,.]{3,})\s*元', text2)
        for p in prices[:10]:
            try:
                val = int(p.replace(',','').replace('.',''))
                print('    PRICE: %s 元' % format(val, ','))
            except:
                pass
        print()
    
    if (pg_idx+1) % 20 == 0:
        print('  ...%d/%d checked...' % (pg_idx+1, len(doc)))

doc.close()
print('Done!')
