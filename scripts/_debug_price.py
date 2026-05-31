import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\6，739.143532万基建四川护理职业学院成都校区学生宿舍维修项目第二次-磋商-唐裕民-省采\0、四川护理职业学院成都校区学生宿舍维修项目(二次)存档资料\成都校区学生宿舍维修项目(二次)-一体化系统导出存档资料 2025.5.9"
BID_DIR = os.path.join(BASE, "投标文件", "采购包1")

import warnings
warnings.filterwarnings('ignore')

# Deep debug: 四川之信 (has text but no price match)
import pdfplumber

for bidder in sorted(os.listdir(BID_DIR)):
    bname = bidder.split('(')[0]
    if '四川之信' not in bname and '四川圣地垣' not in bname:
        continue
    
    bidder_dir = os.path.join(BID_DIR, bidder)
    for fn in os.listdir(bidder_dir):
        if '已标价工程量清单' in fn and fn.endswith('.pdf') and not fn.startswith('._'):
            fp = os.path.join(bidder_dir, fn)
            print(f'=== {bname} ===')
            with pdfplumber.open(fp) as pdf:
                # Dump first 3 pages raw text
                for i in range(min(3, len(pdf.pages))):
                    text = pdf.pages[i].extract_text()
                    if text:
                        print(f'--- Page {i+1} ({len(text)} chars) ---')
                        # Print lines containing keywords
                        for line in text.split('\n'):
                            line_s = line.strip()
                            if line_s and len(line_s) > 5:
                                # Check if it contains Chinese chars
                                has_cn = any('\u4e00' <= c <= '\u9fff' for c in line_s)
                                if has_cn:
                                    print(f'  {line_s[:200]}')
                    else:
                        print(f'--- Page {i+1}: NO TEXT ---')
            print()
            break
    break  # Only do one
