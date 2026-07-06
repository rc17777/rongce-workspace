#!/usr/bin/env python3
"""dim1: 工程变更签证合理性检测"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--changes','-c', required=True, help='变更签证台账')
    parser.add_argument('--contract','-b', help='中标合同(含合同金额)')
    parser.add_argument('--output','-o', default='change_order_anomalies.xlsx')
    args = parser.parse_args()
    
    changes = pd.read_excel(args.changes)
    findings = []
    
    # 1. 同标段变更频率
    section_col = [c for c in changes.columns if '标段' in str(c) or '合同段' in str(c) or '项目' in str(c)]
    if section_col:
        freq = changes[section_col[0]].value_counts()
        for s, cnt in freq.items():
            if cnt > 10:
                print(f'   🔴 {s}: 变更{cnt}次')
                findings.append({'类型':'高频变更','标段':str(s),'变更次数':cnt,'风险等级':'🔴' if cnt>15 else '🟡'})
    
    # 2. 变更金额占合同比
    amt_col = [c for c in changes.columns if '金额' in str(c) or '增加' in str(c) or '变更额' in str(c)]
    if args.contract and amt_col:
        contract = pd.read_excel(args.contract)
        contract_amt_col = [c for c in contract.columns if '合同金额' in str(c) or '中标价' in str(c) or '签约价' in str(c)]
        project_col = [c for c in changes.columns if '项目' in str(c) or '名称' in str(c) or '工程' in str(c)]
        c_project_col = [c for c in contract.columns if '项目' in str(c) or '名称' in str(c)]
        
        if contract_amt_col and project_col and c_project_col:
            contract_map = contract.set_index(c_project_col[0])[contract_amt_col[0]].to_dict()
            for idx, row in changes.iterrows():
                proj = row.get(project_col[0])
                if proj in contract_map and contract_map[proj] > 0:
                    ratio = row[amt_col[0]] / contract_map[proj] * 100
                    if ratio > 10:
                        print(f'   🔴 {proj}: 变更占比{ratio:.0f}%')
                        findings.append({'类型':'变更超比例','项目':str(proj),'变更比例':f'{ratio:.0f}%','风险等级':'🔴' if ratio>15 else '🟡'})
    
    # 3. 变更原因聚类
    reason_col = [c for c in changes.columns if '原因' in str(c) or '理由' in str(c) or '类型' in str(c)]
    if reason_col:
        reasons = changes[reason_col[0]].value_counts()
        total = len(changes)
        for r, cnt in reasons.items():
            if cnt > total * 0.4:
                print(f'   🟡 变更原因集中: {r} ({cnt}/{total})')
                findings.append({'类型':'原因集中','原因':str(r),'次数':cnt,'占比':f'{cnt/total*100:.0f}%','风险等级':'🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n变更签证: 🔴{red} → {args.output}')
    else:
        print('\n✅ 变更签证未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
