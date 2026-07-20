# -*- coding: utf-8 -*-
"""提取关键PDF文本（合同、发票）"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

outdir = r'C:\Users\scrccpa\.openclaw\workspace\temp_review'

pdfs = [
    (r'C:\Users\scrccpa\Desktop\新建文件夹\0.审计业务约定书\审计业务约定书（科服-竞泽）.pdf', 'engagement.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\1、科服集团19.52万元\20260525科服&信通院服务合同.pdf', 'main_contract.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\1、科服集团19.52万元\发票.pdf', 'main_invoice.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\2、信通院\制造业数字化转型促进中心“深度行”（四川站）活动服务采购项目合同14.1858.pdf', 'sub_contract.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\2、信通院\活动服务发票14.1858万元.pdf', 'sub_invoice.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\2、信通院\软文投放服务采购合同4.43.pdf', 'soft_contract.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\2、信通院\软文投放发票1.772.pdf', 'soft_invoice1.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\2、信通院\软文投放发票2.658.pdf', 'soft_invoice2.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\3、鼎函九筹会议公司资料\场地租赁合同.pdf', 'venue_contract.txt'),
    (r'C:\Users\scrccpa\Desktop\新建文件夹\1.深度行四川站合同审核资料\3、鼎函九筹会议公司资料\用餐费用明细.pdf', 'meal_detail.txt'),
]

try:
    import pdfplumber
    HAS_PLUMBER = True
except ImportError:
    HAS_PLUMBER = False
    import pypdf

for src, dst in pdfs:
    try:
        txt_parts = []
        if HAS_PLUMBER:
            with pdfplumber.open(src) as pdf:
                for i, page in enumerate(pdf.pages):
                    t = page.extract_text() or ''
                    txt_parts.append(f'--- page {i+1} ---\n{t}')
        else:
            r = pypdf.PdfReader(src)
            for i, page in enumerate(r.pages):
                t = page.extract_text() or ''
                txt_parts.append(f'--- page {i+1} ---\n{t}')
        txt = '\n'.join(txt_parts)
        with open(os.path.join(outdir, dst), 'w', encoding='utf-8') as f:
            f.write(txt)
        print(f'[OK] {dst}: {len(txt)} chars')
    except Exception as e:
        print(f'[FAIL] {dst}: {e}')
