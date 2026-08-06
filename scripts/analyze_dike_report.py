#!/usr/bin/env python3
"""Run TextQualityFilter on extracted dike project audit report."""
import sys
sys.path.insert(0, '.')

from tools.audit_cross_checker.text_quality_filter import TextQualityFilter, quick_check

# Load extracted text
with open(r'C:\Users\15528\.openclaw\workspace-main\reports\extracted_dike_report.txt', 'r', encoding='utf-8') as f:
    full_text = f.read()

# ----- Header: Try to identify report type from content -----
report_type = 'general'
report_category = 'government_audit'  # default

if '经济责任' in full_text or '经济责任审计' in full_text:
    report_type = 'econ_accountability'
elif '自然资源' in full_text or '离任' in full_text:
    report_type = 'natural_resources'

# Detect CPA report (has 注册会计师/会计师事务所/审核报告/鉴证)
if any(kw in full_text for kw in ['注册会计师', '会计师事务所', '中国注册会计师审计准则', '鉴证业务']):
    report_category = 'cpa_attestation'
elif any(kw in full_text for kw in ['内部审计', '内部审核']):
    report_category = 'internal_audit'

print(f'Report type: {report_type}')
print(f'Report category: {report_category}')
print(f'Report length: {len(full_text)} chars')
print()

# ----- Run TextQualityFilter -----
tqf = TextQualityFilter(report_category=report_category)
results = tqf.evaluate(full_text, report_type=report_type)
score = tqf.score(results)
classified = tqf.classify(results)

# ----- Print results -----
print('=' * 80)
print(f'OVERALL SCORE: {score["overall_score"]}/100  |  GRADE: {score["grade"]}')
print(f'Checks: {score["total_checks"]} total, {score["passed_checks"]} passed, {score["failed_checks"]} failed, {score["needs_human_review"]} need review')
print()

print('--- Dimension Scores ---')
dim_names = {
    '1': '审计评价恰当性', '2': '问题定性准确性', '3': '事实表述清晰性',
    '4': '依据引用合理性', '5': '处理处罚合法性', '6': '责任界定科学性',
    '7': '审计建议操作性', '8': '采纳意见合理性', '9': '同类问题一致性',
    '10': '报告格式规范性',
}
for dim, info in sorted(score['dimension_scores'].items()):
    name = dim_names.get(dim, dim)
    bar = '#' * int(info['score'] / 5) + '-' * (20 - int(info['score'] / 5))
    print(f'  Dim {dim} {name}: {info["score"]:5.1f} [{bar}]')

print()
print('=' * 80)
print('FAILED CHECKS')
print('=' * 80)

for r in results:
    if not r.passed:
        tag = 'HUMAN' if r.requires_human_review else r.severity.upper()
        print(f'[{tag}] [{r.rule_id}] {r.description}')
        if r.detail:
            print(f'       detail: {r.detail}')
        if r.excerpt:
            for line in r.excerpt.split('\n')[:3]:
                print(f'       excerpt: {line[:120]}')
        if r.suggestion:
            print(f'       suggestion: {r.suggestion}')
        print()

print('=' * 80)
print('NEEDS HUMAN REVIEW')
print('=' * 80)
for r in results:
    if r.requires_human_review and r.passed:
        print(f'[REVIEW] [{r.rule_id}] {r.description}')
        if r.detail:
            print(f'         detail: {r.detail}')
        if r.suggestion:
            print(f'         suggestion: {r.suggestion}')
        print()

# ----- Generate Markdown Report -----
md_report = tqf.generate_review_report(results, report_type)
md_path = r'C:\Users\15528\.openclaw\workspace-main\reports\dike_report_quality_review.md'
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md_report)
print(f'Markdown report saved to: {md_path}')
