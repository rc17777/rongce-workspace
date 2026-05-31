import sys, io, os, re, gc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\6，739.143532万基建四川护理职业学院成都校区学生宿舍维修项目第二次-磋商-唐裕民-省采\0、四川护理职业学院成都校区学生宿舍维修项目(二次)存档资料\成都校区学生宿舍维修项目(二次)-一体化系统导出存档资料 2025.5.9"
BID_DIR = os.path.join(BASE, "投标文件", "采购包1")
BUDGET = 7391435.32

import warnings
warnings.filterwarnings('ignore')

# Strategy: pdfplumber on 已标价工程量清单, scan pages 1-10 and last 5

for bidder in sorted(os.listdir(BID_DIR)):
    bidder_dir = os.path.join(BID_DIR, bidder)
    name = bidder.split('(')[0]
    
    # Find 已标价工程量清单
    boq_file = None
    for fn in os.listdir(bidder_dir):
        if '已标价工程量清单' in fn and fn.endswith('.pdf') and not fn.startswith('._'):
            boq_file = os.path.join(bidder_dir, fn)
            break
    
    if not boq_file:
        print(f'{name}: NO BOQ FILE')
        continue
    
    try:
        import pdfplumber
        with pdfplumber.open(boq_file) as pdf:
            total_pages = len(pdf.pages)
            price = None
            
            # Scan first 10 pages
            pages_to_check = list(range(min(10, total_pages)))
            # Also last 5 pages
            if total_pages > 10:
                for p in range(max(0, total_pages-5), total_pages):
                    if p not in pages_to_check:
                        pages_to_check.append(p)
            
            for i in pages_to_check:
                text = pdf.pages[i].extract_text()
                if not text:
                    continue
                for pat in [
                    r'投标总价[（(]小写[)）]\s*[：:]\s*([\d,]+\.?\d{2})',
                    r'投标总价[（(]小写[)）]\s*([\d,]+\.?\d{2})',
                    r'投标总价\s*[：:]\s*([\d,]+\.?\d{2})',
                    r'投标报价[（(]小写[)）]\s*[：:]\s*([\d,]+\.?\d{2})',
                    r'投标报价\s*[：:]\s*([\d,]+\.?\d{2})',
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
                print(f'{name}: {price:,.2f} (dev: {dev:+.4f}%) [{total_pages}p]')
            else:
                # Debug: search for any price-like pattern near "投标" keyword
                for i in range(min(5, total_pages)):
                    text = pdf.pages[i].extract_text()
                    if text and '投标' in text:
                        # Find all numbers that look like prices (6-8 digits with .xx)
                        nums = re.findall(r'([\d,]{6,10}\.\d{2})', text)
                        if nums:
                            # Filter out budget amounts (exact match to budget)
                            unique_nums = []
                            for n in nums:
                                v = float(n.replace(',', ''))
                                if v != BUDGET:
                                    unique_nums.append(v)
                            if unique_nums:
                                print(f'{name}: POSSIBLE={unique_nums[:5]} [{total_pages}p]')
                            else:
                                print(f'{name}: ONLY_BUDGET [{total_pages}p]')
                        else:
                            print(f'{name}: NO_PRICE_PATTERN [{total_pages}p]')
                        break
                else:
                    print(f'{name}: NO_TEXT [{total_pages}p]')
                    
        pdf = None
        gc.collect()
        
    except Exception as e:
        print(f'{name}: ERROR - {str(e)[:100]}')
