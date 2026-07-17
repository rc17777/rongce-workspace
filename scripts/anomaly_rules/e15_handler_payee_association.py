#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E15 — 报销经办人×收款方工商关联检测
══════════════════════════════════════
核查逻辑：长期向同一收款方付款 → 收款方工商法人/股东是否与经办人存在关联？

检测维度：
  1. 收款方集中度：单一收款方被同一经办人频繁使用
  2. 同名信号：经办人与收款方法人/股东同名
  3. 高频组合：特定(经办人,收款方)组合频次异常
  4. 一人付多方：同一经办人向多家不同收款方的大额支出

输入：
  报销台账 (expense.csv): 经办人 | 收款方名称 | 金额 | 日期 | 事由
  工商信息 (biz_info.csv, 可选): 企业名称 | 法人 | 股东 | 注册地址

输出：
  anomalies_e15.csv: 异常(经办人,收款方)组合 + 风险等级

难度：⭐ | 数据要求：报销台账（工商信息可选，无则仅做集中度分析）
"""

import csv
import sys
from collections import defaultdict

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
        return float(str(val).replace(',', '').replace('元', '').strip() or 0)
    except (ValueError, TypeError):
        return 0


def normalize_name(name):
    return str(name).strip().replace(' ', '').replace('\u3000', '')


def main(expense_path, biz_info_path=None, output_path=None, min_total=0, max_ratio=0.5):
    """
    Args:
        expense_path: 报销台账CSV
        biz_info_path: 工商信息CSV（可选）
        output_path: 输出路径
        min_total: 最小累计金额过滤
        max_ratio: 单一收款方占比阈值（超过此比例标记为高集中度）
    """
    print(f"E15 报销经办人×收款方工商关联检测")
    print(f"═" * 50)

    # --- 加载报销数据 ---
    print(f"[1/3] 加载报销台账: {expense_path}")
    expenses, _ = load_csv(expense_path)
    print(f"      共 {len(expenses)} 条报销记录")

    # --- 加载工商数据（可选）---
    biz_index = {}
    if biz_info_path and biz_info_path != 'none':
        print(f"[2/3] 加载工商信息: {biz_info_path}")
        biz_records, _ = load_csv(biz_info_path)
        for b in biz_records:
            name = normalize_name(b.get('企业名称', '') or b.get('名称', ''))
            if name:
                biz_index[name] = b
        print(f"      共 {len(biz_index)} 家企业")
    else:
        print(f"[2/3] 无工商信息，仅做报销台账集中度分析")

    # --- 分析 ---
    print(f"[3/3] 执行关联分析...")
    anomalies = []

    # 维度1: 按(经办人, 收款方)组合汇总
    handler_payee = defaultdict(lambda: {'count': 0, 'total': 0, 'items': []})
    handler_total = defaultdict(float)
    payee_total = defaultdict(float)

    for e in expenses:
        handler = normalize_name(e.get('经办人', '') or e.get('姓名', ''))
        payee = normalize_name(e.get('收款方名称', '') or e.get('收款方', '') or e.get('对方', ''))
        amount = to_float(e.get('金额', '') or e.get('报销金额', '0'))
        date = e.get('日期', '') or e.get('报销日期', '')
        purpose = e.get('事由', '') or e.get('用途', '') or e.get('摘要', '')

        if not handler or not payee:
            continue

        key = (handler, payee)
        handler_payee[key]['count'] += 1
        handler_payee[key]['total'] += amount
        handler_payee[key]['items'].append({'date': date, 'amount': amount, 'purpose': purpose})
        handler_total[handler] += amount
        payee_total[payee] += amount

    # 维度1: 收款方集中度
    print(f"\n  [维度1] 单一收款方集中度分析...")
    for handler, h_total in sorted(handler_total.items(), key=lambda x: -x[1]):
        if h_total < min_total:
            continue
        # 找出该经办人最大的收款方
        for (h, payee), info in handler_payee.items():
            if h != handler:
                continue
            ratio = info['total'] / h_total if h_total > 0 else 1
            if ratio > max_ratio and info['count'] >= 3:
                risk = '🔴高' if ratio > 0.8 else '🟡中'
                anomalies.append({
                    '检测维度': '收款方集中度',
                    '风险等级': risk,
                    '经办人': handler,
                    '收款方': payee,
                    '交易笔数': info['count'],
                    '累计金额': f"{info['total']:,.0f}",
                    '占该经办人总报销比': f"{ratio*100:.0f}%",
                    '关键信号': f'单一收款方占{handler}全部报销的{ratio*100:.0f}%',
                    '建议动作': f'核实{handler}与{payee}是否存在利益关联；查看工商关联',
                    '工商法人': biz_index.get(payee, {}).get('法人', ''),
                    '工商股东': biz_index.get(payee, {}).get('股东', ''),
                })
                print(f"    {risk} {handler} → {payee}: {info['count']}笔 {info['total']:,.0f}元 ({ratio*100:.0f}%)")

    # 维度2: 同名信号（经办人与收款方法人/股东同名）
    if biz_index:
        print(f"\n  [维度2] 同名信号检测...")
        for (handler, payee), info in handler_payee.items():
            biz = biz_index.get(payee)
            if not biz:
                continue
            legal_person = normalize_name(biz.get('法人', '') or biz.get('法定代表人', ''))
            shareholders = normalize_name(biz.get('股东', '') or biz.get('主要股东', ''))

            matched = []
            if legal_person and handler in legal_person:
                matched.append(f'与法人"{legal_person}"同名')
            if shareholders and handler in shareholders:
                matched.append(f'与股东"{shareholders}"同名')

            if matched:
                anomalies.append({
                    '检测维度': '同名关联',
                    '风险等级': '🔴高',
                    '经办人': handler,
                    '收款方': payee,
                    '交易笔数': info['count'],
                    '累计金额': f"{info['total']:,.0f}",
                    '占该经办人总报销比': f"{info['total']/handler_total[handler]*100:.0f}%" if handler_total[handler] > 0 else '',
                    '关键信号': '; '.join(matched),
                    '建议动作': '经办人与收款方疑似存在关联关系，需进一步核实',
                    '工商法人': legal_person,
                    '工商股东': shareholders,
                })
                print(f"    🔴 {handler} ↔ {payee}: {'; '.join(matched)}")

    # 维度3: 一人付多方（同一经办人向超过5家不同收款方的大额支付）
    print(f"\n  [维度3] 一人付多方检测...")
    handler_payee_count = defaultdict(set)
    for (h, p), info in handler_payee.items():
        if info['total'] > 10000:  # 只关注大额
            handler_payee_count[h].add(p)

    for handler, payees in handler_payee_count.items():
        if len(payees) >= 5 and handler_total[handler] > 50000:
            anomalies.append({
                '检测维度': '一人付多方',
                '风险等级': '🟡中',
                '经办人': handler,
                '收款方': '/'.join(list(payees)[:5]) + f'等{len(payees)}家',
                '交易笔数': sum(1 for (h,p),i in handler_payee.items() if h==handler),
                '累计金额': f"{handler_total[handler]:,.0f}",
                '占该经办人总报销比': 'N/A',
                '关键信号': f'向{len(payees)}家不同收款方支付超{handler_total[handler]:,.0f}元',
                '建议动作': '核实这些收款方之间是否存在关联；是否有分散支付规避审批',
                '工商法人': '',
                '工商股东': '',
            })
            print(f"    🟡 {handler}: 向{len(payees)}家收款方支付{handler_total[handler]:,.0f}元")

    # 输出
    if not output_path:
        output_path = 'anomalies_e15.csv'

    if anomalies:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=anomalies[0].keys())
            writer.writeheader()
            writer.writerows(anomalies)
    else:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('未发现经办人×收款方关联异常\n')

    # 汇总
    high = sum(1 for a in anomalies if a['风险等级'] == '🔴高')
    mid = sum(1 for a in anomalies if a['风险等级'] == '🟡中')
    print(f"\n═" * 50)
    print(f"检测完成:")
    print(f"  经办人总数: {len(handler_total)}")
    print(f"  收款方总数: {len(payee_total)}")
    print(f"  交易组合数: {len(handler_payee)}")
    print(f"  发现异常: {len(anomalies)} (🔴{high} 🟡{mid})")
    print(f"  结果保存至: {output_path}")
    return anomalies


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='E15 报销经办人×收款方工商关联检测')
    parser.add_argument('expense', help='报销台账CSV')
    parser.add_argument('-b', '--biz-info', default=None, help='工商信息CSV（可选，含法人/股东列）')
    parser.add_argument('-o', '--output', default='anomalies_e15.csv', help='输出路径')
    parser.add_argument('-m', '--min-total', type=float, default=10000, help='最小累计金额过滤')
    parser.add_argument('-r', '--max-ratio', type=float, default=0.5, help='单一收款方占比阈值')
    args = parser.parse_args()

    main(args.expense, args.biz_info, args.output, args.min_total, args.max_ratio)
