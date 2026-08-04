# -*- coding: utf-8 -*-
"""
审盾发现校验器 (Finding Validator) v1.0
按可解释性三级标准校验审计发现，输出达标率报告。

用法：
    python finding_validator.py --file findings.json
    python finding_validator.py --dir findings/ --threshold
    python finding_validator.py --file findings.json --strict
"""
import sys, os, json, argparse, re, datetime
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

# ═══════════════════════════════════════════════════
# Level 1: 规则可解释 (必须100%)
# ═══════════════════════════════════════════════════

def validate_l1(finding):
    """
    检查 Level 1 可解释性：
    - rule_id 必须存在且非空
    - rule_name 必须存在且非空
    - trigger_condition 必须存在且有实质内容（至少10个字符，含数值对比）
    """
    l1 = finding.get('explainability_l1', {})
    issues = []

    rule_id = l1.get('rule_id', '').strip()
    if not rule_id:
        issues.append('L1_FAIL: rule_id 缺失或为空')

    rule_name = l1.get('rule_name', '').strip()
    if not rule_name:
        issues.append('L1_FAIL: rule_name 缺失或为空')

    trigger = l1.get('trigger_condition', '').strip()
    if not trigger:
        issues.append('L1_FAIL: trigger_condition 缺失或为空')
    elif len(trigger) < 10:
        issues.append(f'L1_WARN: trigger_condition 过短 ({len(trigger)}字符)，可能不够具体')

    passed = len([i for i in issues if 'L1_FAIL' in i]) == 0
    return {
        'level': 1,
        'passed': passed,
        'issues': issues,
        'score': 1.0 if passed else 0.0
    }


# ═══════════════════════════════════════════════════
# Level 2: 证据可溯源 (文件100%/页≥90%/行≥70%)
# ═══════════════════════════════════════════════════

def validate_l2(finding):
    """
    检查 Level 2 可解释性：
    - file_source: 100% 必须
    - page: ≥90%
    - line_ref: ≥70%
    """
    l2 = finding.get('explainability_l2', {})
    issues = []
    checks = {
        'file_source': False,
        'page': False,
        'line_ref': False
    }

    file_src = l2.get('file_source', '').strip()
    if file_src:
        checks['file_source'] = True
    else:
        issues.append('L2_FAIL: file_source 缺失 — 文件级溯源必须100%覆盖')

    page = l2.get('page')
    if page is not None and str(page).strip():
        checks['page'] = True
    else:
        issues.append('L2_GAP: page 缺失 — 页级溯源目标≥90%')

    line_ref = l2.get('line_ref', '').strip()
    if line_ref:
        checks['line_ref'] = True
    else:
        issues.append('L2_GAP: line_ref 缺失 — 行级溯源目标≥70%')

    raw_val = l2.get('raw_value', '').strip()
    if not raw_val:
        issues.append('L2_WARN: raw_value 缺失')

    data_hash = l2.get('data_hash', '').strip()
    if not data_hash:
        issues.append('L2_WARN: data_hash 缺失（建议添加防篡改）')

    passed = checks['file_source']
    return {
        'level': 2,
        'passed': passed,
        'checks': checks,
        'issues': issues,
        'score': _l2_score(checks)
    }


def _l2_score(checks):
    """加权计算 L2 分数: file_source 占 40%, page 占 35%, line_ref 占 25%"""
    score = 0.0
    if checks['file_source']:
        score += 0.4
    if checks['page']:
        score += 0.35
    if checks['line_ref']:
        score += 0.25
    return score


# ═══════════════════════════════════════════════════
# Level 3: 因果可解释 (目标≥60%)
# ═══════════════════════════════════════════════════

def validate_l3(finding):
    """
    检查 Level 3 可解释性：
    - causal_chain: 完整风险逻辑链
    - risk_type: 风险类型
    - suggestion: 核查建议
    """
    l3 = finding.get('explainability_l3', {})
    issues = []
    checks = {
        'causal_chain': False,
        'risk_type': False,
        'suggestion': False,
        'related_cases': False
    }

    chain = l3.get('causal_chain', '').strip()
    if chain and len(chain) >= 20:
        checks['causal_chain'] = True
    else:
        issues.append('L3_GAP: causal_chain 缺失或过短 — 风险逻辑链目标≥60%')

    risk_type = l3.get('risk_type', '').strip()
    if risk_type:
        checks['risk_type'] = True
    else:
        issues.append('L3_GAP: risk_type 缺失')

    suggestion = l3.get('suggestion', '').strip()
    if suggestion and len(suggestion) >= 10:
        checks['suggestion'] = True
    else:
        issues.append('L3_GAP: suggestion 缺失或过短')

    related = l3.get('related_cases', [])
    if related and len(related) > 0:
        checks['related_cases'] = True

    impact = l3.get('impact_estimate', '').strip()
    if not impact:
        issues.append('L3_WARN: impact_estimate 缺失')

    passed = checks['causal_chain']
    score = sum([0.4, 0.25, 0.25, 0.1][i] for i, k in enumerate(checks) if checks[k])
    return {
        'level': 3,
        'passed': passed,
        'checks': checks,
        'issues': issues,
        'score': round(score, 2)
    }


# ═══════════════════════════════════════════════════
# 综合校验
# ═══════════════════════════════════════════════════

def validate_finding(finding):
    """校验单条发现的三级可解释性"""
    fid = finding.get('finding_id', 'unknown')
    l1 = validate_l1(finding)
    l2 = validate_l2(finding)
    l3 = validate_l3(finding)

    overall_score = round(l1['score'] * 0.3 + l2['score'] * 0.35 + l3['score'] * 0.35, 2)
    all_pass = l1['passed'] and l2['passed'] and l3['passed']

    return {
        'finding_id': fid,
        'dimension': finding.get('dimension', 'unknown'),
        'severity': finding.get('severity', 'unknown'),
        'source_model': finding.get('source_model', 'unknown'),
        'l1': l1,
        'l2': l2,
        'l3': l3,
        'overall_score': overall_score,
        'overall_pass': all_pass,
        'explainability_grade': _grade(overall_score)
    }


def _grade(score):
    if score >= 0.9:
        return 'A (完整可解释)'
    elif score >= 0.7:
        return 'B (基本可解释)'
    elif score >= 0.5:
        return 'C (部分可解释)'
    else:
        return 'D (不可解释，不能作为审计证据)'


def validate_batch(findings, threshold=True):
    """
    批量校验 + 达标率报告。
    threshold=True 时按一期验收标准判定是否通过。
    """
    results = []
    for f in findings:
        results.append(validate_finding(f))

    total = len(results)
    if total == 0:
        return {'error': '没有发现需要校验', 'results': []}

    # 各级达标统计
    l1_pass = sum(1 for r in results if r['l1']['passed'])
    l2_pass = sum(1 for r in results if r['l2']['passed'])
    l3_pass = sum(1 for r in results if r['l3']['passed'])
    overall_pass = sum(1 for r in results if r['overall_pass'])

    # L2 子指标
    l2_file = sum(1 for r in results if r['l2']['checks']['file_source'])
    l2_page = sum(1 for r in results if r['l2']['checks']['page'])
    l2_line = sum(1 for r in results if r['l2']['checks']['line_ref'])

    avg_score = round(sum(r['overall_score'] for r in results) / total, 2)

    report = {
        'total_findings': total,
        'timestamp': datetime.datetime.now().isoformat(),
        'summary': {
            'L1_规则可解释': f'{l1_pass}/{total} ({l1_pass/total*100:.1f}%)',
            'L2_证据可溯源': f'{l2_pass}/{total} ({l2_pass/total*100:.1f}%)',
            'L3_因果可解释': f'{l3_pass}/{total} ({l3_pass/total*100:.1f}%)',
            'overall_pass': f'{overall_pass}/{total} ({overall_pass/total*100:.1f}%)',
            'average_score': avg_score
        },
        'l2_detail': {
            'file_source': f'{l2_file}/{total} ({l2_file/total*100:.1f}%) 要求100%',
            'page': f'{l2_page}/{total} ({l2_page/total*100:.1f}%) 要求≥90%',
            'line_ref': f'{l2_line}/{total} ({l2_line/total*100:.1f}%) 要求≥70%'
        },
        'grade_distribution': dict(Counter(r['explainability_grade'] for r in results))
    }

    if threshold:
        report['threshold_check'] = _check_thresholds(report, total)

    report['details'] = results
    return report


def _check_thresholds(report, total):
    """按一期验收标准逐项判定"""
    checks = {
        'L1规则编号+触发条件覆盖率100%': report['summary']['L1_规则可解释'].startswith(f'{total}/{total}'),
        'L2文件级溯源率100%': report['l2_detail']['file_source'].startswith(f'{total}/{total}'),
        'L2页级溯源率≥90%': int(report['l2_detail']['page'].split('/')[0]) / total >= 0.9,
        'L2行级溯源率≥70%': int(report['l2_detail']['line_ref'].split('/')[0]) / total >= 0.7,
        'L3因果链完整率≥60%': report['summary']['L3_因果可解释'].endswith('%)') and float(report['summary']['L3_因果可解释'].split('(')[1].split('%')[0]) >= 60.0
    }
    all_pass = all(checks.values())
    return {
        'passed': all_pass,
        'verdict': '✅ 可解释性验收通过' if all_pass else '❌ 可解释性验收不通过，需要整改',
        'items': [{'check': k, 'pass': v} for k, v in checks.items()]
    }


# ═══════════════════════════════════════════════════
# 快速校验：判断单条发现是否能作为证据
# ═══════════════════════════════════════════════════

def is_evidence_ready(finding):
    """快速判断：这条发现能写进审计报告吗？"""
    result = validate_finding(finding)
    if result['overall_score'] < 0.5:
        return False, 'D级: 不可解释，不能作为审计证据'
    if result['l1']['score'] < 1.0:
        return False, f'L1不达标: {result["l1"]["issues"]}'
    if result['l2']['score'] < 0.4:
        return False, 'L2不达标: 缺少文件级溯源'
    if result['l3']['score'] < 0.4:
        return False, 'L3不达标: 缺少因果逻辑链'
    return True, result['explainability_grade']


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════

def load_findings(path):
    """从JSON文件或目录加载发现"""
    p = Path(path)
    if p.is_file():
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if 'findings' in data:
                return data['findings']
            return [data]
    elif p.is_dir():
        all_findings = []
        for f in sorted(p.glob('*.json')):
            all_findings.extend(load_findings(str(f)))
        return all_findings
    return []


def main():
    p = argparse.ArgumentParser(description='审盾发现校验器 v1.0 — 可解释性三级标准校验')
    p.add_argument('--file', help='发现JSON文件路径')
    p.add_argument('--dir', help='发现JSON目录路径')
    p.add_argument('--threshold', action='store_true', default=True, help='按一期验收标准判定（默认开启）')
    p.add_argument('--strict', action='store_true', help='严格模式：L3不通过也算整体不通过')
    p.add_argument('--verbose', '-v', action='store_true', help='输出每条发现的详细校验结果')
    p.add_argument('--output', help='输出校验报告JSON路径')
    args = p.parse_args()

    if not args.file and not args.dir:
        p.print_help()
        sys.exit(1)

    source = args.file or args.dir
    findings = load_findings(source)
    if not findings:
        print(f'❌ 未找到发现数据: {source}')
        sys.exit(1)

    report = validate_batch(findings, threshold=args.threshold)

    # 输出报告
    print('=' * 60)
    print('  审盾发现可解释性校验报告')
    print('=' * 60)
    print(f'  总数: {report["total_findings"]}')
    print()
    for k, v in report['summary'].items():
        print(f'  {k}: {v}')
    print()
    print('  L2 溯源详情:')
    for k, v in report['l2_detail'].items():
        print(f'    {k}: {v}')
    print()
    print('  等级分布:')
    for grade, count in sorted(report['grade_distribution'].items()):
        print(f'    {grade}: {count}条')

    if args.threshold and 'threshold_check' in report:
        tc = report['threshold_check']
        print()
        print('─' * 60)
        print(f'  {tc["verdict"]}')
        for item in tc['items']:
            icon = '✅' if item['pass'] else '❌'
            print(f'    {icon} {item["check"]}')

    if args.verbose:
        print()
        print('─' * 60)
        print('  逐条详情:')
        for r in report['details']:
            icon = '✅' if r['overall_pass'] else '❌'
            print(f'  {icon} [{r["finding_id"]}] {r["dimension"]} | {r["explainability_grade"]} ({r["overall_score"]:.2f})')
            for level in ['l1', 'l2', 'l3']:
                issues = r[level]['issues']
                if issues:
                    for issue in issues:
                        print(f'      {issue}')

    print()
    print('=' * 60)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f'💾 报告已保存: {out_path}')

    # 退出码：不通过则非0
    if args.threshold and 'threshold_check' in report:
        sys.exit(0 if report['threshold_check']['passed'] else 1)


if __name__ == '__main__':
    main()
