#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
anomaly_rules 批量执行器
═══════════════════════
一键运行所有可用规则，输出汇总报告。

用法：
  python run_all.py --data-dir 项目数据目录/
  python run_all.py --e01 --travel travel.csv --access access.csv   # 仅运行E01
  python run_all.py --list                                          # 列出所有可用规则
"""

import sys
import os
import csv
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 规则注册表
RULES = {
    'E01': {
        'name': '门禁打卡×出差报销时空矛盾',
        'module': 'e01_door_access_vs_travel',
        'function': 'main',
        'inputs': ['差旅报销表', '门禁记录'],
        'output': 'anomalies_e01.csv',
        'difficulty': '⭐',
        'coordinate': '时空',
        'audit_type': '预算执行',
    },
    'E05': {
        'name': '投标文件元数据同源检测',
        'module': 'e05_bid_metadata_homology',
        'function': 'main',
        'inputs': ['投标文件目录'],
        'output': 'anomalies_e05.csv',
        'difficulty': '⭐',
        'coordinate': '时空',
        'audit_type': '采购/招投标',
    },
    'E13': {
        'name': '进销存三向比对',
        'module': 'e13_purchase_sales_inventory',
        'function': 'main',
        'inputs': ['进货台账', '销售台账', '库存台账'],
        'output': 'anomalies_e13.csv',
        'difficulty': '⭐',
        'coordinate': '物理',
        'audit_type': '两新补贴',
    },
    'E15': {
        'name': '报销经办人×收款方工商关联',
        'module': 'e15_handler_payee_association',
        'function': 'main',
        'inputs': ['报销台账', '工商信息（可选）'],
        'output': 'anomalies_e15.csv',
        'difficulty': '⭐',
        'coordinate': '社会关系',
        'audit_type': '预算执行',
    },
    'E23': {
        'name': '年末突击支出节奏检测',
        'module': 'e23_year_end_spending',
        'function': 'main',
        'inputs': ['月度支出表'],
        'output': 'anomalies_e23.csv',
        'difficulty': '⭐',
        'coordinate': '时间序列',
        'audit_type': '预算执行',
    },
}


def list_rules():
    print(f"{'编号':<6} {'规则名称':<30} {'难度':<6} {'坐标系':<10} {'审计类型':<15}")
    print('─' * 70)
    for rid, rule in sorted(RULES.items()):
        print(f"{rid:<6} {rule['name']:<30} {rule['difficulty']:<6} {rule['coordinate']:<10} {rule['audit_type']:<15}")


def run_rule(rule_id, **kwargs):
    """运行单个规则"""
    if rule_id not in RULES:
        print(f"❌ 未知规则: {rule_id}")
        return None

    rule = RULES[rule_id]
    print(f"\n{'═' * 60}")
    print(f"▶ {rule_id} — {rule['name']}")
    print(f"  坐标系: {rule['coordinate']} | 审计类型: {rule['audit_type']} | 难度: {rule['difficulty']}")
    print(f"{'═' * 60}")

    try:
        module = __import__(rule['module'])
        func = getattr(module, rule['function'])

        # 根据不同规则的参数签名调用
        if rule_id == 'E01':
            result = func(
                kwargs.get('travel', 'travel.csv'),
                kwargs.get('access', 'access.csv'),
            )
        elif rule_id == 'E05':
            result = func(
                kwargs.get('dir', '.'),
            )
        elif rule_id == 'E13':
            result = func(
                kwargs.get('purchase', 'purchase.csv'),
                kwargs.get('sales', 'sales.csv'),
                kwargs.get('inventory', 'inventory.csv'),
            )
        elif rule_id == 'E15':
            result = func(
                kwargs.get('expense', 'expense.csv'),
                kwargs.get('biz_info', None),
            )
        elif rule_id == 'E23':
            result = func(
                kwargs.get('input', 'monthly_spending.csv'),
                year=kwargs.get('year'),
            )
        else:
            result = func(**kwargs)

        return {'rule_id': rule_id, 'name': rule['name'], 'result': result, 'status': 'ok'}

    except FileNotFoundError as e:
        print(f"❌ 数据文件缺失: {e}")
        return {'rule_id': rule_id, 'name': rule['name'], 'error': str(e), 'status': 'skipped'}
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {'rule_id': rule_id, 'name': rule['name'], 'error': str(e), 'status': 'failed'}


def generate_summary(results, output_dir='.'):
    """生成汇总报告"""
    summary_path = os.path.join(output_dir, 'anomaly_summary.json')
    md_path = os.path.join(output_dir, 'anomaly_summary.md')

    summary = {
        'execution_time': datetime.now().isoformat(),
        'rules': [],
    }

    for r in results:
        if r['status'] == 'ok':
            anomaly_count = len(r['result']) if isinstance(r['result'], list) else 0
            summary['rules'].append({
                'rule_id': r['rule_id'],
                'name': r['name'],
                'status': 'ok',
                'anomaly_count': anomaly_count,
            })
        else:
            summary['rules'].append({
                'rule_id': r['rule_id'],
                'name': r['name'],
                'status': r['status'],
                'error': r.get('error', ''),
            })

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 生成Markdown报告
    lines = [
        f'# 自动化筛查报告',
        f'',
        f'**执行时间**: {summary["execution_time"]}',
        f'',
        f'| 规则 | 状态 | 异常数 |',
        f'|:--|:--|--:|',
    ]
    total_anomalies = 0
    for r in summary['rules']:
        status_icon = {'ok': '✅', 'skipped': '⏭️', 'failed': '❌'}.get(r['status'], '❓')
        count = r.get('anomaly_count', 0)
        lines.append(f'| {r["name"]} | {status_icon} {r["status"]} | {count} |')
        total_anomalies += count
    lines.append(f'| **合计** | | **{total_anomalies}** |')

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n📊 汇总报告: {md_path}")
    print(f"📊 汇总JSON: {summary_path}")
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='融策审计异常筛查规则批量执行器')
    parser.add_argument('--list', action='store_true', help='列出所有可用规则')
    parser.add_argument('--data-dir', default='.', help='数据目录')
    parser.add_argument('--e01', action='store_true')
    parser.add_argument('--e05', action='store_true')
    parser.add_argument('--e13', action='store_true')
    parser.add_argument('--e15', action='store_true')
    parser.add_argument('--e23', action='store_true')
    parser.add_argument('--all', action='store_true', help='运行所有规则')
    parser.add_argument('--travel', default='travel.csv')
    parser.add_argument('--access', default='access.csv')
    parser.add_argument('--purchase', default='purchase.csv')
    parser.add_argument('--sales', default='sales.csv')
    parser.add_argument('--inventory', default='inventory.csv')
    parser.add_argument('--expense', default='expense.csv')
    parser.add_argument('--biz-info', default=None)
    parser.add_argument('--year', type=int, default=None)

    args = parser.parse_args()

    if args.list:
        list_rules()
        sys.exit(0)

    os.makedirs(args.data_dir, exist_ok=True)
    os.chdir(args.data_dir)

    # 确定要运行的规则
    selected = []
    if args.all:
        selected = list(RULES.keys())
    else:
        for rid in ['E01', 'E05', 'E13', 'E15', 'E23']:
            if getattr(args, rid.lower()):
                selected.append(rid)

    if not selected:
        print("请指定要运行的规则 (--e01/--e05/--e13/--e15/--e23 或 --all)")
        print("或 --list 查看所有规则")
        sys.exit(1)

    results = []
    for rid in selected:
        result = run_rule(rid, **vars(args))
        if result:
            results.append(result)

    if results:
        generate_summary(results, args.data_dir)
