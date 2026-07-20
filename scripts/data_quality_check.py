# -*- coding: utf-8 -*-
"""
数据质量检查器 v1.0 — Data Quality Gateway
==========================================
OCR后、Agent分析前的数据校验关卡。
三模型评审一致认定：脏数据直喂Agent = 13倍浪费。

检查项:
  1. 字段完整性 — 必填字段缺失率
  2. 金额合理性 — 发票金额不超过1亿、负数标记
  3. 日期合理性 — 未来日期、早于2000年的日期
  4. 重复检测 — 完全相同的行、相同发票号
  5. 关联一致性 — 同一合同号在不同表里的金额是否一致
  6. OCR置信度 — 标记低置信度记录

用法:
  python data_quality_check.py --project "XX项目"
  python data_quality_check.py --dir "path/to/.ocr_cache" --output report.json
"""
import os, sys, json, argparse, re, csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))


def check_invoices(csv_path):
    """检查发票CSV数据质量"""
    issues = []
    rows = _read_csv(csv_path)
    if not rows:
        return issues, {'total_rows': 0}

    stats = {'total_rows': len(rows), 'missing_fields': defaultdict(int), 'amount_issues': 0,
             'date_issues': 0, 'duplicates': 0, 'low_confidence': 0}

    seen = set()
    for i, row in enumerate(rows, 1):
        # 1. 必填字段检查
        for field in ['发票号码', '开票日期', '价税合计']:
            if not row.get(field, '').strip():
                stats['missing_fields'][field] += 1
                issues.append({'row': i, 'type': 'missing_field', 'field': field, 'severity': 'P1'})

        # 2. 金额合理性
        amount_str = row.get('价税合计', row.get('金额', '0'))
        try:
            amount = float(amount_str.replace(',', '').replace('元', '').replace(' ', ''))
            if amount <= 0:
                stats['amount_issues'] += 1
                issues.append({'row': i, 'type': 'negative_amount', 'value': amount, 'severity': 'P1'})
            elif amount > 100000000:  # 超过1亿
                stats['amount_issues'] += 1
                issues.append({'row': i, 'type': 'unreasonable_amount', 'value': amount,
                              'hint': '发票金额超过1亿元，请确认', 'severity': 'P2'})
        except:
            stats['amount_issues'] += 1
            issues.append({'row': i, 'type': 'invalid_amount', 'value': amount_str, 'severity': 'P1'})

        # 3. 日期合理性
        date_str = row.get('开票日期', '')
        if date_str:
            try:
                # 尝试多种日期格式
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日', '%Y%m%d']:
                    try:
                        d = datetime.strptime(date_str.strip(), fmt)
                        if d.year < 2000:
                            stats['date_issues'] += 1
                            issues.append({'row': i, 'type': 'old_date', 'value': date_str, 'severity': 'P2'})
                        if d > datetime.now():
                            stats['date_issues'] += 1
                            issues.append({'row': i, 'type': 'future_date', 'value': date_str, 'severity': 'P1'})
                        break
                    except:
                        continue
            except:
                pass

        # 4. 重复检测（基于发票号）
        invoice_no = row.get('发票号码', row.get('发票代码', ''))
        if invoice_no:
            if invoice_no in seen:
                stats['duplicates'] += 1
                issues.append({'row': i, 'type': 'duplicate_invoice', 'value': invoice_no, 'severity': 'P0'})
            seen.add(invoice_no)

        # 5. OCR置信度
        confidence = row.get('ocr_confidence', row.get('置信度', ''))
        if confidence:
            try:
                conf = float(confidence)
                if conf < 0.8:
                    stats['low_confidence'] += 1
                    issues.append({'row': i, 'type': 'low_ocr_confidence', 'value': conf,
                                  'hint': 'OCR置信度低于80%，建议人工核对', 'severity': 'P2'})
            except:
                pass

    return issues, stats


def check_contracts(csv_path):
    """检查合同CSV数据质量"""
    issues = []
    rows = _read_csv(csv_path)
    if not rows:
        return issues, {'total_rows': 0}

    stats = {'total_rows': len(rows), 'missing_fields': defaultdict(int),
             'amount_issues': 0, 'date_issues': 0}

    for i, row in enumerate(rows, 1):
        for field in ['合同编号', '合同金额']:
            if not row.get(field, '').strip():
                stats['missing_fields'][field] += 1
                issues.append({'row': i, 'type': 'missing_field', 'field': field, 'severity': 'P1'})

        # 金额检查
        amount_str = row.get('合同金额', '0')
        try:
            amount = float(amount_str.replace(',', '').replace('元', '').replace(' ', ''))
            if amount <= 0:
                stats['amount_issues'] += 1
                issues.append({'row': i, 'type': 'negative_amount', 'value': amount, 'severity': 'P1'})
        except:
            stats['amount_issues'] += 1
            issues.append({'row': i, 'type': 'invalid_amount', 'value': amount_str, 'severity': 'P1'})

    return issues, stats


def check_bank_transactions(csv_path):
    """检查银行交易CSV数据质量"""
    issues = []
    rows = _read_csv(csv_path)
    if not rows:
        return issues, {'total_rows': 0}

    stats = {'total_rows': len(rows), 'missing_fields': defaultdict(int),
             'amount_issues': 0, 'date_issues': 0}

    for i, row in enumerate(rows, 1):
        for field in ['交易日期', '交易金额']:
            if not row.get(field, '').strip():
                stats['missing_fields'][field] += 1

        amount_str = row.get('交易金额', '0')
        try:
            amount = float(amount_str.replace(',', '').replace(' ', ''))
            if amount == 0:
                stats['amount_issues'] += 1
                issues.append({'row': i, 'type': 'zero_amount', 'severity': 'P2'})
        except:
            stats['amount_issues'] += 1

    return issues, stats


def cross_table_check(invoices_path, contracts_path, bank_path):
    """跨表关联一致性检查"""
    cross_issues = []

    # 发票金额 vs 合同金额（如果有关联字段）
    invoices = _read_csv(invoices_path) if invoices_path else []
    contracts = _read_csv(contracts_path) if contracts_path else []

    if invoices and contracts:
        inv_amounts = {}
        for row in invoices:
            contract_ref = row.get('合同编号', row.get('关联合同', ''))
            if contract_ref:
                try:
                    amt = float(str(row.get('价税合计', '0')).replace(',', '').replace('元', ''))
                    if contract_ref not in inv_amounts:
                        inv_amounts[contract_ref] = 0
                    inv_amounts[contract_ref] += amt
                except:
                    pass

        for row in contracts:
            contract_no = row.get('合同编号', '')
            if contract_no in inv_amounts:
                try:
                    contract_amt = float(str(row.get('合同金额', '0')).replace(',', '').replace('元', ''))
                    inv_total = inv_amounts[contract_no]
                    diff_pct = abs(inv_total - contract_amt) / max(contract_amt, 1)
                    if diff_pct > 0.1:  # 差异超过10%
                        cross_issues.append({
                            'type': 'contract_invoice_mismatch',
                            'contract': contract_no,
                            'contract_amount': contract_amt,
                            'invoice_total': inv_total,
                            'diff_pct': f'{diff_pct:.1%}',
                            'severity': 'P0',
                            'hint': '合同金额与关联发票合计差异超过10%',
                        })
                except:
                    pass

    return cross_issues


def run_all_checks(project_dir):
    """对一个项目执行全部数据质量检查"""
    ocr_cache = Path(project_dir) / 'raw_data' / '.ocr_cache'
    if not ocr_cache.exists():
        return {'status': 'error', 'message': '.ocr_cache 不存在，请先运行OCR'}

    invoice_csv = ocr_cache / '发票' / 'invoices.csv'
    contract_csv = ocr_cache / '合同' / 'contracts.csv'
    bank_csv = ocr_cache / '银行' / 'bank_transactions.csv'

    results = {
        'checked_at': datetime.now(CST).isoformat(),
        'project': str(project_dir),
        'sections': {},
        'summary': {'total_issues': 0, 'P0': 0, 'P1': 0, 'P2': 0},
    }

    # 发票检查
    if invoice_csv.exists():
        inv_issues, inv_stats = check_invoices(str(invoice_csv))
        results['sections']['invoices'] = {'stats': dict(inv_stats), 'issues': inv_issues}
        for iss in inv_issues:
            results['summary']['total_issues'] += 1
            results['summary'][iss['severity']] += 1

    # 合同检查
    if contract_csv.exists():
        ctr_issues, ctr_stats = check_contracts(str(contract_csv))
        results['sections']['contracts'] = {'stats': dict(ctr_stats), 'issues': ctr_issues}
        for iss in ctr_issues:
            results['summary']['total_issues'] += 1
            results['summary'][iss['severity']] += 1

    # 银行交易检查
    if bank_csv.exists():
        bank_issues, bank_stats = check_bank_transactions(str(bank_csv))
        results['sections']['bank_transactions'] = {'stats': dict(bank_stats), 'issues': bank_issues}
        for iss in bank_issues:
            results['summary']['total_issues'] += 1
            results['summary'][iss['severity']] += 1

    # 跨表关联检查
    cross_issues = cross_table_check(
        str(invoice_csv) if invoice_csv.exists() else None,
        str(contract_csv) if contract_csv.exists() else None,
        str(bank_csv) if bank_csv.exists() else None,
    )
    results['sections']['cross_table'] = {'issues': cross_issues}
    for iss in cross_issues:
        results['summary']['total_issues'] += 1
        results['summary'][iss['severity']] += 1

    # 质量评级
    total = results['summary']['total_issues']
    p0 = results['summary']['P0']
    if p0 > 0:
        results['quality_grade'] = '🔴 不合格 — 存在P0级问题，数据不应进入Agent分析'
    elif total > 20:
        results['quality_grade'] = '🟡 需关注 — 问题较多，建议人工复核后再入Agent'
    elif total > 5:
        results['quality_grade'] = '🟢 合格 — 少量问题，可入Agent分析'
    else:
        results['quality_grade'] = '✅ 优秀 — 数据质量良好'

    return results


def _read_csv(path):
    """读取CSV，支持编码自动检测"""
    for enc in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']:
        try:
            with open(path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                return list(reader)
        except:
            continue
    return []


def main():
    parser = argparse.ArgumentParser(description='数据质量检查器 v1.0')
    parser.add_argument('--project', help='项目名称（在 audit-blackboard/projects/ 下）')
    parser.add_argument('--dir', help='直接指定.ocr_cache目录路径')
    args = parser.parse_args()

    if args.project:
        project_dir = Path(__file__).parent.parent / 'audit-blackboard' / 'projects' / args.project
    elif args.dir:
        project_dir = Path(args.dir).parent.parent  # .ocr_cache的父目录的父目录=项目根
    else:
        parser.print_help()
        return

    results = run_all_checks(str(project_dir))

    # 保存报告
    report_path = Path(project_dir) / 'outputs' / 'data_quality_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 终端输出摘要
    print(f"数据质量检查完成")
    print(f"  质量评级: {results['quality_grade']}")
    print(f"  总问题: {results['summary']['total_issues']}")
    print(f"    P0: {results['summary']['P0']}  P1: {results['summary']['P1']}  P2: {results['summary']['P2']}")
    print(f"  报告: {report_path}")

    if results['summary']['P0'] > 0:
        print("\n⚠️ 存在P0级问题！建议在进入Agent分析前修复。")
        for section, data in results['sections'].items():
            for iss in data.get('issues', []):
                if iss.get('severity') == 'P0':
                    print(f"  [{section}] {iss['type']}: {iss.get('hint', iss)}")


if __name__ == '__main__':
    main()
