#!/usr/bin/env python3
"""dim1: 预算执行偏差分析"""
import argparse, sys
from pathlib import Path
import pandas as pd
import numpy as np

def load_budget_data(budget_path, final_path):
    budget = pd.read_excel(budget_path)
    final = pd.read_excel(final_path)
    return budget, final

def check_variance(budget, final):
    """检测预算vs决算偏差"""
    print('\n📊 预算执行偏差分析:')
    findings = []
    
    # Try to find common columns
    for col in budget.columns:
        if col in final.columns and col not in ['项目','科目','名称','单位','序号']:
            try:
                b_vals = pd.to_numeric(budget[col], errors='coerce')
                f_vals = pd.to_numeric(final[col], errors='coerce')
                variance = (f_vals - b_vals) / b_vals.abs().replace(0, np.nan) * 100
                
                anomalies = variance.dropna()
                for idx, v in anomalies.items():
                    if abs(v) > 15:
                        item = budget.iloc[idx].get('项目', budget.iloc[idx].get('科目', f'行{idx}'))
                        level = '🔴' if abs(v) > 30 else '🟡'
                        print(f'   {level} {item}: {v:+.1f}%')
                        findings.append({
                            '项目': str(item),
                            '指标': col,
                            '预算数': budget[col].iloc[idx],
                            '决算数': final[col].iloc[idx],
                            '偏差率': f'{v:.1f}%',
                            '风险等级': level,
                        })
            except:
                continue
    
    return findings

def check_progress(budget, final):
    """检测支出进度"""
    print('\n📅 支出进度检查:')
    findings = []
    
    for col in budget.columns:
        if '支出' in str(col) or '拨付' in str(col):
            if col in final.columns:
                try:
                    b_vals = pd.to_numeric(budget[col], errors='coerce')
                    f_vals = pd.to_numeric(final[col], errors='coerce')
                    progress = f_vals / b_vals.abs().replace(0, np.nan) * 100
                    
                    for idx, p in progress.dropna().items():
                        if p < 50 or p > 120:
                            item = budget.iloc[idx].get('项目', f'行{idx}')
                            level = '🔴' if p < 30 or p > 130 else '🟡'
                            tag = '严重滞后' if p < 30 else ('滞后' if p < 50 else '超支')
                            print(f'   {level} {item}: 进度{p:.0f}% ({tag})')
                            findings.append({
                                '项目': str(item),
                                '指标': f'{col}进度',
                                '进度': f'{p:.0f}%',
                                '状态': tag,
                                '风险等级': level,
                            })
                except:
                    continue
    
    return findings

def main():
    parser = argparse.ArgumentParser(description='预算执行偏差分析')
    parser.add_argument('--budget','-b', required=True, help='预算批复表')
    parser.add_argument('--final','-d', required=True, help='决算报表')
    parser.add_argument('--output','-o', default='budget_variance_result.xlsx')
    args = parser.parse_args()
    
    budget, final = load_budget_data(args.budget, args.final)
    
    all_findings = []
    all_findings.extend(check_variance(budget, final))
    all_findings.extend(check_progress(budget, final))
    
    if all_findings:
        df = pd.DataFrame(all_findings)
        df.to_excel(args.output, index=False)
        df[df['风险等级']=='🔴'].to_excel(
            args.output.replace('.xlsx','_anomalies.xlsx'), index=False)
        
        red = sum(1 for f in all_findings if f['风险等级']=='🔴')
        yellow = sum(1 for f in all_findings if f['风险等级']=='🟡')
        print(f'\n预算执行偏差: 🔴{red}项 🟡{yellow}项 → {args.output}')
    else:
        print('\n✅ 预算执行偏差在正常范围')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__':
    main()
