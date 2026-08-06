"""
国企负责人履职待遇合规校验 — Executive Perks Compliance Checker

核心功能：六维限额对标（薪酬/用车/住房/通讯/兼职/培训）。
适用场景：国有企业审计、巡视巡察、负责人经责审计。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from typing import Dict, List, Any


# 限额标准（可配置，基于《国有企业负责人履职待遇和业务支出管理办法》）
DEFAULT_LIMITS = {
    "salary": {"annual_cap": 600000, "bonus_ratio_cap": 0.3, "unit": "年"},
    "vehicle": {"purchase_cap": 250000, "annual_maintenance_cap": 30000, "unit": "辆"},
    "housing": {"rental_monthly_cap": 5000, "area_cap_sqm": 120, "unit": "月"},
    "communication": {"monthly_cap": 500, "unit": "月"},
    "part_time": {"max_positions": 2, "max_annual_income": 100000, "unit": "年"},
    "training": {"domestic_annual_cap": 50000, "overseas_annual_cap": 150000, "overseas_count_cap": 1, "unit": "年"},
}


def check_executive_perks(
    executives: List[Dict[str, Any]],
    *,
    limits: Dict = None,
) -> Dict[str, Any]:
    """
    六维履职待遇合规校验。

    Args:
        executives: 负责人列表 [{name, position, dept, salary: {annual, bonus_ratio}, vehicle: {purchase_price, annual_maintenance},
                    housing: {monthly_rental, area_sqm}, communication: {monthly_cost},
                    part_time: [{position, annual_income}], training: {domestic_annual, overseas_annual, overseas_count}}]
        limits: 自定义限额标准（默认使用 DEFAULT_LIMITS）

    Returns:
        {
            "status": "success",
            "data": {
                "executives": [...],  # 每人的超限情况
                "overall_stats": {...},  # 汇总统计
                "violation_details": [...],  # 所有超限明细
            },
            "summary": str
        }
    """
    try:
        if limits is None:
            limits = DEFAULT_LIMITS

        results = []
        all_violations = []
        total_violations = 0
        total_over_amount = 0.0
        person_violations = 0

        for exec_info in executives:
            name = exec_info.get("name", "")
            violations = []
            over_amount = 0.0

            # 1. 薪酬
            salary = exec_info.get("salary", {})
            annual_salary = float(salary.get("annual", 0))
            bonus_ratio = float(salary.get("bonus_ratio", 0))
            salary_cap = limits["salary"]["annual_cap"]
            bonus_cap = limits["salary"]["bonus_ratio_cap"]

            if annual_salary > salary_cap:
                excess = annual_salary - salary_cap
                violations.append({"dimension": "薪酬", "item": "年薪", "actual": annual_salary,
                                    "limit": salary_cap, "excess": excess, "unit": "元/年"})
                over_amount += excess
            if bonus_ratio > bonus_cap:
                violations.append({"dimension": "薪酬", "item": "绩效比例", "actual": f"{bonus_ratio*100:.0f}%",
                                    "limit": f"{bonus_cap*100:.0f}%", "excess": 0, "unit": ""})

            # 2. 用车
            vehicle = exec_info.get("vehicle", {})
            purchase = float(vehicle.get("purchase_price", 0))
            maint = float(vehicle.get("annual_maintenance", 0))
            if purchase > limits["vehicle"]["purchase_cap"]:
                excess = purchase - limits["vehicle"]["purchase_cap"]
                violations.append({"dimension": "用车", "item": "购车价格", "actual": purchase,
                                    "limit": limits["vehicle"]["purchase_cap"], "excess": excess, "unit": "元"})
                over_amount += excess
            if maint > limits["vehicle"]["annual_maintenance_cap"]:
                excess = maint - limits["vehicle"]["annual_maintenance_cap"]
                violations.append({"dimension": "用车", "item": "年度维保", "actual": maint,
                                    "limit": limits["vehicle"]["annual_maintenance_cap"], "excess": excess, "unit": "元/年"})
                over_amount += excess

            # 3. 住房
            housing = exec_info.get("housing", {})
            rental = float(housing.get("monthly_rental", 0))
            area = float(housing.get("area_sqm", 0))
            if rental > limits["housing"]["rental_monthly_cap"]:
                excess = rental - limits["housing"]["rental_monthly_cap"]
                violations.append({"dimension": "住房", "item": "月租金", "actual": rental,
                                    "limit": limits["housing"]["rental_monthly_cap"], "excess": excess, "unit": "元/月"})
                over_amount += excess * 12
            if area > limits["housing"]["area_sqm_cap"]:
                violations.append({"dimension": "住房", "item": "面积", "actual": area,
                                    "limit": limits["housing"]["area_sqm_cap"], "excess": area - limits["housing"]["area_sqm_cap"], "unit": "平米"})

            # 4. 通讯
            comm = float(exec_info.get("communication", {}).get("monthly_cost", 0))
            if comm > limits["communication"]["monthly_cap"]:
                excess = comm - limits["communication"]["monthly_cap"]
                violations.append({"dimension": "通讯", "item": "月度通讯费", "actual": comm,
                                    "limit": limits["communication"]["monthly_cap"], "excess": excess, "unit": "元/月"})
                over_amount += excess * 12

            # 5. 兼职
            part_time_jobs = exec_info.get("part_time", [])
            pt_count = len(part_time_jobs)
            pt_income = sum(float(j.get("annual_income", 0)) for j in part_time_jobs)
            if pt_count > limits["part_time"]["max_positions"]:
                violations.append({"dimension": "兼职", "item": "兼职数量", "actual": pt_count,
                                    "limit": limits["part_time"]["max_positions"], "excess": pt_count - limits["part_time"]["max_positions"], "unit": "个"})
            if pt_income > limits["part_time"]["max_annual_income"]:
                excess = pt_income - limits["part_time"]["max_annual_income"]
                violations.append({"dimension": "兼职", "item": "兼职年收入", "actual": pt_income,
                                    "limit": limits["part_time"]["max_annual_income"], "excess": excess, "unit": "元/年"})
                over_amount += excess

            # 6. 培训
            training = exec_info.get("training", {})
            domestic = float(training.get("domestic_annual", 0))
            overseas = float(training.get("overseas_annual", 0))
            overseas_count = int(training.get("overseas_count", 0))
            if domestic > limits["training"]["domestic_annual_cap"]:
                excess = domestic - limits["training"]["domestic_annual_cap"]
                violations.append({"dimension": "培训", "item": "国内培训费", "actual": domestic,
                                    "limit": limits["training"]["domestic_annual_cap"], "excess": excess, "unit": "元/年"})
                over_amount += excess
            if overseas > limits["training"]["overseas_annual_cap"]:
                excess = overseas - limits["training"]["overseas_annual_cap"]
                violations.append({"dimension": "培训", "item": "境外培训费", "actual": overseas,
                                    "limit": limits["training"]["overseas_annual_cap"], "excess": excess, "unit": "元/年"})
                over_amount += excess
            if overseas_count > limits["training"]["overseas_count_cap"]:
                violations.append({"dimension": "培训", "item": "境外培训次数", "actual": overseas_count,
                                    "limit": limits["training"]["overseas_count_cap"], "excess": overseas_count - limits["training"]["overseas_count_cap"], "unit": "次/年"})

            if violations:
                person_violations += 1
                total_violations += len(violations)
                total_over_amount += over_amount

            results.append({
                "name": name,
                "position": exec_info.get("position", ""),
                "dept": exec_info.get("dept", ""),
                "violations": violations,
                "violation_count": len(violations),
                "over_amount": round(over_amount, 2),
                "risk_level": "high" if len(violations) >= 3 or over_amount > 100000 else ("medium" if violations else "low"),
            })
            all_violations.extend([{**v, "name": name, "position": exec_info.get("position", "")} for v in violations])

        risk_level = "严重" if person_violations > len(executives) * 0.5 else ("关注" if person_violations > 0 else "合规")

        return {
            "status": "success",
            "data": {
                "executives": results,
                "overall_stats": {
                    "total_persons": len(executives),
                    "persons_with_violations": person_violations,
                    "total_violations": total_violations,
                    "total_over_amount": round(total_over_amount, 2),
                    "risk_level": risk_level,
                },
                "violation_details": sorted(all_violations, key=lambda x: x.get("excess", 0), reverse=True),
            },
            "summary": f"{len(executives)}名负责人中{person_violations}人存在超限，共{total_violations}项违规，超限金额{total_over_amount:,.0f}元。评级：{risk_level}"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"校验异常: {str(e)}"}


def handle_request(method: str, params: dict) -> dict:
    if method == "check_executive_perks":
        return check_executive_perks(
            params.get("executives", []),
            limits=params.get("limits"),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    execs = [
        {"name": "王某", "position": "董事长", "dept": "总部",
         "salary": {"annual": 800000, "bonus_ratio": 0.35},
         "vehicle": {"purchase_price": 350000, "annual_maintenance": 45000},
         "housing": {"monthly_rental": 8000, "area_sqm": 150},
         "communication": {"monthly_cost": 600},
         "part_time": [{"position": "子公司董事", "annual_income": 50000}],
         "training": {"domestic_annual": 30000, "overseas_annual": 200000, "overseas_count": 2}},
        {"name": "赵某", "position": "总经理", "dept": "总部",
         "salary": {"annual": 550000, "bonus_ratio": 0.25},
         "vehicle": {"purchase_price": 200000, "annual_maintenance": 25000},
         "housing": {"monthly_rental": 4500, "area_sqm": 110},
         "communication": {"monthly_cost": 400},
         "part_time": [],
         "training": {"domestic_annual": 20000, "overseas_annual": 50000, "overseas_count": 1}},
    ]

    result = check_executive_perks(execs)
    print("=" * 60)
    print("履职待遇合规校验")
    print("=" * 60)

    for e in result["data"]["executives"]:
        print(f"\n{e['name']} ({e['position']}): {e['violation_count']}项超标，超限金额{e['over_amount']:,.0f}元 [{e['risk_level']}]")
        for v in e["violations"]:
            print(f"  [{v['dimension']}] {v['item']}: 实际{v['actual']}{v['unit']}, 限额{v['limit']}{v['unit']}, 超出{v['excess']}{v['unit']}")

    print(f"\n{result['summary']}")

    # 王某应有多个超标项
    wang = next(e for e in result["data"]["executives"] if e["name"] == "王某")
    assert wang["violation_count"] >= 5
    assert wang["risk_level"] == "high"
    # 赵某应合规
    zhao = next(e for e in result["data"]["executives"] if e["name"] == "赵某")
    assert zhao["violation_count"] == 0

    print("\n✅ 全部测试通过")
