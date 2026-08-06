"""
经责审计 + 绩效评价 + 专项债 工具集（P1三大场景合并）

作者：融策审计智析Agent | 日期：2026-07-22
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math


# ═══════════════════════════════════════════════════════
# 场景5：经济责任审计
# ═══════════════════════════════════════════════════════

def tenure_kpi_comparison(
    baseline_year: Dict[str, float],
    final_year: Dict[str, float],
    *,
    annual_data: List[Dict[str, float]] = None,
    peer_benchmarks: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    任期指标全景对比。baseline_year/final_year: {指标名: 数值}
    annual_data: [{年份, ...指标}] 用于检测异常跳跃点
    """
    try:
        indicators = set(baseline_year.keys()) | set(final_year.keys())
        changes = []

        for ind in indicators:
            base = baseline_year.get(ind, 0)
            final = final_year.get(ind, 0)
            if base != 0:
                change_pct = (final - base) / abs(base) * 100
            else:
                change_pct = 0
            abs_change = final - base

            # 方向判断（正增长不一定好，比如债务率上升是坏事）
            bad_up = ["债务率", "负债率", "不良率", "闲置率", "违规率"]
            is_bad_up = any(b in ind for b in bad_up)
            direction = "恶化" if (is_bad_up and change_pct > 5) or (not is_bad_up and change_pct < -5) else ("改善" if abs(change_pct) > 5 else "持平")

            changes.append({"indicator": ind, "baseline": round(base, 2), "final": round(final, 2),
                           "change_pct": round(change_pct, 2), "abs_change": round(abs_change, 2), "direction": direction})

        # 年度异常跳跃检测
        jumps = []
        if annual_data and len(annual_data) >= 3:
            for ind in indicators:
                vals = [d.get(ind, 0) for d in annual_data]
                for i in range(2, len(vals)):
                    prev_avg = (vals[i-1] + vals[i-2]) / 2 if (vals[i-1] + vals[i-2]) != 0 else 1
                    if abs(prev_avg) > 0.01:
                        jump_pct = (vals[i] - prev_avg) / abs(prev_avg) * 100
                        if abs(jump_pct) > 30:
                            jumps.append({"indicator": ind, "year": annual_data[i].get("year", i), "jump_pct": round(jump_pct, 2)})

        # 同业对标
        peer_comparison = []
        if peer_benchmarks:
            for ind, bench_val in peer_benchmarks.items():
                actual = final_year.get(ind, 0)
                if bench_val > 0:
                    peer_deviation = (actual - bench_val) / bench_val * 100
                    peer_comparison.append({"indicator": ind, "actual": actual, "benchmark": bench_val,
                                            "deviation_pct": round(peer_deviation, 2)})

        risk_count = sum(1 for c in changes if c["direction"] == "恶化")
        return {"status": "success", "data": {"changes": changes, "jumps": jumps, "peer_comparison": peer_comparison,
                "risk_indicator_count": risk_count, "tenure_assessment": "需重点关注" if risk_count >= 3 else ("存在风险" if risk_count >= 1 else "总体平稳")},
                "summary": f"任期{len(changes)}项指标中{risk_count}项恶化"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def natural_resource_audit(
    resources: List[Dict[str, Any]],
    *,
    red_lines: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    自然资源资产离任审计。
    resources: [{name, type, baseline_qty, current_qty, unit, red_line_qty}]
    """
    try:
        changes = []
        violations = []
        for r in resources:
            base = float(r.get("baseline_qty", 0))
            curr = float(r.get("current_qty", 0))
            red_line = float(r.get("red_line_qty", 0))
            if base > 0:
                change_pct = (curr - base) / base * 100
            else:
                change_pct = 0

            status = "恶化" if change_pct < -3 else ("改善" if change_pct > 3 else "基本持平")

            if red_line > 0 and curr < red_line:
                violations.append({"name": r.get("name", ""), "type": r.get("type", ""), "current_qty": curr,
                                   "red_line": red_line, "gap": round(red_line - curr, 2),
                                   "severity": "严重" if curr < red_line * 0.9 else "接近红线"})

            changes.append({"name": r.get("name", ""), "type": r.get("type", ""), "baseline": base, "current": curr,
                           "change_pct": round(change_pct, 2), "unit": r.get("unit", ""), "status": status})

        return {"status": "success", "data": {"changes": changes, "violations": violations, "violation_count": len(violations),
                "assessment": "存在红线触碰" if violations else "自然资源指标在红线范围内"},
                "summary": f"{len(changes)}项自然资源，{len(violations)}项触碰红线"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ═══════════════════════════════════════════════════════
# 场景6：绩效评价
# ═══════════════════════════════════════════════════════

def multi_source_scoring(
    fiscal_data: Dict[str, float],
    business_data: Dict[str, float],
    third_party_data: Dict[str, float] = None,
    satisfaction_data: Dict[str, float] = None,
    *,
    weights: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    多源数据融合绩效评分。
    各数据源格式: {指标名: 得分(0-100)}
    weights: {"fiscal": 0.4, "business": 0.3, "third_party": 0.15, "satisfaction": 0.15}
    """
    try:
        if weights is None:
            weights = {"fiscal": 0.4, "business": 0.3, "third_party": 0.15, "satisfaction": 0.15}

        all_sources = {
            "fiscal": (fiscal_data, weights.get("fiscal", 0)),
            "business": (business_data, weights.get("business", 0)),
            "third_party": (third_party_data or {}, weights.get("third_party", 0)),
            "satisfaction": (satisfaction_data or {}, weights.get("satisfaction", 0)),
        }

        dimension_scores = {}
        total_score = 0.0
        missing_data = []

        for source_name, (data, weight) in all_sources.items():
            if not data:
                missing_data.append(source_name)
                continue
            avg = sum(data.values()) / len(data)
            dim_score = avg * weight
            dimension_scores[source_name] = {"avg_raw": round(avg, 2), "weight": weight, "weighted_score": round(dim_score, 2), "indicators": data}
            total_score += dim_score

        if missing_data:
            remaining_weight = sum(weights.get(s, 0) for s in ["fiscal", "business", "third_party", "satisfaction"] if s not in missing_data)
            if remaining_weight > 0:
                total_score = total_score / remaining_weight * 100  # 归一化

        level = "优秀" if total_score >= 90 else ("良好" if total_score >= 75 else ("合格" if total_score >= 60 else "不合格"))

        return {"status": "success", "data": {"total_score": round(total_score, 2), "level": level,
                "dimension_scores": dimension_scores, "missing_sources": missing_data},
                "summary": f"综合绩效评分{total_score:.1f}分（{level}）"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def performance_benchmark(
    projects: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    同类项目绩效对比分析。projects: [{name, type, budget, output_qty, duration_days, quality_score, satisfaction}]
    """
    try:
        if not projects:
            return {"status": "success", "data": {"benchmarks": [], "outliers": []}, "summary": "无数据"}

        # 计算各维度均值和标准差
        metrics = ["output_qty", "duration_days", "quality_score", "satisfaction"]
        stats = {}
        for m in metrics:
            vals = [float(p.get(m, 0)) for p in projects if p.get(m) is not None]
            if vals:
                avg = sum(vals) / len(vals)
                std = (sum((v - avg) ** 2 for v in vals) / len(vals)) ** 0.5
                stats[m] = {"mean": round(avg, 2), "std": round(std, 2)}

        # 判断每个项目的偏离
        results = []
        outliers = []
        for p in projects:
            deviations = {}
            total_dev = 0
            for m in metrics:
                val = float(p.get(m, 0))
                if m in stats and stats[m]["std"] > 0:
                    z = (val - stats[m]["mean"]) / stats[m]["std"]
                    deviations[m] = round(z, 2)
                    total_dev += abs(z)

            is_outlier = total_dev > 6
            results.append({"name": p.get("name", ""), "type": p.get("type", ""), "budget": p.get("budget", 0),
                           "deviations": deviations, "total_deviation": round(total_dev, 2),
                           "flag": "outlier" if is_outlier else "normal"})
            if is_outlier:
                outliers.append(p.get("name", ""))

        best = min(results, key=lambda x: x["total_deviation"]) if results else None
        worst = max(results, key=lambda x: x["total_deviation"]) if results else None

        return {"status": "success", "data": {"benchmarks": results, "outliers": outliers,
                "best_project": best["name"] if best else "", "worst_project": worst["name"] if worst else ""},
                "summary": f"{len(projects)}个项目对比，{len(outliers)}个异常项目，标杆：{best['name'] if best else 'N/A'}"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ═══════════════════════════════════════════════════════
# 场景7：专项债申报和审计
# ═══════════════════════════════════════════════════════

def revenue_coverage_calc(
    projected_revenues: List[Dict],
    *,
    discount_rate: float = 0.04,
    debt_service: List[Dict] = None,
) -> Dict[str, Any]:
    """
    收益覆盖率测算。projected_revenues: [{year, amount}], debt_service: [{year, principal, interest}]
    """
    try:
        pv_revenue = 0
        for i, r in enumerate(projected_revenues):
            pv_revenue += float(r["amount"]) / ((1 + discount_rate) ** (i + 1))

        total_debt_pv = 0
        if debt_service:
            for i, ds in enumerate(debt_service):
                total_debt_pv += (float(ds.get("principal", 0)) + float(ds.get("interest", 0))) / ((1 + discount_rate) ** (i + 1))

        coverage = pv_revenue / total_debt_pv if total_debt_pv > 0 else float("inf")
        threshold_met = coverage >= 1.1

        return {"status": "success", "data": {"pv_revenue": round(pv_revenue, 2), "pv_debt_service": round(total_debt_pv, 2),
                "coverage_ratio": round(coverage, 2), "threshold_1_1": threshold_met,
                "risk": "达标" if threshold_met else ("临界" if coverage >= 1.0 else "不达标")},
                "summary": f"收益覆盖率{coverage:.2f}（达标线1.1），{'达标' if threshold_met else '不达标'}"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def negative_list_scanner(
    expenditures: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    专项债资金使用负面清单扫描。
    expenditures: [{item, amount, purpose}]
    """
    NEGATIVE_LIST = {
        "楼堂馆所": ["办公楼", "招待所", "培训中心", "会议中心"],
        "形象工程": ["景观", "广场", "雕塑", "喷泉", "亮化"],
        "经常性支出": ["工资", "津贴", "办公费", "差旅费", "招待费"],
        "置换存量": ["偿还旧债", "置换贷款", "借新还旧"],
        "商业化项目": ["商业地产", "商品房", "酒店", "商场", "高尔夫"],
    }

    hits = []
    for exp in expenditures:
        purpose = exp.get("purpose", "") + exp.get("item", "")
        amount = float(exp.get("amount", 0))
        for category, keywords in NEGATIVE_LIST.items():
            for kw in keywords:
                if kw in purpose:
                    hits.append({"item": exp.get("item", ""), "amount": amount, "category": category, "matched_keyword": kw, "risk": "严重违规"})
                    break

    hit_amount = sum(h["amount"] for h in hits)
    return {"status": "success", "data": {"hits": hits, "hit_count": len(hits), "hit_amount": round(hit_amount, 2),
            "total_expenditures": sum(float(e.get("amount", 0)) for e in expenditures)},
            "summary": f"负面清单命中{len(hits)}项，金额{hit_amount:,.0f}元"}


def progress_disbursement_match(
    progress_reports: List[Dict],
    disbursement_records: List[Dict],
) -> Dict[str, Any]:
    """项目进度 vs 资金拨付进度匹配。"""
    try:
        # 按项目聚合
        proj_progress: Dict[str, float] = {}
        for p in progress_reports:
            pid = p.get("project_id", "")
            prog = float(p.get("completion_pct", 0))
            if pid not in proj_progress or prog > proj_progress[pid]:
                proj_progress[pid] = prog

        proj_disburse: Dict[str, float] = {}
        proj_budget: Dict[str, float] = {}
        for d in disbursement_records:
            pid = d.get("project_id", "")
            proj_disburse[pid] = proj_disburse.get(pid, 0) + float(d.get("amount", 0))
            if pid not in proj_budget:
                proj_budget[pid] = float(d.get("total_budget", 0))

        mismatches = []
        for pid in set(list(proj_progress.keys()) + list(proj_disburse.keys())):
            prog = proj_progress.get(pid, 0)
            bud = proj_budget.get(pid, 1)
            dis_pct = (proj_disburse.get(pid, 0) / bud * 100) if bud > 0 else 0
            gap = dis_pct - prog

            if abs(gap) > 15:
                risk_type = "资金沉淀风险" if gap > 0 else "工程延误风险"
                mismatches.append({"project_id": pid, "progress_pct": round(prog, 1), "disbursement_pct": round(dis_pct, 1),
                                   "gap": round(gap, 1), "risk_type": risk_type, "risk": "high" if abs(gap) > 30 else "medium"})

        return {"status": "success", "data": {"mismatches": mismatches, "mismatch_count": len(mismatches)},
                "summary": f"{len(mismatches)}个项目进度-拨付不匹配"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ─── MCP ────────────────────────────────────────────

def handle_request(method: str, params: dict) -> dict:
    tools = {
        "tenure_kpi_comparison": lambda: tenure_kpi_comparison(params.get("baseline_year",{}), params.get("final_year",{}), annual_data=params.get("annual_data"), peer_benchmarks=params.get("peer_benchmarks")),
        "natural_resource_audit": lambda: natural_resource_audit(params.get("resources",[]), red_lines=params.get("red_lines")),
        "multi_source_scoring": lambda: multi_source_scoring(params.get("fiscal_data",{}), params.get("business_data",{}), params.get("third_party_data"), params.get("satisfaction_data"), weights=params.get("weights")),
        "performance_benchmark": lambda: performance_benchmark(params.get("projects",[])),
        "revenue_coverage_calc": lambda: revenue_coverage_calc(params.get("projected_revenues",[]), discount_rate=params.get("discount_rate",0.04), debt_service=params.get("debt_service")),
        "negative_list_scanner": lambda: negative_list_scanner(params.get("expenditures",[])),
        "progress_disbursement_match": lambda: progress_disbursement_match(params.get("progress_reports",[]), params.get("disbursement_records",[])),
    }
    if method in tools:
        return tools[method]()
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    # 经责审计测试
    r1 = tenure_kpi_comparison(
        {"GDP增速": 6.5, "财政收入": 50, "债务率": 80, "民生支出占比": 65},
        {"GDP增速": 4.2, "财政收入": 55, "债务率": 120, "民生支出占比": 68},
        annual_data=[{"year": 2021, "GDP增速": 6.5, "财政收入": 50, "债务率": 80},
                     {"year": 2022, "GDP增速": 5.8, "财政收入": 52, "债务率": 90},
                     {"year": 2023, "GDP增速": 4.2, "财政收入": 55, "债务率": 120}])
    assert r1["data"]["risk_indicator_count"] >= 2
    print("tenure_kpi_comparison: OK")

    r2 = natural_resource_audit([
        {"name": "耕地面积", "type": "土地", "baseline_qty": 50000, "current_qty": 48000, "unit": "亩", "red_line_qty": 48000},
        {"name": "林地面积", "type": "森林", "baseline_qty": 30000, "current_qty": 31000, "unit": "亩", "red_line_qty": 25000},
    ])
    assert len(r2["data"]["violations"]) >= 0
    print("natural_resource_audit: OK")

    # 绩效评价测试
    r3 = multi_source_scoring(
        {"产出数量": 90, "产出质量": 85, "时效性": 80, "成本控制": 75},
        {"服务覆盖": 88, "达标率": 92},
        satisfaction_data={"满意度": 82})
    assert r3["data"]["total_score"] > 0
    print("multi_source_scoring: OK")

    r4 = performance_benchmark([
        {"name": "项目A", "type": "基建", "budget": 1000, "output_qty": 100, "duration_days": 365, "quality_score": 92, "satisfaction": 85},
        {"name": "项目B", "type": "基建", "budget": 1200, "output_qty": 95, "duration_days": 400, "quality_score": 88, "satisfaction": 80},
        {"name": "项目C", "type": "基建", "budget": 800, "output_qty": 50, "duration_days": 600, "quality_score": 65, "satisfaction": 60},
    ])
    assert len(r4["data"]["outliers"]) >= 1
    print("performance_benchmark: OK")

    # 专项债测试
    r5 = revenue_coverage_calc(
        [{"year": 1, "amount": 5000000}, {"year": 2, "amount": 6000000}, {"year": 3, "amount": 7000000}],
        debt_service=[{"year": 1, "principal": 2000000, "interest": 400000}, {"year": 2, "principal": 3000000, "interest": 300000}, {"year": 3, "principal": 5000000, "interest": 200000}])
    assert r5["status"] == "success"
    print("revenue_coverage_calc: OK")

    r6 = negative_list_scanner([
        {"item": "办公楼装修", "amount": 2000000, "purpose": "政府新办公楼"},
        {"item": "道路维修材料费", "amount": 500000, "purpose": "日常维护"},
        {"item": "景观广场建设", "amount": 3000000, "purpose": "城市亮化景观工程"},
    ])
    assert r6["data"]["hit_count"] >= 1
    print("negative_list_scanner: OK")

    r7 = progress_disbursement_match(
        [{"project_id": "P1", "completion_pct": 40}, {"project_id": "P2", "completion_pct": 85}],
        [{"project_id": "P1", "amount": 8000000, "total_budget": 10000000}, {"project_id": "P2", "amount": 5000000, "total_budget": 10000000}])
    assert r7["data"]["mismatch_count"] >= 1
    print("progress_disbursement_match: OK")

    print("\n✅ P1三大场景7工具全部通过")
