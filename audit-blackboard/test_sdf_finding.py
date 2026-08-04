# -*- coding: utf-8 -*-
"""SDF Adapter + Finding Validator 集成测试"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from sdf_adapter import build_sdf, save_sdf

print('=' * 60)
print('  测试1: SDF Adapter')
print('=' * 60)

headers = ['日期', '凭证号', '科目名称', '借方金额', '贷方金额', '摘要']
data_rows = [
    ['2025-01-05', '记-0001', '库存现金', '15000.00', '', '收到保证金'],
    ['2025-01-05', '记-0001', '其他应付款', '', '15000.00', '收到保证金'],
    ['2025-01-06', '记-0002', '管理费用', '2300.50', '', '购买办公用品'],
    ['2025-01-06', '记-0002', '银行存款', '', '2300.50', '购买办公用品'],
    ['2025-01-07', '记-0003', '库存现金', '50000.00', '', '大额整数转账(Friday)'],
]

sdf = build_sdf(headers, data_rows, 'excel', 'test/序时账.xlsx', 'test_project', '序时账', header_rows=1)

print(f'SDF版本: {sdf["sdf_version"]}')
print(f'行数: {sdf["profile"]["row_count"]}  列数: {sdf["profile"]["col_count"]}')
print(f'空值率: {sdf["profile"]["null_rate"]:.2%}')
print('字段角色:')
for c in sdf['columns']:
    extra = ''
    if 'stats' in c:
        extra = f' 范围[{c["stats"]["min"]}, {c["stats"]["max"]}]'
    print(f'  {c["name"]}: role={c["role"]} dtype={c["dtype"]}{extra}')

print(f'\n数据预览 ({len(sdf["data_preview"])}条):')
for row in sdf['data_preview']:
    print(f'  {row}')

tmpdir = tempfile.gettempdir()
saved = save_sdf(sdf, tmpdir, 'test_project', '序时账')
print(f'\nSDF saved: {saved}')

# ─── Test 2: Finding Validator ───
print()
print('=' * 60)
print('  测试2: Finding Validator')
print('=' * 60)

from finding_validator import validate_finding, is_evidence_ready

# 一条达标发现
good_finding = {
    'finding_id': 'F-2026-0804-001',
    'source_model': 'L1.R001',
    'indicator_id': 'I-P-002',
    'entity': {'type': 'project', 'id': 'PJ-2025-017', 'name': 'XX项目'},
    'dimension': '产出完成率',
    'observed_value': '88.7%',
    'expected_range': [0.95, 1.05],
    'deviation': 'below_threshold',
    'severity': 'P1',
    'risk_score': 72.5,
    'explainability_l1': {
        'rule_id': 'R001',
        'rule_name': '产出指标完成率低于合同约定',
        'trigger_condition': '实际完成率88.7%低于合同约定95%阈值6.3个百分点'
    },
    'explainability_l2': {
        'file_source': '绩效评价报告.docx',
        'page': 23,
        'line_ref': '表5-3第3行',
        'raw_value': '88.7%',
        'data_hash': 'sha256:abc123'
    },
    'explainability_l3': {
        'causal_chain': '①完成率88.7%低于目标95% → ②差口6.3pp → ③构成资金使用效率风险 → ④建议核查差口原因',
        'risk_type': '资金使用效率',
        'impact_estimate': '约6.3%项目资金可能存在闲置或挪用',
        'related_cases': ['F-2025-郫都-007'],
        'suggestion': '核查88.7%与95%之间6.3个百分点的差口对应资金去向及原因'
    },
    'confirmation': {'status': 'pending'},
    'metadata': {'created_at': '2026-08-04T16:00:00', 'created_by': '审盾'}
}

result = validate_finding(good_finding)
print(f'✅ 达标发现: {result["explainability_grade"]} ({result["overall_score"]:.2f})')
print(f'   L1: {"PASS" if result["l1"]["passed"] else "FAIL"}')
print(f'   L2: {"PASS" if result["l2"]["passed"] else "FAIL"} (file={result["l2"]["checks"]["file_source"]} page={result["l2"]["checks"]["page"]} line={result["l2"]["checks"]["line_ref"]})')
print(f'   L3: {"PASS" if result["l3"]["passed"] else "FAIL"} (chain={result["l3"]["checks"]["causal_chain"]} risk={result["l3"]["checks"]["risk_type"]} suggest={result["l3"]["checks"]["suggestion"]})')

ready, msg = is_evidence_ready(good_finding)
print(f'   证据就绪: {ready} ({msg})')

# 一条不达标发现（缺少解释）
bad_finding = {
    'finding_id': 'F-2026-0804-002',
    'source_model': 'L2.zscore',
    'dimension': '报价偏离',
    'observed_value': '0.98',
    'severity': 'P2',
    'risk_score': 45.0,
    'explainability_l1': {
        'rule_id': '',
        'rule_name': '',
        'trigger_condition': ''
    },
    'explainability_l2': {
        'file_source': ''
    },
    'explainability_l3': {}
}

result2 = validate_finding(bad_finding)
print(f'\n❌ 不达标发现: {result2["explainability_grade"]} ({result2["overall_score"]:.2f})')
ready2, msg2 = is_evidence_ready(bad_finding)
print(f'   证据就绪: {ready2} ({msg2})')

# 批量测试
print()
print('=' * 60)
print('  测试3: 批量校验 + 阈值判定')
print('=' * 60)
from finding_validator import validate_batch
batch = [good_finding, bad_finding,
    {**good_finding, 'finding_id': 'F-2026-0804-003', 'explainability_l2': {**good_finding['explainability_l2'], 'line_ref': ''}},
    {**good_finding, 'finding_id': 'F-2026-0804-004', 'explainability_l3': {**good_finding['explainability_l3'], 'causal_chain': '', 'related_cases': []}},
]
report = validate_batch(batch, threshold=True)

print(f'总数: {report["total_findings"]}')
for k, v in report['summary'].items():
    print(f'  {k}: {v}')
print(f'\nL2详情:')
for k, v in report['l2_detail'].items():
    print(f'  {k}: {v}')
print(f'\n等级分布: {report["grade_distribution"]}')
tc = report['threshold_check']
print(f'\n{tc["verdict"]}')
for item in tc['items']:
    icon = '✅' if item['pass'] else '❌'
    print(f'  {icon} {item["check"]}')

print()
print('=' * 60)
print('  ✅ 全部测试通过')
print('=' * 60)
