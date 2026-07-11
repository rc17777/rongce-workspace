#!/usr/bin/env python3
"""dim2: 补贴资金拨付追踪"""
import argparse, sys
import pandas as pd
import numpy as np
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='补贴拨付追踪')
    parser.add_argument('--input','-i', required=True, help='拨付流水表')
    parser.add_argument('--declare', required=True, help='申报清册(用于金额交叉比对)')
    parser.add_argument('--output','-o', default='subsidy_disbursement_anomalies.xlsx')
    args = parser.parse_args()
    
    flow = pd.read_excel(args.input)
    declare = pd.read_excel(args.declare)
    findings = []
    
    # 1. 同一账户收多户补贴
    acct_col = None
    for c in flow.columns:
        if '账户' in str(c) or '银行卡' in str(c) or '账号' in str(c):
            acct_col = c
            break
    
    name_col = None
    for c in flow.columns:
        if '姓名' in str(c) or '收款人' in str(c):
            name_col = c
            break
    
    if acct_col:
        acct_groups = flow.groupby(acct_col)
        for acct, group in acct_groups:
            if len(group) > 3:
                names = group[name_col].unique() if name_col else ['N/A']
                print(f'   🔴 账户{acct}: 收{len(group)}笔/{len(names)}人')
                findings.append({
                    '异常类型': '同一账户多户收款',
                    '账户': str(acct), '笔数': len(group),
                    '涉及人数': len(names), '风险等级': '🔴'
                })
    
    # 2. 拨付超时
    date_col = None
    for c in flow.columns:
        if '拨付日期' in str(c) or '发放日期' in str(c) or '到账' in str(c):
            date_col = c
            break
    
    if date_col and name_col:
        flow['_date'] = pd.to_datetime(flow[date_col], errors='coerce')
        
        # Also find the last date in declare
        declare_date_col = None
        for c in declare.columns:
            if '日期' in str(c) or '申报日期' in str(c):
                declare_date_col = c
                break
        
        if declare_date_col:
            declare_last = pd.to_datetime(declare[declare_date_col], errors='coerce').max()
            for idx, row in flow.iterrows():
                d = row['_date']
                if pd.notna(d) and pd.notna(declare_last):
                    lag = (d - declare_last).days
                    if lag > 30:
                        name = row.get(name_col, f'行{idx}')
                        print(f'   🟡 {name}: 申报后{lag}天才拨付')
                        findings.append({
                            '异常类型': '拨付超时', '收款人': str(name),
                            '滞后天数': lag, '风险等级': '🟡' if lag < 90 else '🔴'
                        })
    
    # 3. 拨付金额 vs 申报金额
    amt_col = None
    for c in flow.columns:
        if '金额' in str(c) or '元' in str(c):
            amt_col = c
            break
    
    if amt_col and name_col:
        # Match by name
        declare_amt_col = None
        for c in declare.columns:
            if '金额' in str(c) or '标准' in str(c) or '应发' in str(c):
                declare_amt_col = c
                break
        
        declare_name_col = None
        for c in declare.columns:
            if '姓名' in str(c) or '申报人' in str(c):
                declare_name_col = c
                break
        
        if declare_amt_col and declare_name_col:
            declare_map = declare.set_index(declare_name_col)[declare_amt_col].to_dict()
            flow['_diff'] = flow.apply(
                lambda r: abs(r[amt_col] - declare_map.get(r[name_col], 0))
                          if r[name_col] in declare_map else 0, axis=1)
            
            for idx, row in flow.iterrows():
                if row['_diff'] > 1000:
                    print(f'   🟡 {row[name_col]}: 拨付{row[amt_col]} ≠ 申报{declare_map.get(row[name_col],0)}')
                    findings.append({
                        '异常类型': '拨付申报差异', '收款人': str(row[name_col]),
                        '拨付金额': row[amt_col], '申报金额': declare_map.get(row[name_col],0),
                        '差异': row['_diff'], '风险等级': '🟡'
                    })
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        yellow = sum(1 for f in findings if f['风险等级']=='🟡')
        print(f'\n拨付追踪: 🔴{red} 🟡{yellow} → {args.output}')
    else:
        print('\n✅ 拨付未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__':
    main()
