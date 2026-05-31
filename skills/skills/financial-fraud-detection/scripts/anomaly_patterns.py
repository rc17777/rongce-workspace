#!/usr/bin/env python3
"""
财务造假 — 异常交易模式检测（IQR/Z分/Isolation Forest三选一）
来源：群众语言堂《七大核心方法玩转审计数据分析》
"""
import pandas as pd
import numpy as np
import argparse
import sys
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def detect_outliers(df, amount_col, method, threshold):
    if method == 'iqr':
        Q1, Q3 = df[amount_col].quantile(0.25), df[amount_col].quantile(0.75)
        IQR = Q3 - Q1
        lo, hi = Q1 - threshold*IQR, Q3 + threshold*IQR
        out = df[(df[amount_col] < lo) | (df[amount_col] > hi)].copy()
        out['异常类型'] = 'IQR'
        out['下限/上限'] = f"{round(lo,2)}~{round(hi,2)}"
    elif method == 'zscore':
        mean, std = df[amount_col].mean(), df[amount_col].std()
        z = np.abs((df[amount_col] - mean) / std)
        out = df[z > threshold].copy()
        out['异常类型'] = f'Z分({threshold}σ)'
        out['Z分数'] = z[z > threshold].round(2)
    else:
        features = [amount_col]
        mask = df[features].notna().all(axis=1)
        X = df.loc[mask, features]
        Xs = StandardScaler().fit_transform(X)
        model = IsolationForest(contamination=0.05, random_state=42)
        df.loc[mask, '异常标签'] = model.fit_predict(Xs)
        out = df[df['异常标签'] == -1].copy()
        out['异常类型'] = 'IsolationForest'
    return out

def detect_patterns(df, amount_col, date_col=None):
    results = []
    
    # 1. 时间模式：月末/周末/深夜交易
    if date_col and date_col in df.columns:
        d = pd.to_datetime(df[date_col], errors='coerce')
        weekend = df[d.dt.dayofweek >= 5]
        if len(weekend) > 0:
            results.append({'模式': '周末交易', '数量': len(weekend), '金额': round(weekend[amount_col].sum(), 2)})
        night = df[(d.dt.hour >= 22) | (d.dt.hour <= 6)]
        if len(night) > 0:
            results.append({'模式': '深夜交易(22-6点)', '数量': len(night), '金额': round(night[amount_col].sum(), 2)})
    
    # 2. 临近限额交易
    limits = [5000, 10000, 50000, 100000, 500000]
    for lim in limits:
        near = df[(df[amount_col] > lim * 0.95) & (df[amount_col] < lim)]
        if len(near) > 2:
            results.append({'模式': f'接近{lim}元限额', '数量': len(near), '金额': round(near[amount_col].sum(), 2)})
    
    return results

def main():
    parser = argparse.ArgumentParser(description='财务异常检测')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--amount-col', '-a', help='金额列')
    parser.add_argument('--date-col', '-d', help='日期列（用于时间模式分析）')
    parser.add_argument('--method', '-m', default='iqr', choices=['iqr', 'zscore', 'isolation_forest'])
    parser.add_argument('--output', '-o', default='./output/')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')

    amount_col = args.amount_col or [c for c in df.columns if '金额' in c or '金额' in c][0]
    
    print(f"📊 财务异常模式检测")
    print("=" * 50)
    
    # 1. 统计异常
    outliers = detect_outliers(df, amount_col, args.method, 1.5)
    print(f"\n1. 金额异常 (方法={args.method}): {len(outliers)} 条")
    if len(outliers) > 0:
        outliers.to_excel(os.path.join(args.output, '疑点_金额异常.xlsx'), index=False)
    
    # 2. 时模式
    patterns = detect_patterns(df, amount_col, args.date_col)
    print(f"\n2. 异常模式:")
    if patterns:
        pd.DataFrame(patterns).to_excel(os.path.join(args.output, '疑点_交易模式.xlsx'), index=False)
        for p in patterns:
            print(f"   {p['模式']}: {p['数量']}笔, {p['金额']}元")
    else:
        print("   未发现明显异常模式")
    
    print(f"\n✅ 输出目录: {args.output}")

if __name__ == '__main__':
    main()
