import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\6，739.143532万基建四川护理职业学院成都校区学生宿舍维修项目第二次-磋商-唐裕民-省采\0、四川护理职业学院成都校区学生宿舍维修项目(二次)存档资料\成都校区学生宿舍维修项目(二次)-一体化系统导出存档资料 2025.5.9"
BID_DIR = os.path.join(BASE, "投标文件", "采购包1")

# Test on a few bidders that failed
import pdfplumber

# Pick 四川之信 (price extraction failed)
test_bidders = [
    "四川之信建设工程有限公司(包1)",
    "四川京投建设工程有限公司(包1)",
    "四川春航建设集团有限公司(包1)",
    "四川省建筑机械化工程有限公司(包1)",
]

for bidder in sorted(os.listdir(BID_DIR)):
    if bidder not in test_bidders:
        continue
    bidder_dir = os.path.join(BID_DIR, bidder)
    name = bidder.split('(')[0]
    
    for fn in os.listdir(bidder_dir):
        if '已标价工程量清单' in fn and fn.endswith('.pdf'):
            fp = os.path.join(bidder_dir, fn)
            print(f'=== {name} ({os.path.getsize(fp)} bytes) ===')
            try:
                with pdfplumber.open(fp) as pdf:
                    # Check first 8 pages for price
                    for i in range(min(8, len(pdf.pages))):
                        text = pdf.pages[i].extract_text()
                        if text and ('总价' in text or '报价' in text or '小写' in text or '大写' in text):
                            print(f'  Page {i+1} (has price keywords):')
                            # Show lines containing price keywords
                            for line in text.split('\n'):
                                if any(kw in line for kw in ['总价', '报价', '小写', '大写', '投标', '元']):
                                    print(f'    {line.strip()[:200]}')
                    
                    # Also check last few pages
                    for i in range(max(0, len(pdf.pages)-5), len(pdf.pages)):
                        text = pdf.pages[i].extract_text()
                        if text and ('总价' in text or '报价' in text or '小写' in text):
                            print(f'  Page {i+1} (late page with price):')
                            for line in text.split('\n'):
                                if any(kw in line for kw in ['总价', '报价', '小写', '大写']):
                                    print(f'    {line.strip()[:200]}')
            except Exception as e:
                print(f'  Error: {e}')
            print()
            break
