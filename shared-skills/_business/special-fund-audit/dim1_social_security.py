#!/usr/bin/env python3
"""dim1: 社保资金审计"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input','-i', required=True, help='参保/待遇发放表')
    parser.add_argument('--death', help='死亡人员名单(可选)')
    parser.add_argument('--output','-o', default='social_security_anomalies.xlsx')
    args = parser.parse_args()
    
    df = pd.read_excel(args.input)
    findings = []
    
    # 1. 身份证重复
    id_col = None
    for c in df.columns:
        if '身份证' in str(c) or '证件号' in str(c):
            id_col = c; break
    if id_col:
        dup = df[id_col].value_counts()
        for val, cnt in dup[dup>1].items():
            name_col = [c for c in df.columns if '姓名' in str(c)]
            names = df[df[id_col]==val][name_col[0]].values if name_col else ['N/A']
            print(f'   🔴 身份证重复: {val} ({cnt}次) {names[0]}')
            findings.append({'类型':'身份证重复','值':str(val),'次数':cnt,'风险等级':'🔴'})
    
    # 2. 死亡人员继续领取
    if args.death:
        death = pd.read_excel(args.death)
        death_id_col = [c for c in death.columns if '身份证' in str(c) or '证件' in str(c)]
        if death_id_col and id_col:
            dead_ids = set(death[death_id_col[0]].astype(str))
            for idx, row in df.iterrows():
                if str(row[id_col]) in dead_ids:
                    name = row.get([c for c in df.columns if '姓名' in str(c)][0], 'N/A') if [c for c in df.columns if '姓名' in str(c)] else 'N/A'
                    print(f'   🔴 死亡人员仍领取: {name}')
                    findings.append({'类型':'死亡仍领','姓名':str(name),'身份证':str(row[id_col]),'风险等级':'🔴'})
    
    # 3. 待遇发放集中度
    amt_cols = [c for c in df.columns if '金额' in str(c) or '待遇' in str(c) or '发放' in str(c)]
    bank_col = [c for c in df.columns if '银行' in str(c) or '账户' in str(c)]
    if amt_cols and bank_col:
        bank_groups = df.groupby(bank_col[0])
        for bank, group in bank_groups:
            if len(group) >= 5:
                total = group[amt_cols[0]].sum()
                print(f'   🟡 账户{bank}: {len(group)}人, 总额{total/1e4:.1f}万')
                findings.append({'类型':'账户集中','账户':str(bank),'人数':len(group),'总额':f'{total/1e4:.1f}万','风险等级':'🔴' if len(group)>=10 else '🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n社保资金: 🔴{red} → {args.output}')
    else:
        print('\n✅ 社保资金未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
