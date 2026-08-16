#!/usr/bin/env python3
"""
方法7: 时间序列分析 — 趋势+季节性+异常波动
"""
import pandas as pd
import numpy as np
import argparse
import sys
from sklearn.linear_model import LinearRegression

def trend_analysis(df, date_col, value_col, window=3):
    df = df.copy().sort_values(date_col)
    df['移动平均'] = df[value_col].rolling(window=window, min_periods=1).mean()
    df['时间索引'] = range(len(df))
    model = LinearRegression()
    model.fit(df[['时间索引']], df[value_col])
    slope = model.coef_[0]
    df['趋势值'] = model.predict(df[['时间索引']])
    df['趋势偏离'] = df[value_col] - df['趋势值']
    threshold = df['趋势偏离'].std() * 2
    anomaly = df[np.abs(df['趋势偏离']) > threshold]
    return df, slope, anomaly

def seasonal_analysis(df, date_col, value_col):
    df = df.copy()
    df['month'] = pd.to_datetime(df[date_col]).dt.month
    monthly_avg = df.groupby('month')[value_col].mean()
    overall_avg = df[value_col].mean()
    seasonal_index = monthly_avg / overall_avg
    df['季节指数'] = df['month'].map(seasonal_index)
    df['预期值'] = overall_avg * df['季节指数']
    df['季节偏离'] = (df[value_col] - df['预期值']) / df['预期值']
    anomaly = df[np.abs(df['季节偏离']) > 0.2]
    return seasonal_index, anomaly

def main():
    parser = argparse.ArgumentParser(description='时间序列分析')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--date-col', '-d', required=True, help='日期列')
    parser.add_argument('--value-col', '-v', required=True, help='数值列')
    parser.add_argument('--output', '-o', default='./输出_时间序列.xlsx')
    parser.add_argument('--method', '-m', default='both', choices=['trend', 'seasonal', 'both'])
    args = parser.parse_args()

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')

    print(f"📊 时间序列分析 — {args.value_col}")
    print("=" * 50)

    if args.method in ('trend', 'both'):
        print("\n--- 趋势分析 ---")
        trend_df, slope, trend_anomaly = trend_analysis(df, args.date_col, args.value_col)
        print(f"趋势斜率: {slope:.4f} ({'上升中' if slope > 0 else '下降中'})")
        print(f"异常偏离点: {len(trend_anomaly)} 个")
        trend_anomaly.to_excel(args.output.replace('.xlsx', '_趋势异常.xlsx'), index=False)

    if args.method in ('seasonal', 'both'):
        print("\n--- 季节性分析 ---")
        seasonal_index, seasonal_anomaly = seasonal_analysis(df, args.date_col, args.value_col)
        print("季节指数 (1.0=平均水平):")
        for month, idx in seasonal_index.items():
            bar = '█' * int(idx * 20)
            print(f"  {int(month)}月: {idx:.2f} {bar}")
        print(f"异常月份 (偏离>20%): {len(seasonal_anomaly)} 个")
        seasonal_anomaly.to_excel(args.output.replace('.xlsx', '_季节异常.xlsx'), index=False)

    print(f"\n✅ 完成")

if __name__ == '__main__':
    main()
