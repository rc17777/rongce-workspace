#!/usr/bin/env python3
"""dim4: 工程项目合规性检查"""
import argparse, sys
import pandas as pd
import numpy as np
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input','-i', required=True, help='项目基本信息表')
    parser.add_argument('--bids','-w', help='招标文件台账')
    parser.add_argument('--contracts','-t', help='合同台账')
    parser.add_argument('--output','-o', default='compliance_anomalies.xlsx')
    args = parser.parse_args()
    
    projects = pd.read_excel(args.input)
    findings = []
    
    # 1. 超概算
    budget_col = [c for c in projects.columns if '概算' in str(c) or '批复' in str(c) or '总投资' in str(c)]
    actual_col = [c for c in projects.columns if '决算' in str(c) or '实际' in str(c) or '结算' in str(c)]
    name_col = [c for c in projects.columns if '项目' in str(c) or '名称' in str(c)]
    
    if budget_col and actual_col and name_col:
        for idx, row in projects.iterrows():
            budget = row.get(budget_col[0], 0)
            actual = row.get(actual_col[0], 0)
            if pd.notna(budget) and pd.notna(actual) and budget > 0 and actual > budget:
                ratio = (actual/budget - 1) * 100
                print(f'   🔴 {row[name_col[0]]}: 超概{ratio:.0f}%')
                findings.append({'类型':'超概算','项目':str(row[name_col[0]]),'超概率':f'{ratio:.0f}%','风险等级':'🔴'})
    
    # 2. 招标合规: 开工日期 vs 中标日期
    if args.bids and args.contracts:
        bids = pd.read_excel(args.bids)
        contracts = pd.read_excel(args.contracts)
        bid_date_col = [c for c in bids.columns if '中标日期' in str(c) or '定标日期' in str(c)]
        start_date_col = [c for c in contracts.columns if '开工' in str(c) or '施工日期' in str(c)]
        contract_name = [c for c in contracts.columns if '项目' in str(c) or '名称' in str(c)]
        
        if bid_date_col:
            bids['_bid_d'] = pd.to_datetime(bids[bid_date_col[0]], errors='coerce')
            min_bid = bids['_bid_d'].min()
            
            if start_date_col and contract_name:
                for idx, row in contracts.iterrows():
                    start = pd.to_datetime(row.get(start_date_col[0]), errors='coerce')
                    if pd.notna(start) and pd.notna(min_bid) and start < min_bid:
                        print(f'   🔴 {row[contract_name[0]]}: 开工早于招标')
                        findings.append({'类型':'未招先建','项目':str(row[contract_name[0]]),'风险等级':'🔴'})
    
    # 3. 合同签订滞后
    if args.contracts and name_col:
        contracts = pd.read_excel(args.contracts)
        sign_date_col = [c for c in contracts.columns if '签订日期' in str(c) or '签约日期' in str(c)]
        if sign_date_col:
            contracts['_sign'] = pd.to_datetime(contracts[sign_date_col[0]], errors='coerce')
            for idx, row in contracts.iterrows():
                lag = (datetime.now() - row['_sign']).days
                if pd.notna(row['_sign']) and lag > 90:
                    proj = row.get(name_col[0], f'合同{idx}') if name_col else f'合同{idx}'
                    print(f'   🟡 {proj}: 合同签订{lag}天未归档')
                    findings.append({'类型':'合同滞后','项目':str(proj),'滞后天数':lag,'风险等级':'🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n合规性: 🔴{red} → {args.output}')
    else:
        print('\n✅ 项目合规性未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
