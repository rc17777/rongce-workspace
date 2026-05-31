import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\6，739.143532万基建四川护理职业学院成都校区学生宿舍维修项目第二次-磋商-唐裕民-省采\0、四川护理职业学院成都校区学生宿舍维修项目(二次)存档资料\成都校区学生宿舍维修项目(二次)-一体化系统导出存档资料 2025.5.9"
BID_DIR = os.path.join(BASE, "投标文件", "采购包1")

import pdfplumber

# Test a few bidders with broader page search (all pages)
test_names = [
    "四川之信建设工程有限公司(包1)",
    "四川乙庭环境建设有限公司(包1)",
    "四川京投建设工程有限公司(包1)",
]

for bidder in sorted(os.listdir(BID_DIR)):
    if bidder not in test_names:
        continue
    bidder_dir = os.path.join(BID_DIR, bidder)
    name = bidder.split('(')[0]
    
    for fn in os.listdir(bidder_dir):
        if '已标价工程量清单' in fn and fn.endswith('.pdf'):
            fp = os.path.join(bidder_dir, fn)
            print(f'=== {name} ===')
            try:
                with pdfplumber.open(fp) as pdf:
                    found = False
                    for i in range(len(pdf.pages)):
                        text = pdf.pages[i].extract_text()
                        if text and '投标总价' in text:
                            print(f'  [Page {i+1}] Found 投标总价:')
                            for line in text.split('\n'):
                                if '投标总价' in line or '小写' in line or '大写' in line:
                                    print(f'    >> {line.strip()[:300]}')
                            found = True
                            break
                    if not found:
                        # Search for any price total
                        for i in range(len(pdf.pages)):
                            text = pdf.pages[i].extract_text()
                            if text and ('总价' in text or '合计' in text):
                                # Check if page has number patterns
                                nums = re.findall(r'[\d,]+\.?\d*', text)
                                if len(nums) > 5:
                                    continue  # Skip detailed BOQ pages
                                print(f'  [Page {i+1}] 总价/合计 page:')
                                for line in text.split('\n'):
                                    if any(kw in line for kw in ['总价', '合计', '小写', '大写', '元']):
                                        print(f'    >> {line.strip()[:300]}')
                                break
            except Exception as e:
                print(f'  Error: {e}')
            print()
            break

# Also test with pypdf for comparison
print('=== Testing with pypdf ===')
from pypdf import PdfReader
for bidder in sorted(os.listdir(BID_DIR)):
    if bidder not in test_names[:1]:
        continue
    bidder_dir = os.path.join(BID_DIR, bidder)
    name = bidder.split('(')[0]
    
    for fn in os.listdir(bidder_dir):
        if '已标价工程量清单' in fn and fn.endswith('.pdf'):
            fp = os.path.join(bidder_dir, fn)
            print(f'=== {name} (pypdf) ===')
            reader = PdfReader(fp)
            for i in range(min(10, len(reader.pages))):
                text = reader.pages[i].extract_text()
                if text and '投标总价' in text:
                    print(f'  [Page {i+1}] Found:')
                    print(text[:500])
                    break
            break
