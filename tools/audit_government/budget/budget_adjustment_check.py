"""
预算调整程序合规检测 — Budget Adjustment Compliance Checker

核心功能：检测预算调整是否经过法定审批程序，识别违规调整。
适用场景：预算执行审计、财政纪律检查。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Any, Optional


# 审批层级-金额阈值映射
APPROVAL_THRESHOLDS = [
    (500000, "部门审批"),
    (5000000, "政府审批（常务会议）"),
    (float("inf"), "人大审批（人大常委会）"),
]

# 审批层级-最低天数（公告/审议需要的时间，用于检测"闪电审批"）
APPROVAL_MIN_DAYS = {
    "部门审批": 1,
    "政府审批（常务会议）": 5,
    "人大审批（人大常委会）": 15,
}


def get_required_approval_level(amount: float) -> str:
    """根据调整金额返回所需的审批层级"""
    for threshold, level in APPROVAL_THRESHOLDS:
        if amount <= threshold:
            return level
    return "人大审批（人大常委会）"


def check_budget_adjustment_compliance(
    adjustment_records: List[Dict[str, Any]],
    *,
    budget_total: Optional[float] = None,
    single_adjust_cap_pct: float = 30.0,
) -> Dict[str, Any]:
    """
    预算调整程序合规检测。

    Args:
        adjustment_records: 调整记录列表，每项格式:
            {
                "adjust_id": str,
                "adjust_date": str(YYYY-MM-DD),
                "amount": float,
                "original_budget": float,
                "approval_date": str(YYYY-MM-DD) or None,
                "approval_level": str or None,
                "approval_doc_exists": bool,
                "dept": str,
                "reason": str,
            }
        budget_total: 预算总额(用于计算调整占比)
        single_adjust_cap_pct: 单次调整占原预算比例上限(默认30%)

    Returns:
        {
            "status": "success"/"error",
            "data": {
                "violations": [...],     # 违规调整
                "warnings": [...],       # 需关注的调整
                "compliant": [...],      # 合规调整
                "total_adjustments": int,
                "total_amount": float,
                "violation_rate": float,
                "risk_summary": dict,
            },
            "summary": str
        }
    """
    try:
        violations: List[Dict] = []
        warnings: List[Dict] = []
        compliant: List[Dict] = []
        total_amount = 0.0

        for rec in adjustment_records:
            adjust_id = rec.get("adjust_id", "")
            amount = float(rec.get("amount", 0))
            original = float(rec.get("original_budget", 0))
            adjust_date = rec.get("adjust_date", "")
            approval_date = rec.get("approval_date") or ""
            approval_doc_exists = bool(rec.get("approval_doc_exists", False))
            actual_level = rec.get("approval_level", "") or ""
            dept = rec.get("dept", "")
            reason = rec.get("reason", "")

            total_amount += amount
            required_level = get_required_approval_level(amount)
            issues: List[str] = []
            risk_items: List[str] = []

            # 检测1：审批文档存在性
            if not approval_doc_exists:
                issues.append("无审批文档")

            # 检测2：时间逻辑（先批后调）
            time_violation = False
            try:
                a_date = datetime.strptime(adjust_date, "%Y-%m-%d")
                if approval_date:
                    app_date = datetime.strptime(approval_date, "%Y-%m-%d")
                    if app_date > a_date:
                        time_violation = True
                        delta = (app_date - a_date).days
                        issues.append(f"审批日期晚于调整日期{delta}天（先调后批）")
            except ValueError:
                pass

            # 检测3：审批层级不匹配
            if actual_level and required_level != actual_level:
                # 判断是否越级
                level_order = {"部门审批": 1, "政府审批（常务会议）": 2, "人大审批（人大常委会）": 3}
                actual_rank = level_order.get(actual_level, 0)
                required_rank = level_order.get(required_level, 0)
                if actual_rank < required_rank:
                    issues.append(f"审批层级不匹配：需{required_level}，实际{actual_level}")
                else:
                    risk_items.append(f"审批层级高于最低要求（{required_level}→{actual_level}）")

            # 检测4：调整幅度异常
            if original > 0:
                adjust_pct = amount / original * 100
                if adjust_pct > single_adjust_cap_pct:
                    risk_items.append(f"调整幅度{adjust_pct:.1f}%超过{single_adjust_cap_pct}%关注线")

            # 检测5：预算总额占比
            if budget_total and budget_total > 0:
                total_pct = amount / budget_total * 100
                if total_pct > 10:
                    risk_items.append(f"单次调整占预算总额{total_pct:.1f}%")

            # 检测6：闪电审批
            if not time_violation and approval_date and adjust_date:
                try:
                    a_date = datetime.strptime(adjust_date, "%Y-%m-%d")
                    app_date = datetime.strptime(approval_date, "%Y-%m-%d")
                    delta = (a_date - app_date).days
                    min_days = APPROVAL_MIN_DAYS.get(required_level, 3)
                    if 0 <= delta < min_days:
                        risk_items.append(f"审批到调整仅间隔{delta}天，可能存在闪电审批")
                except ValueError:
                    pass

            record = {
                "adjust_id": adjust_id,
                "dept": dept,
                "amount": round(amount, 2),
                "original_budget": round(original, 2),
                "adjust_date": adjust_date,
                "approval_date": approval_date,
                "required_level": required_level,
                "actual_level": actual_level,
                "reason": reason,
                "issues": issues,
                "risks": risk_items,
                "risk_level": "high" if issues else ("medium" if risk_items else "low"),
            }

            if issues:
                violations.append(record)
            elif risk_items:
                warnings.append(record)
            else:
                compliant.append(record)

        total_count = len(adjustment_records)
        violation_rate = len(violations) / max(total_count, 1) * 100

        result = {
            "violations": violations,
            "warnings": warnings,
            "compliant": compliant,
            "total_adjustments": total_count,
            "total_amount": round(total_amount, 2),
            "violation_rate": round(violation_rate, 1),
            "risk_summary": {
                "violation_count": len(violations),
                "warning_count": len(warnings),
                "compliant_count": len(compliant),
                "top_issue": _top_issue(violations),
            },
        }

        # 综合风险判断
        if violation_rate > 30:
            risk_verdict = "预算调整管理存在重大缺陷，违规率超过30%"
        elif violation_rate > 10:
            risk_verdict = "预算调整管理有待加强，存在多项违规"
        elif len(warnings) > len(compliant):
            risk_verdict = "预算调整程序基本合规，但需关注多项风险信号"
        else:
            risk_verdict = "预算调整程序总体合规"

        summary = f"共{total_count}项调整：违规{len(violations)}项（{violation_rate:.0f}%）、关注{len(warnings)}项、合规{len(compliant)}项。{risk_verdict}"

        return {"status": "success", "data": result, "summary": summary}

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"检测异常: {str(e)}"}


def _top_issue(violations: List[Dict]) -> str:
    """统计最高频违规类型"""
    from collections import Counter
    all_issues = []
    for v in violations:
        all_issues.extend(v.get("issues", []))
    if not all_issues:
        return "无"
    counter = Counter(all_issues)
    return counter.most_common(1)[0][0]


def handle_request(method: str, params: dict) -> dict:
    if method == "check_budget_adjustment_compliance":
        return check_budget_adjustment_compliance(
            params.get("adjustment_records", []),
            budget_total=params.get("budget_total"),
            single_adjust_cap_pct=params.get("single_adjust_cap_pct", 30.0),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    records = [
        {"adjust_id": "ADJ001", "adjust_date": "2025-06-15", "amount": 300000, "original_budget": 1000000, "approval_date": "2025-06-10", "approval_level": "部门审批", "approval_doc_exists": True, "dept": "市教育局", "reason": "生均拨款标准调整"},
        {"adjust_id": "ADJ002", "adjust_date": "2025-08-20", "amount": 3000000, "original_budget": 10000000, "approval_date": "2025-09-01", "approval_level": "部门审批", "approval_doc_exists": False, "dept": "市交通局", "reason": "道路抢修追加"},
        {"adjust_id": "ADJ003", "adjust_date": "2025-09-10", "amount": 8000000, "original_budget": 20000000, "approval_date": "2025-09-05", "approval_level": "政府审批（常务会议）", "approval_doc_exists": True, "dept": "市住建局", "reason": "棚改追加"},
        {"adjust_id": "ADJ004", "adjust_date": "2025-11-01", "amount": 600000, "original_budget": 2000000, "approval_date": "2025-10-28", "approval_level": "部门审批", "approval_doc_exists": True, "dept": "市财政局", "reason": "追加公用经费"},
        {"adjust_id": "ADJ005", "adjust_date": "2025-12-15", "amount": 8000000, "original_budget": 15000000, "approval_date": "2025-12-16", "approval_level": "部门审批", "approval_doc_exists": True, "dept": "市农业农村局", "reason": "年末突击追加"},
    ]

    result = check_budget_adjustment_compliance(records, budget_total=100000000)
    print("=" * 60)
    print("预算调整程序合规检测")
    print("=" * 60)

    print(f"\n🔴 违规调整 ({len(result['data']['violations'])}项):")
    for v in result["data"]["violations"]:
        print(f"  {v['adjust_id']} ({v['dept']}): {v['amount']:,.0f}元 — {v['issues']}")

    print(f"\n🟡 需关注 ({len(result['data']['warnings'])}项):")
    for w in result["data"]["warnings"]:
        print(f"  {w['adjust_id']} ({w['dept']}): {w['amount']:,.0f}元 — {w['risks']}")

    print(f"\n违规率: {result['data']['violation_rate']}%")
    print(f"最高频问题: {result['data']['risk_summary']['top_issue']}")

    # ADJ002: 无审批文档 + 审批层级不足 → violation
    assert any(v["adjust_id"] == "ADJ002" for v in result["data"]["violations"])
    # ADJ005: 先调后批 + 审批层级不足 → violation
    assert any(v["adjust_id"] == "ADJ005" for v in result["data"]["violations"])
    # ADJ003: 审批层级匹配但有闪电审批风险 → warning
    assert any(w["adjust_id"] == "ADJ003" for w in result["data"]["warnings"])

    print("\n✅ 全部测试通过")
    print(result["summary"])
