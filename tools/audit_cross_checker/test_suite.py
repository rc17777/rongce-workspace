#!/usr/bin/env python3
"""Test suite for audit_cross_checker module (standalone)."""

import sys, os, tempfile

# Add the workspace root to path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

# Package imports (works with python -m tools.audit_cross_checker.test_suite)
from .table_model import extract_table_from_rows, TableDocument, parse_number
from .domain_adapter import (
    list_adapters, auto_detect_domain,
    AnnualReportAdapter, PerformanceAdapter,
    EngineeringAdapter, SpecialAuditAdapter,
)
from .rule_engine import load_rule_package, load_thresholds, RuleEngine
from .review_filter import ReviewFilter
from .review_report_generator import ReviewReportGenerator

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"[PASS] {name}")
        passed += 1
    except Exception as e:
        import traceback
        print(f"[FAIL] {name}: {e}")
        traceback.print_exc()
        failed += 1

# Test 1: Number parsing
def t1():
    assert parse_number('1,234,567.89') == 1234567.89
    assert parse_number('(123.45)') == -123.45
    assert parse_number('12.5%') == 0.125
    assert parse_number('—') is None
    assert parse_number('100', 'wan_unit') == 1_000_000
test("Number parsing", t1)

# Test 2: Table extraction
def t2():
    bs_rows = [
        ['项目', '期末余额', '年初余额'],
        ['货币资金', '500,000.00', '300,000.00'],
        ['应收账款', '200,000.00', '150,000.00'],
        ['存货', '100,000.00', '80,000.00'],
        ['流动资产合计', '800,000.00', '530,000.00'],
        ['固定资产', '400,000.00', '350,000.00'],
        ['资产总计', '1,200,000.00', '880,000.00'],
    ]
    sheet = extract_table_from_rows('资产负债表', bs_rows)
    assert sheet.name == '资产负债表'
    assert len(sheet.columns) == 3
    assert sheet.columns[0].role == 'item_name'
    assert sheet.columns[1].role == 'end_balance'
    assert sheet.rows[4].is_total
test("Table extraction", t2)

# Test 3: Domain adapters
def t3():
    adapters = list_adapters()
    assert len(adapters) == 4
    names = [a['domain'] for a in adapters]
    assert 'annual_report' in names
    assert 'performance' in names
    print(f"    Available: {names}")
test("Domain adapters", t3)

# Test 4: Rule packages
def t4():
    for domain in ['annual_report', 'special_audit', 'engineering', 'performance']:
        rules = load_rule_package(domain)
        assert len(rules) > 0, f'No rules for {domain}'
        print(f"    {domain}: {len(rules)} rules")
test("Rule packages", t4)

# Test 5: Thresholds
def t5():
    thresh = load_thresholds()
    assert 'annual_report' in thresh
    assert 'performance' in thresh
    assert thresh['performance']['indicator']['weight_closure'] == True
    print(f"    Domains: {list(thresh.keys())}")
test("Thresholds", t5)

# Test 6: Full pipeline with mock data
def t6():
    bs_rows = [
        ['项目', '期末余额', '年初余额'],
        ['货币资金', '500,000.00', '300,000.00'],
        ['应收账款', '200,000.00', '150,000.00'],
        ['存货', '100,000.00', '80,000.00'],
        ['流动资产合计', '800,000.00', '530,000.00'],
        ['固定资产', '400,000.00', '350,000.00'],
        ['资产总计', '1,200,000.00', '880,000.00'],
    ]
    sheet = extract_table_from_rows('资产负债表', bs_rows)
    doc = TableDocument(source_type='test')
    doc.sheets = [sheet]
    
    engine = RuleEngine(doc)
    results = engine.run_intra_note_checks(sheet)
    assert len(results) > 0
    print(f"    Intra-note checks: {len(results)} results")
    for r in results:
        print(f"      [{r.passed}] {r.description}: exp={r.expected}, act={r.actual}, diff={r.diff}")
    
    s = engine.summary()
    assert 'total_checks' in s
    print(f"    Summary: {s['total_checks']} checks, passed={s['passed']}, failed={s['failed']}")
test("Full pipeline (mock)", t6)

# Test 7: Review filter
def t7():
    bs_rows = [
        ['项目', '金额'],
        ['A', '100.00'],
        ['B', '200.00'],
        ['其中：B1', '80.00'],
        ['合计', '299.00'],
    ]
    sheet = extract_table_from_rows('测试表', bs_rows)
    doc = TableDocument(source_type='test')
    doc.sheets = [sheet]
    
    engine = RuleEngine(doc)
    results = engine.run_intra_note_checks(sheet)
    print(f"    Raw results: {len(results)}")
    for r in results:
        print(f"      {r.description}: exp={r.expected}, act={r.actual}, diff={r.diff}")
    
    filt = ReviewFilter(doc)
    filtered = filt.filter(results)
    classified = filt.classify(filtered)
    
    print(f"    Confirmed: {len(classified['confirmed'])}")
    print(f"    Needs review: {len(classified['needs_review'])}")
    print(f"    False positives: {len(classified['false_positive'])}")
    for r in classified['false_positive']:
        print(f"      FP: {r.description} — reason: {r.false_positive_reason}")
test("Review filter", t7)

# Test 8: Report generation
def t8():
    # Intentionally wrong: A + B = 300 but total says 301
    bs_rows = [['项目', '金额'], ['A', '100'], ['B', '200'], ['合计', '301']]
    sheet = extract_table_from_rows('测试', bs_rows)
    doc = TableDocument(source_type='test')
    doc.sheets = [sheet]
    engine = RuleEngine(doc)
    results = engine.run_intra_note_checks(sheet)
    filt = ReviewFilter(doc)
    filtered = filt.filter(results)
    classified = filt.classify(filtered)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ReviewReportGenerator(classified, domain='test')
        paths = gen.generate_all(tmpdir, 'test_report')
        assert os.path.exists(paths['excel']), f"Excel not found: {paths['excel']}"
        assert os.path.exists(paths['markdown']), f"MD not found: {paths['markdown']}"
        print(f"    Excel: {os.path.getsize(paths['excel'])} bytes")
        print(f"    MD: {os.path.getsize(paths['markdown'])} bytes")
        with open(paths['markdown'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert os.path.getsize(paths['markdown']) > 100
        print(f"    MD preview: {content[:250]}...")
test("Report generation", t8)

# Test 9: Auto-detect domain
def t9():
    bs_rows = [
        ['项目', '期末余额', '年初余额'],
        ['资产总计', '1,000', '800'],
    ]
    sheet = extract_table_from_rows('资产负债表', bs_rows)
    doc = TableDocument(source_type='test')
    doc.sheets = [sheet]
    
    adapter = AnnualReportAdapter()
    cat = adapter.classify_sheet(sheet)
    assert cat == 'balance_sheet', f"Expected balance_sheet, got {cat}"
    print(f"    Classified as: {cat}")
test("Auto-detect domain", t9)

# Test 10: Performance adapter
def t10():
    perf_rows = [
        ['指标', '权重'],
        ['一级A', '0.40'],
        ['一级B', '0.35'],
        ['一级C', '0.25'],
    ]
    sheet = extract_table_from_rows('绩效指标体系', perf_rows)
    doc = TableDocument(source_type='test')
    doc.sheets = [sheet]
    
    adapter = PerformanceAdapter()
    adapter.apply(doc)
    
    assert doc.metadata['domain'] == 'performance'
    assert doc.manifest['domain'] == 'performance'
    print(f"    Domain: {doc.metadata['domain']}")
    print(f"    Manifest tables: {list(doc.manifest.get('tables', {}).keys())}")
test("Performance adapter", t10)

# Test 11: Engineering adapter
def t11():
    rows = [
        ['项目', '概算金额', '预算金额', '合同价', '结算价', '决算价'],
        ['土建工程', '1000', '950', '900', '880', '870'],
        ['安装工程', '500', '480', '450', '440', '435'],
    ]
    sheet = extract_table_from_rows('五算对比表', rows)
    doc = TableDocument(source_type='test')
    doc.sheets = [sheet]
    
    adapter = EngineeringAdapter()
    adapter.apply(doc)
    
    assert doc.metadata['domain'] == 'engineering'
    assert 'five_way_comparison' in str(doc.manifest)
    print(f"    Domain: {doc.metadata['domain']}")
    # Check column roles
    roles = [(c.header, c.role) for c in sheet.columns]
    print(f"    Column roles: {roles}")
    assert any(r[1] == 'estimate_amount' for r in roles)
    assert any(r[1] == 'final_amount' for r in roles)
test("Engineering adapter", t11)

# Test 12: Special audit adapter
def t12():
    rows = [
        ['项目', '批复预算', '实际支出', '差异'],
        ['人员经费', '500', '480', '-20'],
        ['公用经费', '300', '310', '10'],
    ]
    sheet = extract_table_from_rows('预算执行情况表', rows)
    doc = TableDocument(source_type='test')
    doc.sheets = [sheet]
    
    adapter = SpecialAuditAdapter()
    adapter.apply(doc)
    
    cat = adapter.classify_sheet(sheet)
    assert cat == 'budget_vs_actual', f"Got: {cat}"
    print(f"    Classified as: {cat}")
test("Special audit adapter", t12)

print()
print("=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
if failed:
    print("SOME TESTS FAILED")
else:
    print("ALL TESTS PASSED")
