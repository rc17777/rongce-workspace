#!/usr/bin/env python3
"""
Benford 定律财务数据检验工具 — CSV/Excel 通用版
=================================================
适用场景：国企审计、政府采购审计、专项资金审计中的凭证/流水/发票金额异常检测。

检测方法：
  1. Benford 首位数字分布检验（卡方检验）
  2. 圆整交易检测（千元倍数）
  3. 金额末位数字分布检测

用法：
  python benford_test.py --input 凭证明细.csv --amount-col 金额
  python benford_test.py --input 采购明细.xlsx --amount-col 支付金额 --alpha 0.01
  python benford_test.py --input demo_ledger.csv  # 自动检测金额列

依赖：pip install pandas numpy scipy openpyxl
"""

import argparse
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import chisquare


# ──────────────────────────────────────────────
# 1. Benford 首位数字分布检验（核心方法）
# ──────────────────────────────────────────────

def benford_first_digit_test(amounts: pd.Series, alpha: float = 0.05):
    """
    对金额序列执行 Benford 首位数字分布检验。

    参数:
        amounts : 金额序列（自动过滤 <=0 的值）
        alpha   : 显著性水平，默认 0.05

    返回:
        dict: {
            '样本量', '卡方统计量', 'p值', '显著性水平',
            '结论', 'p值解释', '最大偏差数字', '分布表'
        }
    """
    # 过滤正数金额
    positive = amounts[amounts > 0].dropna()
    n = len(positive)

    if n < 100:
        return {
            '错误': f'样本量不足 ({n}<100)，Benford 检验不可靠，建议至少 100 条记录',
            '样本量': n,
        }

    # 提取首位数字（从 1 到 9 的整数部分）
    first_digits = positive.astype(str).str.lstrip('-0').str[0]
    first_digits = pd.to_numeric(first_digits, errors='coerce').dropna().astype(int)

    n_valid = len(first_digits)
    if n_valid < 100:
        return {
            '错误': f'有效样本量不足 ({n_valid}<100)',
            '样本量': n_valid,
        }

    # 实际分布
    actual_counts = first_digits.value_counts().sort_index()

    # Benford 理论概率
    benford_probs = [np.log10(1 + 1 / d) for d in range(1, 10)]

    # 理论频数
    expected_counts = [p * n_valid for p in benford_probs]

    # 卡方检验
    actual_vals = [actual_counts.get(d, 0) for d in range(1, 10)]
    chi2, p_value = chisquare(actual_vals, expected_counts)

    # 构建分布对比表
    distribution = []
    max_dev = 0
    max_dev_digit = None
    for d in range(1, 10):
        actual_pct = actual_counts.get(d, 0) / n_valid * 100
        benford_pct = benford_probs[d - 1] * 100
        deviation = actual_pct - benford_pct
        if abs(deviation) > abs(max_dev):
            max_dev = deviation
            max_dev_digit = d
        distribution.append({
            '首位数字': d,
            '实际频次': actual_counts.get(d, 0),
            '实际占比(%)': round(actual_pct, 2),
            'Benford理论(%)': round(benford_pct, 2),
            '偏差(%点)': round(deviation, 2),
        })

    is_significant = p_value < alpha

    return {
        '样本量': n_valid,
        '卡方统计量': round(chi2, 4),
        'p值': round(p_value, 6),
        '显著性水平': alpha,
        '结论': '⚠️ 可能存在人为操纵' if is_significant else '✅ 未发现明显异常',
        'p值解释': (
            f"p={p_value:.6f} < α={alpha}，统计显著，金额分布与 Benford 定律存在显著差异"
            if is_significant
            else f"p={p_value:.4f} ≥ α={alpha}，统计不显著，金额分布符合 Benford 定律"
        ),
        '最大偏差数字': f'数字 {max_dev_digit} (偏差 {max_dev:+.2f}%)',
        '分布表': distribution,
    }


# ──────────────────────────────────────────────
# 2. 圆整交易检测
# ──────────────────────────────────────────────

def detect_round_amounts(amounts: pd.Series, threshold_pct: float = 15.0):
    """
    检测千元倍数的圆整交易（可能是人为构造）。

    自然发生的交易很少恰好是整数，大量圆整交易往往意味着人为构造。

    返回:
        dict: {'圆整数': N, '占比': 'xx%', '阈值': '>15%可能异常', '明细': DataFrame}
    """
    positive = amounts[amounts > 0].dropna()
    round_mask = positive % 1000 == 0
    round_count = round_mask.sum()
    total = len(positive)
    pct = round_count / total * 100 if total > 0 else 0

    detail = pd.DataFrame({
        '金额': positive[round_mask].values,
        '是否异常': ['⚠️' if pct > threshold_pct else '✅'] * round_count,
    })

    return {
        '圆整交易数': int(round_count),
        '总交易数': total,
        '占比': f'{pct:.1f}%',
        '阈值': f'>{threshold_pct}%可能异常',
        '判断': '⚠️ 圆整交易占比过高' if pct > threshold_pct else '✅ 圆整交易占比正常',
        '明细': detail if round_count > 0 else None,
    }


# ──────────────────────────────────────────────
# 3. 末位数字分布检测
# ──────────────────────────────────────────────

def detect_last_digit_pattern(amounts: pd.Series):
    """
    检测金额末位数字分布。

    正常数据末位数字应接近均匀分布（~10%）。
    金额末位大量出现 0 或 5，属于人为构造痕迹。

    返回:
        dict: {'末位分布': dict, '末位0占比': 'xx%', '判断': str}
    """
    positive = amounts[amounts > 0].dropna()
    last_digits = (positive % 10).astype(int)
    total = len(positive)

    distribution = last_digits.value_counts().sort_index().to_dict()
    zero_pct = distribution.get(0, 0) / total * 100 if total > 0 else 0

    # 均匀分布检验也可以用卡方，但这里给简单判断
    if zero_pct > 30:
        verdict = f'⚠️ 末位 0 占比 {zero_pct:.1f}% > 30%，可能存在人为构造'
    elif zero_pct > 20:
        verdict = f'⚠️ 末位 0 占比 {zero_pct:.1f}% 偏高，建议进一步核查'
    else:
        verdict = f'✅ 末位分布正常 (末位0占比 {zero_pct:.1f}%)'

    detail = []
    for d in range(10):
        detail.append({
            '末位数字': d,
            '频次': distribution.get(d, 0),
            '占比(%)': round(distribution.get(d, 0) / total * 100, 1) if total > 0 else 0,
        })

    return {
        '末位0占比': f'{zero_pct:.1f}%',
        '判断': verdict,
        '明细': detail,
    }


# ──────────────────────────────────────────────
# 4. 综合报告生成
# ──────────────────────────────────────────────

def generate_report(data_name, amount_col, benford_result, round_result, digit_result):
    """生成 Markdown 格式的完整检测报告"""
    lines = []
    lines.append(f'# 🔍 财务数据 Benford 定律检测报告')
    lines.append(f'')
    lines.append(f'**数据名称**: {data_name}')
    lines.append(f'**金额列**: {amount_col}')
    lines.append(f'**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'')
    lines.append('---')
    lines.append('')

    # Section 1: Benford 检验
    lines.append('## 1. Benford 首位数字分布检验')
    lines.append('')
    if '错误' in benford_result:
        lines.append(f'⚠️ **{benford_result["错误"]}**')
    else:
        lines.append(f'| 指标 | 值 |')
        lines.append(f'|------|-----|')
        lines.append(f'| 样本量 | {benford_result["样本量"]} |')
        lines.append(f'| 卡方统计量 χ² | {benford_result["卡方统计量"]} |')
        lines.append(f'| p 值 | {benford_result["p值"]} |')
        lines.append(f'| 显著性水平 α | {benford_result["显著性水平"]} |')
        lines.append(f'| 结论 | **{benford_result["结论"]}** |')
        lines.append('')
        lines.append(f'**{benford_result["p值解释"]}**')
        lines.append('')
        lines.append(f'最大偏差: {benford_result["最大偏差数字"]}')
        lines.append('')

        # 分布对比表
        lines.append('### 首位数字分布对比')
        lines.append('')
        lines.append('| 首位数字 | 实际频次 | 实际占比(%) | Benford理论(%) | 偏差(%点) |')
        lines.append('|:--------:|:--------:|:----------:|:-------------:|:---------:|')
        for row in benford_result['分布表']:
            deviation = row['偏差(%点)']
            flag = ' ⚠️' if abs(deviation) > 5 else ''
            lines.append(
                f'| {row["首位数字"]} '
                f'| {row["实际频次"]} '
                f'| {row["实际占比(%)"]} '
                f'| {row["Benford理论(%)"]} '
                f'| {deviation}{flag} |'
            )

    lines.append('')
    lines.append('---')
    lines.append('')

    # Section 2: 圆整交易
    lines.append('## 2. 圆整交易检测（千元倍数）')
    lines.append('')
    if round_result['圆整交易数'] == 0:
        lines.append('✅ 未发现圆整交易')
    else:
        lines.append(f'| 指标 | 值 |')
        lines.append(f'|------|-----|')
        lines.append(f'| 圆整交易数 | {round_result["圆整交易数"]} |')
        lines.append(f'| 总交易数 | {round_result["总交易数"]} |')
        lines.append(f'| 占比 | {round_result["占比"]} |')
        lines.append(f'| 阈值 | {round_result["阈值"]} |')
        lines.append(f'| 判断 | **{round_result["判断"]}** |')

    lines.append('')
    lines.append('---')
    lines.append('')

    # Section 3: 末位分布
    lines.append('## 3. 金额末位数字分布')
    lines.append('')
    lines.append(f'**{digit_result["判断"]}**')
    lines.append('')
    lines.append('| 末位数字 | 频次 | 占比(%) |')
    lines.append('|:--------:|:----:|:-------:|')
    for row in digit_result['明细']:
        lines.append(f'| {row["末位数字"]} | {row["频次"]} | {row["占比(%)"]} |')

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('*报告由 benford_test.py 自动生成*')

    return '\n'.join(lines)


# ──────────────────────────────────────────────
# 5. 自动检测金额列
# ──────────────────────────────────────────────

def detect_amount_column(df: pd.DataFrame):
    """
    自动检测 DataFrame 中的金额列。
    优先级: 列名含"金额" > 数值列且最大值 > 100
    """
    for col in df.columns:
        if any(keyword in col for keyword in ['金额', '金额', '金额', '金额']):
            return col

    # 找数值列
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].abs().max() > 100 and df[col].abs().max() < 1e12:
                return col

    return None


# ──────────────────────────────────────────────
# 6. 主入口
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Benford 定律财务数据检验工具 — 支持 CSV/Excel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python benford_test.py --input 凭证明细.csv
  python benford_test.py --input 采购明细.xlsx --amount-col 支付金额
  python benford_test.py --input demo_ledger.csv --alpha 0.01
  python benford_test.py --input data.csv --output ./reports/
        """,
    )

    parser.add_argument('--input', '-i', required=True,
                       help='输入文件路径（支持 .csv / .xlsx / .xls）')
    parser.add_argument('--amount-col', '-a',
                       help='金额列名（不指定则自动检测）')
    parser.add_argument('--alpha', type=float, default=0.05,
                       help='显著性水平（默认 0.05）')
    parser.add_argument('--output', '-o', default='./output/',
                       help='报告输出目录（默认 ./output/）')
    parser.add_argument('--name', '-n', default=None,
                       help='数据名称（用于报告标题，默认取文件名）')
    parser.add_argument('--no-report', action='store_true',
                       help='不生成 Markdown 报告文件')

    args = parser.parse_args()

    # ── 读取数据 ──
    filepath = args.input
    if not os.path.exists(filepath):
        print(f'❌ 文件不存在: {filepath}')
        sys.exit(1)

    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.csv':
            df = pd.read_csv(filepath, encoding='utf-8')
        elif ext in ('.xlsx', '.xls'):
            df = pd.read_excel(filepath)
        else:
            print(f'❌ 不支持的文件格式: {ext}，请使用 .csv / .xlsx / .xls')
            sys.exit(1)
    except UnicodeDecodeError:
        # 尝试 GBK 编码
        df = pd.read_csv(filepath, encoding='gbk')
    except Exception as e:
        print(f'❌ 读取文件失败: {e}')
        sys.exit(1)

    print(f'📊 数据概览: {len(df)} 条记录, {len(df.columns)} 列')
    print(f'   列名: {list(df.columns)[:10]}', end='')
    if len(df.columns) > 10:
        print(f' ... 共 {len(df.columns)} 列')
    else:
        print()

    # ── 检测金额列 ──
    amount_col = args.amount_col
    if not amount_col:
        amount_col = detect_amount_column(df)
        if not amount_col:
            print('❌ 无法自动识别金额列，请用 --amount-col 指定')
            sys.exit(1)
        print(f'🔍 自动检测金额列: {amount_col}')
    else:
        if amount_col not in df.columns:
            print(f'❌ 列 "{amount_col}" 不存在，可用列: {list(df.columns)}')
            sys.exit(1)
        print(f'📌 金额列: {amount_col}')

    # ── 数据名称 ──
    data_name = args.name or os.path.splitext(os.path.basename(filepath))[0]

    # ── 创建输出目录 ──
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    print(f'\n{"=" * 60}')
    print(f'🔍 财务数据 Benford 定律检测报告: {data_name}')
    print(f'{"=" * 60}')

    # 1. Benford 检验
    print(f'\n{"─" * 40}')
    print('1. Benford 首位数字分布检验')
    print(f'{"─" * 40}')
    amounts = df[amount_col].astype(float)
    benford_result = benford_first_digit_test(amounts, alpha=args.alpha)

    if '错误' in benford_result:
        print(f'   ⚠️ {benford_result["错误"]}')
    else:
        for key in ['样本量', '卡方统计量', 'p值', '结论', '最大偏差数字']:
            print(f'   {key}: {benford_result[key]}')
        print(f'   → {benford_result["p值解释"]}')

        # 分布表
        print(f'\n   {"首位数字":<8} {"实际%":<10} {"Benford%":<12} {"偏差":<10}')
        print(f'   {"─" * 40}')
        for row in benford_result['分布表']:
            flag = ' ⚠️' if abs(row['偏差(%点)']) > 5 else ''
            print(f'   {row["首位数字"]:<8} {row["实际占比(%)"]:<10} {row["Benford理论(%)"]:<12} {row["偏差(%点)"]:+}{flag}')

        # 保存分布表
        dist_df = pd.DataFrame(benford_result['分布表'])
        dist_df.to_csv(os.path.join(output_dir, 'benford_分布表.csv'), index=False, encoding='utf-8-sig')

    # 2. 圆整交易
    print(f'\n{"─" * 40}')
    print('2. 圆整交易检测')
    print(f'{"─" * 40}')
    round_result = detect_round_amounts(amounts)
    for key in ['圆整交易数', '总交易数', '占比', '判断']:
        print(f'   {key}: {round_result[key]}')

    if round_result['明细'] is not None and len(round_result['明细']) > 0:
        round_detail = round_result['明细']
        if len(round_detail) <= 20:
            print(f'\n   圆整交易明细:')
            for _, row in round_detail.iterrows():
                print(f'   - ¥{row["金额"]:,.2f}')
        round_detail.to_csv(os.path.join(output_dir, '疑点_圆整交易.csv'), index=False, encoding='utf-8-sig')

    # 3. 末位分布
    print(f'\n{"─" * 40}')
    print('3. 金额末位数字分布')
    print(f'{"─" * 40}')
    digit_result = detect_last_digit_pattern(amounts)
    print(f'   {digit_result["判断"]}')

    # ── 生成报告 ──
    if not args.no_report:
        report = generate_report(data_name, amount_col, benford_result, round_result, digit_result)
        report_path = os.path.join(output_dir, '检测报告.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'\n📄 报告已保存: {os.path.abspath(report_path)}')

    print(f'\n{"=" * 60}')
    print(f'📁 输出文件: {os.path.abspath(output_dir)}')
    for f in sorted(os.listdir(output_dir)):
        print(f'   📄 {f}')
    print(f'{"=" * 60}')

    # 返回码 — p<0.05时非0退出，便于CI集成
    if '错误' not in benford_result and benford_result['p值'] < args.alpha:
        sys.exit(2)  # 异常退出码
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
