"""Targeted approach: first/last pages + archive OCR"""
import fitz, pytesseract, re, pdfplumber, os
from PIL import Image

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目"

bidders = {
    '胤皓': os.path.join(BASE, '供应商投标文件', '四川胤皓文化传媒有限公司.pdf'),
    '太格': os.path.join(BASE, '供应商投标文件', '太格电子文档.pdf'),
    '立美': os.path.join(BASE, '供应商投标文件', '立美响应文件.pdf'),
}

# 1. Try archive PDF with pdfplumber
print('=== ARCHIVE PDF ===')
import os
archive_path = os.path.join(BASE, '备案资料-ZHH-F〔2025〕85号--四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目.pdf')
try:
    with pdfplumber.open(archive_path) as pdf:
        print('Pages: %d' % len(pdf))
        # Check first 10 and last 10 pages for embedded text
        for pg in range(min(10, len(pdf))):
            text = pdf.pages[pg].extract_text()
            if text:
                print('Page %d: %d chars' % (pg+1, len(text)))
                print('  %s' % text[:300])
            if pg < 3:
                print()
except Exception as e:
    print('Archive PDF error: %s' % e)

# 2. For each bidder, only scan first 5 + last 5 pages
print('\n=== BIDDER PDFs (first 5 + last 5 pages) ===')
price_kws = ['报价','总价','最后','磋商','金额','大写','小写','响应','最终','费用','元']

for name, path in bidders.items():
    if not os.path.exists(path):
        print('%s: not found' % name)
        continue
    try:
        doc = fitz.open(path)
        total = len(doc)
        print('\n[%s] %d pages' % (name, total))
        
        pages_to_check = list(range(0, min(5, total))) + list(range(max(0, total-5), total))
        found = False
        
        for pg_idx in pages_to_check:
            page = doc[pg_idx]
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang='chi_sim', config='--psm 6')
            
            if any(kw in text for kw in price_kws):
                print('  Page %d: PRICE FOUND!' % (pg_idx+1))
                found = True
                prices = re.findall(r'(\d[\d,.]{3,})\s*元', text)
                for p in prices[:8]:
                    try:
                        val = int(p.replace(',','').replace('.',''))
                        print('    PRICE: %s 元' % format(val, ','))
                    except:
                        pass
                print('    Text: %s...' % text[:250].replace('\n',' '))
        if not found:
            print('  No price on first/last 5 pages')
        doc.close()
    except Exception as e:
        print('%s: ERROR - %s' % (name, str(e)[:100]))

print('\nDone!')
