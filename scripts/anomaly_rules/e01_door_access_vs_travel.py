#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E01 — 门禁打卡×出差报销时空矛盾检测
════════════════════════════════════════
核查逻辑：报销声称某人于X日在A地出差 → 公司门禁系统显示X日该人在B地有完整进出记录 → 出差不成立

输入：
  差旅报销表 (travel.csv):  姓名 | 出差日期 | 出差地点 | 报销金额 | 事由
  门禁打卡记录 (access.csv): 姓名 | 日期 | 首次进门 | 末次出门

输出：
  anomalies_e01.csv: 时空矛盾的报销记录 + 对应的门禁证据

难度：⭐ | 数据要求：两张Excel/CSV表
"""

import csv
import sys
import os
from datetime import datetime
from collections import defaultdict

# Windows GBK 兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def load_csv(path):
    """加载CSV文件，自动识别编码"""
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
        try:
            with open(path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows, reader.fieldnames
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"无法解码文件 {path}")


def normalize_name(name):
    """标准化姓名（去空格、统一大小写）"""
    return name.strip().replace(' ', '').replace('\u3000', '')


def normalize_date(date_str):
    """标准化日期（处理各种格式）"""
    date_str = str(date_str).strip()
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y%m%d', '%m/%d/%Y'):
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return date_str  # 返回原文


def main(travel_path, access_path, output_path=None, min_amount=0):
    """
    Args:
        travel_path: 差旅报销表路径
        access_path: 门禁打卡记录路径
        output_path: 输出路径（默认 anomalies_e01.csv）
        min_amount: 最小报销金额过滤（默认0=不过滤）
    """
    print(f"E01 门禁×出差时空矛盾检测")
    print(f"═" * 50)

    # 加载数据
    print(f"[1/3] 加载差旅报销表: {travel_path}")
    travels, travel_cols = load_csv(travel_path)
    print(f"      共 {len(travels)} 条报销记录")

    print(f"[2/3] 加载门禁记录: {access_path}")
    accesses, access_cols = load_csv(access_path)
    print(f"      共 {len(accesses)} 条门禁记录")

    # 构建门禁索引: (姓名, 日期) → [门禁记录列表]
    access_index = defaultdict(list)
    for a in accesses:
        name = normalize_name(a.get('姓名', ''))
        date = normalize_date(a.get('日期', ''))
        if name and date:
            access_index[(name, date)].append(a)

    print(f"      去重后 {len(access_index)} 个 (姓名,日期) 组合")

    # 逐条比对
    print(f"[3/3] 执行时空矛盾检测...")
    anomalies = []
    checked = 0
    matched = 0

    for t in travels:
        name = normalize_name(t.get('姓名', ''))
        date = normalize_date(t.get('出差日期', '') or t.get('日期', ''))
        location = t.get('出差地点', '') or t.get('地点', '')
        amount_str = t.get('报销金额', '') or t.get('金额', '0')
        purpose = t.get('事由', '') or t.get('出差事由', '')

        if not name or not date:
            continue

        # 金额过滤
        try:
            amount = float(str(amount_str).replace(',', '').replace('元', ''))
        except ValueError:
            amount = 0
        if amount < min_amount:
            continue

        checked += 1

        # 查询该人该日在门禁系统是否有记录
        key = (name, date)
        if key in access_index:
            matched += 1
            for a in access_index[key]:
                first_in = a.get('首次进门', '') or a.get('进入时间', '') or a.get('进门', '')
                last_out = a.get('末次出门', '') or a.get('离开时间', '') or a.get('出门', '')
                anomalies.append({
                    '姓名': name,
                    '出差日期': date,
                    '出差地点': location,
                    '报销金额': amount,
                    '事由': purpose,
                    '门禁首次进门': first_in,
                    '门禁末次出门': last_out,
                    '矛盾说明': f'{name}于{date}声称在{location}出差，但门禁记录显示同日有完整进出记录',
                    '建议动作': '核实是否实际出差；如是委托他人打卡，查明原因'
                })

    # 输出
    if not output_path:
        output_path = 'anomalies_e01.csv'

    write_csv(output_path, anomalies)
    print(f"\n═" * 50)
    print(f"检测完成:")
    print(f"  共核查 {checked} 条报销（排除金额<{min_amount}的）")
    print(f"  发现时空矛盾 {len(anomalies)} 条（命中率 {len(anomalies)/checked*100:.1f}%）")
    print(f"  门禁记录命中 {matched} 条")
    print(f"  结果保存至: {output_path}")
    return anomalies


def write_csv(path, rows):
    if not rows:
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('无时空矛盾记录\n')
        return
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='E01 门禁打卡×出差报销时空矛盾检测')
    parser.add_argument('travel', help='差旅报销表CSV路径')
    parser.add_argument('access', help='门禁打卡记录CSV路径')
    parser.add_argument('-o', '--output', default='anomalies_e01.csv', help='输出文件路径')
    parser.add_argument('-m', '--min-amount', type=float, default=0, help='最小报销金额过滤')
    args = parser.parse_args()

    main(args.travel, args.access, args.output, args.min_amount)
