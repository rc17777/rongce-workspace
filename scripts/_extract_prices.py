import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\6，739.143532万基建四川护理职业学院成都校区学生宿舍维修项目第二次-磋商-唐裕民-省采\0、四川护理职业学院成都校区学生宿舍维修项目(二次)存档资料\成都校区学生宿舍维修项目(二次)-一体化系统导出存档资料 2025.5.9"
BID_DIR = os.path.join(BASE, "投标文件", "采购包1")
BUDGET = 7391435.32

from pypdf import PdfReader
import gc

# Use lighter approach: pypdf, only check specific pages
# Strategy: check first 5 pages for 投标总价, then check last 3 pages

results = []
for bidder in sorted(os.listdir(BID_DIR)):
    bidder_dir = os.path.join(BID_DIR, bidder)
    name = bidder.split('(')[0]
    
    # Try 报价表 first (smaller file)
    price_file = None
    for fn in os.listdir(bidder_dir):
        if '报价表' in fn and fn.endswith('.pdf') and not fn.startswith('._'):
            price_file = os.path.join(bidder_dir, fn)
            break
    if not price_file:
        for fn in os.listdir(bidder_dir):
            if '已标价工程量清单' in fn and fn.endswith('.pdf') and not fn.startswith('._'):
                price_file = os.path.join(bidder_dir, fn)
                break
    
    if not price_file:
        results.append((name, None, "no file"))
        continue
    
    try:
        reader = PdfReader(price_file)
        total_pages = len(reader.pages)
        price = None
        
        # Check first 6 pages
        for i in range(min(6, total_pages)):
            text = reader.pages[i].extract_text()
            if not text:
                continue
            for pat in [
                r'投标总价[（(]小写[)）]\s*[：:]\s*([\d,]+\.?\d*)',
                r'投标总价[（(]小写[)）]\s*([\d,]+\.?\d*)',
                r'投标总价\s*[：:]\s*([\d,]+\.?\d*)',
                r'投标报价[（(]小写[)）]\s*[：:]\s*([\d,]+\.?\d*)',
                r'投标报价\s*[：:]\s*([\d,]+\.?\d*)',
            ]:
                m = re.search(pat, text)
                if m:
                    val = m.group(1).replace(',', '')
                    price = float(val)
                    break
            if price:
                break
        
        # If not found, check last 3 pages
        if price is None and total_pages > 3:
            for i in range(total_pages-3, total_pages):
                text = reader.pages[i].extract_text()
                if not text:
                    continue
                for pat in [
                    r'投标总价[（(]小写[)）]\s*[：:]\s*([\d,]+\.?\d*)',
                    r'投标总价[（(]小写[)）]\s*([\d,]+\.?\d*)',
                    r'投标总价\s*[：:]\s*([\d,]+\.?\d*)',
                ]:
                    m = re.search(pat, text)
                    if m:
                        val = m.group(1).replace(',', '')
                        price = float(val)
                        break
                if price:
                    break
        
        if price:
            dev = (price - BUDGET) / BUDGET * 100
            print(f'{name}: {price:,.2f} (dev: {dev:+.4f}%) [pages: {total_pages}]')
        else:
            print(f'{name}: NOT FOUND [pages: {total_pages}]')
        
        results.append((name, price, total_pages))
        reader = None
        gc.collect()
        
    except Exception as e:
        print(f'{name}: ERROR - {e}')
        results.append((name, None, str(e)))

print(f'\n=== SUMMARY ===')
found = sum(1 for r in results if r[1] is not None)
print(f'Extracted: {found}/{len(results)}')
