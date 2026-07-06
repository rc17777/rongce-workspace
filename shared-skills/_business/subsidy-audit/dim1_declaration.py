#!/usr/bin/env python3
"""dim1: 补贴申报合规性检查"""
import argparse, sys
import pandas as pd
import numpy as np
from collections import Counter

def main():
    parser = argparse.ArgumentParser(description='补贴申报合规性检查')
    parser.add_argument('--input','-i', required=True, help='补贴申报清册')
    parser.add_argument('--output','-o', default='subsidy_declaration_anomalies.xlsx')
    args = parser.parse_args()
    
    df = pd.read_excel(args.input)
    findings = []
    
    # 1. 重复申报（同名/同身份证/同地块多次出现）
    for col in df.columns:
        for tag in ['姓名','身份证','地块','地址']:
            if tag in str(col):
                dup = df[col].value_counts()
                for val, cnt in dup[dup > 1].items():
                    if pd.notna(val) and str(val).strip():
                        print(f'   🔴 {tag}重复: {val} ({cnt}次)')
                        findings.append({
                            '异常类型': f'{tag}重复',
                            '值': str(val)[:50], '次数': cnt,
                            '风险等级': '🔴'
                        })
    
    # 2. 面积异常（同村相同面积过多）
    area_col = None
    for c in df.columns:
        if '面积' in str(c) or '亩' in str(c):
            area_col = c
            break
    
    village_col = None
    for c in df.columns:
        if '村' in str(c) or '社区' in str(c) or '乡镇' in str(c):
            village_col = c
            break
    
    if area_col and village_col:
        for v in df[village_col].dropna().unique():
            vdata = df[df[village_col]==v]
            areas = vdata[area_col].value_counts()
            for a, cnt in areas.items():
                if cnt >= 3 and a > 0:
                    print(f'   🟡 {v}: {cnt}户面积均为{a}亩')
                    findings.append({
                        '异常类型': '同村面积雷同', '村': str(v),
                        '面积': f'{a}亩', '户数': cnt, '风险等级': '🔴' if cnt>=5 else '🟡'
                    })
    
    # 3. 时间聚类（申报集中在某一天）
    date_col = None
    for c in df.columns:
        if '日期' in str(c) or '时间' in str(c) or '申报日期' in str(c):
            date_col = c
            break
    
    if date_col:
        dates = df[date_col].value_counts()
        total = len(df)
        for d, cnt in dates.items():
            if cnt > total * 0.3:
                print(f'   🟡 申报时间聚类: {d} 日{cnt}户({cnt/total*100:.0f}%)')
                findings.append({
                    '异常类型': '申报时间聚类', '日期': str(d),
                    '户数': cnt, '占比': f'{cnt/total*100:.0f}%', '风险等级': '🟡'
                })
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        yellow = sum(1 for f in findings if f['风险等级']=='🟡')
        print(f'\n申报合规性: 🔴{red} 🟡{yellow} → {args.output}')
    else:
        print('\n✅ 申报合规性未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__':
    main()
