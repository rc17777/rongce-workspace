"""
融策审计16场景算法工具箱 — MCP服务注册模块

将所有39个新工具注册到MCP Server，供Agent调用。

作者：融策审计智析Agent | 日期：2026-07-22
"""

import sys
import os
import importlib.util
import json
from typing import Dict, Any

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 工具注册表 ────────────────────────────────────────

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── P0: 预算执行审计 ──
    "budget_deviation_engine": {
        "file": "budget/budget_deviation_engine.py",
        "function": "analyze_budget_deviation",
        "description": "预算执行偏差多维分析引擎",
        "params": {"budget_data": "预算批复表", "execution_data": "执行报表", "year_end_check": "年末检测开关"},
        "tags": ["预算执行审计", "财政审计"],
    },
    "no_budget_detector": {
        "file": "budget/no_budget_detector.py",
        "function": "detect_no_budget_expenditure",
        "description": "无预算支出检测器",
        "params": {"budget_data": "预算批复表", "execution_data": "执行报表", "threshold": "金额阈值"},
        "tags": ["预算执行审计", "财政纪律"],
    },
    "carryover_compliance": {
        "file": "budget/carryover_compliance.py",
        "function": "check_carryover_compliance",
        "description": "结转结余合规判定（预算法第42条）",
        "params": {"project_ledger": "项目台账", "reference_date": "参考日期"},
        "tags": ["预算执行审计", "存量资金清理"],
    },
    "budget_adjustment_check": {
        "file": "budget/budget_adjustment_check.py",
        "function": "check_budget_adjustment_compliance",
        "description": "预算调整程序合规检测",
        "params": {"adjustment_records": "调整记录", "budget_total": "预算总额"},
        "tags": ["预算执行审计", "财政纪律"],
    },

    # ── P0: 国有企业审计 ──
    "triple_one_detector": {
        "file": "soe/triple_one_detector.py",
        "function": "check_triple_one_compliance",
        "description": "三重一大决策程序合规检测（决策/人事/项目/资金四维）",
        "params": {"major_decisions": "重大决策", "personnel_appointments": "人事任免", "major_projects": "重大项目", "large_funds": "大额资金"},
        "tags": ["国有企业审计", "经责审计"],
    },
    "asset_preservation_alert": {
        "file": "soe/asset_preservation_alert.py",
        "function": "analyze_asset_preservation",
        "description": "国有资产保值增值风险预警（减值/处置/划转三维）",
        "params": {"assets": "资产台账", "disposals": "处置记录", "transfers": "划转记录"},
        "tags": ["国有企业审计", "资产监管"],
    },
    "executive_perks_check": {
        "file": "soe/executive_perks_check.py",
        "function": "check_executive_perks",
        "description": "国企负责人履职待遇六维合规校验（薪酬/用车/住房/通讯/兼职/培训）",
        "params": {"executives": "负责人列表", "limits": "自定义限额"},
        "tags": ["国有企业审计", "巡视巡察"],
    },
    "mixed_reform_asset_check": {
        "file": "soe/mixed_reform_asset_check.py",
        "function": "check_mixed_reform_assets",
        "description": "混合所有制改革资产流失检测",
        "params": {"reforms": "混改项目", "related_party_db": "关联方名单"},
        "tags": ["国有企业审计", "混改监督"],
    },

    # ── P0: 内控制度审计 ──
    "coso_five_elements": {
        "file": "internal_control/coso_five_elements.py",
        "function": "evaluate_coso_coverage",
        "description": "COSO五要素制度覆盖度评估（17项原则80+关注点）",
        "params": {"documents": "制度文件列表"},
        "tags": ["内控制度审计", "制度体系建设"],
    },
    "segregation_duties_check": {
        "file": "internal_control/segregation_duties_check.py",
        "function": "detect_segregation_duties_conflicts",
        "description": "不相容职务分离冲突检测（六大职务对）",
        "params": {"authorization_matrix": "授权矩阵", "business_logs": "业务日志"},
        "tags": ["内控制度审计", "岗位权限"],
    },
    "walkthrough_test_engine": {
        "file": "internal_control/walkthrough_test_engine.py",
        "function": "run_walkthrough_test",
        "description": "穿行测试自动化引擎",
        "params": {"process_definition": "流程定义", "transaction_samples": "交易样本"},
        "tags": ["内控制度审计", "业务合规"],
    },
    "ic_deficiency_grading": {
        "file": "internal_control/ic_deficiency_grading.py",
        "function": "grade_deficiencies",
        "description": "内控缺陷分级模型（定量+定性双维，重大/重要/一般三级）",
        "params": {"deficiencies": "缺陷清单"},
        "tags": ["内控制度审计", "内控评价"],
    },

    # ── P1: 工程竣工财务决算 ──
    "four_stage_penetration": {
        "file": "engineering_completion/all_tools.py",
        "function": "four_stage_penetration",
        "description": "四阶段穿透比对（概算→预算→结算→决算）",
        "params": {"estimate": "概算", "budget": "预算", "settlement": "结算", "final_accounts": "决算"},
        "tags": ["工程竣工决算", "工程造价"],
    },
    "apportioned_investment_check": {
        "file": "engineering_completion/all_tools.py",
        "function": "apportioned_investment_check",
        "description": "待摊投资分摊合理性校验",
        "params": {"apportioned_items": "待摊项目", "asset_list": "资产清单"},
        "tags": ["工程竣工决算", "基建财务"],
    },
    "delivery_asset_reconciliation": {
        "file": "engineering_completion/all_tools.py",
        "function": "delivery_asset_reconciliation",
        "description": "交付使用资产-竣工决算勾稽",
        "params": {"delivery_list": "交付清单", "final_accounts": "决算报表"},
        "tags": ["工程竣工决算", "资产移交"],
    },

    # ── P1: 经责审计+绩效+专项债 ──
    "tenure_kpi_comparison": {
        "file": "economic_responsibility/all_tools.py",
        "function": "tenure_kpi_comparison",
        "description": "任期指标全景对比（绝对值+排名+增速+异常跳跃+同业对标）",
        "params": {"baseline_year": "任前基准", "final_year": "任期结束", "annual_data": "年度数据", "peer_benchmarks": "同业对标"},
        "tags": ["经济责任审计", "任期评价"],
    },
    "natural_resource_audit": {
        "file": "economic_responsibility/all_tools.py",
        "function": "natural_resource_audit",
        "description": "自然资源资产离任审计模型",
        "params": {"resources": "资源数据", "red_lines": "红线标准"},
        "tags": ["经济责任审计", "自然资源"],
    },
    "multi_source_scoring": {
        "file": "economic_responsibility/all_tools.py",
        "function": "multi_source_scoring",
        "description": "多源数据融合绩效评分（财政+业务+第三方+满意度）",
        "params": {"fiscal_data": "财政数据", "business_data": "业务数据", "weights": "权重配置"},
        "tags": ["绩效评价", "结果应用"],
    },
    "performance_benchmark": {
        "file": "economic_responsibility/all_tools.py",
        "function": "performance_benchmark",
        "description": "同类项目绩效对比分析（Z-Score异常检测+标杆识别）",
        "params": {"projects": "项目列表"},
        "tags": ["绩效评价", "横向对比"],
    },
    "revenue_coverage_calc": {
        "file": "economic_responsibility/all_tools.py",
        "function": "revenue_coverage_calc",
        "description": "专项债项目收益覆盖率测算（DCF折现+1.1倍底线）",
        "params": {"projected_revenues": "预期收益", "discount_rate": "折现率", "debt_service": "偿债计划"},
        "tags": ["专项债审计", "收益测算"],
    },
    "negative_list_scanner": {
        "file": "economic_responsibility/all_tools.py",
        "function": "negative_list_scanner",
        "description": "专项债资金使用负面清单自动扫描",
        "params": {"expenditures": "支出明细"},
        "tags": ["专项债审计", "资金合规"],
    },
    "progress_disbursement_match": {
        "file": "economic_responsibility/all_tools.py",
        "function": "progress_disbursement_match",
        "description": "项目进度-资金拨付进度匹配分析",
        "params": {"progress_reports": "进度报告", "disbursement_records": "拨付记录"},
        "tags": ["专项债审计", "工程审计"],
    },

    # ── P1补充: 收支审计+工程结算 ──
    "non_tax_revenue_completeness": {
        "file": "settlement/all_tools.py",
        "function": "non_tax_revenue_completeness",
        "description": "非税收入完整性校验",
        "params": {"receivable_records": "应收记录", "actual_collections": "实际征缴"},
        "tags": ["收支审计", "非税收入"],
    },
    "revenue_expenditure_two_lines": {
        "file": "settlement/all_tools.py",
        "function": "revenue_expenditure_two_lines",
        "description": "收支两条线合规检测（截留+坐支+应缴未缴）",
        "params": {"revenue_records": "收入记录", "expenditure_records": "支出记录"},
        "tags": ["收支审计", "财政纪律"],
    },
    "boq_vs_actual_quantity_check": {
        "file": "settlement/all_tools.py",
        "function": "boq_vs_actual_quantity_check",
        "description": "工程量清单量vs报审量偏差检测",
        "params": {"boq_items": "清单项", "actual_quantities": "报审量", "tolerance_pct": "容忍度"},
        "tags": ["工程结算", "清单编制"],
    },
    "unit_price_compliance_check": {
        "file": "settlement/all_tools.py",
        "function": "unit_price_compliance_check",
        "description": "综合单价套用合规检测（定额对标+历史价格对标）",
        "params": {"claimed_prices": "申报单价", "quota_database": "定额库", "historical_prices": "历史价格"},
        "tags": ["工程结算", "造价审计"],
    },
    "change_order_reasonableness": {
        "file": "settlement/all_tools.py",
        "function": "change_order_reasonableness",
        "description": "变更签证合理性三维评分（理由/量/价）",
        "params": {"change_orders": "变更记录", "contract_amount": "合同总额"},
        "tags": ["工程结算", "变更管理"],
    },

    # ── P2: 司法+监督+清单编制 ──
    "fund_trace_visualizer": {
        "file": "judicial/all_tools.py",
        "function": "fund_trace_visualizer",
        "description": "资金追踪网络分析（司法标准，中转账户+终点账户识别）",
        "params": {"transactions": "交易记录", "target_account": "目标账户", "max_depth": "追踪深度"},
        "tags": ["司法审计", "资金追踪"],
    },
    "loss_quantification_model": {
        "file": "judicial/all_tools.py",
        "function": "loss_quantification_model",
        "description": "损失金额计算模型（虚增成本/虚减收入/非公允/侵占四类）",
        "params": {"loss_items": "损失项"},
        "tags": ["司法审计", "损失量化"],
    },
    "risk_based_inspection_planner": {
        "file": "judicial/all_tools.py",
        "function": "risk_based_inspection_planner",
        "description": "风险导向检查计划生成（历史问题+资金规模+政策优先级三维排序）",
        "params": {"history_issues": "历史问题", "fund_distribution": "资金分布", "policy_priorities": "政策优先级"},
        "tags": ["监督检查", "检查计划"],
    },
    "rectification_tracker": {
        "file": "judicial/all_tools.py",
        "function": "rectification_tracker",
        "description": "整改销号管理+同类问题跨项目归因",
        "params": {"issues": "问题清单", "rectification_reports": "整改报告", "reference_date": "参考日期"},
        "tags": ["监督检查", "整改跟踪"],
    },
    "boq_omission_detector": {
        "file": "judicial/all_tools.py",
        "function": "boq_omission_detector",
        "description": "工程量清单漏项检测",
        "params": {"design_items": "设计内容", "boq_items": "清单项"},
        "tags": ["清单编制", "漏项检测"],
    },
    "unit_price_benchmark": {
        "file": "judicial/all_tools.py",
        "function": "unit_price_benchmark",
        "description": "综合单价合理性多维度对比（同期同类项目对标）",
        "params": {"current_prices": "当前报价", "historical_prices": "历史价格", "max_deviation_pct": "最大偏离"},
        "tags": ["清单编制", "单价审核"],
    },

    # ── P2: 财政评审+全过程咨询 ──
    "estimate_reasonableness": {
        "file": "fiscal_review/all_tools.py",
        "function": "estimate_reasonableness",
        "description": "概算合理性评审模型（建设标准+行业造价双重对标）",
        "params": {"estimate": "概算数据", "construction_standards": "建设标准", "cost_index": "造价指数"},
        "tags": ["财政评审", "概算审核"],
    },
    "investment_control_evaluation": {
        "file": "fiscal_review/all_tools.py",
        "function": "investment_control_evaluation",
        "description": "投资控制效果评价（概/预/结/决四阶段管控效果）",
        "params": {"projects": "项目数据"},
        "tags": ["财政评审", "投资管控"],
    },
    "evm_auto_analyzer": {
        "file": "fiscal_review/all_tools.py",
        "function": "evm_auto_analyzer",
        "description": "挣值管理(EVM)自动分析（SPI/CPI/EAC/VAC+趋势预测）",
        "params": {"plan_data": "计划数据(PV/BAC)", "actual_data": "实际数据(EV/AC)"},
        "tags": ["全过程咨询", "项目管理"],
    },
    "contract_performance_monitor": {
        "file": "fiscal_review/all_tools.py",
        "function": "contract_performance_monitor",
        "description": "合同履约风险动态监测（里程碑+人员+材料+变更膨胀）",
        "params": {"contracts": "合同列表", "reference_date": "参考日期"},
        "tags": ["全过程咨询", "合同管理"],
    },
    "document_chain_trace": {
        "file": "fiscal_review/all_tools.py",
        "function": "document_chain_trace",
        "description": "全过程文档链自动化追溯（5阶段×必需文档+时间逻辑+交叉引用）",
        "params": {"documents": "文档列表", "required_docs_per_phase": "必需文档配置"},
        "tags": ["全过程咨询", "文档管理"],
    },
    "audit_plan_generator": {
        "file": "fiscal_review/all_tools.py",
        "function": "audit_plan_generator",
        "description": "专项审计方案自动生成器（工具推荐+抽样策略+历史问题聚焦）",
        "params": {"audit_objective": "审计目标", "fund_amount": "资金规模", "history_issues": "历史问题"},
        "tags": ["专项审计", "方案编制"],
    },
}


# ── MCP工具动态加载 ────────────────────────────────────

def _load_tool_module(tool_name: str):
    """动态加载工具模块"""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"未注册的工具: {tool_name}")

    file_path = os.path.join(TOOLS_DIR, TOOL_REGISTRY[tool_name]["file"])
    module_name = f"audit_tool_{tool_name}"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"无法加载: {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP调用入口。通过handle_request或直接函数调用。

    Args:
        tool_name: 工具名称（与TOOL_REGISTRY中的key一致）
        params: 参数字典
    """
    if tool_name not in TOOL_REGISTRY:
        return {"status": "error", "data": None, "summary": f"未知工具: {tool_name}"}

    try:
        module = _load_tool_module(tool_name)
        func_name = TOOL_REGISTRY[tool_name]["function"]
        func = getattr(module, func_name)

        # 优先使用 handle_request 接口
        if hasattr(module, "handle_request"):
            return module.handle_request(func_name, params)
        else:
            return func(**params)

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"工具调用异常({tool_name}): {str(e)}"}


def list_tools(filter_tags: list = None) -> list:
    """列出所有注册的工具"""
    tools = []
    for name, info in TOOL_REGISTRY.items():
        if filter_tags:
            if not any(tag in info.get("tags", []) for tag in filter_tags):
                continue
        tools.append({
            "name": name,
            "description": info["description"],
            "params": info["params"],
            "tags": info["tags"],
        })
    return tools


def get_tools_by_tag(tag: str) -> list:
    """按标签获取工具列表"""
    return list_tools(filter_tags=[tag])


def get_tool_count() -> int:
    return len(TOOL_REGISTRY)


# ─── MCP JSON-RPC 入口 ─────────────────────────────────

def handle_mcp_request(method: str, params: dict) -> dict:
    """
    统一的MCP JSON-RPC入口。

    支持的方法：
    - tools/list: 列出所有工具
    - tools/call: 调用指定工具
    - tools/tags: 按标签查询工具
    """
    if method == "tools/list":
        tags = params.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        return {"status": "success", "data": {"tools": list_tools(tags), "total": get_tool_count()}}

    elif method == "tools/call":
        tool_name = params.get("tool", "")
        tool_params = params.get("params", {})
        return call_tool(tool_name, tool_params)

    elif method == "tools/tags":
        tag = params.get("tag", "")
        return {"status": "success", "data": {"tools": get_tools_by_tag(tag)}}

    elif method == "tools/stats":
        # 按标签统计
        from collections import Counter
        all_tags = []
        for info in TOOL_REGISTRY.values():
            all_tags.extend(info.get("tags", []))
        tag_counts = Counter(all_tags)
        return {"status": "success", "data": {
            "total_tools": get_tool_count(),
            "by_tag": dict(tag_counts.most_common()),
        }}

    else:
        return {"status": "error", "data": None, "summary": f"不支持的MCP方法: {method}"}


if __name__ == "__main__":
    print("=" * 60)
    print("  融策审计16场景算法工具箱 — MCP服务")
    print("=" * 60)
    print(f"  注册工具: {get_tool_count()} 个")
    print(f"  覆盖场景: 16 个")
    print()

    # 按标签统计
    result = handle_mcp_request("tools/stats", {})
    print("按审计场景分布:")
    for tag, count in sorted(result["data"]["by_tag"].items()):
        print(f"  {tag}: {count}个工具")

    # 试调用一个工具
    test_result = call_tool("multi_source_scoring", {
        "fiscal_data": {"产出数量": 90, "成本控制": 75},
        "business_data": {"服务覆盖": 88},
    })
    print(f"\nMCP调用测试: multi_source_scoring → {test_result['summary']}")

    print(f"\n✅ MCP服务就绪，{get_tool_count()}个工具已注册")
