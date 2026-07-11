#!/usr/bin/env python3
"""dim3: 民政救济资金"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--relief','-r', required=True, help='救济发放表')
    parser.add_argument('--vehicle','-v', help='车辆登记数据(交叉比对)')
    parser.add_argument('--house','-p', help='房产登记数据(交叉比对)')
    parser.add_argument('--business','-b', help='工商登记数据(交叉比对)')
    parser.add_argument('--output','-o', default='civil_relief_anomalies.xlsx')
    args = parser.parse_args()
    
    relief = pd.read_excel(args.relief)
    findings = []
    
    id_col = [c for c in relief.columns if '身份证' in str(c) or '证件' in str(c)]
    name_col = [c for c in relief.columns if '姓名' in str(c)]
    income_col = [c for c in relief.columns if '收入' in str(c) or '月收入' in str(c)]
    
    # 1. 收入超标
    if income_col and id_col:
        for idx, row in relief.iterrows():
            inc = row[income_col[0]]
            if pd.notna(inc) and inc > 10000:
                name = row.get(name_col[0], 'N/A') if name_col else 'N/A'
                print(f'   🔴 {name}: 月收入{inc}元')
                findings.append({'类型':'收入超标','姓名':str(name),'月收入':inc,'风险等级':'🔴'})
    
    # 2. 车辆/房产/工商交叉
    cross_sources = [('车辆','vehicle'), ('房产','house'), ('工商','business')]
    for label, attr in cross_sources:
        path = getattr(args, attr)
        if not path or not id_col: continue
        cross = pd.read_excel(path)
        cross_id = [c for c in cross.columns if '身份证' in str(c) or '证件' in str(c)]
        if not cross_id: continue
        
        cross_ids = set(cross[cross_id[0]].astype(str))
        for idx, row in relief.iterrows():
            if str(row[id_col[0]]) in cross_ids:
                name = row.get(name_col[0], 'N/A') if name_col else 'N/A'
                print(f'   🔴 {name}: 持有{label}')
                findings.append({'类型':f'{label}资产','姓名':str(name),'风险等级':'🔴'})
    
    # 3. 重复领取多类救济
    if name_col and id_col:
        # 检查同一人是否领取多种救济
        dup = relief.groupby(id_col[0]).size()
        for val, cnt in dup[dup>1].items():
            name = relief[relief[id_col[0]]==val][name_col[0]].iloc[0] if name_col else val
            types = relief[relief[id_col[0]]==val].get('类型', relief.get('救济类别', pd.Series(['N/A']*len(relief)))).unique()
            print(f'   🟡 {name}: 领取{cnt}项 ({list(types)})')
            findings.append({'类型':'多类救济','姓名':str(name),'项数':cnt,'救济类型':str(list(types)),'风险等级':'🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n民政救济: 🔴{red} → {args.output}')
    else:
        print('\n✅ 民政救济未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
