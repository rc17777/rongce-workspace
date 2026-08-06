"""
结转结余合规判定 — Carryover Compliance Checker

核心功能：按《预算法》第四十二条判定结转结余资金的合规性。
适用场景：预算执行审计、财政决算审计、存量资金清理。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def check_carryover_compliance(
    project_ledger: Dict[str, Dict[str, Any]],
    *,
    reference_date: Optional[str] = None,
    carryover_limit_years: int = 2,
    zombie_years: int = 3,
    zombie_inactive_days: int = 730,
) -> Dict[str, Any]:
    """
    结转结余资金合规性检查。

    Args:
        project_ledger: 项目台账，{项目ID: {"name": str, "years_carried": int, "current_balance": float,
                          "original_amount": float, "last_used_date": str(YYYY-MM-DD),
                          "dept": str, "project_type": str}}
        reference_date: 参考日期(默认今天)
        carryover_limit_years: 结转年限上限(默认2年，依据预算法第42条)
        zombie_years: 僵尸项目判定结转年限
        zombie_inactive_days: 僵尸项目判定未使用天数

    Returns:
        {
            "status": "success"/"error",
            "data": {
                "overdue_carryover": [...],  # 超期未收回
                "zombie_projects": [...],     # 僵尸项目
                "healthy_projects": [...],    # 正常项目
                "total_should_recover": float,
                "total_balance": float,
                "project_count": int,
                "summary_stats": dict
            },
            "summary": str
        }
    """
    try:
        ref_date = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()

        overdue_carryover: List[Dict] = []
        zombie_projects: List[Dict] = []
        healthy_projects: List[Dict] = []
        total_should_recover = 0.0
        total_balance = 0.0

        for pid, proj in project_ledger.items():
            name = proj.get("name", pid)
            years = int(proj.get("years_carried", 0))
            balance = float(proj.get("current_balance", 0))
            original = float(proj.get("original_amount", 0))
            last_used = proj.get("last_used_date", "")
            dept = proj.get("dept", "")
            ptype = proj.get("project_type", "")

            total_balance += balance

            # 计算闲置天数
            inactive_days = 0
            if last_used:
                try:
                    last_date = datetime.strptime(last_used, "%Y-%m-%d")
                    inactive_days = (ref_date - last_date).days
                except ValueError:
                    pass

            is_overdue = years >= carryover_limit_years and balance > 0
            is_zombie = (years >= zombie_years or inactive_days >= zombie_inactive_days) and balance > 0

            project_info = {
                "project_id": pid,
                "name": name,
                "years_carried": years,
                "current_balance": round(balance, 2),
                "original_amount": round(original, 2),
                "last_used_date": last_used,
                "inactive_days": inactive_days,
                "dept": dept,
                "project_type": ptype,
                "usage_rate": round((1 - balance / original) * 100, 1) if original > 0 else 0,
            }

            if is_overdue:
                project_info["should_recover"] = round(balance, 2)
                project_info["legal_basis"] = f"《预算法》第四十二条：连续{years}年未用完的结转资金应收回财政"
                overdue_carryover.append(project_info)
                total_should_recover += balance

            if is_zombie:
                zombie_reason = []
                if years >= zombie_years:
                    zombie_reason.append(f"连续结转{years}年")
                if inactive_days >= zombie_inactive_days:
                    zombie_reason.append(f"闲置{inactive_days}天")
                project_info["zombie_reason"] = "；".join(zombie_reason)
                zombie_projects.append(project_info)

            if not is_overdue and not is_zombie:
                healthy_projects.append(project_info)

        # 排序：金额大的排前面
        overdue_carryover.sort(key=lambda x: x["should_recover"], reverse=True)
        zombie_projects.sort(key=lambda x: x["inactive_days"], reverse=True)

        result = {
            "overdue_carryover": overdue_carryover,
            "zombie_projects": zombie_projects,
            "healthy_projects": healthy_projects,
            "total_should_recover": round(total_should_recover, 2),
            "total_balance": round(total_balance, 2),
            "total_projects": len(project_ledger),
            "summary_stats": {
                "overdue_count": len(overdue_carryover),
                "zombie_count": len(zombie_projects),
                "healthy_count": len(healthy_projects),
                "overdue_ratio": round(len(overdue_carryover) / max(len(project_ledger), 1) * 100, 1),
            },
        }

        summary = f"共{len(project_ledger)}个项目：超期结转{len(overdue_carryover)}个（应收回{total_should_recover:,.2f}元）"
        if zombie_projects:
            summary += f"，僵尸项目{len(zombie_projects)}个"
        if len(overdue_carryover) > len(project_ledger) * 0.3:
            summary += " — ⚠️ 超期比例超过30%，存量资金管理存在系统性问题"

        return {"status": "success", "data": result, "summary": summary}

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"检查异常: {str(e)}"}


def handle_request(method: str, params: dict) -> dict:
    if method == "check_carryover_compliance":
        return check_carryover_compliance(
            params.get("project_ledger", {}),
            reference_date=params.get("reference_date"),
            carryover_limit_years=params.get("carryover_limit_years", 2),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    ledger = {
        "P001": {"name": "城区道路改造", "years_carried": 3, "current_balance": 2500000, "original_amount": 10000000, "last_used_date": "2023-06-15", "dept": "市交通局", "project_type": "基建"},
        "P002": {"name": "智慧校园建设", "years_carried": 1, "current_balance": 5000000, "original_amount": 20000000, "last_used_date": "2025-12-01", "dept": "市教育局", "project_type": "信息化"},
        "P003": {"name": "农村饮水安全", "years_carried": 2, "current_balance": 800000, "original_amount": 5000000, "last_used_date": "2024-08-20", "dept": "市水利局", "project_type": "民生"},
        "P004": {"name": "老旧小区电梯加装补贴", "years_carried": 4, "current_balance": 1200000, "original_amount": 3000000, "last_used_date": "2022-03-10", "dept": "市住建局", "project_type": "民生"},
        "P005": {"name": "政务云平台运维", "years_carried": 0, "current_balance": 3000000, "original_amount": 8000000, "last_used_date": "2026-07-01", "dept": "市数据局", "project_type": "运行维护"},
        "P006": {"name": "历史遗留项目-XX广场", "years_carried": 5, "current_balance": 5000000, "original_amount": 50000000, "last_used_date": "2021-01-01", "dept": "市住建局", "project_type": "基建"},
    }

    result = check_carryover_compliance(ledger, reference_date="2026-07-22")
    print("=" * 60)
    print("结转结余合规检查")
    print("=" * 60)
    print(f"项目总数: {result['data']['total_projects']}")
    print(f"结转资金总额: {result['data']['total_balance']:,.0f}元")

    print(f"\n🔴 超期结转（应收回财政）:")
    for p in result["data"]["overdue_carryover"]:
        print(f"  {p['name']}: 余额{p['current_balance']:,.0f}元，结转{p['years_carried']}年 — {p.get('legal_basis','')}")

    print(f"\n💀 僵尸项目:")
    for p in result["data"]["zombie_projects"]:
        print(f"  {p['name']}: 闲置{p['inactive_days']}天，{p.get('zombie_reason','')}")

    print(f"\n应收回合计: {result['data']['total_should_recover']:,.0f}元")
    print(f"超期比例: {result['data']['summary_stats']['overdue_ratio']}%")

    assert result["status"] == "success"
    assert len(result["data"]["overdue_carryover"]) >= 4  # P001/P003/P004/P006
    assert len(result["data"]["zombie_projects"]) >= 3
    assert result["data"]["total_should_recover"] > 5000000

    print("\n✅ 全部测试通过")
    print(result["summary"])
