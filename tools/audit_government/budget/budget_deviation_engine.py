"""
预算执行偏差引擎 — Budget Deviation Engine

核心功能：预算批复数 vs 实际执行数，多维度偏差分析 + 分级预警。
适用场景：预算执行情况审计、财政决算审计。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
import json
import math
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple


# ─── 核心引擎 ───────────────────────────────────────────

def analyze_budget_deviation(
    budget_data: Dict[str, Dict[str, Any]],
    execution_data: Dict[str, Dict[str, Any]],
    *,
    year_end_check: bool = False,
) -> Dict[str, Any]:
    """
    多维预算执行偏差分析。

    Args:
        budget_data: 预算批复表，格式 {科目代码: {"name": str, "budget": float, "category": str(功能分类), "economic": str(经济分类), "dept": str(部门)}}
        execution_data: 执行报表，格式 {科目代码: {"name": str, "actual": float, "category": str, "economic": str, "dept": str}}
        year_end_check: 是否启用年末执行偏慢特别检测

    Returns:
        {
            "status": "success"/"error",
            "data": {
                "overall_execution_rate": float,
                "by_category": [{"name": str, "budget": float, "actual": float, "deviation_pct": float, "alert": str}],
                "by_economic": [...],
                "by_dept": [...],
                "alerts": [{"code": str, "name": str, "budget": float, "actual": float, "deviation_pct": float, "level": str, "type": str, "reason": str}],
                "year_end_slow": [...]  (如果启用)
            },
            "summary": str
        }
    """
    try:
        # ── 合并科目数据 ──
        combined = {}
        for code, item in budget_data.items():
            combined[code] = {
                "name": item.get("name", ""),
                "budget": float(item.get("budget", 0)),
                "actual": 0.0,
                "category": item.get("category", ""),
                "economic": item.get("economic", ""),
                "dept": item.get("dept", ""),
            }

        for code, item in execution_data.items():
            if code in combined:
                combined[code]["actual"] = float(item.get("actual", 0))
            else:
                # 预算中没有、执行中有的科目（无预算支出）
                combined[code] = {
                    "name": item.get("name", ""),
                    "budget": 0.0,
                    "actual": float(item.get("actual", 0)),
                    "category": item.get("category", ""),
                    "economic": item.get("economic", ""),
                    "dept": item.get("dept", ""),
                }

        # ── 总体执行率 ──
        total_budget = sum(v["budget"] for v in combined.values())
        total_actual = sum(v["actual"] for v in combined.values())
        overall_rate = (total_actual / total_budget * 100) if total_budget > 0 else 0.0

        # ── 多维度聚合 ──
        by_category = _aggregate_by(combined, "category")
        by_economic = _aggregate_by(combined, "economic")
        by_dept = _aggregate_by(combined, "dept")

        # ── 单项偏差 + 预警 ──
        alerts: List[Dict[str, Any]] = []
        for code, v in combined.items():
            if v["budget"] == 0:
                # 无预算支出 → 特殊处理
                if v["actual"] > 0:
                    alerts.append({
                        "code": code, "name": v["name"],
                        "budget": 0.0, "actual": v["actual"],
                        "deviation_pct": float("inf"),
                        "level": "red",
                        "type": "no_budget_expenditure",
                        "reason": f"无预算安排但发生支出{v['actual']:,.2f}元"
                    })
                continue

            deviation = (v["actual"] - v["budget"]) / v["budget"] * 100
            alert_level, alert_type, reason = _classify_deviation(deviation, v, year_end_check)

            if alert_level:
                alerts.append({
                    "code": code, "name": v["name"],
                    "budget": v["budget"], "actual": v["actual"],
                    "deviation_pct": round(deviation, 2),
                    "level": alert_level,
                    "type": alert_type,
                    "reason": reason,
                })

        # 按预警级别排序：red > orange > yellow
        level_order = {"red": 0, "orange": 1, "yellow": 2}
        alerts.sort(key=lambda x: (level_order.get(x["level"], 99), -abs(x.get("deviation_pct", 0))))

        result = {
            "overall_execution_rate": round(overall_rate, 2),
            "total_budget": round(total_budget, 2),
            "total_actual": round(total_actual, 2),
            "total_items": len(combined),
            "alert_count": len(alerts),
            "by_category": by_category,
            "by_economic": by_economic,
            "by_dept": by_dept,
            "alerts": alerts,
        }

        if year_end_check:
            result["year_end_slow"] = _detect_year_end_slow(combined, total_budget)

        return {
            "status": "success",
            "data": result,
            "summary": f"预算总体执行率{overall_rate:.1f}%，共{len(alerts)}项预警（红{sum(1 for a in alerts if a['level']=='red')}、橙{sum(1 for a in alerts if a['level']=='orange')}、黄{sum(1 for a in alerts if a['level']=='yellow')}）"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"分析异常: {str(e)}"}


# ─── 内部辅助函数 ────────────────────────────────────────

def _aggregate_by(combined: Dict, field: str) -> List[Dict[str, Any]]:
    """按指定维度聚合预算执行数据"""
    groups: Dict[str, Dict[str, float]] = defaultdict(lambda: {"budget": 0.0, "actual": 0.0})
    for v in combined.values():
        key = v.get(field, "未分类")
        groups[key]["budget"] += v["budget"]
        groups[key]["actual"] += v["actual"]

    result = []
    for name, vals in groups.items():
        if vals["budget"] == 0:
            deviation = float("inf") if vals["actual"] > 0 else 0.0
        else:
            deviation = round((vals["actual"] - vals["budget"]) / vals["budget"] * 100, 2)
        alert = _get_aggregate_alert(deviation)
        result.append({
            "name": name,
            "budget": round(vals["budget"], 2),
            "actual": round(vals["actual"], 2),
            "deviation_pct": deviation,
            "alert": alert,
        })
    # 按偏差绝对值降序
    result.sort(key=lambda x: abs(x["deviation_pct"]) if math.isfinite(x["deviation_pct"]) else 999999, reverse=True)
    return result


def _classify_deviation(
    deviation: float, item: Dict, year_end: bool
) -> Tuple[Optional[str], Optional[str], str]:
    """对单项偏差进行分级分类"""
    abs_dev = abs(deviation)

    if abs_dev <= 10:
        return None, None, ""

    # 确定级别
    if abs_dev > 30:
        level = "red"
    elif abs_dev > 20:
        level = "orange"
    else:
        level = "yellow"

    # 确定类型
    if deviation > 0:
        deviation_type = "overspend"
        if deviation > 50:
            reason = f"超预算支出{deviation:.1f}%（预算{item['budget']:,.0f}元→实际{item['actual']:,.0f}元），金额异常偏高"
        else:
            reason = f"超预算支出{deviation:.1f}%（预算{item['budget']:,.0f}元→实际{item['actual']:,.0f}元）"
    else:
        # 预算执行偏慢
        deviation_type = "underspend"
        execution_rate = item["actual"] / item["budget"] * 100 if item["budget"] > 0 else 0
        if year_end and execution_rate < 50:
            reason = f"年末预算执行率仅{execution_rate:.1f}%，存在资金沉淀风险"
        else:
            reason = f"预算执行偏慢，执行率{execution_rate:.1f}%（预算{item['budget']:,.0f}元→实际{item['actual']:,.0f}元）"

    return level, deviation_type, reason


def _get_aggregate_alert(deviation: float) -> str:
    """聚合层面的预警标签"""
    if not math.isfinite(deviation):
        return "red"
    abs_dev = abs(deviation)
    if abs_dev > 30:
        return "red"
    elif abs_dev > 20:
        return "orange"
    elif abs_dev > 10:
        return "yellow"
    return "normal"


def _detect_year_end_slow(combined: Dict, total_budget: float) -> List[Dict[str, Any]]:
    """年末执行偏慢特别检测（通常用于Q4分析）"""
    slow_items = []
    for code, v in combined.items():
        if v["budget"] == 0:
            continue
        rate = v["actual"] / v["budget"] * 100
        if rate < 50:
            slow_items.append({
                "code": code,
                "name": v["name"],
                "budget": v["budget"],
                "actual": v["actual"],
                "execution_rate": round(rate, 1),
                "remaining": round(v["budget"] - v["actual"], 2),
            })
    slow_items.sort(key=lambda x: x["execution_rate"])
    return slow_items


# ─── MCP JSON-RPC 接口 ──────────────────────────────────

def handle_request(method: str, params: dict) -> dict:
    """MCP JSON-RPC 请求分发"""
    if method == "analyze_budget_deviation":
        budget_data = params.get("budget_data", {})
        execution_data = params.get("execution_data", {})
        year_end = params.get("year_end_check", False)
        return analyze_budget_deviation(budget_data, execution_data, year_end_check=year_end)
    elif method == "analyze_budget_deviation_batch":
        # 批量分析多个年度
        results = []
        for item in params.get("items", []):
            results.append(analyze_budget_deviation(
                item.get("budget_data", {}),
                item.get("execution_data", {}),
                year_end_check=item.get("year_end_check", False),
            ))
        return {"status": "success", "data": results, "summary": f"批量分析{len(results)}个年度"}
    else:
        return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


# ─── 测试用例 ──────────────────────────────────────────

if __name__ == "__main__":
    # 模拟某市2025年预算执行数据
    budget = {
        "2010101": {"name": "行政运行-人员经费", "budget": 5000000, "category": "一般公共服务", "economic": "工资福利", "dept": "市财政局"},
        "2010102": {"name": "行政运行-公用经费", "budget": 1200000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市财政局"},
        "2050201": {"name": "学前教育-生均拨款", "budget": 8000000, "category": "教育", "economic": "对个人和家庭的补助", "dept": "市教育局"},
        "2050202": {"name": "小学教育-公用经费", "budget": 15000000, "category": "教育", "economic": "商品和服务", "dept": "市教育局"},
        "2080101": {"name": "社保-基本养老保险", "budget": 20000000, "category": "社会保障", "economic": "社会保障缴费", "dept": "市人社局"},
        "2120101": {"name": "城乡社区-环境卫生", "budget": 6000000, "category": "城乡社区", "economic": "商品和服务", "dept": "市城管局"},
        "2130101": {"name": "农业农村-耕地补贴", "budget": 10000000, "category": "农林水", "economic": "对个人和家庭的补助", "dept": "市农业农村局"},
    }

    execution = {
        "2010101": {"name": "行政运行-人员经费", "actual": 5200000, "category": "一般公共服务", "economic": "工资福利", "dept": "市财政局"},
        "2010102": {"name": "行政运行-公用经费", "actual": 980000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市财政局"},
        "2050201": {"name": "学前教育-生均拨款", "actual": 7500000, "category": "教育", "economic": "对个人和家庭的补助", "dept": "市教育局"},
        "2050202": {"name": "小学教育-公用经费", "actual": 16000000, "category": "教育", "economic": "商品和服务", "dept": "市教育局"},
        "2080101": {"name": "社保-基本养老保险", "actual": 18000000, "category": "社会保障", "economic": "社会保障缴费", "dept": "市人社局"},
        "2120101": {"name": "城乡社区-环境卫生", "actual": 3500000, "category": "城乡社区", "economic": "商品和服务", "dept": "市城管局"},
        "2130101": {"name": "农业农村-耕地补贴", "actual": 13000000, "category": "农林水", "economic": "对个人和家庭的补助", "dept": "市农业农村局"},
        # 无预算支出
        "2140101": {"name": "交通运输-突发事件处置", "actual": 800000, "category": "交通运输", "economic": "商品和服务", "dept": "市交通局"},
    }

    result = analyze_budget_deviation(budget, execution, year_end_check=True)
    print("=" * 60)
    print("预算执行偏差分析")
    print("=" * 60)
    print(f"总体执行率: {result['data']['overall_execution_rate']}%")
    print(f"预算总额: {result['data']['total_budget']:,.0f} 元")
    print(f"实际支出: {result['data']['total_actual']:,.0f} 元")
    print(f"\n预警项数: {result['data']['alert_count']}")
    for a in result['data']['alerts']:
        emoji = {"red": "🔴", "orange": "🟠", "yellow": "🟡"}.get(a["level"], "⚪")
        print(f"  {emoji} [{a['level']}] {a['name']}: {a['reason']}")

    print(f"\n按部门维度执行率:")
    for d in result['data']['by_dept']:
        print(f"  {d['name']}: 预算{d['budget']:,.0f} → 实际{d['actual']:,.0f} (偏差{d['deviation_pct']}%)")

    # ── 断言测试 ──
    assert result["status"] == "success"
    assert result["data"]["overall_execution_rate"] > 0
    assert result["data"]["alert_count"] >= 1  # 至少有无预算支出和超预算
    # 城乡社区执行率应该很低
    dept_map = {d["name"]: d for d in result["data"]["by_dept"]}
    assert dept_map["市城管局"]["deviation_pct"] < -30  # 严重偏慢
    # 农业农村应该超预算30%
    assert dept_map["市农业农村局"]["deviation_pct"] > 20
    # 交通运输是无预算支出
    assert any(a["type"] == "no_budget_expenditure" for a in result["data"]["alerts"])
    # 年末检测应该有偏慢项
    assert len(result["data"].get("year_end_slow", [])) > 0

    print("\n✅ 全部测试通过")
    print(result["summary"])
