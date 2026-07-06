#!/usr/bin/env python3
"""dim3: 补贴使用核查"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser(description='补贴使用核查')
    parser.add_argument('--input','-i', required=True, help='补贴使用记录表')
    parser.add_argument('--verify', help='实地核查数据(可选)')
    parser.add_argument('--output','-o', default='subsidy_usage_anomalies.xlsx')
    args = parser.parse_args()
    
    usage = pd.read_excel(args.input)
    findings = []
    
    # 1. 农机GPS轨迹异常
    gps_cols = [c for c in usage.columns if any(k in str(c) for k in ['GPS','轨迹','作业面积','行驶'])]
    if gps_cols:
        for g in gps_cols:
            vals = pd.to_numeric(usage[g], errors='coerce')
            zero = (vals == 0).sum()
            if zero > 0:
                print(f'   🔴 {g}: {zero}条记录为0')
                findings.append({
                    '异常类型': 'GPS轨迹为空', '指标': g,
                    '异常数': zero, '风险等级': '🔴'
                })
    
    # 2. 面积vs申报面积不一致
    area_cols = [c for c in usage.columns if '面积' in str(c)]
    if len(area_cols) >= 2:
        a1 = pd.to_numeric(usage[area_cols[0]], errors='coerce')
        a2 = pd.to_numeric(usage[area_cols[1]], errors='coerce')
        diff = abs(a1 - a2)
        for idx, d in diff.dropna().items():
            if d > 0.5:
                name = usage.iloc[idx].get('姓名','N/A')
                print(f'   🟡 {name}: 面积差异{d:.1f}亩')
                findings.append({
                    '异常类型': '面积不一致', '姓名': str(name),
                    '面积1': a1[idx], '面积2': a2[idx],
                    '差异': f'{d:.1f}亩', '风险等级': '🟡'
                })
    
    # 3. 实地核查数据比对
    if args.verify:
        verify = pd.read_excel(args.verify)
        # Match by name
        for c in verify.columns:
            if '实地面积' in str(c) or '核实面积' in str(c):
                varea_col = c
                # Find matching columns in usage
                for uc in usage.columns:
                    if '面积' in str(uc) and '核实' not in str(uc):
                        vname_col = None
                        for vc in verify.columns:
                            if '姓名' in str(vc) or '户主' in str(vc):
                                vname_col = vc
                                break
                        uname_col = None
                        for unc in usage.columns:
                            if '姓名' in str(unc) or '户主' in str(unc):
                                uname_col = unc
                                break
                        
                        if vname_col and uname_col:
                            vmap = verify.set_index(vname_col)[varea_col].to_dict()
                            for idx, row in usage.iterrows():
                                name = row.get(uname_col)
                                if name in vmap:
                                    gap = abs(row[uc] - vmap[name])
                                    if gap > 1:
                                        print(f'   🔴 {name}: 申报{row[uc]}亩 vs 实地{vmap[name]}亩')
                                        findings.append({
                                            '异常类型': '实地核查偏差',
                                            '姓名': str(name),
                                            '申报面积': row[uc],
                                            '实地面积': vmap[name],
                                            '差异': f'{gap:.1f}亩',
                                            '风险等级': '🔴'
                                        })
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        yellow = sum(1 for f in findings if f['风险等级']=='🟡')
        print(f'\n使用核查: 🔴{red} 🟡{yellow} → {args.output}')
    else:
        print('\n✅ 使用核查未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__':
    main()
