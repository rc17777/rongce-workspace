#!/usr/bin/env python3
"""dim3: 进度款vs形象进度匹配 & dim4: 项目合规性"""
import argparse, sys
import pandas as pd
import numpy as np

def main_progress():
    parser = argparse.ArgumentParser()
    parser.add_argument('--payment','-p', required=True, help='进度款支付表')
    parser.add_argument('--report','-r', required=True, help='监理月报进度')
    parser.add_argument('--output','-o', default='progress_payment_anomalies.xlsx')
    args = parser.parse_args()
    
    payment = pd.read_excel(args.payment)
    report = pd.read_excel(args.report)
    findings = []
    
    # Match by project/contract
    pay_proj = [c for c in payment.columns if '项目' in str(c) or '合同' in str(c)]
    rep_proj = [c for c in report.columns if '项目' in str(c) or '合同' in str(c)]
    pay_amt = [c for c in payment.columns if '金额' in str(c) or '累计' in str(c)]
    pay_budget = [c for c in payment.columns if '合同额' in str(c) or '总价' in str(c)]
    rep_progress = [c for c in report.columns if '进度' in str(c) or '完工' in str(c)]
    
    if pay_proj and rep_proj and pay_amt and rep_progress:
        for idx, row in payment.iterrows():
            proj = row[pay_proj[0]]
            matched = report[report[rep_proj[0]] == proj]
            if len(matched) > 0:
                pay_ratio = row[pay_amt[0]] / row.get(pay_budget[0], 1) * 100 if pay_budget and row.get(pay_budget[0], 0) > 0 else 0
                progress = matched[rep_progress[0]].iloc[0]
                if pay_ratio > progress + 10:
                    print(f'   🔴 {proj}: 支付{pay_ratio:.0f}% > 进度{progress}%')
                    findings.append({'类型':'超进度支付','项目':str(proj),'支付率':f'{pay_ratio:.0f}%','形象进度':f'{progress}%','风险等级':'🔴'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n进度款匹配: 🔴{red} → {args.output}')
    else:
        print('\n✅ 进度款匹配正常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main_progress()
