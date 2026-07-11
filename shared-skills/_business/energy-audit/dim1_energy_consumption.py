#!/usr/bin/env python3
"""dim1: 能耗单耗核查"""
import argparse, sys
import pandas as pd
import numpy as np

# 行业基准 (kgce/单位)
BENCHMARKS = {
    '水泥': {'unit': 't熟料', 'limit': 117, 'src': 'GB16780-2021'},
    '钢铁': {'unit': 't粗钢', 'limit': 560, 'src': 'GB21256'},
    '合成氨': {'unit': 't', 'limit': 1420, 'src': 'GB21344'},
    '火电': {'unit': '万kWh', 'limit': 3000, 'src': 'GB21258'},
    '建筑': {'unit': 'm²·a', 'limit': 80, 'src': 'GB50189'},
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--energy','-e', required=True, help='能耗统计表')
    parser.add_argument('--production','-p', help='产量台账')
    parser.add_argument('--sector', default='水泥', help='行业')
    parser.add_argument('--output','-o', default='energy_consumption_anomalies.xlsx')
    args = parser.parse_args()
    
    energy = pd.read_excel(args.energy)
    findings = []
    benchmark = BENCHMARKS.get(args.sector, BENCHMARKS['水泥'])
    
    # 1. 单位产品能耗 vs 行业基准
    if args.production:
        prod = pd.read_excel(args.production)
        e_amt = [c for c in energy.columns if '能耗' in str(c) or '用电' in str(c) or '用能' in str(c) or '标煤' in str(c)]
        p_amt = [c for c in prod.columns if '产量' in str(c) or '产出' in str(c)]
        
        if e_amt and p_amt:
            total_energy = energy[e_amt[0]].sum()
            total_prod = prod[p_amt[0]].sum()
            if total_prod > 0:
                unit_energy = total_energy / total_prod
                dev = (unit_energy - benchmark['limit']) / benchmark['limit'] * 100
                if dev > 10:
                    print(f'   {"🔴" if dev>20 else "🟡"} 单耗{unit_energy:.0f} vs 基准{benchmark["limit"]} {benchmark["unit"]} ({dev:+.0f}%)')
                    findings.append({'类型':'能耗超标','行业基准':benchmark['limit'],'实际单耗':f'{unit_energy:.0f}','偏离':f'{dev:+.0f}%','风险等级':'🔴' if dev>20 else '🟡'})
    
    # 2. 月度能耗波动
    date_col = [c for c in energy.columns if '月' in str(c) or '日期' in str(c)]
    val_col = [c for c in energy.columns if '能耗' in str(c) or '用电' in str(c) or '用能' in str(c)]
    if val_col:
        vals = pd.to_numeric(energy[val_col[0]], errors='coerce').dropna()
        if len(vals) >= 3:
            mean = vals.mean()
            for i, v in enumerate(vals):
                if v > mean * 1.5:
                    print(f'   🟡 月份{i+1}: 能耗{v} (均值{mean:.0f}的{v/mean:.1f}倍)')
                    findings.append({'类型':'能耗突增','月份':i+1,'能耗':v,'偏离倍数':f'{v/mean:.1f}','风险等级':'🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n能耗核查: 🔴{red} → {args.output}')
    else:
        print('\n✅ 能耗在行业基准范围内')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
