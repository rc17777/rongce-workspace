#!/usr/bin/env python3
"""dim2: 造价偏差分析"""
import argparse, sys
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bq','-b', required=True, help='工程量清单(中标)')
    parser.add_argument('--market','-m', help='市场价参考')
    parser.add_argument('--settlement','-s', help='结算书')
    parser.add_argument('--output','-o', default='cost_deviation_anomalies.xlsx')
    args = parser.parse_args()
    
    bq = pd.read_excel(args.bq)
    findings = []
    
    # 1. 清单项单价 vs 市场价偏离
    if args.market:
        market = pd.read_excel(args.market)
        item_col = [c for c in bq.columns if '项目' in str(c) or '名称' in str(c) or '清单' in str(c)]
        price_col = [c for c in bq.columns if '单价' in str(c) or '综合单价' in str(c)]
        m_item = [c for c in market.columns if '项目' in str(c) or '名称' in str(c)]
        m_price = [c for c in market.columns if '价' in str(c) or '市场' in str(c)]
        
        if item_col and price_col and m_item and m_price:
            market_map = market.set_index(m_item[0])[m_price[0]].to_dict()
            for idx, row in bq.iterrows():
                item = row.get(item_col[0])
                if item in market_map and market_map[item] > 0:
                    dev = (row[price_col[0]] - market_map[item]) / market_map[item] * 100
                    if abs(dev) > 20:
                        print(f'   {"🔴" if abs(dev)>40 else "🟡"} {item}: {dev:+.0f}%')
                        findings.append({'类型':'单价偏离','清单项':str(item),'中标单价':row[price_col[0]],'市场价':market_map[item],'偏离':f'{dev:+.0f}%','风险等级':'🔴' if abs(dev)>40 else '🟡'})
    
    # 2. 工程量偏差(中标清单 vs 结算)
    if args.settlement:
        settlement = pd.read_excel(args.settlement)
        s_item = [c for c in settlement.columns if '项目' in str(c) or '清单' in str(c)]
        s_qty = [c for c in settlement.columns if '工程量' in str(c) or '数量' in str(c)]
        bq_item = [c for c in bq.columns if '项目' in str(c) or '清单' in str(c)]
        bq_qty = [c for c in bq.columns if '工程量' in str(c) or '数量' in str(c)]
        
        if s_item and s_qty and bq_item and bq_qty:
            bq_map = bq.set_index(bq_item[0])[bq_qty[0]].to_dict()
            for idx, row in settlement.iterrows():
                item = row.get(s_item[0])
                if item in bq_map and bq_map[item] > 0:
                    dev = (row[s_qty[0]] - bq_map[item]) / bq_map[item] * 100
                    if abs(dev) > 15:
                        print(f'   {"🔴" if abs(dev)>30 else "🟡"} {item}: 工程量偏差{dev:+.0f}%')
                        findings.append({'类型':'工程量偏差','清单项':str(item),'中标量':bq_map[item],'结算量':row[s_qty[0]],'偏差':f'{dev:+.0f}%','风险等级':'🔴' if abs(dev)>30 else '🟡'})
    
    if findings:
        pd.DataFrame(findings).to_excel(args.output, index=False)
        red = sum(1 for f in findings if f['风险等级']=='🔴')
        print(f'\n造价偏差: 🔴{red} → {args.output}')
    else:
        print('\n✅ 造价偏差在正常范围')
        pd.DataFrame().to_excel(args.output)

if __name__ == '__main__': main()
