"""
不相容职务分离检测 — Segregation of Duties Checker

核心功能：检测六大不相容职务对（申请/审批/执行/记录/保管/检查）的冲突。
适用场景：内控制度审计、岗位权限合规检查。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from typing import Dict, List, Any, Set, Tuple

# 六大不相容职务对（冲突矩阵）
INCOMPATIBLE_PAIRS = [
    ("申请", "审批"),  # 不能自己申请自己批
    ("申请", "执行"),  # 不能自己申请自己做
    ("审批", "执行"),  # 不能自己批了自己做
    ("执行", "记录"),  # 不能自己做了自己记账
    ("保管", "记录"),  # 不能自己管着东西又记账
    ("保管", "检查"),  # 不能自己管着又自己检查
    ("执行", "检查"),  # 不能自己执行又自己检查
    ("记录", "检查"),  # 不能自己记账又自己审计
]


def detect_segregation_duties_conflicts(
    authorization_matrix: List[Dict[str, Any]],
    business_logs: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    不相容职务分离冲突检测。

    Args:
        authorization_matrix: 授权矩阵 [{user_id, user_name, roles: [str], dept,
                               business_scopes: [str]}]
        business_logs: 业务日志 [{transaction_id, business_type, applicant_id, approver_id,
                        executor_id, recorder_id, custodian_id, inspector_id, date, amount}]

    Returns:
        冲突报告
    """
    try:
        conflicts: List[Dict] = []
        conflict_stats: Dict[str, int] = {}

        if not business_logs:
            return {
                "status": "success",
                "data": {
                    "conflicts": [],
                    "total_transactions": 0,
                    "conflicted_transactions": 0,
                    "conflict_rate": 0.0,
                    "high_risk_users": [],
                    "conflict_stats": {},
                },
                "summary": "无业务日志数据"
            }

        user_role_map = {a.get("user_id"): a for a in authorization_matrix}
        user_conflicts: Dict[str, int] = {}

        for log in business_logs:
            tx_id = log.get("transaction_id", "")
            # 提取各角色担任者
            actors = {
                "申请": log.get("applicant_id"),
                "审批": log.get("approver_id"),
                "执行": log.get("executor_id"),
                "记录": log.get("recorder_id"),
                "保管": log.get("custodian_id"),
                "检查": log.get("inspector_id"),
            }

            tx_conflicts = []
            for role_a, role_b in INCOMPATIBLE_PAIRS:
                user_a = actors.get(role_a)
                user_b = actors.get(role_b)
                if user_a and user_b and user_a == user_b:
                    # 同一个人担任了两个不相容职务
                    user_name = log.get(f"{role_a}_name", "") or log.get(f"{role_b}_name", "")
                    label = f"{role_a}+{role_b}于同一人"
                    tx_conflicts.append({
                        "conflict_type": label,
                        "user_id": user_a,
                        "user_name": user_name,
                        "role_a": role_a,
                        "role_b": role_b,
                    })
                    conflict_stats[label] = conflict_stats.get(label, 0) + 1

                    if user_a not in user_conflicts:
                        user_conflicts[user_a] = 0
                    user_conflicts[user_a] += 1

            if tx_conflicts:
                conflicts.append({
                    "transaction_id": tx_id,
                    "business_type": log.get("business_type", ""),
                    "date": log.get("date", ""),
                    "amount": log.get("amount", 0),
                    "conflicts": tx_conflicts,
                    "risk_level": "high" if len(tx_conflicts) >= 2 else "medium",
                })

        # 高风险用户
        high_risk_users = []
        for uid, count in sorted(user_conflicts.items(), key=lambda x: x[1], reverse=True):
            user_info = user_role_map.get(uid, {})
            high_risk_users.append({
                "user_id": uid,
                "user_name": user_info.get("user_name", uid),
                "dept": user_info.get("dept", ""),
                "roles": user_info.get("roles", []),
                "conflict_count": count,
                "risk_level": "严重" if count >= 10 else ("高度关注" if count >= 5 else "关注"),
            })

        conflict_rate = len(conflicts) / max(len(business_logs), 1) * 100

        return {
            "status": "success",
            "data": {
                "conflicts": conflicts,
                "total_transactions": len(business_logs),
                "conflicted_transactions": len(conflicts),
                "conflict_rate": round(conflict_rate, 1),
                "high_risk_users": high_risk_users,
                "conflict_stats": conflict_stats,
                "risk_verdict": "严重" if conflict_rate > 20 else ("需关注" if conflict_rate > 5 else "基本合规"),
            },
            "summary": f"共{len(business_logs)}笔业务，{len(conflicts)}笔存在不相容职务冲突（{conflict_rate:.1f}%），{len(high_risk_users)}名高风险用户"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"检测异常: {str(e)}"}


def handle_request(method: str, params: dict) -> dict:
    if method == "detect_segregation_duties_conflicts":
        return detect_segregation_duties_conflicts(
            params.get("authorization_matrix", []),
            params.get("business_logs"),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    auth = [
        {"user_id": "U001", "user_name": "张某", "roles": ["部门经理"], "dept": "财务部"},
        {"user_id": "U002", "user_name": "李某", "roles": ["会计"], "dept": "财务部"},
        {"user_id": "U003", "user_name": "王某", "roles": ["出纳"], "dept": "财务部"},
    ]

    logs = [
        {"transaction_id": "TX001", "business_type": "费用报销", "applicant_id": "U001", "approver_id": "U001", "executor_id": "U002", "recorder_id": "U002", "custodian_id": "U003", "inspector_id": "U003", "applicant_name": "张某", "date": "2025-03-15", "amount": 50000},
        {"transaction_id": "TX002", "business_type": "采购付款", "applicant_id": "U002", "approver_id": "U001", "executor_id": "U002", "recorder_id": "U002", "custodian_id": "U003", "inspector_id": "U001", "date": "2025-04-01", "amount": 200000},
        {"transaction_id": "TX003", "business_type": "费用报销", "applicant_id": "U001", "approver_id": "U002", "executor_id": "U003", "recorder_id": "U003", "custodian_id": "U003", "inspector_id": "U001", "date": "2025-05-10", "amount": 30000},
    ]

    result = detect_segregation_duties_conflicts(auth, logs)
    print("=" * 60)
    print("不相容职务分离检测")
    print("=" * 60)
    print(f"业务笔数: {result['data']['total_transactions']}")
    print(f"冲突笔数: {result['data']['conflicted_transactions']} ({result['data']['conflict_rate']}%)")
    print(f"风险评估: {result['data']['risk_verdict']}")

    for c in result["data"]["conflicts"]:
        print(f"\n  {c['transaction_id']} ({c['business_type']}, {c['amount']:,.0f}元):")
        for cc in c["conflicts"]:
            print(f"    - {cc['conflict_type']} ({cc['user_name']})")

    print(f"\n高风险用户:")
    for u in result["data"]["high_risk_users"]:
        print(f"  [{u['risk_level']}] {u['user_name']}: {u['conflict_count']}次冲突")

    # TX001: U001申请+审批，U002执行+记录
    tx001 = next(c for c in result["data"]["conflicts"] if c["transaction_id"] == "TX001")
    assert len(tx001["conflicts"]) >= 2
    # TX002: U002执行+记录
    tx002 = next(c for c in result["data"]["conflicts"] if c["transaction_id"] == "TX002")
    assert any("执行+记录" in cc["conflict_type"] for cc in tx002["conflicts"])

    print(f"\n{result['summary']}")
    print("\n✅ 全部测试通过")
