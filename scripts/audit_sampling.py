# -*- coding: utf-8 -*-
"""
审计抽样引擎 v1.0 — Audit Sampling Engine
=========================================
政府审计的基础方法论——风险导向抽样、分层抽样、金额单位抽样（MUS）。
三模型评审一致认定：审计抽样是政府审计的基本功，当前工作流完全缺失。

支持三种抽样方法:
  1. 分层抽样 (Stratified) — 按金额/风险分层，每层按比例抽取
  2. 金额单位抽样 (MUS)    — 大金额高概率被抽中（符合审计逻辑）
  3. 随机抽样 (Random)     — 纯随机，用于控制测试

置信度/误差参数内置中国政府审计常用值。

用法:
  python audit_sampling.py --input "invoices.csv" --method stratified --amount-col "价税合计"
  python audit_sampling.py --input "contracts.csv" --method mus --amount-col "合同金额" --confidence 95
  python audit_sampling.py --input "journal.csv" --method random --sample-size 50
"""
import sys, json, argparse, random, math, csv
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


def stratified_sampling(data, amount_col, total_samples=60,
                         strata_rules=None, risk_col=None):
    """
    分层抽样：先分层，再每层按比例分配样本量。

    默认分层规则（金额）:
      - 大额层: 金额 > 均值×3 → 50%样本
      - 中额层: 金额 > 均值 → 30%样本
      - 小额层: 其余 → 20%样本
    """
    if not data:
        return {'error': '数据为空'}

    amounts = [_parse_amount(row.get(amount_col, 0)) for row in data]
    valid_amounts = [a for a in amounts if a > 0]
    if not valid_amounts:
        return {'error': '无有效金额数据'}

    mean_amt = sum(valid_amounts) / len(valid_amounts)

    # 默认分层
    if strata_rules is None:
        strata_rules = {
            '大额层': {'condition': lambda a: a > mean_amt * 3, 'sample_pct': 0.50},
            '中额层': {'condition': lambda a: a > mean_amt, 'sample_pct': 0.30},
            '小额层': {'condition': lambda a: True, 'sample_pct': 0.20},
        }

    # 分层
    strata = defaultdict(list)
    for i, row in enumerate(data):
        amt = amounts[i]
        for sname, srule in strata_rules.items():
            if srule['condition'](amt):
                strata[sname].append((i, amt, row))
                break

    # 每层抽样
    results = []
    strata_details = {}
    for sname, items in strata.items():
        n_items = len(items)
        n_samples = max(1, int(total_samples * strata_rules[sname]['sample_pct']))
        n_samples = min(n_samples, n_items)

        # 在该层内按金额加权随机抽取
        if n_items > 0:
            sample_weights = [max(1, items[j][1]) for j in range(n_items)]
            sampled_indices = _weighted_sample(range(n_items), n_samples, sample_weights)

            for idx in sampled_indices:
                orig_idx, amt, row = items[idx]
                results.append({
                    'row_index': orig_idx,
                    'stratum': sname,
                    'amount': amt,
                    'data': {k: v for k, v in row.items() if k in ('发票号码', '合同编号', '交易日期', '摘要', '价税合计', '合同金额', '交易金额', '供应商', '对方户名')},
                })

            strata_details[sname] = {
                'total_items': n_items,
                'sampled': n_samples,
                'rate': f'{n_samples/n_items:.1%}',
                'amount_range': f'{min(i[1] for i in items):,.0f} ~ {max(i[1] for i in items):,.0f}',
                'total_amount': sum(i[1] for i in items),
            }

    return {
        'method': 'stratified',
        'total_population': len(data),
        'total_sampled': len(results),
        'sampling_rate': f'{len(results)/max(len(data),1):.1%}',
        'strata': strata_details,
        'samples': results,
    }


def mus_sampling(data, amount_col, confidence=95, materiality_pct=0.05,
                 expected_error_pct=0.01):
    """
    金额单位抽样 (Monetary Unit Sampling)：
    金额越大的项目被抽中的概率越高——最符合审计逻辑。
    """
    if not data:
        return {'error': '数据为空'}

    amounts = [_parse_amount(row.get(amount_col, 0)) for row in data]
    total_amount = sum(amounts)
    if total_amount <= 0:
        return {'error': '总金额为零或负数'}

    # MUS样本量计算（基于置信度和可容忍误差）
    # 简化版：95%置信度 → 取系数3.0
    confidence_factors = {90: 2.3, 95: 3.0, 99: 4.6}
    cf = confidence_factors.get(confidence, 3.0)

    # 样本量 = 可靠性系数 / (可容忍误差率)
    sample_size = int(cf / materiality_pct)
    sample_size = min(sample_size, len(data))

    # 按金额累积分布抽样
    cumsum = 0
    cumsums = []
    for amt in amounts:
        cumsum += amt
        cumsums.append(cumsum)

    # 等距抽样
    interval = total_amount / sample_size
    start = random.uniform(0, interval)
    selected = set()
    for s in range(sample_size):
        target = start + s * interval
        # 二分查找
        lo, hi = 0, len(cumsums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cumsums[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        selected.add(lo)

    results = []
    for idx in sorted(selected):
        results.append({
            'row_index': idx,
            'amount': amounts[idx],
            'weight': f'{amounts[idx]/total_amount:.2%}',
            'data': {k: v for k, v in data[idx].items() if k in ('发票号码', '合同编号', '摘要', '价税合计', '合同金额', '供应商', '对方户名')},
        })

    return {
        'method': 'MUS',
        'confidence': f'{confidence}%',
        'materiality': f'{materiality_pct:.1%}',
        'total_population': len(data),
        'total_amount': total_amount,
        'interval': f'{interval:,.0f}',
        'total_sampled': len(results),
        'coverage': f'{sum(r["amount"] for r in results)/total_amount:.1%}',
        'samples': results,
    }


def random_sampling(data, sample_size=50, seed=None):
    """简单随机抽样"""
    if seed:
        random.seed(seed)

    n = min(sample_size, len(data))
    indices = random.sample(range(len(data)), n)

    results = []
    for idx in sorted(indices):
        results.append({
            'row_index': idx,
            'data': data[idx],
        })

    return {
        'method': 'random',
        'total_population': len(data),
        'total_sampled': len(results),
        'sampling_rate': f'{len(results)/max(len(data),1):.1%}',
        'seed': seed,
        'samples': results,
    }


def _parse_amount(val):
    """解析金额字符串/数字"""
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace(',', '').replace('元', '').replace('万', '0000').replace(' ', ''))
    except:
        return 0.0


def _weighted_sample(population, k, weights):
    """加权不放回抽样"""
    population = list(population)
    weights = list(weights)

    if k >= len(population):
        return list(range(len(population)))

    selected = []
    remaining = list(range(len(population)))
    remaining_weights = weights[:]

    for _ in range(k):
        total_w = sum(remaining_weights)
        if total_w <= 0:
            break
        r = random.uniform(0, total_w)
        cumsum = 0
        for i, idx in enumerate(remaining):
            cumsum += remaining_weights[i]
            if cumsum >= r:
                selected.append(idx)
                remaining.pop(i)
                remaining_weights.pop(i)
                break

    return selected


def _read_csv(path):
    for enc in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return list(csv.DictReader(f))
        except:
            continue
    return []


def main():
    parser = argparse.ArgumentParser(description='审计抽样引擎 v1.0')
    parser.add_argument('--input', required=True, help='输入CSV文件路径')
    parser.add_argument('--method', required=True, choices=['stratified', 'mus', 'random'],
                       help='抽样方法: stratified(分层) / mus(金额单位) / random(随机)')
    parser.add_argument('--amount-col', default='金额', help='金额列名（stratified/mus方法需要）')
    parser.add_argument('--sample-size', type=int, default=60, help='目标样本量（stratified/random方法）')
    parser.add_argument('--confidence', type=int, default=95, choices=[90, 95, 99],
                       help='置信度%（MUS方法）')
    parser.add_argument('--materiality', type=float, default=0.05, help='可容忍误差率（MUS方法）')
    parser.add_argument('--output', help='输出JSON文件路径')
    parser.add_argument('--seed', type=int, help='随机种子（random方法）')

    args = parser.parse_args()

    data = _read_csv(args.input)
    if not data:
        print(f'错误: 无法读取 {args.input} 或无数据')
        return

    if args.method == 'stratified':
        result = stratified_sampling(data, args.amount_col, args.sample_size)
    elif args.method == 'mus':
        result = mus_sampling(data, args.amount_col, args.confidence, args.materiality)
    elif args.method == 'random':
        result = random_sampling(data, args.sample_size, args.seed)

    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'抽样结果已保存: {args.output}')

    # 终端摘要
    print(f"\n{'='*50}")
    print(f"  审计抽样报告")
    print(f"{'='*50}")
    print(f"  方法: {result['method']}")
    print(f"  总体: {result['total_population']} 条")
    print(f"  抽样: {result['total_sampled']} 条")
    print(f"  抽样率: {result.get('sampling_rate', result.get('coverage', 'N/A'))}")
    print(f"{'='*50}")

    if result['method'] == 'stratified':
        print(f"\n  分层详情:")
        for sname, sdetail in result['strata'].items():
            print(f"    {sname}: {sdetail['total_items']}条 → 抽{sdetail['sampled']}条 ({sdetail['rate']})")

    print(f"\n  前5条抽样结果:")
    for s in result['samples'][:5]:
        print(f"    #{s['row_index']} | {s.get('amount', 'N/A')} | {s.get('data', {})}")


if __name__ == '__main__':
    main()
