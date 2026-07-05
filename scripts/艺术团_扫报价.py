import fitz, pytesseract, re, sys, os
from PIL import Image

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目\供应商投标文件"

def ocr_page(doc, pg_idx):
    page = doc[pg_idx]
    pix = page.get_pixmap(dpi=72)
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img, lang='chi_sim', config='--psm 6').strip()
    return text

price_kws = ['报价','总价','金额','大写','最后','费用','磋商报价']

for name, fname in [('胤皓','四川胤皓文化传媒有限公司.pdf'), ('太格','太格电子文档.pdf')]:
    path = os.path.join(BASE, fname)
    doc = fitz.open(path)
    total = len(doc)
    
    # Check pages 1-10 and last 5
    pages = list(range(0, min(10, total))) + list(range(max(0, total-5), total))
    
    for p in pages:
        text = ocr_page(doc, p)
        hits = [k for k in price_kws if k in text]
        if hits:
            sys.stdout.flush()
            print('=== %s Page %d: %s ===' % (name, p+1, str(hits)))
            # Print all text
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 2:
                    print('  ' + line[:130])
            print()
            sys.stdout.flush()
    
    doc.close()

# Check if we found any prices
print('\n=== SUMMARY ===')
# Try pages 15-25 of 胤皓 as backup  
doc = fitz.open(os.path.join(BASE, '四川胤皓文化传媒有限公司.pdf'))
for p in [15, 16, 17, 18, 19, 20]:
    text = ocr_page(doc, p)
    print('胤皓 Page %d: %d chars | %s' % (p+1, len(text), text[:150].replace('\n',' ')))
doc.close()

# Try pages 15-30 of 太格
doc = fitz.open(os.path.join(BASE, '太格电子文档.pdf'))
for p in [15, 16, 17, 18, 19, 20]:
    text = ocr_page(doc, p)
    print('太格 Page %d: %d chars | %s' % (p+1, len(text), text[:150].replace('\n',' ')))
doc.close()

print('Done!')
