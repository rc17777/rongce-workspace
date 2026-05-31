"""Ultra-fast OCR: 50 DPI, only strategic pages, for all three bidders"""
import fitz, pytesseract, re, os
from PIL import Image

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目\供应商投标文件"
OUT = r"D:\openclaw-workspace\output\艺术团采购"

files = [
    ('胤皓', os.path.join(BASE, '四川胤皓文化传媒有限公司.pdf')),
    ('太格', os.path.join(BASE, '太格电子文档.pdf')),
    ('立美', os.path.join(BASE, '立美响应文件.pdf')),
]

price_kws = ['报价','总价','最后','磋商','金额','大写','响应','最终','费用','万','报价表','价格表']

for name, path in files:
    print('=== %s ===' % name)
    try:
        doc = fitz.open(path)
    except Exception as e:
        print('  CANNOT OPEN: %s' % e)
        continue
    
    total = len(doc)
    if total == 0:
        print('  0 PAGES - CORRUPT PDF')
        continue
    
    print('  %d pages, checking every 10th + last 3...' % total)
    
    # Check pages strategically: every 10th page + last 3
    check_pages = set()
    for p in range(0, total, 10):
        check_pages.add(p)
    for p in range(max(0, total-3), total):
        check_pages.add(p)
    check_pages = sorted(check_pages)
    
    for pg_idx in check_pages:
        page = doc[pg_idx]
        pix = page.get_pixmap(dpi=50)  # Ultra low DPI for speed
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img, lang='chi_sim', config='--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.元万仟佰拾报价总价最后磋商金额大写响应最终费用壹贰叁肆伍陆柒捌玖拾零整分角年月日')[:500]
        
        kw_hits = [kw for kw in price_kws if kw in text]
        if kw_hits:
            print('  Page %d: KEYWORDS=%s (%d chars)' % (pg_idx+1, str(kw_hits), len(text)))
            prices = re.findall(r'(\d[\d,.]{3,})\s*[元]', text)
            for p in prices[:5]:
                try:
                    val = int(p.replace(',','').replace('.',''))
                    print('    PRICE: %s 元' % format(val, ','))
                except:
                    pass
            # Print OCR text
            for line in text.split('\n')[:10]:
                line = line.strip()
                if len(line) > 3:
                    print('    |%s' % line[:120])
            # Found what we need, stop checking this bidder
            if '报价' in kw_hits or '总价' in kw_hits or '最后' in kw_hits:
                break
    doc.close()

print('\nDone!')
