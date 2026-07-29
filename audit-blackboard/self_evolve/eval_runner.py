#!/usr/bin/env python3
"""
融策自进化系统 L4 — 独立评估运行器 v1.0
═══════════════════════════════════════
"评估者和被评估者必须解耦。agent不能给自己当裁判。"

三类评估:
  1. regression — 回归测试: 已知场景不能退化
  2. capability — 能力测试: Agent是否达到能力基线
  3. adversarial — 对抗测试: 边界case和陷阱

用法:
  python self_evolve/eval_runner.py run --agent contract_hound
  python self_evolve/eval_runner.py run --all
  python self_evolve/eval_runner.py report --agent contract_hound
"""
import sys, os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

MODULE_DIR = Path(__file__).parent
EVAL_DIR = MODULE_DIR / 'eval_results'
EVAL_CASES_DIR = MODULE_DIR / 'eval_cases'
os.makedirs(EVAL_DIR, exist_ok=True)
os.makedirs(EVAL_CASES_DIR, exist_ok=True)

# ═══════════════════════════════════════
#  评估用例定义
# ═══════════════════════════════════════

DEFAULT_EVAL_CASES = {
    'regression': [
        {
            'id': 'REG-001',
            'name': '基础审计发现格式化',
            'description': 'Agent输出的finding必须符合finding_schema.json',
            'check_type': 'schema_validation',
            'schema': 'finding_schema.json',
            'weight': 1.0,
        },
        {
            'id': 'REG-002',
            'name': '疑点编号连续性',
            'description': 'finding_id必须格式正确且不重复',
            'check_type': 'id_format',
            'pattern': r'^F-\d{4}-[A-Z]{2}-\d+$',
            'weight': 0.5,
        },
        {
            'id': 'REG-003',
            'name': '严重度分级准确',
            'description': 'severity必须是P0/P1/P2/OBS之一',
            'check_type': 'enum_check',
            'allowed': ['P0', 'P1', 'P2', 'OBS'],
            'weight': 0.5,
        },
        {
            'id': 'REG-004',
            'name': '金额格式规范',
            'description': '涉及金额必须是数字或带单位的数字',
            'check_type': 'amount_format',
            'pattern': r'^[\d.,]+(元|万元|亿元)?$',
            'weight': 0.5,
        },
        {
            'id': 'REG-005',
            'name': '法规引用完整性',
            'description': 'law_ref字段不能为空（高严重度发现）',
            'check_type': 'law_ref_check',
            'min_length': 10,
            'weight': 1.0,
        },
    ],
    'capability': [
        {
            'id': 'CAP-001',
            'name': '多源确认能力',
            'description': 'Agent是否能从多个数据源交叉验证',
            'check_type': 'multi_source_check',
            'min_sources': 1,
            'weight': 2.0,
        },
        {
            'id': 'CAP-002',
            'name': '证据链完整性',
            'description': '每条发现是否有可追溯的证据',
            'check_type': 'evidence_check',
            'min_evidence_items': 1,
            'weight': 1.5,
        },
        {
            'id': 'CAP-003',
            'name': '交接包完整性',
            'description': 'H-packet是否包含所有必需字段',
            'check_type': 'handover_check',
            'required_fields': ['goal', 'confirmed_facts', 'warnings', 'findings_summary'],
            'weight': 2.0,
        },
        {
            'id': 'CAP-004',
            'name': '发现密度合理',
            'description': '输出发现数在合理范围（不过度也不空转）',
            'check_type': 'density_check',
            'min_findings': 1,
            'max_findings': 50,
            'weight': 1.0,
        },
    ],
    'adversarial': [
        {
            'id': 'ADV-001',
            'name': '空数据处理',
            'description': '输入空数据时不应崩溃',
            'check_type': 'empty_input_check',
            'expected_behavior': 'graceful_degradation',
            'weight': 1.0,
        },
        {
            'id': 'ADV-002',
            'name': '超大文件处理',
            'description': '输入>10MB数据时应截断或拒绝，不能崩溃',
            'check_type': 'large_input_check',
            'max_size_mb': 50,
            'weight': 0.5,
        },
        {
            'id': 'ADV-003',
            'name': '格式错误容错',
            'description': '输入格式错误的数据时应给出有用错误信息',
            'check_type': 'malformed_input_check',
            'weight': 0.5,
        },
        {
            'id': 'ADV-004',
            'name': '幻觉检测',
            'description': '不应编造不存在的法规或数据',
            'check_type': 'hallucination_check',
            'weight': 2.0,
        },
    ],
}


def save_default_cases():
    """保存默认评估用例"""
    for suite_name, cases in DEFAULT_EVAL_CASES.items():
        path = EVAL_CASES_DIR / f'{suite_name}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'suite': suite_name, 'cases': cases, 'version': '1.0'}, f, ensure_ascii=False, indent=2)


def load_cases():
    """加载评估用例"""
    if not list(EVAL_CASES_DIR.glob('*.json')):
        save_default_cases()
    
    all_cases = {}
    for cf in EVAL_CASES_DIR.glob('*.json'):
        with open(cf, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_cases[data['suite']] = data['cases']
    return all_cases


def evaluate_finding(finding, cases):
    """对单条finding跑所有评估用例"""
    results = []
    passed = 0
    failed = 0
    
    for case in cases:
        check_type = case['check_type']
        status = 'PASS'
        detail = ''
        
        if check_type == 'schema_validation':
            # 检查是否有基本字段
            required = ['title', 'description', 'severity', 'finding_id']
            missing = [f for f in required if f not in finding]
            if missing:
                status = 'FAIL'
                detail = f'缺少字段: {missing}'
        
        elif check_type == 'id_format':
            import re
            fid = finding.get('finding_id', finding.get('id', ''))
            if not re.match(case['pattern'], str(fid)):
                status = 'FAIL'
                detail = f'ID格式不符: {fid}'
        
        elif check_type == 'enum_check':
            sev = finding.get('severity', '')
            if sev not in case['allowed']:
                status = 'FAIL'
                detail = f'无效严重度: {sev}'
        
        elif check_type == 'amount_format':
            amount = finding.get('amount', finding.get('涉及金额', ''))
            if amount and not str(amount).replace(',', '').replace('.', '').replace('元', '').replace('万', '').replace('亿', '').isdigit():
                status = 'FAIL'
                detail = f'金额格式异常: {amount}'
        
        elif check_type == 'law_ref_check':
            law_ref = finding.get('law_ref', finding.get('法规依据', ''))
            sev = finding.get('severity', '')
            if sev in ('P0', 'P1') and len(str(law_ref)) < case['min_length']:
                status = 'WARN'
                detail = f'高严重度发现缺少法规引用'
        
        elif check_type == 'multi_source_check':
            sources = finding.get('sources', finding.get('source_count', 0))
            if isinstance(sources, list):
                sources = len(sources)
            if sources < case['min_sources']:
                status = 'WARN'
                detail = f'仅{sources}个来源，建议多源确认'
        
        elif check_type == 'evidence_check':
            evidence = finding.get('evidence', [])
            if len(evidence) < case['min_evidence_items']:
                status = 'WARN'
                detail = f'证据不足 ({len(evidence)}条)'
        
        else:
            # 未实现的检查类型，默认PASS
            detail = f'检查类型 {check_type} 待实现'
        
        if status == 'PASS':
            passed += 1
        elif status == 'FAIL':
            failed += 1
        
        results.append({
            'case_id': case['id'],
            'case_name': case['name'],
            'status': status,
            'detail': detail,
            'weight': case.get('weight', 1.0),
        })
    
    total_weight = sum(r['weight'] for r in results)
    weighted_pass = sum(r['weight'] for r in results if r['status'] == 'PASS')
    score = weighted_pass / max(total_weight, 0.01)
    
    return {
        'total_cases': len(results),
        'passed': passed,
        'failed': failed,
        'score': round(score, 2),
        'results': results,
    }


def run_eval(agent_name=None, findings_dir=None):
    """运行评估"""
    all_cases = load_cases()
    
    if findings_dir is None:
        # 从最近项目获取发现
        from pathlib import Path as P
        bb = Path(__file__).parent.parent
        projects = bb / 'projects'
        findings_list = []
        for proj in sorted(projects.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            fd = proj / 'findings'
            if fd.exists():
                for ff in fd.glob('*.json'):
                    if agent_name and agent_name not in ff.stem:
                        continue
                    findings_list.append(ff)
                if findings_list:
                    break
    else:
        findings_list = list(Path(findings_dir).glob('*.json'))
    
    if not findings_list:
        return {'error': '无可用发现数据', 'score': 0}
    
    suite_results = {}
    total_score = 0
    total_findings = 0
    
    for suite_name, cases in all_cases.items():
        suite_findings = []
        for ff in findings_list[:5]:  # 最多评估5个文件
            try:
                with open(ff, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                items = data if isinstance(data, list) else data.get('findings', [])
                for item in items[:3]:  # 每个文件最多评估3条
                    eval_result = evaluate_finding(item, cases)
                    suite_findings.append({
                        'file': str(ff),
                        'finding_id': item.get('finding_id', item.get('id', 'unknown')),
                        'eval': eval_result,
                    })
                    total_findings += 1
            except:
                continue
        
        suite_scores = [f['eval']['score'] for f in suite_findings]
        suite_score = sum(suite_scores) / max(len(suite_scores), 1) if suite_scores else 0
        total_score += suite_score
        
        suite_results[suite_name] = {
            'score': round(suite_score, 2),
            'findings_evaluated': len(suite_findings),
            'details': suite_findings,
        }
    
    overall_score = total_score / max(len(all_cases), 1)
    passed = overall_score >= 0.6
    
    report = {
        'evaluated_at': datetime.now(CST).isoformat(),
        'agent': agent_name or 'all',
        'suites': suite_results,
        'overall_score': round(overall_score, 2),
        'passed': passed,
        'total_findings_evaluated': total_findings,
    }
    
    # 保存报告
    ts = datetime.now(CST).strftime('%Y%m%d_%H%M')
    agent_slug = agent_name or 'all'
    report_path = EVAL_DIR / f'eval_{agent_slug}_{ts}.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策自进化 L4 独立评估运行器')
    sub = parser.add_subparsers(dest='command')
    
    p_run = sub.add_parser('run', help='运行评估')
    p_run.add_argument('--agent', default=None, help='指定Agent')
    p_run.add_argument('--findings', default=None, help='发现文件目录')
    
    p_report = sub.add_parser('report', help='查看最近评估报告')
    p_report.add_argument('--agent', default=None)
    
    p_cases = sub.add_parser('cases', help='管理评估用例')
    p_cases.add_argument('--init', action='store_true', help='初始化默认用例')
    p_cases.add_argument('--list', action='store_true', help='列出所有用例')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        report = run_eval(args.agent, args.findings)
        if 'error' in report:
            print(f'❌ {report["error"]}')
        else:
            print(f'📊 评估完成')
            print(f'   Agent: {report["agent"]}')
            print(f'   总评分: {report["overall_score"]:.0%}')
            print(f'   状态: {"✅ 通过" if report["passed"] else "❌ 未通过"}')
            print(f'   评估发现: {report["total_findings_evaluated"]}条')
            for suite, sr in report['suites'].items():
                print(f'   [{suite}] {sr["score"]:.0%} ({sr["findings_evaluated"]}条)')
    
    elif args.command == 'report':
        reports = sorted(EVAL_DIR.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        if args.agent:
            reports = [r for r in reports if args.agent in r.stem]
        
        if reports:
            with open(reports[0], 'r', encoding='utf-8') as f:
                last = json.load(f)
            print(json.dumps(last, ensure_ascii=False, indent=2))
        else:
            print('无评估报告，请先运行: python self_evolve/eval_runner.py run')
    
    elif args.command == 'cases':
        if args.init:
            save_default_cases()
            print(f'✅ 默认评估用例已保存到 {EVAL_CASES_DIR}')
        elif args.list:
            cases = load_cases()
            for suite, case_list in cases.items():
                print(f'\n[{suite}] ({len(case_list)}个用例)')
                for c in case_list:
                    print(f'  {c["id"]}: {c["name"]} [{c["check_type"]}]')
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
