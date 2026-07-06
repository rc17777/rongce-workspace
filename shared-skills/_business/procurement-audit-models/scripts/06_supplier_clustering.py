#!/usr/bin/env python3
"""
模型6: 供应商聚类分析 — 基于交易特征自动分群
来源：群众语言堂《七大核心方法玩转审计数据分析》
"""
import pandas as pd
import numpy as np
import argparse
import sys
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def main():
    parser = argparse.ArgumentParser(description='供应商聚类分析')
    parser.add_argument('--input', '-i', required=True, help='供应商交易特征表.xlsx')
    parser.add_argument('--output', '-o', default='./output/', help='输出目录')
    parser.add_argument('--clusters', '-k', type=int, default=4, help='聚类数')
    parser.add_argument('--label', '-l', help='供应商名称列')
    args = parser.parse_args()

    import os
    os.makedirs(args.output, exist_ok=True)
    
    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')

    label_col = args.label or (df.columns[0] if not pd.api.types.is_numeric_dtype(df.iloc[:, 0]) else None)
    features = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != '聚类标签']
    
    if len(features) < 2:
        print(f"❌ 需要至少2个数值特征列，当前: {features}")
        sys.exit(1)

    print(f"📊 供应商聚类分析 — {args.clusters}类, {len(features)}个特征")
    print(f"   特征: {features}")
    print(f"   数据量: {len(df)}")

    df_clean = df[features].dropna()
    mask = df[features].notna().all(axis=1)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_clean)

    kmeans = KMeans(n_clusters=args.clusters, random_state=42, n_init=10)
    df.loc[mask, '聚类标签'] = kmeans.fit_predict(X_scaled)
    df.loc[mask, '聚类标签'] = df.loc[mask, '聚类标签'].astype(int)

    # 特征均值
    summary = df.groupby('聚类标签')[features].mean().round(2)
    summary['供应商数量'] = df.groupby('聚类标签').size()

    # 风险评分（基于价格偏离、交易频率等）
    if 'avg_price_deviation' in df.columns:
        for label in range(args.clusters):
            avg_dev = df[df['聚类标签'] == label]['avg_price_deviation'].mean()
            if avg_dev > 15:
                print(f"  ⚠️ 类别 {label}: 平均价格偏离{avg_dev:.1f}% → 高风险")
            elif avg_dev > 10:
                print(f"  ⚠️ 类别 {label}: 平均价格偏离{avg_dev:.1f}% → 中风险")

    print("\n各聚类特征均值:")
    print(summary.to_string())

    out_file = os.path.join(args.output, '结果_供应商聚类.xlsx')
    with pd.ExcelWriter(out_file) as w:
        df.to_excel(w, sheet_name='全部_含聚类标签', index=False)
        summary.to_excel(w, sheet_name='聚类特征汇总')
    print(f"\n✅ 输出: {out_file}")

if __name__ == '__main__':
    main()
