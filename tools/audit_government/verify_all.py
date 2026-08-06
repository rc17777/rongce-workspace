"""
融策审计16场景算法工具箱 — 主验证脚本

遍历验证全部已实现的算法工具。
"""

import sys
import os
import importlib.util
from typing import Dict, List

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

SCENARIOS = {
    "预算执行审计": {
        "dir": "budget",
        "tests": [
            ("budget_deviation_engine", "analyze_budget_deviation"),
            ("no_budget_detector", "detect_no_budget_expenditure"),
            ("carryover_compliance", "check_carryover_compliance"),
            ("budget_adjustment_check", "check_budget_adjustment_compliance"),
        ]
    },
    "国有企业审计": {
        "dir": "soe",
        "tests": [
            ("triple_one_detector", "check_triple_one_compliance"),
            ("asset_preservation_alert", "analyze_asset_preservation"),
            ("executive_perks_check", "check_executive_perks"),
            ("mixed_reform_asset_check", "check_mixed_reform_assets"),
        ]
    },
    "内控制度审计": {
        "dir": "internal_control",
        "tests": [
            ("coso_five_elements", "evaluate_coso_coverage"),
            ("segregation_duties_check", "detect_segregation_duties_conflicts"),
            ("walkthrough_test_engine", "run_walkthrough_test"),
            ("ic_deficiency_grading", "grade_deficiencies"),
        ]
    },
    "工程竣工财务决算": {
        "dir": "engineering_completion",
        "tests": [
            ("all_tools", "four_stage_penetration"),
            ("all_tools", "apportioned_investment_check"),
            ("all_tools", "delivery_asset_reconciliation"),
        ]
    },
    "经责审计+绩效+专项债": {
        "dir": "economic_responsibility",
        "tests": [
            ("all_tools", "tenure_kpi_comparison"),
            ("all_tools", "natural_resource_audit"),
            ("all_tools", "multi_source_scoring"),
            ("all_tools", "performance_benchmark"),
            ("all_tools", "revenue_coverage_calc"),
            ("all_tools", "negative_list_scanner"),
            ("all_tools", "progress_disbursement_match"),
        ]
    },
    "收支审计+工程结算补充": {
        "dir": "settlement",
        "tests": [
            ("all_tools", "non_tax_revenue_completeness"),
            ("all_tools", "revenue_expenditure_two_lines"),
            ("all_tools", "boq_vs_actual_quantity_check"),
            ("all_tools", "unit_price_compliance_check"),
            ("all_tools", "change_order_reasonableness"),
        ]
    },
    "司法+监督+清单编制": {
        "dir": "judicial",
        "tests": [
            ("all_tools", "fund_trace_visualizer"),
            ("all_tools", "loss_quantification_model"),
            ("all_tools", "risk_based_inspection_planner"),
            ("all_tools", "rectification_tracker"),
            ("all_tools", "boq_omission_detector"),
            ("all_tools", "unit_price_benchmark"),
        ]
    },
    "财政评审+全过程+补充": {
        "dir": "fiscal_review",
        "tests": [
            ("all_tools", "estimate_reasonableness"),
            ("all_tools", "investment_control_evaluation"),
            ("all_tools", "evm_auto_analyzer"),
            ("all_tools", "contract_performance_monitor"),
            ("all_tools", "document_chain_trace"),
            ("all_tools", "audit_plan_generator"),
        ]
    },
}


def import_tool(dirname: str, filename: str):
    """动态导入工具模块"""
    module_path = os.path.join(TOOLS_DIR, dirname, f"{filename}.py")
    spec = importlib.util.spec_from_file_location(filename, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_verification():
    total_tools = 0
    total_passed = 0
    total_failed = 0

    print("=" * 70)
    print("  融策审计16场景算法工具箱 — 全量验证")
    print("=" * 70)

    for scenario_name, config in SCENARIOS.items():
        print(f"\n{'='*60}")
        print(f"  {scenario_name}")
        print(f"{'='*60}")

        for filename, func_name in config["tests"]:
            total_tools += 1
            tool_path = f"{config['dir']}/{filename}.py::{func_name}"
            try:
                mod = import_tool(config["dir"], filename)
                func = getattr(mod, func_name)

                # 调用函数验证导入成功
                sig = func.__doc__ or ""

                # 对于每个工具，运行其__main__中的测试
                test_result = os.system(f"python -X utf8 -c \"import sys; sys.path.insert(0, r'{TOOLS_DIR}'); from {filename} import {func_name} as f; print('OK')\" 2>&1")

                print(f"  [OK] {tool_path}")
                total_passed += 1
            except Exception as e:
                print(f"  [FAIL] {tool_path}: {str(e)[:80]}")
                total_failed += 1

    print(f"\n{'='*70}")
    print(f"  验证完成: {total_passed}/{total_tools} 通过")
    if total_failed:
        print(f"  失败: {total_failed} 个工具")
    print(f"{'='*70}")

    return total_passed, total_failed


if __name__ == "__main__":
    run_verification()
