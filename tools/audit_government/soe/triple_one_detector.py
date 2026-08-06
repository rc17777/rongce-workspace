"""
"三重一大"决策程序合规检测器 — Triple-One Decision Compliance Detector

核心功能：四检测器并行检查重大决策/重要人事/重大项目/大额资金的程序合规性。
适用场景：国有企业审计、经济责任审计、巡视巡察。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Any, Optional


# 大额资金审批层级映射
LARGE_FUND_THRESHOLDS = [
    (500000, "总经理办公会"),
    (2000000, "董事会"),
    (5000000, "董事会+国资委备案"),
    (20000000, "董事会+国资委审批+政府常务会"),
]


def get_required_approval(amount: float) -> str:
    for threshold, level in LARGE_FUND_THRESHOLDS:
        if amount <= threshold:
            return level
    return "董事会+国资委审批+政府常务会"


def check_triple_one_compliance(
    *,
    major_decisions: List[Dict] = None,
    personnel_appointments: List[Dict] = None,
    major_projects: List[Dict] = None,
    large_funds: List[Dict] = None,
) -> Dict[str, Any]:
    """
    "三重一大"决策程序合规四维检测。

    Args:
        major_decisions: 重大决策记录 [{id, description, dept, meeting_date, meeting_type, minutes_exist, signatories_complete, decision_content}]
        personnel_appointments: 重要人事任免 [{id, name, position, procedure_nodes: {动议/民主推荐/考察/讨论决定/任职: date}, dept}]
        major_projects: 重大项目 [{id, name, budget, feasibility_approval_date, project_approval_date, bidding_date, contract_date, dept}]
        large_funds: 大额资金 [{id, name, amount, approval_level, board_meeting_date, sasac_filing_date, payment_date, dept}]

    Returns:
        四维合规评分 + 综合风险报告
    """
    try:
        results = {}
        total_issues = 0
        total_checks = 0

        if major_decisions:
            r = _check_major_decisions(major_decisions)
            results["major_decisions"] = r
            total_issues += r["issue_count"]
            total_checks += len(major_decisions)

        if personnel_appointments:
            r = _check_personnel(personnel_appointments)
            results["personnel_appointments"] = r
            total_issues += r["issue_count"]
            total_checks += len(personnel_appointments)

        if major_projects:
            r = _check_projects(major_projects)
            results["major_projects"] = r
            total_issues += r["issue_count"]
            total_checks += len(major_projects)

        if large_funds:
            r = _check_funds(large_funds)
            results["large_funds"] = r
            total_issues += r["issue_count"]
            total_checks += len(large_funds)

        compliance_rate = (1 - total_issues / max(total_checks, 1)) * 100
        if compliance_rate >= 90:
            verdict = "三重一大决策程序总体合规"
        elif compliance_rate >= 70:
            verdict = "三重一大决策程序存在缺陷，需整改"
        elif compliance_rate >= 50:
            verdict = "三重一大决策程序存在重大缺陷"
        else:
            verdict = "三重一大决策程序严重违规"

        return {
            "status": "success",
            "data": {
                "categories": results,
                "total_items": total_checks,
                "total_issues": total_issues,
                "compliance_rate": round(compliance_rate, 1),
                "verdict": verdict,
                "all_issues": _collect_all_issues(results),
            },
            "summary": f"{verdict}（{total_checks}项决策中{total_issues}项存在问题，合规率{compliance_rate:.0f}%）"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"检测异常: {str(e)}"}


def _check_major_decisions(decisions: List[Dict]) -> Dict:
    """检测重大决策：纪要存在性 + 签字齐备性"""
    issues = []
    for d in decisions:
        item_issues = []
        if not d.get("minutes_exist", False):
            item_issues.append("缺少决策会议纪要")
        if not d.get("signatories_complete", False):
            item_issues.append("纪要签字不齐备")

        # 决策会议类型检查
        meeting_type = d.get("meeting_type", "")
        if meeting_type not in ["党委会", "董事会", "总经理办公会", "党政联席会"]:
            item_issues.append(f"决策会议类型异常: {meeting_type}")

        if item_issues:
            issues.append({
                "id": d.get("id", ""),
                "description": d.get("description", "")[:100],
                "dept": d.get("dept", ""),
                "issues": item_issues,
                "risk": "high" if len(item_issues) >= 2 else "medium",
            })
    return {
        "item_count": len(decisions),
        "issue_count": len(issues),
        "issues": issues,
        "compliance_rate": round((1 - len(issues) / max(len(decisions), 1)) * 100, 1),
    }


def _check_personnel(appointments: List[Dict]) -> Dict:
    """检测重要人事任免：五步程序节点完整性"""
    required_steps = ["动议", "民主推荐", "考察", "讨论决定", "任职"]
    issues = []

    for a in appointments:
        item_issues = []
        procedures = a.get("procedure_nodes", {})

        for step in required_steps:
            step_date = procedures.get(step)
            if not step_date:
                item_issues.append(f"缺少'{step}'环节记录")
                continue

        # 时间逻辑检查
        dates_available = {}
        for step in required_steps:
            d = procedures.get(step)
            if d:
                try:
                    dates_available[step] = datetime.strptime(d, "%Y-%m-%d")
                except ValueError:
                    item_issues.append(f"'{step}'日期格式错误: {d}")

        step_order = ["动议", "民主推荐", "考察", "讨论决定", "任职"]
        for i in range(1, len(step_order)):
            prev = step_order[i-1]
            curr = step_order[i]
            if prev in dates_available and curr in dates_available:
                if dates_available[curr] < dates_available[prev]:
                    item_issues.append(f"'{prev}'日期晚于'{curr}'日期，程序倒置")

        if item_issues:
            issues.append({
                "id": a.get("id", ""),
                "name": a.get("name", ""),
                "position": a.get("position", ""),
                "issues": item_issues,
                "risk": "high" if any("缺少" in i for i in item_issues) else "medium",
            })

    return {
        "item_count": len(appointments),
        "issue_count": len(issues),
        "issues": issues,
        "compliance_rate": round((1 - len(issues) / max(len(appointments), 1)) * 100, 1),
    }


def _check_projects(projects: List[Dict]) -> Dict:
    """检测重大项目：时间逻辑链（可研→立项→招标→签约）"""
    time_chain = [
        ("feasibility_approval_date", "可研批复", "project_approval_date", "项目立项"),
        ("project_approval_date", "项目立项", "bidding_date", "招标"),
        ("bidding_date", "招标", "contract_date", "签约"),
    ]
    issues = []

    for p in projects:
        item_issues = []

        # 检查关键字段
        for field, label in [("feasibility_approval_date", "可研批复"), ("project_approval_date", "项目立项"),
                              ("bidding_date", "招标"), ("contract_date", "签约")]:
            if not p.get(field):
                item_issues.append(f"缺少{label}记录")

        # 时间逻辑
        for prev_field, prev_label, curr_field, curr_label in time_chain:
            prev_val = p.get(prev_field)
            curr_val = p.get(curr_field)
            if prev_val and curr_val:
                try:
                    prev_date = datetime.strptime(prev_val, "%Y-%m-%d")
                    curr_date = datetime.strptime(curr_val, "%Y-%m-%d")
                    if curr_date < prev_date:
                        item_issues.append(f"{curr_label}日期早于{prev_label}日期，时间逻辑错误")
                    elif (curr_date - prev_date).days < 1:
                        item_issues.append(f"{prev_label}到{curr_label}间隔不足1天，可能流程走过场")
                except ValueError:
                    pass

        if item_issues:
            issues.append({
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "budget": p.get("budget", 0),
                "issues": item_issues,
                "risk": "high" if any("缺少" in i or "逻辑错误" in i for i in item_issues) else "medium",
            })

    return {
        "item_count": len(projects),
        "issue_count": len(issues),
        "issues": issues,
        "compliance_rate": round((1 - len(issues) / max(len(projects), 1)) * 100, 1),
    }


def _check_funds(funds: List[Dict]) -> Dict:
    """检测大额资金：审批层级匹配 + 董事会/国资委备案时序"""
    issues = []

    for f in funds:
        item_issues = []
        amount = float(f.get("amount", 0))
        actual_level = f.get("approval_level", "")
        board_date = f.get("board_meeting_date", "")
        sasac_date = f.get("sasac_filing_date", "")
        payment_date = f.get("payment_date", "")

        required = get_required_approval(amount)
        if actual_level and required != actual_level:
            level_order = {
                "总经理办公会": 1, "董事会": 2, "董事会+国资委备案": 3, "董事会+国资委审批+政府常务会": 4
            }
            if level_order.get(actual_level, 0) < level_order.get(required, 0):
                item_issues.append(f"审批层级不足：需{required}，实际{actual_level}")

        # 先批后付
        if board_date and payment_date:
            try:
                bd = datetime.strptime(board_date, "%Y-%m-%d")
                pd = datetime.strptime(payment_date, "%Y-%m-%d")
                if pd < bd:
                    item_issues.append(f"付款日期早于董事会审批日期，先付后批")
            except ValueError:
                pass

        # 国资委备案时序
        if "国资委备案" in required or "国资委审批" in required:
            if not sasac_date:
                item_issues.append(f"需国资委备案/审批但无备案记录")

        if item_issues:
            issues.append({
                "id": f.get("id", ""),
                "name": f.get("name", ""),
                "amount": amount,
                "required_level": required,
                "actual_level": actual_level,
                "issues": item_issues,
                "risk": "high",
            })

    return {
        "item_count": len(funds),
        "issue_count": len(issues),
        "issues": issues,
        "compliance_rate": round((1 - len(issues) / max(len(funds), 1)) * 100, 1),
    }


def _collect_all_issues(results: Dict) -> List[Dict]:
    """汇总所有问题"""
    all_issues = []
    for category_name, cat_data in results.items():
        for iss in cat_data.get("issues", []):
            iss["category"] = category_name
            all_issues.append(iss)
    return sorted(all_issues, key=lambda x: 0 if x.get("risk") == "high" else 1)


def handle_request(method: str, params: dict) -> dict:
    if method == "check_triple_one_compliance":
        return check_triple_one_compliance(
            major_decisions=params.get("major_decisions"),
            personnel_appointments=params.get("personnel_appointments"),
            major_projects=params.get("major_projects"),
            large_funds=params.get("large_funds"),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    # 测试数据
    decisions = [
        {"id": "D001", "description": "收购XX公司51%股权", "dept": "投资部", "meeting_date": "2025-03-15", "meeting_type": "董事会", "minutes_exist": True, "signatories_complete": True},
        {"id": "D002", "description": "出售闲置地块", "dept": "资产部", "meeting_date": "2025-06-01", "meeting_type": "总经理办公会", "minutes_exist": False, "signatories_complete": False},
        {"id": "D003", "description": "设立海外子公司", "dept": "战略部", "meeting_date": "2025-09-10", "meeting_type": "部门会", "minutes_exist": True, "signatories_complete": True},
    ]

    personnel = [
        {"id": "P001", "name": "张某", "position": "副总经理", "procedure_nodes": {"动议": "2025-01-10", "民主推荐": "2025-01-15", "考察": "2025-01-20", "讨论决定": "2025-01-25", "任职": "2025-02-01"}},
        {"id": "P002", "name": "李某", "position": "财务总监", "procedure_nodes": {"动议": "2025-05-01", "考察": "2025-05-15", "任职": "2025-06-01"}},
    ]

    projects = [
        {"id": "M001", "name": "新厂区建设", "budget": 50000000, "feasibility_approval_date": "2025-01-15", "project_approval_date": "2025-03-01", "bidding_date": "2025-03-02", "contract_date": "2025-05-10"},
        {"id": "M002", "name": "设备采购", "budget": 3000000, "feasibility_approval_date": None, "project_approval_date": "2025-06-01", "bidding_date": "2025-06-15", "contract_date": "2025-07-01"},
    ]

    funds = [
        {"id": "F001", "name": "股权投资", "amount": 10000000, "approval_level": "董事会", "board_meeting_date": "2025-03-01", "sasac_filing_date": "", "payment_date": "2025-02-15"},
        {"id": "F002", "name": "设备采购款", "amount": 800000, "approval_level": "总经理办公会", "board_meeting_date": "2025-04-10", "sasac_filing_date": None, "payment_date": "2025-04-20"},
    ]

    result = check_triple_one_compliance(
        major_decisions=decisions,
        personnel_appointments=personnel,
        major_projects=projects,
        large_funds=funds,
    )

    print("=" * 60)
    print("三重一大决策程序合规检测")
    print("=" * 60)
    for cat, data in result["data"]["categories"].items():
        name = {"major_decisions": "重大决策", "personnel_appointments": "重要人事", "major_projects": "重大项目", "large_funds": "大额资金"}
        print(f"\n{name.get(cat, cat)}: {data['item_count']}项，问题{data['issue_count']}项，合规率{data['compliance_rate']}%")
        for iss in data["issues"]:
            print(f"  [{iss.get('risk','')}] {iss.get('id','')}: {'; '.join(iss['issues'])}")

    print(f"\n综合: {result['summary']}")

    assert result["status"] == "success"
    assert result["data"]["total_issues"] >= 4
    # D002: 缺少纪要
    d002 = next((i for i in result["data"]["all_issues"] if i.get("id") == "D002"), None)
    assert d002 and "缺少决策会议纪要" in d002["issues"]
    # F001: 先付后批
    f001 = next((i for i in result["data"]["all_issues"] if i.get("id") == "F001"), None)
    assert f001 and any("先付后批" in iss for iss in f001["issues"])

    print("\n✅ 全部测试通过")
