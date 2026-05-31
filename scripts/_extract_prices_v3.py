import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\6，739.143532万基建四川护理职业学院成都校区学生宿舍维修项目第二次-磋商-唐裕民-省采\0、四川护理职业学院成都校区学生宿舍维修项目(二次)存档资料\成都校区学生宿舍维修项目(二次)-一体化系统导出存档资料 2025.5.9"
BID_DIR = os.path.join(BASE, "投标文件", "采购包1")
BUDGET = 7391435.32

import warnings
warnings.filterwarnings('ignore')

# Fast scan: find which page has the bid total price table
# The page typically has: 投标人, 投标总价, 大写, 小写 in a small table
# Use pypdf for speed, scan ALL pages

from pypdf import PdfReader
import gc

for bidder in sorted(os.listdir(BID_DIR)):
    bidder_dir = os.path.join(BID_DIR, bidder)
    name = bidder.split('(')[0]
    
    boq = None
    for fn in os.listdir(bidder_dir):
        if '已标价工程量清单' in fn and fn.endswith('.pdf') and not fn.startswith('._'):
            boq = os.path.join(bidder_dir, fn)
            break
    if not boq:
        print(f'{name}: NO BOQ')
        continue
    
    try:
        reader = PdfReader(boq)
        total = len(reader.pages)
        found = False
        
        # Search ALL pages for 投标总价
        for i in range(total):
            text = reader.pages[i].extract_text()
            if not text:
                continue
            # Try multiple patterns
            for pat in [
                r'投标总价[（(]?小写[)）]?\s*[：:]*\s*[¥￥]?\s*([\d,]+\.?\d{2})',
                r'投标总价.*?([\d,]+\.?\d{2})',
                r'总价[（(]小写[)）].*?([\d,]+\.?\d{2})',
                r'大写.*?([\d,]+\.?\d{2})',
            ]:
                m = re.search(pat, text, re.DOTALL)
                if m:
                    val = m.group(1).replace(',', '')
                    price = float(val)
                    if abs(price - BUDGET) < 1000000:  # Within 1M of budget
                        dev = (price - BUDGET) / BUDGET * 100
                        print(f'{name}: {price:,.2f} ({dev:+.4f}%) [p{i+1}/{total}]')
                        found = True
                        break
            if found:
                break
        
        if not found:
            # Check if any page has "投标" at all
            has_toubiao = False
            for i in range(min(5, total)):
                text = reader.pages[i].extract_text()
                if text and '投标' in text:
                    has_toubiao = True
                    break
            
            # Fallback: find the page with most numbers around 7M
            best_page = None
            best_nums = []
            for i in range(total):
                text = reader.pages[i].extract_text()
                if not text:
                    continue
                nums = re.findall(r'([\d,]{7,9}\.\d{2})', text)
                budget_near = [float(n.replace(',','')) for n in nums 
                              if abs(float(n.replace(',','')) - BUDGET) < 500000 
                              and float(n.replace(',','')) != BUDGET]
                if budget_near:
                    best_page = i
                    best_nums = budget_near
                    break
            
            if best_page is not None and best_nums:
                price = min(best_nums, key=lambda x: abs(x-BUDGET))
                dev = (price - BUDGET) / BUDGET * 100
                print(f'{name}: {price:,.2f} ({dev:+.4f}%) [p{best_page+1}/{total}] *heuristic')
            else:
                print(f'{name}: NOT FOUND [total={total}p, has投标={has_toubiao}]')
        
        reader = None
        gc.collect()
        
    except Exception as e:
        print(f'{name}: ERROR - {str(e)[:100]}')
