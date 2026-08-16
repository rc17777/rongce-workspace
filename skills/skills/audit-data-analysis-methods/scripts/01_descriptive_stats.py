#!/usr/bin/env python3
"""
方法1: 描述性统计分析 — 给数据做体检报告
来源：群众语言堂《七大核心方法玩转审计数据分析》
"""
import pandas as pd
import numpy as np
import argparse
import sys
import os

def descriptive_statistics(df, column):
    stats = {
        '样本数量': df[column].count(),
        '平均值': round(df[column].mean(), 2),
        '中位数': round(df[column].median(), 2),
        '众数': round(df[column].mode()[0], 2) if not df[column].mode().empty else None,
        '标准差': round(df[column].std(), 2),
        '最小值': round(df[column].min(), 2),
        '最大值': round(df[column].max(), 2),
        '数据范围': round(df[column].max() - df[column].min(), 2),
        'Q1(25%分位)': round(df[column].quantile(0.25), 2),
        'Q3(75%分位)': round(df[column].quantile(0.75), 2),
        '四分位距IQR': round(df[column].quantile(0.75) - df[column].quantile(0.25), 2),
        '偏度': round(df[column].skew(), 4),
        '峰度': round(df[column].kurtosis(), 4),
    }
    return pd.DataFrame.from_dict(stats, orient='index', columns=['数值'])

def main():
    parser = argparse.ArgumentParser(description='描述性统计分析')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--column', '-c', help='要分析的列名')
    parser.add_argument('--output', '-o', default='./输出_描述性统计.xlsx')
    args = parser.parse_args()

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')
    
    if not args.column:
        # 自动找数值列
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                args.column = c
                break
        if not args.column:
            print("❌ 未找到数值列，请用 --column 指定")
            sys.exit(1)
        print(f"🔍 自动选择数值列: {args.column}")

    result = descriptive_statistics(df, args.column)
    print(f"📊 描述性统计 — {args.column}")
    print("=" * 50)
    for idx, row in result.iterrows():
        print(f"  {idx}: {row['数值']}")

    # 异常标记
    mean = df[args.column].mean()
    std = df[args.column].std()
    threshold = 2 * std
    outliers = df[(df[args.column] > mean + threshold) | (df[args.column] < mean - threshold)]
    print(f"\n⚠️ 异常值 (±2σ): {len(outliers)} 条")
    if len(outliers) > 0:
        outliers.to_excel(args.output.replace('.xlsx', '_异常值.xlsx'), index=False)
    
    result.to_excel(args.output)
    print(f"✅ 输出: {args.output}")

if __name__ == '__main__':
    main()
