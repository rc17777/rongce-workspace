#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E23 — 年末突击支出节奏检测
══════════════════════════
核查逻辑：全年支出中Q4（尤其是12月）占比显著高于历史水平 → 突击花钱/以拨代支/虚列支出

检测维度：
  1. Q4支出占比异常（>35%标记）
  2. 12月支出占比异常（>15%标记）
  3. 月度支出标准差异常（年度内分布不均）
  4. 与历史同期对比

输入：
  月度支出表 (monthly_spending.csv):
    格式1（按部门）: 部门 | 年份 | 1月 | 2月 | ... | 12月
    格式2（明细）:   日期 | 金额 | 部门 | 科目

输出：
  anomalies_e23.csv: 年末突击支出异常记录 + 支出节奏分布图数据

难度：⭐ | 数据要求：月度支出汇总表
"""

import csv
import sys
import json
from collections import defaultdict
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def load_csv(path):
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
        try:
            with open(path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                return list(reader), reader.fieldnames
        except (UnicodeDecodeError, UnicodeError):
            continue
    return [], []


def to_float(val):
    try:
        return float(str(val).replace(',', '').replace('元', '').replace('万', '').strip() or 0)
    except (ValueError, TypeError):
        return 0


def detect_format(headers):
    """自动识别输入格式"""
    months = ['1月', '2月', '3月', '4月', '5月', '6月',
              '7月', '8月', '9月', '10月', '11月', '12月']
    if all(m in headers for m in months):
        return 'wide'  # 宽表格式：部门 | 年份 | 1月 | 2月 | ... | 12月
    return 'long'  # 长表格式：日期 | 金额 | 部门


def analyze_department(name, monthly_data):
    """
    分析单个部门/科目的支出节奏
    Args:
        name: 部门/科目名称
        monthly_data: dict {月份(int): 金额}
    Returns:
        anomalies list + stats dict
    """
    if not monthly_data or sum(monthly_data.values()) <= 0:
        return [], None

    total = sum(monthly_data.values())

    # 按季度汇总
    q1 = sum(monthly_data.get(m, 0) for m in range(1, 4))
    q2 = sum(monthly_data.get(m, 0) for m in range(4, 7))
    q3 = sum(monthly_data.get(m, 0) for m in range(7, 10))
    q4 = sum(monthly_data.get(m, 0) for m in range(10, 13))

    dec = monthly_data.get(12, 0)
    avg_monthly = total / 12 if total > 0 else 0

    q4_ratio = q4 / total if total > 0 else 0
    dec_ratio = dec / total if total > 0 else 0

    # 计算标准差判断分布均匀度
    values = [monthly_data.get(m, 0) for m in range(1, 13)]
    mean = sum(values) / 12
    variance = sum((v - mean) ** 2 for v in values) / 12
    std = variance ** 0.5
    cv = std / mean if mean > 0 else 0  # 变异系数

    stats = {
        'name': name,
        'total': total,
        'avg_monthly': avg_monthly,
        'q1': q1, 'q1_pct': q1/total*100 if total > 0 else 0,
        'q2': q2, 'q2_pct': q2/total*100 if total > 0 else 0,
        'q3': q3, 'q3_pct': q3/total*100 if total > 0 else 0,
        'q4': q4, 'q4_pct': q4/total*100 if total > 0 else 0,
        'dec': dec, 'dec_pct': dec/total*100 if total > 0 else 0,
        'cv': cv,
    }

    anomalies = []
    # 阈值判断
    if q4_ratio > 0.35:
        level = '🔴高' if q4_ratio > 0.45 else '🟡中'
        anomalies.append({
            '部门/科目': name,
            '年度总支出': f'{total:,.0f}',
            'Q4支出': f'{q4:,.0f}',
            'Q4占比': f'{q4_ratio*100:.1f}%',
            '12月支出': f'{dec:,.0f}',
            '12月占比': f'{dec_ratio*100:.1f}%',
            '月度变异系数': f'{cv:.2f}',
            '风险等级': level,
            '异常类型': 'Q4集中',
            '关键信号': f'Q4支出占比{q4_ratio*100:.1f}%，远超正常水平（正常≤35%）',
            '建议动作': f'抽查Q4大额支出凭证，核实是否存在以拨代支或虚列支出',
        })

    if dec_ratio > 0.15:
        anomalies.append({
            '部门/科目': name,
            '年度总支出': f'{total:,.0f}',
            'Q4支出': f'{q4:,.0f}',
            'Q4占比': f'{q4_ratio*100:.1f}%',
            '12月支出': f'{dec:,.0f}',
            '12月占比': f'{dec_ratio*100:.1f}%',
            '月度变异系数': f'{cv:.2f}',
            '风险等级': '🔴高',
            '异常类型': '12月集中',
            '关键信号': f'仅12月就占全年支出{dec_ratio*100:.1f}%',
            '建议动作': f'逐笔核查12月大额支出：是否存在突击花钱、虚列支出或资金空转',
        })

    if cv > 0.8 and dec_ratio > 0.1:
        anomalies.append({
            '部门/科目': name,
            '年度总支出': f'{total:,.0f}',
            'Q4支出': f'{q4:,.0f}',
            'Q4占比': f'{q4_ratio*100:.1f}%',
            '12月支出': f'{dec:,.0f}',
            '12月占比': f'{dec_ratio*100:.1f}%',
            '月度变异系数': f'{cv:.2f}',
            '风险等级': '🟡中',
            '异常类型': '分布不均',
            '关键信号': f'月度支出极不均衡（变异系数{cv:.2f}），年末明显偏高',
            '建议动作': f'分析支出节奏异常原因：是预算下达晚还是有意集中支出',
        })

    return anomalies, stats


def main(input_path, output_path=None, year=None):
    """
    Args:
        input_path: 月度支出CSV
        output_path: 输出路径
        year: 指定年份（如输入含多年数据）
    """
    print(f"E23 年末突击支出节奏检测")
    print(f"═" * 50)

    print(f"[1/3] 加载月度支出数据: {input_path}")
    rows, headers = load_csv(input_path)
    print(f"      共 {len(rows)} 条记录")

    fmt = detect_format(headers)
    print(f"      识别格式: {'宽表（部门×月度）' if fmt == 'wide' else '长表（逐笔明细）'}")

    # --- 数据整理 ---
    departmental_monthly = defaultdict(lambda: defaultdict(float))

    if fmt == 'wide':
        # 宽表：部门 | 年份 | 1月 | 2月 | ... | 12月
        for r in rows:
            dept = r.get('部门', '') or r.get('单位', '') or r.get('科目', '') or '合计'
            yr = r.get('年份', '') or r.get('年度', '') or str(year or '')
            if year and str(yr) != str(year):
                continue
            for m in range(1, 13):
                col = f'{m}月'
                val = to_float(r.get(col, 0))
                if val > 0:
                    departmental_monthly[dept][m] += val
    else:
        # 长表：日期 | 金额 | 部门
        for r in rows:
            date_str = r.get('日期', '') or r.get('支出日期', '')
            amount = to_float(r.get('金额', '') or r.get('支出金额', '0'))
            dept = r.get('部门', '') or r.get('单位', '') or r.get('科目', '') or '合计'

            if not date_str:
                continue
            try:
                for fmt_str in ('%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y%m%d'):
                    try:
                        dt = datetime.strptime(str(date_str).strip(), fmt_str)
                        break
                    except ValueError:
                        continue
                else:
                    continue
                if year and dt.year != int(year):
                    continue
                departmental_monthly[dept][dt.month] += amount
            except:
                continue

    if not departmental_monthly:
        print("❌ 未能解析有效数据，请检查输入格式")
        return []

    # --- 逐部门分析 ---
    print(f"\n[2/3] 检测 {len(departmental_monthly)} 个部门/科目...")
    all_anomalies = []
    all_stats = []

    for dept in sorted(departmental_monthly.keys()):
        monthly = departmental_monthly[dept]
        total = sum(monthly.values())
        if total <= 0:
            continue
        dept_anomalies, stats = analyze_department(dept, monthly)
        all_anomalies.extend(dept_anomalies)
        if stats:
            all_stats.append(stats)
            q4_flag = '🔴' if stats['q4_pct'] > 35 else ('🟡' if stats['q4_pct'] > 30 else '  ')
            dec_flag = '🔴' if stats['dec_pct'] > 15 else ('🟡' if stats['dec_pct'] > 12 else '  ')
            print(f"  {q4_flag}{dec_flag} {dept}: 全年{total:>12,.0f} | Q4:{stats['q4_pct']:5.1f}% | 12月:{stats['dec_pct']:5.1f}% | CV:{stats['cv']:.2f}")

    # --- 输出 ---
    print(f"\n[3/3] 输出结果...")
    if not output_path:
        output_path = 'anomalies_e23.csv'

    if all_anomalies:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_anomalies[0].keys())
            writer.writeheader()
            writer.writerows(all_anomalies)
    else:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('未发现年末突击支出异常\n')

    # 输出汇总统计
    summary_path = output_path.replace('.csv', '_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)

    # 按风险等级汇总
    high = sum(1 for a in all_anomalies if '🔴' in a['风险等级'])
    mid = sum(1 for a in all_anomalies if '🟡' in a['风险等级'])

    print(f"\n═" * 50)
    print(f"检测完成:")
    print(f"  部门/科目: {len(departmental_monthly)}")
    print(f"  发现异常: {len(all_anomalies)} (🔴高{high} 🟡中{mid})")

    if all_stats:
        overall_q4 = sum(s['q4'] for s in all_stats) / sum(s['total'] for s in all_stats) * 100
        overall_dec = sum(s['dec'] for s in all_stats) / sum(s['total'] for s in all_stats) * 100
        print(f"  整体Q4占比: {overall_q4:.1f}%")
        print(f"  整体12月占比: {overall_dec:.1f}%")
        if overall_q4 > 35:
            print(f"  ⚠️ 整体Q4占比偏高，建议纳入审计重点")

    print(f"  异常清单: {output_path}")
    print(f"  汇总统计: {summary_path}")

    return all_anomalies


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='E23 年末突击支出节奏检测')
    parser.add_argument('input', help='月度支出CSV路径')
    parser.add_argument('-o', '--output', default='anomalies_e23.csv', help='输出路径')
    parser.add_argument('-y', '--year', type=int, default=None, help='指定年份')
    args = parser.parse_args()

    main(args.input, args.output, args.year)
