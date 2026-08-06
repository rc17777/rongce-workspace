"""
预算执行审计 — 综合测试场景

模拟某县级市2025年度预算执行数据，跑通全部4个工具并输出综合审计报告。

作者：融策审计智析Agent
日期：2026-07-22
"""

import sys
import os

# 添加工具路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from budget_deviation_engine import analyze_budget_deviation
from no_budget_detector import detect_no_budget_expenditure
from carryover_compliance import check_carryover_compliance
from budget_adjustment_check import check_budget_adjustment_compliance


def run_full_audit():
    """运行完整的预算执行审计场景"""
    print("=" * 70)
    print("  XX市2025年度预算执行情况 — 自动化审计报告")
    print("=" * 70)
    print(f"  审计日期: 2026-07-22")
    print(f"  审计范围: XX市2025年度一般公共预算")
    print()

    # ─── 数据准备 ───
    budget = {
        "2010101": {"name": "行政运行-人员经费", "budget": 8000000, "category": "一般公共服务", "economic": "工资福利", "dept": "市政府办"},
        "2010102": {"name": "行政运行-公用经费", "budget": 2000000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市政府办"},
        "2010301": {"name": "政务公开与信息化", "budget": 1500000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市政府办"},
        "2050201": {"name": "学前教育-生均拨款", "budget": 6000000, "category": "教育", "economic": "对个人和家庭的补助", "dept": "市教育局"},
        "2050202": {"name": "小学教育-公用经费", "budget": 12000000, "category": "教育", "economic": "商品和服务", "dept": "市教育局"},
        "2050203": {"name": "义务教育校舍维修", "budget": 5000000, "category": "教育", "economic": "资本性支出", "dept": "市教育局"},
        "2080101": {"name": "社保-基本养老保险", "budget": 15000000, "category": "社会保障", "economic": "社会保障缴费", "dept": "市人社局"},
        "2080102": {"name": "社保-低保补助", "budget": 8000000, "category": "社会保障", "economic": "对个人和家庭的补助", "dept": "市民政局"},
        "2100101": {"name": "医疗卫生-基本公卫", "budget": 10000000, "category": "卫生健康", "economic": "商品和服务", "dept": "市卫健局"},
        "2120101": {"name": "城乡社区-环境卫生", "budget": 8000000, "category": "城乡社区", "economic": "商品和服务", "dept": "市城管局"},
        "2120102": {"name": "城乡社区-市政维护", "budget": 4000000, "category": "城乡社区", "economic": "资本性支出", "dept": "市城管局"},
        "2130101": {"name": "农业农村-耕地补贴", "budget": 20000000, "category": "农林水", "economic": "对个人和家庭的补助", "dept": "市农业农村局"},
        "2130102": {"name": "农业农村-高标准农田", "budget": 15000000, "category": "农林水", "economic": "资本性支出", "dept": "市农业农村局"},
        "2140101": {"name": "交通运输-公路养护", "budget": 6000000, "category": "交通运输", "economic": "商品和服务", "dept": "市交通局"},
        "2210101": {"name": "住房保障-公租房维护", "budget": 3000000, "category": "住房保障", "economic": "资本性支出", "dept": "市住建局"},
    }
    budget_total = sum(v["budget"] for v in budget.values())

    execution = {
        "2010101": {"name": "行政运行-人员经费", "actual": 8400000, "category": "一般公共服务", "economic": "工资福利", "dept": "市政府办"},
        "2010102": {"name": "行政运行-公用经费", "actual": 1800000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市政府办"},
        "2010301": {"name": "政务公开与信息化", "actual": 2100000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市政府办"},
        "2050201": {"name": "学前教育-生均拨款", "actual": 5800000, "category": "教育", "economic": "对个人和家庭的补助", "dept": "市教育局"},
        "2050202": {"name": "小学教育-公用经费", "actual": 12500000, "category": "教育", "economic": "商品和服务", "dept": "市教育局"},
        "2050203": {"name": "义务教育校舍维修", "actual": 2300000, "category": "教育", "economic": "资本性支出", "dept": "市教育局"},
        "2080101": {"name": "社保-基本养老保险", "actual": 14800000, "category": "社会保障", "economic": "社会保障缴费", "dept": "市人社局"},
        "2080102": {"name": "社保-低保补助", "actual": 7800000, "category": "社会保障", "economic": "对个人和家庭的补助", "dept": "市民政局"},
        "2100101": {"name": "医疗卫生-基本公卫", "actual": 9600000, "category": "卫生健康", "economic": "商品和服务", "dept": "市卫健局"},
        "2120101": {"name": "城乡社区-环境卫生", "actual": 5500000, "category": "城乡社区", "economic": "商品和服务", "dept": "市城管局"},
        "2120102": {"name": "城乡社区-市政维护", "actual": 4000000, "category": "城乡社区", "economic": "资本性支出", "dept": "市城管局"},
        "2130101": {"name": "农业农村-耕地补贴", "actual": 22000000, "category": "农林水", "economic": "对个人和家庭的补助", "dept": "市农业农村局"},
        "2130102": {"name": "农业农村-高标准农田", "actual": 13500000, "category": "农林水", "economic": "资本性支出", "dept": "市农业农村局"},
        "2140101": {"name": "交通运输-公路养护", "actual": 7000000, "category": "交通运输", "economic": "商品和服务", "dept": "市交通局"},
        "2210101": {"name": "住房保障-公租房维护", "actual": 1800000, "category": "住房保障", "economic": "资本性支出", "dept": "市住建局"},
        # 无预算支出
        "2140201": {"name": "交通运输-突发事件处置", "actual": 1200000, "category": "交通运输", "economic": "商品和服务", "dept": "市交通局"},
        "2290201": {"name": "其他支出-临时项目", "actual": 800000, "category": "其他支出", "economic": "商品和服务", "dept": "市政府办"},
    }

    project_ledger = {
        "P001": {"name": "城区道路改造工程", "years_carried": 3, "current_balance": 3500000, "original_amount": 20000000, "last_used_date": "2023-05-20", "dept": "市交通局", "project_type": "基建"},
        "P002": {"name": "智慧校园二期建设", "years_carried": 1, "current_balance": 4000000, "original_amount": 10000000, "last_used_date": "2025-10-15", "dept": "市教育局", "project_type": "信息化"},
        "P003": {"name": "农村饮水安全巩固提升", "years_carried": 2, "current_balance": 1500000, "original_amount": 8000000, "last_used_date": "2024-08-01", "dept": "市水利局", "project_type": "民生"},
        "P004": {"name": "老旧小区改造补贴", "years_carried": 4, "current_balance": 2000000, "original_amount": 5000000, "last_used_date": "2022-12-01", "dept": "市住建局", "project_type": "民生"},
        "P005": {"name": "政务云平台运维服务", "years_carried": 0, "current_balance": 2800000, "original_amount": 6000000, "last_used_date": "2026-06-30", "dept": "市数据局", "project_type": "运行维护"},
    }

    adjustments = [
        {"adjust_id": "ADJ001", "adjust_date": "2025-06-15", "amount": 400000, "original_budget": 1500000, "approval_date": "2025-06-10", "approval_level": "部门审批", "approval_doc_exists": True, "dept": "市政府办", "reason": "政务公开信息化采购追加"},
        {"adjust_id": "ADJ002", "adjust_date": "2025-09-20", "amount": 6200000, "original_budget": 15000000, "approval_date": "2025-10-05", "approval_level": "政府审批（常务会议）", "approval_doc_exists": False, "dept": "市农业农村局", "reason": "高标准农田追加"},
        {"adjust_id": "ADJ003", "adjust_date": "2025-11-01", "amount": 1000000, "original_budget": 6000000, "approval_date": "2025-10-25", "approval_level": "部门审批", "approval_doc_exists": True, "dept": "市交通局", "reason": "公路养护追加"},
        {"adjust_id": "ADJ004", "adjust_date": "2025-12-20", "amount": 5000000, "original_budget": 12000000, "approval_date": "2025-12-22", "approval_level": "部门审批", "approval_doc_exists": True, "dept": "市教育局", "reason": "校舍维修年终追加"},
    ]

    issues = []

    # ─── 1. 预算执行偏差分析 ───
    print("\n" + "-" * 50)
    print("一、预算执行偏差分析")
    print("-" * 50)
    r1 = analyze_budget_deviation(budget, execution, year_end_check=True)
    assert r1["status"] == "success"
    d1 = r1["data"]

    print(f"  预算总额: {d1['total_budget']:,.0f} 元")
    print(f"  实际支出: {d1['total_actual']:,.0f} 元")
    print(f"  总体执行率: {d1['overall_execution_rate']}%")

    # 功能分类执行率
    print("\n  功能分类执行率:")
    for cat in d1["by_category"]:
        flag = " [!]" if cat["alert"] != "normal" else ""
        print(f"    {cat['name']}: 预算{cat['budget']:,.0f} → 实际{cat['actual']:,.0f} ({cat['deviation_pct']:+}%){flag}")

    # 预警
    red_alerts = [a for a in d1["alerts"] if a["level"] == "red"]
    orange_alerts = [a for a in d1["alerts"] if a["level"] == "orange"]
    print(f"\n  预警: 红{len(red_alerts)}项 / 橙{len(orange_alerts)}项 / 黄{len(d1['alerts'])-len(red_alerts)-len(orange_alerts)}项")
    for a in d1["alerts"][:5]:
        print(f"    [{a['level']}] {a['name']}: {a['reason']}")

    for a in red_alerts:
        issues.append(f"【预算偏差-红】{a['name']}: {a['reason']}")
    for a in orange_alerts:
        issues.append(f"【预算偏差-橙】{a['name']}: {a['reason']}")

    # ─── 2. 无预算支出检测 ───
    print("\n" + "-" * 50)
    print("二、无预算支出检测")
    print("-" * 50)
    r2 = detect_no_budget_expenditure(budget, execution)
    assert r2["status"] == "success"
    d2 = r2["data"]

    print(f"  无预算支出: {d2['item_count']}项，合计{d2['total_no_budget_amount']:,.0f}元")
    print(f"  占总支出的: {d2['ratio_pct']}%")
    for item in d2["no_budget_items"]:
        print(f"    {item['name']}: {item['amount']:,.0f}元 [{item['risk_level']}] — {item['suspicious_type']}")
    for item in d2["no_budget_items"]:
        issues.append(f"【无预算支出】{item['name']}: {item['amount']:,.0f}元")

    # 可疑科目间转移
    if d2.get("suspicious_transfers"):
        print(f"\n  可疑科目间调剂: {len(d2['suspicious_transfers'])}项")

    # ─── 3. 结转结余合规检查 ───
    print("\n" + "-" * 50)
    print("三、结转结余合规检查")
    print("-" * 50)
    r3 = check_carryover_compliance(project_ledger, reference_date="2026-07-22")
    assert r3["status"] == "success"
    d3 = r3["data"]

    print(f"  项目总数: {d3['total_projects']}")
    print(f"  结转总额: {d3['total_balance']:,.0f}元")
    print(f"  超期结转: {d3['summary_stats']['overdue_count']}个，应收回{d3['total_should_recover']:,.0f}元")

    for p in d3["overdue_carryover"]:
        print(f"    {p['name']}: 余额{p['current_balance']:,.0f}元，结转{p['years_carried']}年 → 应收回")
    for p in d3["overdue_carryover"]:
        issues.append(f"【结转超期】{p['name']}: 应收回{p['should_recover']:,.0f}元")

    # ─── 4. 预算调整合规检测 ───
    print("\n" + "-" * 50)
    print("四、预算调整程序合规检测")
    print("-" * 50)
    r4 = check_budget_adjustment_compliance(adjustments, budget_total=budget_total)
    assert r4["status"] == "success"
    d4 = r4["data"]

    print(f"  调整总数: {d4['total_adjustments']}项，违规{d4['risk_summary']['violation_count']}项")
    if d4["violations"]:
        print("  违规调整:")
        for v in d4["violations"]:
            print(f"    {v['adjust_id']} ({v['dept']}): {v['amount']:,.0f}元 — {'; '.join(v['issues'])}")
    if d4["warnings"]:
        print("  需关注:")
        for w in d4["warnings"]:
            print(f"    {w['adjust_id']}: {'; '.join(w['risks'])}")

    for v in d4["violations"]:
        issues.append(f"【调整违规】{v['adjust_id']}-{v['dept']}: {v['amount']:,.0f}元 ({', '.join(v['issues'])})")

    # ─── 综合审计报告 ───
    print("\n" + "=" * 70)
    print("  综合审计结论")
    print("=" * 70)
    print(f"\n  共发现问题 {len(issues)} 项：")
    for i, iss in enumerate(issues, 1):
        print(f"    {i}. {iss}")

    high_risk = sum(1 for i in issues if "红" in i or "无预算" in i or "违规" in i)
    print(f"\n  高风险问题: {high_risk}项")
    if high_risk >= 3:
        print("  ⚠️ 预算执行管理存在系统性问题，建议：")
        print("    1. 对无预算支出项目逐项核实审批手续")
        print("    2. 对超预算30%以上项目启动专项资金核查")
        print("    3. 立即清理超期结转资金，按规定收回财政")
        print("    4. 对违规预算调整程序追究相关人员责任")

    print("\n" + "=" * 70)

    # 最终断言
    assert len(issues) >= 5, f"预期至少5个问题，实际{len(issues)}"
    assert d1["overall_execution_rate"] > 0
    assert d2["item_count"] >= 2

    return issues


if __name__ == "__main__":
    run_full_audit()
    print("\n✅ 预算执行审计综合测试全部通过")
