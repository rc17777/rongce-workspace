import sys, io, os, re
# Write to file to avoid encoding issues
log_file = r'D:\openclaw-workspace\output\宿舍维修项目串标分析\_price_debug.txt'
os.makedirs(os.path.dirname(log_file), exist_ok=True)

BASE = r"C:\Users\scrccpa\Desktop\6，739.143532万基建四川护理职业学院成都校区学生宿舍维修项目第二次-磋商-唐裕民-省采\0、四川护理职业学院成都校区学生宿舍维修项目(二次)存档资料\成都校区学生宿舍维修项目(二次)-一体化系统导出存档资料 2025.5.9"
BID_DIR = os.path.join(BASE, "投标文件", "采购包1")
BUDGET = 7391435.32

import warnings
warnings.filterwarnings('ignore')

# Write detailed debug for 3 bidders
import pdfplumber

with open(log_file, 'w', encoding='utf-8') as out:
    count = 0
    for bidder in sorted(os.listdir(BID_DIR)):
        bname = bidder.split('(')[0]
        
        bidder_dir = os.path.join(BID_DIR, bidder)
        boq = None
        for fn in os.listdir(bidder_dir):
            if '已标价工程量清单' in fn and fn.endswith('.pdf') and not fn.startswith('._'):
                boq = os.path.join(bidder_dir, fn)
                break
        if not boq:
            continue
        
        out.write(f'=== {bname} ({os.path.getsize(boq)} bytes) ===\n')
        try:
            with pdfplumber.open(boq) as pdf:
                total = len(pdf.pages)
                # Check pages with most text (skip cover/instruction pages)
                pages_with_text = []
                for i in range(min(20, total)):
                    text = pdf.pages[i].extract_text()
                    if text:
                        cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                        pages_with_text.append((i, cn_chars, text[:500]))
                
                # Show top 5 pages by Chinese text
                pages_with_text.sort(key=lambda x: -x[1])
                for pg, cnt, snippet in pages_with_text[:5]:
                    out.write(f'  Page {pg+1}: {cnt} cn chars\n')
                    out.write(f'    Text: {snippet}\n')
                
                # Also check last 3 pages
                for i in range(max(0, total-3), total):
                    text = pdf.pages[i].extract_text()
                    if text:
                        cn = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                        out.write(f'  Page {i+1} (late): {cn} cn chars\n')
                        if cn > 10:
                            out.write(f'    Text: {text[:500]}\n')
        except Exception as e:
            out.write(f'  ERROR: {e}\n')
        
        out.write('\n')
        count += 1
        if count >= 5:  # Only 5 bidders for now
            break

print(f'Written to {log_file}')
