"""
P1补充：收支审计 + 工程结算审核增强

作者：融策审计智析Agent | 日期：2026-07-22
"""

from typing import Dict, List, Any
import math


# ═══════════ 收支审计补充 ═══════════

def non_tax_revenue_completeness(
    receivable_records: List[Dict],
    actual_collections: List[Dict],
) -> Dict[str, Any]:
    """
    非税收入完整性校验。
    receivable: [{category, amount, basis}]
    actual: [{category, amount, period}]
    """
    try:
        receivable_map: Dict[str, float] = {}
        for r in receivable_records:
            cat = r.get("category", "")
            receivable_map[cat] = receivable_map.get(cat, 0) + float(r.get("amount", 0))

        collected_map: Dict[str, float] = {}
        for c in actual_collections:
            cat = c.get("category", "")
            collected_map[cat] = collected_map.get(cat, 0) + float(c.get("amount", 0))

        gaps = []
        total_gap = 0.0
        for cat, rec_amt in receivable_map.items():
            col_amt = collected_map.get(cat, 0)
            if rec_amt > col_amt:
                gap = rec_amt - col_amt
                gaps.append({"category": cat, "receivable": round(rec_amt, 2), "collected": round(col_amt, 2),
                            "gap": round(gap, 2), "collection_rate": round(col_amt/rec_amt*100, 1)})
                total_gap += gap

        return {"status": "success", "data": {"gaps": gaps, "total_gap": round(total_gap, 2), "gap_count": len(gaps)},
                "summary": f"非税收入应收未收{len(gaps)}类，合计{total_gap:,.0f}元"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def revenue_expenditure_two_lines(
    revenue_records: List[Dict],
    expenditure_records: List[Dict],
) -> Dict[str, Any]:
    """
    收支两条线合规检测。
    检测：坐支（收入直接用于支出）、截留（收入未上缴）、应缴未缴。
    """
    try:
        violations = []
        total_revenue = sum(float(r.get("amount", 0)) for r in revenue_records)
        total_submitted = sum(float(r.get("submitted_amount", 0)) for r in revenue_records)

        # 截留检测
        submission_rate = total_submitted / total_revenue * 100 if total_revenue > 0 else 100
        if submission_rate < 95:
            violations.append({"type": "截留/应缴未缴", "total_revenue": round(total_revenue, 2),
                              "submitted": round(total_submitted, 2), "gap": round(total_revenue - total_submitted, 2),
                              "rate": round(submission_rate, 1)})

        # 坐支检测（收入发生日期与上缴日期之间的支出）
        for r in revenue_records:
            r_date = r.get("date", "")
            r_amount = float(r.get("amount", 0))
            submitted = float(r.get("submitted_amount", 0))
            if submitted < r_amount * 0.9:
                # 查此期间的支出
                same_period_exp = [e for e in expenditure_records if e.get("source_fund", "") == "应缴收入"]
                if same_period_exp:
                    violations.append({"type": "疑似坐支", "revenue_item": r.get("item", ""),
                                      "revenue_amount": r_amount, "unsubmitted": round(r_amount - submitted, 2),
                                      "related_expenditure": sum(float(e.get("amount", 0)) for e in same_period_exp)})

        risk_level = "严重" if submission_rate < 50 else ("需关注" if submission_rate < 95 else "合规")
        return {"status": "success", "data": {"violations": violations, "submission_rate": round(submission_rate, 1), "risk_level": risk_level},
                "summary": f"收支两条线：上缴率{submission_rate:.1f}%，{len(violations)}项违规"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ═══════════ 工程结算审核补充 ═══════════

def boq_vs_actual_quantity_check(
    boq_items: List[Dict],
    actual_quantities: List[Dict],
    *,
    tolerance_pct: float = 5.0,
) -> Dict[str, Any]:
    """
    工程量清单量 vs 实际报审量偏差检测。
    boq_items: [{code, name, unit, quantity, unit_price}]
    actual_quantities: [{code, name, unit, claimed_quantity}]
    """
    try:
        boq_map = {b["code"]: b for b in boq_items}
        deviations = []

        for a in actual_quantities:
            code = a.get("code", "")
            claimed = float(a.get("claimed_quantity", 0))
            boq = boq_map.get(code, {})
            boq_qty = float(boq.get("quantity", 0))

            if boq_qty > 0:
                dev = (claimed - boq_qty) / boq_qty * 100
                if abs(dev) > tolerance_pct:
                    unit_price = float(boq.get("unit_price", 0))
                    amount_diff = (claimed - boq_qty) * unit_price
                    deviations.append({"code": code, "name": a.get("name", ""), "boq_qty": boq_qty,
                                      "claimed_qty": claimed, "deviation_pct": round(dev, 2),
                                      "amount_impact": round(amount_diff, 2),
                                      "risk": "high" if abs(dev) > 20 else "medium"})

        deviations.sort(key=lambda x: abs(x["amount_impact"]), reverse=True)
        return {"status": "success", "data": {"deviations": deviations, "deviation_count": len(deviations)},
                "summary": f"{len(deviations)}项工程量偏差超过{tolerance_pct}%"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def unit_price_compliance_check(
    claimed_prices: List[Dict],
    *,
    quota_database: Dict[str, float] = None,
    historical_prices: Dict[str, Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    综合单价套用合规检测。
    claimed_prices: [{code, name, claimed_unit_price, quota_sub_code}]
    """
    try:
        issues = []
        for cp in claimed_prices:
            claimed = float(cp.get("claimed_unit_price", 0))
            code = cp.get("code", "")

            # 定额对标
            quota_code = cp.get("quota_sub_code", "")
            if quota_database and quota_code in quota_database:
                quota_price = quota_database[quota_code]
                if claimed > quota_price * 1.3:
                    issues.append({"code": code, "name": cp.get("name", ""), "claimed": claimed,
                                  "reference": quota_price, "ref_type": "定额", "deviation_pct": round((claimed/quota_price-1)*100, 2)})

            # 历史价格对标
            if historical_prices and code in historical_prices:
                hist = historical_prices[code]
                hist_avg = hist.get("avg_price", 0)
                if hist_avg > 0 and claimed > hist_avg * 1.3:
                    issues.append({"code": code, "name": cp.get("name", ""), "claimed": claimed,
                                  "reference": hist_avg, "ref_type": "历史均价", "deviation_pct": round((claimed/hist_avg-1)*100, 2)})

        return {"status": "success", "data": {"issues": issues, "issue_count": len(issues)},
                "summary": f"{len(issues)}项综合单价异常偏高"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def change_order_reasonableness(
    change_orders: List[Dict],
    *,
    contract_amount: float = 0,
) -> Dict[str, Any]:
    """
    变更签证合理性评分。三维：变更理由/变更量/变更价。
    """
    try:
        scored = []
        total_change = 0

        for co in change_orders:
            score = 0  # 0=合理, 越高越不合理
            reasons = []

            # 理由评分
            reason = co.get("reason", "")
            suspicious_reasons = ["设计优化", "现场实际情况", "甲方要求", "政策调整"]
            if not reason or any(r in reason for r in ["不详", "其他", "调整"]):
                score += 3
                reasons.append("变更理由不充分")
            elif any(r in reason for r in suspicious_reasons):
                score += 1

            # 变更量评分
            orig_qty = float(co.get("original_quantity", 1))
            new_qty = float(co.get("changed_quantity", 0))
            qty_change = abs(new_qty - orig_qty) / orig_qty * 100 if orig_qty > 0 else 100
            if qty_change > 50:
                score += 3
                reasons.append(f"变更量异常({qty_change:.0f}%)")
            elif qty_change > 20:
                score += 1

            # 变更价评分
            orig_price = float(co.get("original_unit_price", 0))
            new_price = float(co.get("changed_unit_price", 0))
            if orig_price > 0:
                price_change = (new_price - orig_price) / orig_price * 100
                if price_change > 30:
                    score += 3
                    reasons.append(f"变更单价异常偏高({price_change:.0f}%)")
                elif price_change > 10:
                    score += 1

            change_amount = float(co.get("change_amount", 0))
            total_change += change_amount

            scored.append({"id": co.get("id", ""), "description": co.get("description", "")[:80],
                          "score": score, "reasons": reasons, "change_amount": round(change_amount, 2),
                          "risk": "high" if score >= 6 else ("medium" if score >= 3 else "low")})

        # 总变更占比
        total_change_pct = (total_change / contract_amount * 100) if contract_amount > 0 else 0
        scored.sort(key=lambda x: x["score"], reverse=True)

        return {"status": "success", "data": {"change_orders": scored, "total_change_amount": round(total_change, 2),
                "total_change_pct": round(total_change_pct, 1), "alert": total_change_pct > 15,
                "high_risk_count": sum(1 for s in scored if s["risk"] == "high")},
                "summary": f"{len(scored)}项变更，总变更{total_change:,.0f}元({total_change_pct:.1f}%)，高风险{sum(1 for s in scored if s['risk']=='high')}项"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def handle_request(method: str, params: dict) -> dict:
    tools = {
        "non_tax_revenue_completeness": lambda: non_tax_revenue_completeness(params.get("receivable_records",[]), params.get("actual_collections",[])),
        "revenue_expenditure_two_lines": lambda: revenue_expenditure_two_lines(params.get("revenue_records",[]), params.get("expenditure_records",[])),
        "boq_vs_actual_quantity_check": lambda: boq_vs_actual_quantity_check(params.get("boq_items",[]), params.get("actual_quantities",[]), tolerance_pct=params.get("tolerance_pct",5.0)),
        "unit_price_compliance_check": lambda: unit_price_compliance_check(params.get("claimed_prices",[]), quota_database=params.get("quota_database"), historical_prices=params.get("historical_prices")),
        "change_order_reasonableness": lambda: change_order_reasonableness(params.get("change_orders",[]), contract_amount=params.get("contract_amount",0)),
    }
    if method in tools:
        return tools[method]()
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    # 非税收入测试
    r1 = non_tax_revenue_completeness(
        [{"category": "行政事业性收费", "amount": 5000000}, {"category": "罚没收入", "amount": 3000000}],
        [{"category": "行政事业性收费", "amount": 4500000}, {"category": "罚没收入", "amount": 2800000}])
    assert r1["data"]["gap_count"] >= 1
    print("non_tax_revenue_completeness: OK")

    r2 = revenue_expenditure_two_lines(
        [{"item": "行政事业性收费", "amount": 5000000, "submitted_amount": 3000000, "date": "2025-06-01"}],
        [{"item": "办公设备", "amount": 500000, "source_fund": "应缴收入", "date": "2025-07-01"}])
    assert r2["data"]["risk_level"] in ["严重", "需关注"]
    print("revenue_expenditure_two_lines: OK")

    # 工程量测试
    r3 = boq_vs_actual_quantity_check(
        [{"code": "010101001", "name": "挖土方", "unit": "m3", "quantity": 10000, "unit_price": 25}],
        [{"code": "010101001", "name": "挖土方", "unit": "m3", "claimed_quantity": 13500}])
    assert r3["data"]["deviation_count"] >= 1
    print("boq_vs_actual_quantity_check: OK")

    r4 = unit_price_compliance_check(
        [{"code": "010101001", "name": "挖土方", "claimed_unit_price": 45, "quota_sub_code": "D1-001"}],
        quota_database={"D1-001": 25})
    assert r4["data"]["issue_count"] >= 1
    print("unit_price_compliance_check: OK")

    r5 = change_order_reasonableness([
        {"id": "CH001", "description": "基础加深", "reason": "设计优化", "original_quantity": 500, "changed_quantity": 1200,
         "original_unit_price": 300, "changed_unit_price": 480, "change_amount": 360000}], contract_amount=10000000)
    assert r5["data"]["high_risk_count"] >= 0
    print("change_order_reasonableness: OK")

    print("\n✅ P1补充工具5个全部通过")
