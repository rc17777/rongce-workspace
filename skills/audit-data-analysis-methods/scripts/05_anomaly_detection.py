#!/usr/bin/env python3
"""
方法5: 异常检测 — 3种方法（IQR/Z分/Isolation Forest）
"""
import pandas as pd
import numpy as np
import argparse
import sys
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def iqr_detection(df, column, threshold=1.5):
    Q1, Q3 = df[column].quantile(0.25), df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower, upper = Q1 - threshold*IQR, Q3 + threshold*IQR
    outliers = df[(df[column] < lower) | (df[column] > upper)].copy()
    outliers['异常类型'] = 'IQR法'
    outliers['下限'] = round(lower, 2)
    outliers['上限'] = round(upper, 2)
    return outliers

def zscore_detection(df, column, threshold=3):
    mean, std = df[column].mean(), df[column].std()
    z_scores = np.abs((df[column] - mean) / std)
    outliers = df[z_scores > threshold].copy()
    outliers['异常类型'] = 'Z分法'
    outliers['Z分数'] = z_scores[z_scores > threshold].round(2)
    return outliers

def isolation_forest_detection(df, features, contamination=0.05):
    X = df[features].dropna()
    mask = df[features].notna().all(axis=1)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    df.loc[mask, '异常标签'] = model.fit_predict(X_scaled)
    df.loc[mask, '异常分数'] = model.decision_function(X_scaled).round(4)
    
    outliers = df[df['异常标签'] == -1].copy()
    outliers['异常类型'] = 'IsolationForest'
    return outliers

def main():
    parser = argparse.ArgumentParser(description='异常检测')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--column', '-c', help='异常检测列（IQR/Z分用）')
    parser.add_argument('--features', '-f', nargs='+', help='特征列（Isolation Forest用，多个）')
    parser.add_argument('--method', '-m', default='iqr', choices=['iqr', 'zscore', 'isolation_forest'])
    parser.add_argument('--threshold', '-t', type=float, default=1.5, help='IQR系数或Z分阈值')
    parser.add_argument('--output', '-o', default='./输出_异常检测.xlsx')
    args = parser.parse_args()

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')

    if args.method == 'isolation_forest':
        features = args.features or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][:5]
        if len(features) < 2:
            print("❌ Isolation Forest需要至少2个特征")
            sys.exit(1)
        outliers = isolation_forest_detection(df, features, contamination=0.05)
        method_name = "Isolation Forest"
    elif args.method == 'zscore':
        if not args.column:
            args.column = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][0]
        outliers = zscore_detection(df, args.column, threshold=args.threshold)
        method_name = f"Z分法 (±{args.threshold}σ)"
    else:
        if not args.column:
            args.column = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][0]
        outliers = iqr_detection(df, args.column, threshold=args.threshold)
        method_name = f"IQR法 (×{args.threshold})"

    print(f"📊 异常检测 — {method_name}")
    print("=" * 50)
    print(f"总样本: {len(df)}")
    print(f"异常数: {len(outliers)} ({len(outliers)/len(df)*100:.1f}%)")

    if len(outliers) > 0:
        outliers.to_excel(args.output, index=False)
        print(f"✅ 输出: {args.output}")
        print(f"\n异常示例:")
        print(outliers.head(10).to_string())
    else:
        print("✅ 未发现异常")

if __name__ == '__main__':
    main()
