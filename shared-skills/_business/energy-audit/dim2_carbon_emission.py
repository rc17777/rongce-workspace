#!/usr/bin/env python3
"""dim2: 碳排放核查"""
import argparse, sys
import pandas as pd
import numpy as np

# 能源碳排放系数 (tCO2/tce)
EMISSION_FACTORS = {
    '原煤': 2.66, '洗精煤': 2.46, '焦炭': 2.96,
    '原油': 3.02, '汽油': 2.93, '柴油': 3.10,
    '天然气': 1.63, '电力': 7.18,  # 电力单位: tCO2/万kWh
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--carbon','-c', required=True, help='碳排放报告')
    parser.add_argument('--energy','-e', required=True, help='能耗统计表')
    parser.add_argument('--output','-o', default='carbon_emission_anomalies.xlsx')
    args = parser.parse_args()
    
    carbon = pd.read_excel(args.carbon)
    energy = pd.read_excel(args.energy)
    findings = []
    
    # 1. 能耗推算碳排放 vs 报告数据
    e_coal = [c for c in energy.columns if '煤' in str(c) or '标煤' in str(c)]
    e_elec = [c for c in energy.columns if '电' in str(c)]
    c_total = [c for c in carbon.columns if '排放' in str(c) or '碳' in str(c) or 'CO2' in str(c)]
    
    if (e_coal or e_elec) and c_total:
        # Rough estimate: coal * 2.6 + electricity * 7.18
        estimated = 0
        if e_coal:
            estimated += energy[e_coal[0]].sum() * 2.6
        if e_elec:
            estimated += energy[e_elec[0]].sum() * 7.18 / 10000  # kWh→万kWh
        
        reported = carbon[c_total[0]].sum()
        
        if reported > 0:
            dev = (reported - estimated) / reported * 100
            if abs(dev) > 20:
                print(f'   {"🔴" if abs(dev)>40 else "🟡"} 报告{reported:.0f}tCO2 vs 推算{estimated:.0f}tCO2 ({dev:+.0f}%)')
                findings.append({'类型':'报告推算偏离','报告值':f'{reported:.0f}','推算值':f'{estimated:.0f}','偏离':f'{dev:+.0f}%','风险等级':'🔴' if abs(dev)>40 else '🟡'})
    
    # 2. 减排量真实性
    reduction_col = [c for c in carbon.columns if '减排' in str(c) or '减少' in str(c)]
    if reduction_col and c_total:
        base_year_col = [c for c in carbon.columns if '基准' in str(c) or '上年' in str(c)]
        if base_year_col:
            for idx, row in carbon.iterrows():
                if row.get(base_year_col[0], 0) > 0:
                    reduction_ratio = row.get(reduction_col[0], 0) / row[base_year_col[0]] * 100
                    if reduction_ratio > 30:
                        print(f'   🟡 减排率{reduction_ratio:.0f}% (异常高)')
                        findings.append({'类型':'减排率异常','减排率':f'{reduction_ratio:.0f}%','风险等级':'🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n碳排放: 🔴{red} → {args.output}')
    else:
        print('\n✅ 碳排放数据一致')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
