#!/usr/bin/env python3
"""
模型2: 报价规律性识别 — 围标串标特征（等差数列/阶梯报价）
来源：群众语言堂公众号《政府采购审计大数据技术超详细操作》
"""
import pandas as pd
import argparse
import sys
from itertools import combinations

def detect_arithmetic_sequence(prices, tolerance=0.02):
    """检测报价是否呈等差数列"""
    if len(prices) < 3:
        return False, None
    sorted_prices = sorted(prices)
    diffs = [sorted_prices[i+1] - sorted_prices[i] for i in range(len(sorted_prices)-1)]
    if len(diffs) < 2:
        return False, None
    # 检查相邻差值比例是否接近
    avg_diff = sum(diffs) / len(diffs)
    if avg_diff == 0:
        return False, None
    for d in diffs:
        if abs(d - avg_diff) / abs(avg_diff) > tolerance:
            return False, None
    return True, sorted_prices

def main():
    parser = argparse.ArgumentParser(description='报价规律性识别')
    parser.add_argument('--input', '-i', required=True, help='投标报价表.xlsx')
    parser.add_argument('--output', '-o', default='疑点_报价规律性.xlsx', help='输出文件')
    parser.add_argument('--tolerance', type=float, default=0.02, help='等差公差比例容忍度（默认0.02=2%）')
    args = parser.parse_args()

    try:
        df = pd.read_excel(args.input)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    # 检查字段
    required = ['项目名称', '投标单位', '投标报价']
    for col in required:
        if col not in df.columns:
            print(f"❌ 缺少必要字段: {col}")
            print(f"   现有字段: {list(df.columns)}")
            sys.exit(1)

    results = []
    for proj, group in df.groupby('项目名称'):
        prices = group[['投标单位', '投标报价']].drop_duplicates()
        if len(prices) < 3:
            continue
        vals = prices['投标报价'].values
        is_arithmetic, seq = detect_arithmetic_sequence(vals, args.tolerance)
        if is_arithmetic:
            results.append({
                '项目名称': proj,
                '投标单位数': len(prices),
                '报价排序': ' → '.join([f"{r['投标单位']}({r['投标报价']})" 
                               for _, r in prices.sort_values('投标报价').iterrows()]),
                '疑点类型': '报价呈等差数列'
            })

    if len(results) == 0:
        print("✅ 未发现报价呈规律性（等差数列）的疑点")
        pd.DataFrame(columns=['项目名称', '投标单位数', '报价排序', '疑点类型']).to_excel(args.output, index=False)
        return

    result_df = pd.DataFrame(results)
    result_df.to_excel(args.output, index=False)
    print(f"✅ 完成！共发现 {len(result_df)} 个疑点项目")
    print(f"   输出文件: {args.output}")
    print(f"\n   疑点明细:")
    for _, row in result_df.iterrows():
        print(f"   📋 {row['项目名称']} ({row['投标单位数']}家)")
        print(f"      {row['报价排序']}")

if __name__ == '__main__':
    main()
