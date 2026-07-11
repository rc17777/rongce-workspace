#!/usr/bin/env python3
"""dim2: 教育专项资金"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input','-i', required=True, help='教育资金台账')
    parser.add_argument('--output','-o', default='education_fund_anomalies.xlsx')
    args = parser.parse_args()
    
    df = pd.read_excel(args.input)
    findings = []
    
    # 1. 营养餐: 供应商集中度
    supplier_col = [c for c in df.columns if '供应商' in str(c) or '供货商' in str(c)]
    amt_col = [c for c in df.columns if '金额' in str(c) or '价款' in str(c)]
    
    if supplier_col and amt_col:
        total = df[amt_col[0]].sum()
        supplier_share = df.groupby(supplier_col[0])[amt_col[0]].sum() / total * 100
        for s, share in supplier_share.items():
            if share > 50:
                print(f'   🔴 {s}: 占比{share:.0f}%')
                findings.append({'类型':'供应商集中','供应商':str(s),'占比':f'{share:.0f}%','风险等级':'🔴'})
    
    # 2. 助学补贴: 申请人重复检测
    name_cols = [c for c in df.columns if '姓名' in str(c) or '学生' in str(c)]
    if name_cols:
        dup = df[name_cols[0]].value_counts()
        for val, cnt in dup[dup>1].items():
            print(f'   🔴 重复申请助学: {val} ({cnt}次)')
            findings.append({'类型':'重复申请','姓名':str(val),'次数':cnt,'风险等级':'🔴'})
    
    # 3. 校建资金: 进度vs拨付
    budget_col = [c for c in df.columns if '预算' in str(c) or '批复' in str(c)]
    actual_col = [c for c in df.columns if '拨付' in str(c) or '支出' in str(c)]
    progress_col = [c for c in df.columns if '进度' in str(c) or '完工' in str(c)]
    
    if budget_col and actual_col and progress_col:
        for idx, row in df.iterrows():
            budget = row[budget_col[0]]
            actual = row[actual_col[0]]
            progress = row[progress_col[0]]
            if pd.notna(budget) and pd.notna(actual) and pd.notna(progress) and budget > 0:
                pay_ratio = actual / budget * 100
                if pay_ratio > progress + 20:
                    proj = row.get('项目','N/A')
                    print(f'   🟡 {proj}: 拨付{pay_ratio:.0f}% > 进度{progress}%')
                    findings.append({'类型':'超进度拨付','项目':str(proj),'拨付率':f'{pay_ratio:.0f}%','进度':f'{progress}%','风险等级':'🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n教育资金: 🔴{red} → {args.output}')
    else:
        print('\n✅ 教育资金未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
