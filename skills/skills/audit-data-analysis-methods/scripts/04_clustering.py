#!/usr/bin/env python3
"""
方法4: 聚类分析 — 物以类聚，自动分群（供应商/员工等）
"""
import pandas as pd
import numpy as np
import argparse
import sys
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def main():
    parser = argparse.ArgumentParser(description='聚类分析')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--features', '-f', nargs='+', help='聚类特征列')
    parser.add_argument('--clusters', '-k', type=int, default=4, help='聚类数量')
    parser.add_argument('--output', '-o', default='./输出_聚类分析.xlsx')
    parser.add_argument('--label', '-l', help='标签列（如供应商名称）')
    args = parser.parse_args()

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')

    features = args.features or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][:5]
    if len(features) < 2:
        print("❌ 需要至少2个数值特征列")
        sys.exit(1)

    X = df[features].dropna()
    idx_mask = df[features].notna().all(axis=1)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=args.clusters, random_state=42, n_init=10)
    df.loc[idx_mask, '聚类标签'] = kmeans.fit_predict(X_scaled)

    summary = df.groupby('聚类标签')[features].mean().round(2)
    summary['样本数'] = df.groupby('聚类标签').size()

    print(f"📊 聚类分析 ({args.clusters}类, {len(features)}个特征)")
    print("=" * 50)
    for label in range(args.clusters):
        subset = df[df['聚类标签'] == label]
        print(f"\n类别 {label} ({len(subset)} 样本):")
        for feat in features:
            print(f"  {feat}: {subset[feat].mean():.2f}")

    # 标记高风险群（根据特征自动判断）
    print("\n各聚类特征均值:")
    print(summary)

    with pd.ExcelWriter(args.output) as w:
        summary.to_excel(w, sheet_name='聚类特征')
        df.to_excel(w, sheet_name='全部数据_含标签', index=False)
    print(f"✅ 输出: {args.output}")

if __name__ == '__main__':
    main()
