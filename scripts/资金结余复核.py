#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""融策审计 - 资金来源与结余复核"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\scrccpa\Desktop\新建文件夹'

# 找到目录
desktop = r'C:\Users\scrccpa\Desktop'
target_dir = None
for item in os.listdir(desktop):
    full = os.path.join(desktop, item)
    if os.path.isdir(full):
        target_dir = full  # 最后一个文件夹
        # 改为找包含"新建文件夹"的
        if '新建文件夹' in item:
            target_dir = full
            break

if not target_dir:
    # 尝试直接创建临时链接
    print("请在桌面保留 新建文件夹")
    sys.exit(1)

print(f"工作目录: {target_dir}")
print(f"内容: {[os.path.basename(d) for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]}")

import xlrd

def extract_finance_data():
    """提取附表1（财务决算表）和附表2（审核汇总表+资金审核表）的资金数据"""
    
    projs = []
    for d in os.listdir(target_dir):
        full_dir = os.path.join(target_dir, d)
        if not os.path.isdir(full_dir):
            continue
        
        proj = {'name': d, 'files': {}}
        for f in os.listdir(full_dir):
            fp = os.path.join(full_dir, f)
            if '附件1' in f and f.endswith('.xls'):
                proj['files']['附表1'] = fp
            elif '附件2' in f and f.endswith('.xls'):
                proj['files']['附表2'] = fp
        projs.append(proj)
    
    return projs

projs = extract_finance_data()

for proj in projs:
    print(f"\n{'#'*70}")
    print(f"# 项目: {proj['name']}")
    print(f"{'#'*70}")
    
    # ===== 附表1：02财务决算表 =====
    fp1 = proj['files'].get('附表1')
    if fp1:
        book = xlrd.open_workbook(fp1, formatting_info=False)
        for sn in book.sheet_names():
            if '02' in sn:
                sh = book.sheet_by_name(sn)
                print(f"\n【财务状况 - {sn}】")
                print(f"{'─'*60}")
                
                # 提取两列数据：资金来源(C1) vs 资金占用(C3)
                # C0=项目名称, C1=资金来源金额, C2=资金占用名称, C3=资金占用金额
                
                fund_source = {}  # 资金来源
                fund_use = {}     # 资金占用
                
                for r in range(3, sh.nrows):
                    name = str(sh.cell(r, 0).value).strip()
                    val = sh.cell(r, 1).value
                    name2 = str(sh.cell(r, 2).value).strip()
                    val2 = sh.cell(r, 3).value
                    
                    if name and isinstance(val, (int, float)) and val > 0:
                        fund_source[name] = val
                        print(f"  来源 | {name:<24} {val:>14,.2f}")
                    
                    if name2 and isinstance(val2, (int, float)) and val2 > 0:
                        fund_use[name2] = val2
                        print(f"  占用 | {name2:<24} {val2:>14,.2f}")
                
                print(f"\n  {'─'*45}")
                source_total = fund_source.get('合       计', sum(fund_source.values()))
                use_total = fund_use.get('合       计', sum(fund_use.values()))
                print(f"  资金来源合计: {source_total:>14,.2f} 元")
                print(f"  资金占用合计: {use_total:>14,.2f} 元")
                
                balance = source_total - use_total
                print(f"  差额(结余/缺口): {balance:>14,.2f} 元 = {balance/10000:.2f} 万元")
                
                # 分析资金构成
                print(f"\n  【资金来源分析】")
                if '一、基建拨款' in fund_source:
                    print(f"  基建拨款: {fund_source['一、基建拨款']:,.2f}元 = {fund_source['一、基建拨款']/10000:.2f}万元")
                if '二、部门自筹资金' in fund_source:
                    print(f"  自筹资金: {fund_source['二、部门自筹资金']:,.2f}元")
                if '三、项目资本' in fund_source:
                    print(f"  项目资本: {fund_source['三、项目资本']:,.2f}元")
                if '七、应付款合计' in fund_source:
                    print(f"  应付款: {fund_source['七、应付款合计']:,.2f}元")
                
                print(f"\n  【资金占用分析】")
                # 在02表里，资金占用是C2/C3列
                for name2, val2 in fund_use.items():
                    if '在建工程' in name2 or '待核销' in name2 or '交付' in name2 or '货币' in name2:
                        print(f"  {name2}: {val2:,.2f}元 = {val2/10000:.2f}万元")
                if '货币资金合计' in fund_use:
                    mx = fund_use['货币资金合计']
                    print(f"\n  ⚠️ 货币资金余额: {mx:,.2f}元 = {mx/10000:.2f}万元 ——结余资金需退回财政")
    
    # ===== 附表2：02资金审核表 =====
    fp2 = proj['files'].get('附表2')
    if fp2:
        book = xlrd.open_workbook(fp2, formatting_info=False)
        
        for sn in book.sheet_names():
            if any(kw in sn for kw in ['01','审核','汇总']):
                sh = book.sheet_by_name(sn)
                print(f"\n【审核汇总表 - {sn}】")
                print(f"{'─'*60}")
                
                # 找到总计行（R4）
                for r in range(sh.nrows):
                    c0 = str(sh.cell(r, 0).value).strip()
                    c1 = str(sh.cell(r, 1).value).strip()
                    
                    if c1 in ['总    计', '合    计', '合计']:
                        # 读C3(批准概算金额), C5(送审投资金额), C7(审定投资金额)
                        val_c3 = sh.cell(r, 3).value
                        val_c5 = sh.cell(r, 5).value
                        val_c7 = sh.cell(r, 7).value
                        
                        print(f"  批准概算(元): {val_c3:,.2f} = {val_c3/10000:.2f}万") if isinstance(val_c3, (int,float)) and val_c3 > 0 else None
                        print(f"  送审投资(元): {val_c5:,.2f} = {val_c5/10000:.2f}万") if isinstance(val_c5, (int,float)) and val_c5 > 0 else None
                        print(f"  审定投资(元): {val_c7:,.2f} = {val_c7/10000:.2f}万") if isinstance(val_c7, (int,float)) and val_c7 > 0 else None
            
            # 找资金审核表
            if any(kw in sn for kw in ['02','资金']):
                sh = book.sheet_by_name(sn)
                print(f"\n【资金审核表 - {sn}】")
                print(f"{'─'*60}")
                
                # 资金审核表结构：
                # C0=序号/科目, C1=项目, C2=批准金额, C3=未明确
        
        # 找"02资金审核表"
        for sn in book.sheet_names():
            if '02' in sn or '资金' in sn:
                sh = book.sheet_name(sn)
                sh = book.sheet_by_name(sn)
                print(f"\n【资金审核表 - {sn} ({sh.nrows}行)】")
                for r in range(sh.nrows):
                    parts = []
                    for c in range(min(6, sh.ncols)):
                        v = sh.cell(r,c).value
                        if isinstance(v, float) and abs(v) > 0.01:
                            parts.append(f"C{c}={v:,.2f}")
                        elif v:
                            t = str(v).strip()[:30]
                            parts.append(f"C{c}={t}")
                    if parts:
                        print(f"  R{r}: {' | '.join(parts)}")
        
        # 债权债务明细
        for sn in book.sheet_names():
            if '债权' in sn or '债务' in sn or '应收' in sn or '应付' in sn:
                sh = book.sheet_by_name(sn)
                print(f"\n【债权债务明细 - {sn} ({sh.nrows}行)】")
                for r in range(min(sh.nrows, 15)):
                    parts = []
                    for c in range(min(8, sh.ncols)):
                        v = sh.cell(r,c).value
                        if isinstance(v, float) and abs(v) > 0.01:
                            parts.append(f"C{c}={v:,.2f}")
                        elif v:
                            t = str(v).strip()[:25]
                            parts.append(f"C{c}={t}")
                    if parts:
                        print(f"  R{r}: {' | '.join(parts)}")

print("\n完毕")
