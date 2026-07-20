#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""融策审计 - 二类费用计费复核"""
import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')

# 用os.listdir找出桌面文件夹名
desktop = r'C:\Users\scrccpa\Desktop'
items = os.listdir(desktop)

# 找"新建文件夹"
target_dir = None
for item in items:
    full = os.path.join(desktop, item)
    if os.path.isdir(full) and '新建文件夹' in item:
        target_dir = full
        break

if not target_dir:
    print("未找到桌面上的新建文件夹")
    sys.exit(1)

print(f"找到目录: {target_dir}")
sub_dirs = [os.path.join(target_dir, d) for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]

for sd in sub_dirs:
    proj_name = os.path.basename(sd)
    print(f"\n{'#'*70}")
    print(f"# 项目: {proj_name}")
    print(f"{'#'*70}")
    
    # 找附件2
    annex2 = None
    for f in os.listdir(sd):
        if '附件2' in f and f.endswith('.xls'):
            annex2 = os.path.join(sd, f)
            break
    
    if not annex2:
        print("未找到附件2")
        continue
    
    print(f"文件: {os.path.basename(annex2)}")
    
    import xlrd
    book = xlrd.open_workbook(annex2, formatting_info=False)
    
    # 提取01审核汇总表
    for sn in book.sheet_names():
        if any(kw in sn for kw in ['01','审核','汇总']):
            sh = book.sheet_by_name(sn)
            print(f"\n=== 01审核汇总表 ({sh.nrows}行) ===")
            for r in range(sh.nrows):
                parts = []
                for c in range(sh.ncols):
                    v = sh.cell(r,c).value
                    if isinstance(v, float) and v > 0.01:
                        parts.append(f"C{c}={v:,.2f}")
                    elif v:
                        t = str(v).strip()[:35]
                        parts.append(f"C{c}={t}")
                if parts:
                    print(f"  R{r:2d}: {' | '.join(parts)}")
    
    # 提取待摊投资明细表
    for sn in book.sheet_names():
        if '待摊' in sn:
            sh = book.sheet_by_name(sn)
            print(f"\n=== {sn} ({sh.nrows}行) ===")
            for r in range(sh.nrows):
                parts = []
                for c in range(sh.ncols):
                    v = sh.cell(r,c).value
                    if isinstance(v, float) and v > 0.01:
                        parts.append(f"C{c}={v:,.2f}")
                    elif v:
                        t = str(v).strip()[:35]
                        parts.append(f"C{c}={t}")
                if parts:
                    print(f"  R{r:2d}: {' | '.join(parts)}")

print("\n完毕")
