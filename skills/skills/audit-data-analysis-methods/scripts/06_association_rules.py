#!/usr/bin/env python3
"""
方法6: 关联规则分析 — 顺藤摸瓜找组合风险模式
"""
import pandas as pd
import numpy as np
import argparse
import sys

def prepare_itemsets(df, item_cols, id_col=None):
    """从表格数据转换事务格式"""
    transactions = []
    for _, row in df.iterrows():
        items = [str(row[col]) for col in item_cols if pd.notna(row[col])]
        if items:
            transactions.append(items)
    return transactions

def apriori_simple(transactions, min_support=0.1):
    """简单的频繁项集挖掘（不依赖mlxtend）"""
    from itertools import combinations
    
    n = len(transactions)
    item_sets = {}
    
    # 单一项
    for t in transactions:
        for item in t:
            item_sets[frozenset([item])] = item_sets.get(frozenset([item]), 0) + 1
    
    # 二项集
    for t in transactions:
        if len(t) >= 2:
            for pair in combinations(t, 2):
                item_sets[frozenset(pair)] = item_sets.get(frozenset(pair), 0) + 1
    
    # 三项集
    for t in transactions:
        if len(t) >= 3:
            for triple in combinations(t, 3):
                item_sets[frozenset(triple)] = item_sets.get(frozenset(triple), 0) + 1
    
    # 筛出频繁项集
    frequent = {k: v/n for k, v in item_sets.items() if v/n >= min_support}
    
    # 生成规则
    rules = []
    for itemset, support in frequent.items():
        items = list(itemset)
        if len(items) < 2:
            continue
        for i in range(len(items)):
            antecedent = frozenset(items[:i] + items[i+1:])
            consequent = frozenset([items[i]])
            ant_support = frequent.get(antecedent, 0)
            if ant_support > 0:
                confidence = support / ant_support
                lift = support / (ant_support * frequent.get(consequent, 1))
                if confidence > 0.5 and lift > 1:
                    rules.append({
                        '前项': '、'.join(sorted(antecedent)),
                        '后项': '、'.join(sorted(consequent)),
                        '支持度': round(support, 4),
                        '置信度': round(confidence, 4),
                        '提升度': round(lift, 4)
                    })
    
    return sorted(rules, key=lambda x: x['提升度'], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='关联规则分析')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--item-cols', '-c', nargs='+', required=True, help='物品列（用于构建事务）')
    parser.add_argument('--min-support', '-s', type=float, default=0.05, help='最小支持度')
    parser.add_argument('--output', '-o', default='./输出_关联规则.xlsx')
    args = parser.parse_args()

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')
    
    print(f"📊 关联规则分析 ({len(args.item_cols)}个维度)")
    print("=" * 50)
    
    transactions = prepare_itemsets(df, args.item_cols)
    print(f"事务数: {len(transactions)}")
    
    rules = apriori_simple(transactions, min_support=args.min_support)
    print(f"发现 {len(rules)} 条关联规则")
    
    if rules:
        print("\n高提升度规则 Top 10:")
        for r in rules[:10]:
            print(f"  {r['前项']} → {r['后项']}  (支持度={r['支持度']}, 置信度={r['置信度']}, 提升度={r['提升度']})")
        
        pd.DataFrame(rules).to_excel(args.output, index=False)
        print(f"\n✅ 输出: {args.output}")
    else:
        print("✅ 未发现有效关联规则（尝试降低--min-support）")

if __name__ == '__main__':
    main()
