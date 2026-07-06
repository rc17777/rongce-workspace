#!/usr/bin/env python3
"""dim4: 转移支付资金跟踪"""
import argparse, sys
import pandas as pd
import numpy as np
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='转移支付资金跟踪')
    parser.add_argument('--directive','-d', required=True, help='转移支付下达文件')
    parser.add_argument('--flow','-f', required=True, help='资金拨付流水')
    parser.add_argument('--output','-o', default='transfer_result.xlsx')
    args = parser.parse_args()
    
    directive = pd.read_excel(args.directive)
    flow = pd.read_excel(args.flow)
    findings = []
    
    # 1. 下达时效检查
    date_cols = [c for c in directive.columns if any(k in str(c) for k in ['日期','时间','下达'])]
    if date_cols:
        directive[date_cols[0]] = pd.to_datetime(directive[date_cols[0]], errors='coerce')
        now = datetime.now()
        for idx, row in directive.iterrows():
            d = row[date_cols[0]]
            if pd.notna(d):
                days = (now - d).days
                item = row.get('项目', row.get('资金名称', f'行{idx}'))
                if days > 365 * 2:
                    print(f'   🔴 {item}: 下达{days}天（超2年，可能沉淀）')
                    findings.append({'项目': str(item), '异常类型': '超2年未使用',
                                     '下达天数': days, '风险等级': '🔴'})
                elif days > 180:
                    print(f'   🟡 {item}: 下达{days}天（超半年）')
                    findings.append({'项目': str(item), '异常类型': '超半年未拨付',
                                     '下达天数': days, '风险等级': '🟡'})
    
    # 2. 资金挪用检测（同一收款方，不同项目拨款）
    receiver_col = None
    for c in flow.columns:
        if '收款' in str(c) or '单位' in str(c) or '名称' in str(c) or '账户' in str(c):
            receiver_col = c
            break
    
    project_col = None
    for c in flow.columns:
        if '项目' in str(c) or '用途' in str(c) or '资金' in str(c):
            project_col = c
            break
    
    if receiver_col and project_col:
        receiver_projects = flow.groupby(receiver_col)[project_col].nunique()
        for receiver, count in receiver_projects.items():
            if count > 3:
                print(f'   🟡 {receiver}: 接收{count}个项目资金')
                projects = flow[flow[receiver_col]==receiver][project_col].unique()
                findings.append({
                    '收款方': str(receiver), '异常类型': '多项目收款',
                    '项目数': count, '项目列表': '; '.join(str(p) for p in projects),
                    '风险等级': '🟡'
                })
    
    # 3. 大额整数转账
    amt_col = None
    for c in flow.columns:
        if '金额' in str(c) or '笔' in str(c):
            amt_col = c
            break
    
    if amt_col:
        amounts = pd.to_numeric(flow[amt_col], errors='coerce')
        for idx, amt in amounts.dropna().items():
            if amt > 500000 and amt % 100000 == 0:
                receiver = flow.iloc[idx].get(receiver_col, 'N/A') if receiver_col else 'N/A'
                print(f'   🟡 {receiver}: 整数大额{amt/1e4:.0f}万')
                findings.append({
                    '收款方': str(receiver), '异常类型': '整数大额',
                    '金额': f'{amt/1e4:.0f}万', '风险等级': '🟡'
                })
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        yellow = sum(1 for f in findings if f['风险等级']=='🟡')
        print(f'\n转移支付: 🔴{red} 🟡{yellow} → {args.output}')
    else:
        print('\n✅ 转移支付未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__':
    main()
