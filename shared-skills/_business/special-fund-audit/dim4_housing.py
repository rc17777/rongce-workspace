#!/usr/bin/env python3
"""dim4: 保障性住房资金"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input','-i', required=True, help='保障房申请清册')
    parser.add_argument('--house','-p', help='房产登记数据')
    parser.add_argument('--output','-o', default='housing_fund_anomalies.xlsx')
    args = parser.parse_args()
    
    df = pd.read_excel(args.input)
    findings = []
    
    # 1. 申请人已有房产
    if args.house:
        house = pd.read_excel(args.house)
        id_col = [c for c in df.columns if '身份证' in str(c)][0]
        house_id = [c for c in house.columns if '身份证' in str(c)][0]
        name_col = [c for c in df.columns if '姓名' in str(c)]
        
        house_ids = set(house[house_id].astype(str))
        for idx, row in df.iterrows():
            if str(row[id_col]) in house_ids:
                name = row.get(name_col[0], 'N/A') if name_col else 'N/A'
                houses = house[house[house_id]==str(row[id_col])]
                print(f'   🔴 {name}: 已持有房产')
                findings.append({'类型':'已有房产','姓名':str(name),'风险等级':'🔴'})
    
    # 2. 租金补贴: 应缴vs实缴
    due_col = [c for c in df.columns if '应缴' in str(c) or '应收' in str(c)]
    paid_col = [c for c in df.columns if '实缴' in str(c) or '实收' in str(c)]
    if due_col and paid_col:
        due = pd.to_numeric(df[due_col[0]], errors='coerce')
        paid = pd.to_numeric(df[paid_col[0]], errors='coerce')
        gap = due - paid
        name_col = [c for c in df.columns if '姓名' in str(c) or '住户' in str(c)]
        for idx, g in gap.dropna().items():
            if g > 500:
                name = df.iloc[idx].get(name_col[0], 'N/A') if name_col else 'N/A'
                print(f'   🟡 {name}: 欠缴{g:.0f}元')
                findings.append({'类型':'租金欠缴','姓名':str(name),'欠缴金额':g,'风险等级':'🟡'})
    
    # 3. 空置率分析
    occupy_col = [c for c in df.columns if '入住' in str(c) or '空置' in str(c) or '状态' in str(c)]
    if occupy_col:
        empty = sum(1 for _, row in df.iterrows() if '空' in str(row.get(occupy_col[0], '')))
        total = len(df)
        empty_rate = empty/total*100
        if empty_rate > 10:
            print(f'   🟡 空置率{empty_rate:.0f}% ({empty}/{total})')
            findings.append({'类型':'高空置率','空置套数':empty,'总套数':total,'空置率':f'{empty_rate:.0f}%','风险等级':'🟡' if empty_rate<20 else '🔴'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n保障房: 🔴{red} → {args.output}')
    else:
        print('\n✅ 保障房未发现异常')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
