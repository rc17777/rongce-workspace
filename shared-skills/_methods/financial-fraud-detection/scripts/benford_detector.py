#!/usr/bin/env python3
"""
财务造假筛查工具 — Benford定律检测 + 异常交易模式识别
来源：群众语言堂公众号《国有企业审计大数据技术超详细操作》
依赖：pip install pandas openpyxl numpy scipy matplotlib
"""
import pandas as pd
import numpy as np
import argparse
import sys
import os
from scipy.stats import chisquare

def benford_analysis(df, amount_col, output_dir):
    """Benford定律首位数字分布检验"""
    # 提取正数金额的首位数字
    positive = df[df[amount_col] > 0].copy()
    if len(positive) < 100:
        return None, f"样本量不足 ({len(positive)}<100)，Benford检验不可靠"

    positive['首位数字'] = positive[amount_col].astype(str).str.extract(r'([1-9])', expand=False).astype(float)
    positive = positive.dropna(subset=['首位数字'])
    positive['首位数字'] = positive['首位数字'].astype(int)

    if len(positive) < 100:
        return None, f"有效样本量不足 ({len(positive)}<100)"

    # 实际分布
    actual = positive['首位数字'].value_counts().sort_index()
    total = len(positive)

    # Benford分布理论值
    benford_probs = [np.log10(1 + 1/d) for d in range(1, 10)]
    expected = [p * total for p in benford_probs]

    # 卡方检验
    actual_vals = [actual.get(d, 0) for d in range(1, 10)]
    chi2, p_value = chisquare(actual_vals, expected)

    # 计算每个数字的偏差
    digits = list(range(1, 10))
    actual_pcts = [actual.get(d, 0) / total * 100 for d in digits]
    benford_pcts = [p * 100 for p in benford_probs]
    deviations = [actual_pcts[i] - benford_pcts[i] for i in range(9)]

    result_df = pd.DataFrame({
        '首位数字': digits,
        '实际占比(%)': [f"{p:.2f}" for p in actual_pcts],
        'Benford理论(%)': [f"{p:.2f}" for p in benford_pcts],
        '偏差(%点)': [f"{d:+.2f}" for d in deviations]
    })

    result_df.to_excel(os.path.join(output_dir, 'Benford分布分析.xlsx'), index=False)

    # 找出偏差最大的数字
    max_dev_idx = np.argmax(np.abs(deviations))

    verdict = {
        'chi2': round(chi2, 4),
        'p_value': round(p_value, 6),
        'sample_size': total,
        '结论': '可能存在人为操纵 ⚠️' if p_value < 0.05 else '未发现明显异常 ✅',
        'p值解释': f"p={'<0.05' if p_value < 0.05 else f'={p_value:.4f}'}，{'统计显著，可能有人为操纵' if p_value < 0.05 else '统计不显著，分布符合Benford定律'}",
        '最大偏差数字': f"{digits[max_dev_idx]} (偏差{deviations[max_dev_idx]:+.2f}%)"
    }

    return verdict, result_df

def detect_round_amounts(df, amount_col, output_dir):
    """检测整数金额（圆整交易，可能是人为构造）"""
    if amount_col not in df.columns:
        return None

    round_amounts = df[df[amount_col] % 1000 == 0].copy()
    if len(round_amounts) > 0:
        round_pct = len(round_amounts) / len(df) * 100
        result = {
            '圆整交易(千元倍数)': len(round_amounts),
            '占比': f"{round_pct:.1f}%",
            '阈值': '如果>15%可能异常'
        }
        round_amounts.to_excel(os.path.join(output_dir, '疑点_圆整交易.xlsx'), index=False)
        return result
    return {'圆整交易(千元倍数)': 0, '占比': '0%'}

def detect_rounding_digits(df, amount_col, output_dir):
    """检测金额末位数字分布（正常应均匀分布，过多0或5可能异常）"""
    if amount_col not in df.columns:
        return None
    
    positive = df[df[amount_col] > 0].copy()
    positive['末位数字'] = (positive[amount_col] % 10).astype(int)
    
    digit_dist = positive['末位数字'].value_counts().sort_index()
    total = len(positive)
    
    # 末位为0的比例
    zero_pct = digit_dist.get(0, 0) / total * 100
    
    result_df = pd.DataFrame({
        '末位数字': list(range(0,10)),
        '频次': [digit_dist.get(d, 0) for d in range(0,10)],
        '占比(%)': [f"{digit_dist.get(d,0)/total*100:.1f}%" for d in range(0,10)]
    })
    result_df.to_excel(os.path.join(output_dir, '分析_金额末位分布.xlsx'), index=False)
    
    return {
        '末位0占比': f"{zero_pct:.1f}%",
        '判断': '⚠️ 末位0占比过高(>30%)，可能存在人为构造' if zero_pct > 30 else '✅ 末位分布正常'
    }

def main():
    parser = argparse.ArgumentParser(description='Benford财务造假检测')
    parser.add_argument('--input', '-i', required=True, help='财务数据.xlsx（凭证/流水/发票明细）')
    parser.add_argument('--amount-col', '-a', help='金额列名（自动检测）')
    parser.add_argument('--output', '-o', default='./output/', help='输出目录')
    parser.add_argument('--name', '-n', default='数据集', help='数据名称（用于报告标题）')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    try:
        df = pd.read_excel(args.input)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    print(f"📊 数据概览: {len(df)} 条记录, {len(df.columns)} 列")
    print(f"   列名: {list(df.columns)}")

    # 自动检测金额列
    amount_col = args.amount_col
    if not amount_col:
        for c in df.columns:
            if any(k in c for k in ['金额', '金额', '金额', '金额']):
                amount_col = c
                break
        if not amount_col:
            # 尝试找数值列
            for c in df.columns:
                if pd.api.types.is_numeric_dtype(df[c]) and df[c].abs().max() > 100:
                    amount_col = c
                    break
        if not amount_col:
            print("❌ 无法自动识别金额列，请用 --amount-col 指定")
            sys.exit(1)
        print(f"🔍 自动检测金额列: {amount_col}")

    print(f"\n{'='*50}")
    print(f"🔍 财务造假检测报告: {args.name}")
    print(f"{'='*50}")

    # 1. Benford定律分析
    print(f"\n--- 1. Benford首位数字分布 ---")
    verdict, result_df = benford_analysis(df, amount_col, args.output)
    if verdict:
        for k, v in verdict.items():
            print(f"   {k}: {v}")
    else:
        print(f"   ⚠️ {result_df}")

    # 2. 圆整交易检测
    print(f"\n--- 2. 圆整交易检测 ---")
    round_result = detect_round_amounts(df, amount_col, args.output)
    if round_result:
        for k, v in round_result.items():
            print(f"   {k}: {v}")

    # 3. 末位数字分布
    print(f"\n--- 3. 金额末位数字分布 ---")
    digit_result = detect_rounding_digits(df, amount_col, args.output)
    if digit_result:
        for k, v in digit_result.items():
            print(f"   {k}: {v}")

    # 输出汇总报告
    print(f"\n{'='*50}")
    print(f"📁 输出文件: {args.output}")
    for f in os.listdir(args.output):
        print(f"   📄 {f}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
