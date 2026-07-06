#!/usr/bin/env python3
"""dim2: 三公经费审查"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser(description='三公经费审查')
    parser.add_argument('--input','-i', required=True, help='三公经费明细表')
    parser.add_argument('--output','-o', default='public_expense_result.xlsx')
    args = parser.parse_args()
    
    df = pd.read_excel(args.input)
    findings = []
    
    # 1. Check for over-budget
    for col in df.columns:
        if '预算' in str(col):
            actual_col = col.replace('预算','').replace('批复','').strip()
            if actual_col in df.columns:
                budget_vals = pd.to_numeric(df[col], errors='coerce')
                actual_vals = pd.to_numeric(df[actual_col], errors='coerce')
                overs = actual_vals > budget_vals
                for idx in overs[overs].index:
                    ratio = (actual_vals[idx] / budget_vals[idx] - 1) * 100
                    dept = df.iloc[idx].get('部门', df.iloc[idx].get('单位', f'行{idx}'))
                    print(f'   🔴 {dept}: {actual_col}超预算{ratio:.0f}%')
                    findings.append({
                        '部门': str(dept), '异常类型': '超预算',
                        '预算数': budget_vals[idx], '实际数': actual_vals[idx],
                        '超支率': f'{ratio:.0f}%', '风险等级': '🔴'
                    })
    
    # 2. Hidden expenses - check neighbor科目异常增长
    expense_cols = [c for c in df.columns if any(k in str(c) for k in ['支出','费用'])]
    if len(expense_cols) >= 2:
        for i, c in enumerate(expense_cols):
            vals = pd.to_numeric(df[c], errors='coerce')
            mean = vals.mean()
            std = vals.std()
            if std > 0:
                for idx, v in vals.dropna().items():
                    if v > mean + 3*std:
                        dept = df.iloc[idx].get('部门', df.iloc[idx].get('单位', f'行{idx}'))
                        print(f'   🟡 {dept}: {c}={v/1e4:.1f}万 (超出均值{((v-mean)/std):.1f}σ)')
                        findings.append({
                            '部门': str(dept), '异常类型': '异常高支出',
                            '科目': c, '金额': f'{v/1e4:.1f}万',
                            '偏离': f'{((v-mean)/std):.1f}σ', '风险等级': '🟡'
                        })
    
    # 3. Per-capita check
    headcount_col = None
    for c in df.columns:
        if '人数' in str(c) or '编制' in str(c) or '人员' in str(c):
            headcount_col = c
            break
    
    if headcount_col and expense_cols:
        for c in expense_cols:
            vals = pd.to_numeric(df[c], errors='coerce')
            heads = pd.to_numeric(df[headcount_col], errors='coerce')
            per_cap = vals / heads.replace(0, np.nan)
            q3 = per_cap.quantile(0.75)
            for idx, pc in per_cap.dropna().items():
                if pc > q3 * 2:
                    dept = df.iloc[idx].get('部门', df.iloc[idx].get('单位', f'行{idx}'))
                    print(f'   🟡 {dept}: {c}人均{pc/1e4:.1f}万 (Q3的{pc/q3:.1f}倍)')
                    findings.append({
                        '部门': str(dept), '异常类型': '人均异常',
                        '科目': c, '人均': f'{pc/1e4:.1f}万',
                        '倍数': f'{pc/q3:.1f}倍', '风险等级': '🟡'
                    })
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        yellow = sum(1 for f in findings if f['风险等级']=='🟡')
        print(f'\n三公经费: 🔴{red} 🟡{yellow} → {args.output}')
    else:
        print('\n✅ 三公经费未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__':
    main()
