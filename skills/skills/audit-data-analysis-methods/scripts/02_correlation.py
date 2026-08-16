#!/usr/bin/env python3
"""
方法2: 相关性分析 — 找朋友圈
"""
import pandas as pd
import numpy as np
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='相关性分析')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--columns', '-c', nargs='+', help='分析列（多个）')
    parser.add_argument('--threshold', '-t', type=float, default=0.7, help='高相关性阈值')
    parser.add_argument('--output', '-o', default='./输出_相关性分析.xlsx')
    args = parser.parse_args()

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')
    
    cols = args.columns or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][:10]
    if len(cols) < 2:
        print("❌ 需要至少2列数值列")
        sys.exit(1)

    pearson_corr = df[cols].corr(method='pearson')
    spearman_corr = df[cols].corr(method='spearman')

    # 提取高相关性对
    pairs = []
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            p = pearson_corr.iloc[i, j]
            s = spearman_corr.iloc[i, j]
            if abs(p) > args.threshold or abs(s) > args.threshold:
                pairs.append({'变量1': cols[i], '变量2': cols[j], 'Pearson': round(p, 4), 'Spearman': round(s, 4)})

    print(f"📊 相关性分析 ({len(cols)}个变量)")
    print("=" * 50)
    print("\nPearson相关系数矩阵:")
    print(pearson_corr.round(4))
    print(f"\n高相关对 (|r| > {args.threshold}): {len(pairs)} 对")
    for p in pairs:
        print(f"  {p['变量1']} ↔ {p['变量2']}: Pearson={p['Pearson']}, Spearman={p['Spearman']}")

    with pd.ExcelWriter(args.output) as w:
        pearson_corr.to_excel(w, sheet_name='Pearson')
        spearman_corr.to_excel(w, sheet_name='Spearman')
        pd.DataFrame(pairs).to_excel(w, sheet_name='高相关对', index=False)
    print(f"✅ 输出: {args.output}")

if __name__ == '__main__':
    main()
