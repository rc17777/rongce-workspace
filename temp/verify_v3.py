# -*- coding: utf-8 -*-
import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8')

# 1. 语法检查
py_compile.compile(r'C:\Users\scrccpa\.openclaw\workspace\temp\build_algorithm_lib_v3.py', doraise=True)
print('✅ 语法检查通过')

# 2. 导入并验证算法数量与字段完整性
sys.path.insert(0, r'C:\Users\scrccpa\.openclaw\workspace\temp')
import importlib
mod = importlib.import_module('build_algorithm_lib_v3')

algs = mod.algorithms
print('算法总数:', len(algs))

REQUIRED = ['sn','name','scene','objective','risk_hypothesis','scope_yes','scope_no','law_basis',
'data_tables','fields','keys','data_quality','calc_logic','threshold','threshold_basis','output_fields',
'explain','evidence','check_procedure','conclusion_boundary','test_cases','backtest','risk_score',
'multi_rule','sensitivity','fpr_fnr','visual','reuse','perf','privacy','data_readiness','data_grade',
'verify_standard','workpaper_template','explainability','retire_condition','review_cycle','dependency',
'expected_value','history_output']
print('要素总数(不含自动版本号):', len(REQUIRED))

sns = set()
problems = []
for a in algs:
    sn = a['sn']
    if sn in sns:
        problems.append(f'重复编号: {sn}')
    sns.add(sn)
    missing = [k for k in REQUIRED if k not in a or not str(a[k]).strip() or a[k] == '——']
    if missing:
        problems.append(f'{sn} 缺要素: {missing}')

print('编号唯一性:', 'OK' if len(sns) == len(algs) else 'FAIL')
print('问题清单:', problems if problems else '无 — 全部31个算法40要素完整')

print('\n新算法清单:')
for a in algs[23:]:
    print(' ', a['sn'], '|', a['name'], '|', a['scene'])
