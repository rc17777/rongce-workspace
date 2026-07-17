#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E13 — 进销存三向比对
════════════════════════
核查逻辑：商家声称销售X台补贴商品 → 期初库存+进货−销售 ≠ 期末库存 → 虚构销售套补

计算公式：期初库存量 + 进货量 − 补贴销售量 = 理论期末库存量
         理论期末库存量 vs 实际盘点期末库存量 → 偏差 = 套补信号

输入：
  进货台账 (purchase.csv):  商品编码 | 商品名称 | 进货数量 | 进货日期 | 供应商
  销售台账 (sales.csv):     商品编码 | 商品名称 | 销售数量 | 销售日期 | 消费者 | 补贴金额
  库存台账 (inventory.csv): 商品编码 | 商品名称 | 期初库存 | 期末库存(盘点) | 盘点日期

输出：
  anomalies_e13.csv: 进销存不匹配的商品清单，含偏差量和建议

难度：⭐ | 数据要求：三张台账表
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
    raise ValueError(f"无法解码文件 {path}")


def to_float(val):
    """安全转float"""
    try:
        return float(str(val).replace(',', '').replace('台', '').replace('个', '').replace('件', '').strip() or 0)
    except (ValueError, TypeError):
        return 0


def normalize_code(code):
    """标准化商品编码"""
    return str(code).strip().upper().replace(' ', '')


def main(purchase_path, sales_path, inventory_path, output_path=None, tolerance=0.01):
    """
    Args:
        purchase_path: 进货台账CSV
        sales_path: 销售台账CSV
        inventory_path: 库存台账CSV（含期初期末）
        output_path: 输出路径
        tolerance: 允许偏差比例（默认1%）
    """
    print(f"E13 进销存三向比对")
    print(f"═" * 50)

    # 加载数据
    print(f"[1/4] 加载进货台账: {purchase_path}")
    purchases, _ = load_csv(purchase_path)
    print(f"      共 {len(purchases)} 条进货记录")

    print(f"[2/4] 加载销售台账: {sales_path}")
    sales, _ = load_csv(sales_path)
    print(f"      共 {len(sales)} 条销售记录")

    print(f"[3/4] 加载库存台账: {inventory_path}")
    inventories, _ = load_csv(inventory_path)
    print(f"      共 {len(inventories)} 条库存记录")

    # 按商品编码汇总
    print(f"[4/4] 按商品编码汇总并比对...")

    # --- 汇总进货量 ---
    purchase_qty = defaultdict(float)
    for p in purchases:
        code = normalize_code(p.get('商品编码', '') or p.get('编码', ''))
        qty = to_float(p.get('进货数量', '') or p.get('数量', ''))
        if code:
            purchase_qty[code] += qty

    # --- 汇总销售量 ---
    sales_qty = defaultdict(float)
    for s in sales:
        code = normalize_code(s.get('商品编码', '') or s.get('编码', ''))
        qty = to_float(s.get('销售数量', '') or s.get('数量', ''))
        if code:
            sales_qty[code] += qty

    # --- 库存数据 ---
    inventory_start = {}
    inventory_end = {}
    product_names = {}
    for inv in inventories:
        code = normalize_code(inv.get('商品编码', '') or inv.get('编码', ''))
        if not code:
            continue
        start_qty = to_float(inv.get('期初库存', '0'))
        end_qty = to_float(inv.get('期末库存', '') or inv.get('期末库存(盘点)', '0'))
        name = inv.get('商品名称', '') or inv.get('名称', '')
        inventory_start[code] = start_qty
        inventory_end[code] = end_qty
        product_names[code] = name

    # --- 三向比对 ---
    all_codes = set(purchase_qty.keys()) | set(sales_qty.keys()) | set(inventory_start.keys())
    anomalies = []

    for code in sorted(all_codes):
        name = product_names.get(code, code)
        pur = purchase_qty.get(code, 0)
        sal = sales_qty.get(code, 0)
        start_inv = inventory_start.get(code, 0)
        end_inv = inventory_end.get(code, 0)

        theoretical_end = start_inv + pur - sal
        delta = theoretical_end - end_inv

        # 判断偏差
        if end_inv > 0:
            deviation_pct = abs(delta) / max(end_inv, 1) * 100
        elif theoretical_end > 0:
            deviation_pct = abs(delta) / max(theoretical_end, 1) * 100
        else:
            deviation_pct = 0

        status = '✓'
        suggestion = ''
        if deviation_pct > tolerance and abs(delta) > 0.5:
            if delta > 0:
                status = f'🔴 理论库存 > 实际库存（差+{delta:.0f}，偏差{deviation_pct:.1f}%）'
                suggestion = f'疑似虚构销售{delta:.0f}件套取补贴：理论库存比实际多{delta:.0f}件。核实是否虚假申报销售。'
            else:
                status = f'🟡 理论库存 < 实际库存（差{delta:.0f}，偏差{deviation_pct:.1f}%）'
                suggestion = f'实际库存比理论多{abs(delta):.0f}件。可能原因：①未入账进货；②少报销售。需核实。'
            anomalies.append({
                '商品编码': code,
                '商品名称': name,
                '期初库存': start_inv,
                '进货总量': pur,
                '销售总量': sal,
                '理论期末库存': theoretical_end,
                '实际期末库存': end_inv,
                '偏差量': f'{delta:+.1f}',
                '偏差率': f'{deviation_pct:.1f}%',
                '状态': status,
                '建议动作': suggestion
            })
            print(f"  {name}({code}): 期初{start_inv} + 进{pur} - 销{sal} = 理论{theoretical_end} vs 实际{end_inv} → 差{delta:+.1f}")

    # 输出
    if not output_path:
        output_path = 'anomalies_e13.csv'

    if anomalies:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=anomalies[0].keys())
            writer.writeheader()
            writer.writerows(anomalies)
    else:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('进销存三向比对全部通过，未发现偏差\n')

    # 汇总
    total_codes = len(all_codes)
    matched = total_codes - len(anomalies)
    print(f"\n═" * 50)
    print(f"检测完成:")
    print(f"  商品品类: {total_codes}")
    print(f"  三向吻合: {matched}")
    print(f"  存在偏差: {len(anomalies)}")
    print(f"  结果保存至: {output_path}")

    # 商家级汇总
    print(f"\n💰 金额影响估算（如销售台账含补贴金额列）:")
    total_subsidy_risk = 0
    for a in anomalies:
        code = a['商品编码']
        # 查找该编码的补贴金额
        code_subsidy = 0
        for s in sales:
            if normalize_code(s.get('商品编码', '') or s.get('编码', '')) == code:
                sub = to_float(s.get('补贴金额', '0'))
                code_subsidy += sub
        if code_subsidy > 0:
            a['涉及补贴金额'] = f'{code_subsidy:,.0f}'
            total_subsidy_risk += code_subsidy * (abs(float(a['偏差量'])) / max(float(str(a['销售总量'])), 1))
            print(f"  {a['商品名称']}: 涉及补贴{code_subsidy:,.0f}元")

    return anomalies


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='E13 进销存三向比对')
    parser.add_argument('purchase', help='进货台账CSV')
    parser.add_argument('sales', help='销售台账CSV')
    parser.add_argument('inventory', help='库存台账CSV（含期初期末）')
    parser.add_argument('-o', '--output', default='anomalies_e13.csv', help='输出路径')
    parser.add_argument('-t', '--tolerance', type=float, default=0.01, help='允许偏差比例 (默认0.01=1%%)')
    args = parser.parse_args()

    main(args.purchase, args.sales, args.inventory, args.output, args.tolerance)
