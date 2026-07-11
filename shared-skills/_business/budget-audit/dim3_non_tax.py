#!/usr/bin/env python3
"""dim3: 非税收入完整性核查"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser(description='非税收入完整性核查')
    parser.add_argument('--input','-i', required=True, help='非税收入征缴表(应缴/实缴/减免/缓缴)')
    parser.add_argument('--output','-o', default='non_tax_result.xlsx')
    args = parser.parse_args()
    
    df = pd.read_excel(args.input)
    findings = []
    
    # Find 应缴/实缴 columns
    due_col = actual_col = waived_col = defer_col = None
    for c in df.columns:
        if '应缴' in str(c): due_col = c
        elif '实缴' in str(c): actual_col = c
        elif '减免' in str(c): waived_col = c
        elif '缓缴' in str(c): defer_col = c
        elif '欠缴' in str(c): actual_col = c
    
    if due_col and actual_col:
        due = pd.to_numeric(df[due_col], errors='coerce')
        actual = pd.to_numeric(df[actual_col], errors='coerce')
        gap = due - actual
        gap_rate = gap / due.abs().replace(0, np.nan) * 100
        
        for idx, g in gap_rate.dropna().items():
            if g > 5:
                item = df.iloc[idx].get('项目', df.iloc[idx].get('收费项目', df.iloc[idx].get('科目', f'行{idx}')))
                level = '🔴' if g > 20 else '🟡'
                print(f'   {level} {item}: 欠缴{abs(g):.0f}% ({gap[idx]/1e4:.1f}万)')
                findings.append({
                    '项目': str(item), '异常类型': '欠缴',
                    '应缴金额': due[idx], '实缴金额': actual[idx],
                    '欠缴率': f'{abs(g):.0f}%', '风险等级': level
                })
    
    # 减免合规性（减免率异常）
    if waived_col and due_col:
        waived = pd.to_numeric(df[waived_col], errors='coerce')
        due = pd.to_numeric(df[due_col], errors='coerce')
        waiver_rate = waived / due.abs().replace(0, np.nan) * 100
        
        for idx, wr in waiver_rate.dropna().items():
            if wr > 30:
                item = df.iloc[idx].get('项目', df.iloc[idx].get('收费项目', f'行{idx}'))
                print(f'   🟡 {item}: 减免率{wr:.0f}%')
                findings.append({
                    '项目': str(item), '异常类型': '高减免率',
                    '减免金额': waived[idx], '减免率': f'{wr:.0f}%',
                    '风险等级': '🟡'
                })
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        yellow = sum(1 for f in findings if f['风险等级']=='🟡')
        print(f'\n非税收入: 🔴{red} 🟡{yellow} → {args.output}')
    else:
        print('\n✅ 非税收入未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__':
    main()
