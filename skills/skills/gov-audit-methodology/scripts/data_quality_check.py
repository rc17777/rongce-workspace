# -*- coding: utf-8 -*-
"""
数据质量快速检查脚本
用途：进场前对被审计单位数据做基础质量检查
用法：python data_quality_check.py <数据文件.csv/.xlsx>
"""

import pandas as pd
import sys
from datetime import datetime

def check_data_quality(filepath):
    """对数据文件做全面的质量检查"""

    # 读取数据
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif filepath.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(filepath)
    else:
        print("不支持的文件格式，请使用 .csv 或 .xlsx")
        return

    print(f"\n{'='*60}")
    print(f"  数据质量检查报告")
    print(f"  文件: {filepath}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    # 1. 基本信息
    print("【基本信息】")
    print(f"  行数: {len(df):,}")
    print(f"  列数: {len(df.columns)}")
    print(f"  内存占用: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    print()

    # 2. 字段清单
    print("【字段清单】")
    print(f"  {'字段名':<30} {'类型':<15} {'非空数':>10} {'空值率':>8}")
    print(f"  {'-'*63}")
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].count()
        null_rate = (len(df) - non_null) / len(df) * 100
        flag = " ⚠️" if null_rate > 20 else ""
        print(f"  {col:<30} {dtype:<15} {non_null:>10,} {null_rate:>7.1f}%{flag}")
    print()

    # 3. 重复检查
    dup_count = df.duplicated().sum()
    print(f"【重复检查】")
    print(f"  完全重复行: {dup_count:,} ({dup_count/len(df)*100:.2f}%)")
    print()

    # 4. 数值列统计
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    if num_cols:
        print("【数值列统计】")
        for col in num_cols:
            stats = df[col].describe()
            print(f"  {col}:")
            print(f"    均值={stats['mean']:,.2f}  中位数={stats['50%']:,.2f}")
            print(f"    最小={stats['min']:,.2f}  最大={stats['max']:,.2f}")
            print(f"    标准差={stats['std']:,.2f}")
            # 异常值提示
            q1, q3 = stats['25%'], stats['75%']
            iqr = q3 - q1
            outliers = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
            if outliers > 0:
                print(f"    ⚠️ 疑似异常值: {outliers} 条 (IQR法)")
        print()

    # 5. 日期列检查
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    if date_cols:
        print("【日期列范围】")
        for col in date_cols:
            print(f"  {col}: {df[col].min()} ~ {df[col].max()}")
        print()

    # 6. 建议
    print("【检查建议】")
    issues = []
    if dup_count > len(df) * 0.01:
        issues.append(f"重复数据占比 {dup_count/len(df)*100:.1f}%，建议去重")
    for col in df.columns:
        null_rate = (len(df) - df[col].count()) / len(df) * 100
        if null_rate > 30:
            issues.append(f"字段 '{col}' 空值率 {null_rate:.1f}%，需确认数据完整性")
    if not issues:
        print("  ✅ 数据质量良好，未发现显著问题")
    else:
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python data_quality_check.py <数据文件.csv/.xlsx>")
        sys.exit(1)
    check_data_quality(sys.argv[1])
