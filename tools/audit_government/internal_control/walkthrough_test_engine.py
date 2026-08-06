"""
穿行测试自动化引擎 — Walkthrough Test Engine

核心功能：选取典型交易样本，沿全流程逐步验证控制节点存在性和有效性。
适用场景：内控制度审计、业务合规检查。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional


CONTROL_RESULTS = ["存在且有效", "存在但无效", "不存在"]


def run_walkthrough_test(
    process_definition: Dict[str, Any],
    transaction_samples: List[Dict[str, Any]],
    *,
    control_evidence: Dict[str, List[str]] = None,
) -> Dict[str, Any]:
    """
    穿行测试自动化引擎。

    Args:
        process_definition: 流程定义 {process_name, steps: [{step_id, step_name, required_control,
                            control_type, expected_evidence_type, responsible_role}]}
        transaction_samples: 交易样本 [{sample_id, step_results: {step_id: {executed: bool, executor: str,
                            evidence_exists: bool, evidence_ref: str, date: str, comment: str}}}]
        control_evidence: 控制证据索引 {step_id: [evidence_doc_refs]}

    Returns:
        穿行测试报告
    """
    try:
        steps = process_definition.get("steps", [])
        if not steps:
            return {"status": "error", "data": None, "summary": "流程定义中无步骤"}

        test_results = []
        step_stats: Dict[str, Dict[str, int]] = {}

        # 初始化统计
        for step in steps:
            step_stats[step["step_id"]] = {r: 0 for r in CONTROL_RESULTS}

        for sample in transaction_samples:
            sample_id = sample.get("sample_id", "")
            step_results = sample.get("step_results", {})
            sample_details = []

            for step in steps:
                step_id = step["step_id"]
                sr = step_results.get(step_id, {})

                executed = sr.get("executed", False)
                evidence_exists = sr.get("evidence_exists", False)
                executor = sr.get("executor", "")

                # 判定控制状态
                if executed and evidence_exists:
                    status = "存在且有效"
                elif executed and not evidence_exists:
                    status = "存在但无效"
                else:
                    status = "不存在"

                step_stats[step_id][status] += 1

                # 检查执行人权限
                responsible = step.get("responsible_role", "")
                executor_role = sr.get("executor_role", "")
                authority_ok = executor_role == responsible if responsible and executor_role else None

                sample_details.append({
                    "step_id": step_id,
                    "step_name": step.get("step_name", ""),
                    "status": status,
                    "executor": executor,
                    "date": sr.get("date", ""),
                    "authority_ok": authority_ok,
                    "comment": sr.get("comment", ""),
                    "evidence_ref": sr.get("evidence_ref", ""),
                })

            # 计算本样本健康度
            good_steps = sum(1 for d in sample_details if d["status"] == "存在且有效")
            total_steps = len(sample_details)
            health = good_steps / max(total_steps, 1) * 100

            test_results.append({
                "sample_id": sample_id,
                "steps_detail": sample_details,
                "health_score": round(health, 1),
                "risk_level": "严重" if health < 50 else ("需关注" if health < 80 else "正常"),
                "break_points": [d for d in sample_details if d["status"] != "存在且有效"],
            })

        # 汇总每步统计
        step_summary = []
        for step in steps:
            sid = step["step_id"]
            stats = step_stats.get(sid, {})
            total = sum(stats.values())
            effective_rate = stats.get("存在且有效", 0) / max(total, 1) * 100
            step_summary.append({
                "step_id": sid,
                "step_name": step.get("step_name", ""),
                "effective_rate": round(effective_rate, 1),
                "total_samples": total,
                "detail": stats,
                "risk": "严重" if effective_rate < 50 else ("需关注" if effective_rate < 80 else "正常"),
            })

        # 整体评分
        overall_health = sum(t["health_score"] for t in test_results) / max(len(test_results), 1)

        return {
            "status": "success",
            "data": {
                "process_name": process_definition.get("process_name", ""),
                "test_results": test_results,
                "step_summary": step_summary,
                "overall_health": round(overall_health, 1),
                "verdict": "控制有效" if overall_health >= 80 else ("控制部分有效" if overall_health >= 50 else "控制存在重大缺陷"),
            },
            "summary": f"穿行测试：{len(transaction_samples)}个样本，整体健康度{overall_health:.1f}分，{sum(1 for t in test_results if t['risk_level']!='正常')}个样本存在异常"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"测试异常: {str(e)}"}


def detect_pattern_issues(test_results: List[Dict]) -> List[Dict]:
    """检测控制缺陷模式"""
    issues = []
    for tr in test_results:
        for bp in tr.get("break_points", []):
            if bp["status"] == "不存在":
                issues.append({
                    "pattern": "控制缺失",
                    "step": bp["step_name"],
                    "sample": tr["sample_id"],
                    "detail": f"关键控制点'{bp['step_name']}'未执行"
                })
            elif bp["status"] == "存在但无效":
                issues.append({
                    "pattern": "控制失效",
                    "step": bp["step_name"],
                    "sample": tr["sample_id"],
                    "detail": f"控制点'{bp['step_name']}'已执行但缺少有效证据"
                })
    return issues


def handle_request(method: str, params: dict) -> dict:
    if method == "run_walkthrough_test":
        return run_walkthrough_test(
            params.get("process_definition", {}),
            params.get("transaction_samples", []),
            control_evidence=params.get("control_evidence"),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    process = {
        "process_name": "采购付款流程",
        "steps": [
            {"step_id": "S01", "step_name": "采购申请", "required_control": "部门审批", "control_type": "授权审批", "responsible_role": "部门经理"},
            {"step_id": "S02", "step_name": "采购审批", "required_control": "分管领导审批", "control_type": "授权审批", "responsible_role": "分管领导"},
            {"step_id": "S03", "step_name": "验收入库", "required_control": "三方验收", "control_type": "资产保护", "responsible_role": "仓库管理员"},
            {"step_id": "S04", "step_name": "付款审批", "required_control": "财务审核", "control_type": "会计控制", "responsible_role": "财务负责人"},
        ]
    }

    samples = [
        {"sample_id": "SP001", "step_results": {
            "S01": {"executed": True, "executor": "张某", "executor_role": "部门经理", "evidence_exists": True, "date": "2025-06-01", "evidence_ref": "PR2025001"},
            "S02": {"executed": True, "executor": "李某", "executor_role": "分管领导", "evidence_exists": True, "date": "2025-06-03", "evidence_ref": "PO2025001"},
            "S03": {"executed": True, "executor": "王某", "executor_role": "仓库管理员", "evidence_exists": True, "date": "2025-06-10", "evidence_ref": "GRN2025001"},
            "S04": {"executed": True, "executor": "赵某", "executor_role": "财务负责人", "evidence_exists": True, "date": "2025-06-15", "evidence_ref": "PAY2025001"},
        }},
        {"sample_id": "SP002", "step_results": {
            "S01": {"executed": True, "executor": "刘某", "executor_role": "部门经理", "evidence_exists": False, "date": "2025-07-01"},
            "S02": {"executed": False, "executor": "", "executor_role": "", "evidence_exists": False, "date": ""},
            "S03": {"executed": True, "executor": "王某", "executor_role": "仓库管理员", "evidence_exists": True, "date": "2025-07-05", "evidence_ref": "GRN2025015"},
            "S04": {"executed": True, "executor": "赵某", "executor_role": "财务负责人", "evidence_exists": True, "date": "2025-07-10", "evidence_ref": "PAY2025015"},
        }},
        {"sample_id": "SP003", "step_results": {
            "S01": {"executed": True, "executor": "张某", "executor_role": "部门经理", "evidence_exists": True, "date": "2025-08-01", "evidence_ref": "PR2025040"},
            "S02": {"executed": True, "executor": "张某", "executor_role": "部门经理", "evidence_exists": True, "date": "2025-08-02", "evidence_ref": "PO2025040"},
            "S03": {"executed": True, "executor": "张某", "executor_role": "部门经理", "evidence_exists": False, "date": "2025-08-05"},
            "S04": {"executed": True, "executor": "赵某", "executor_role": "财务负责人", "evidence_exists": True, "date": "2025-08-10", "evidence_ref": "PAY2025040"},
        }},
    ]

    result = run_walkthrough_test(process, samples)
    print("=" * 60)
    print("穿行测试报告")
    print("=" * 60)
    print(f"流程: {result['data']['process_name']}")
    print(f"整体健康度: {result['data']['overall_health']}分 [{result['data']['verdict']}]")

    for tr in result["data"]["test_results"]:
        print(f"\n样本 {tr['sample_id']}: 健康度{tr['health_score']}% [{tr['risk_level']}]")
        if tr["break_points"]:
            print(f"  断裂点 ({len(tr['break_points'])}个):")
            for bp in tr["break_points"]:
                print(f"    - {bp['step_name']}: {bp['status']} (执行人: {bp['executor'] or '无'})")

    print(f"\n按步骤统计:")
    for ss in result["data"]["step_summary"]:
        print(f"  {ss['step_name']}: 有效率{ss['effective_rate']}% [{ss['risk']}]")

    # 断言
    assert result["data"]["overall_health"] < 90  # SP002和SP003有问题
    sp002 = next(t for t in result["data"]["test_results"] if t["sample_id"] == "SP002")
    assert len(sp002["break_points"]) >= 1

    print(f"\n{result['summary']}")
    print("\n✅ 全部测试通过")
