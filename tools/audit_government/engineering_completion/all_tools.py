"""
工程竣工财务决算审计工具集
包含：四阶段穿透比对 / 待摊投资分摊校验 / 交付资产-决算勾稽

作者：融策审计智析Agent | 日期：2026-07-22
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


# ─── 工具1：四阶段穿透比对 ──────────────────────────

def four_stage_penetration(
    estimate: Dict[str, Any],
    budget: Dict[str, Any],
    settlement: Dict[str, Any],
    final_accounts: Dict[str, Any],
) -> Dict[str, Any]:
    """
    概算→预算→结算→决算四阶段穿透比对。
    每阶段格式: {total_amount, items: [{name, amount, category}]}
    """
    try:
        stages = [
            ("概算", estimate),
            ("预算", budget),
            ("结算", settlement),
            ("决算", final_accounts),
        ]

        transitions = []
        for i in range(len(stages) - 1):
            from_name, from_data = stages[i]
            to_name, to_data = stages[i + 1]
            from_amt = float(from_data.get("total_amount", 0))
            to_amt = float(to_data.get("total_amount", 0))

            if from_amt > 0:
                deviation = (to_amt - from_amt) / from_amt * 100
            else:
                deviation = 0

            transitions.append({
                "from": from_name, "to": to_name,
                "from_amount": from_amt, "to_amount": to_amt,
                "deviation_pct": round(deviation, 2),
                "deviation_abs": round(to_amt - from_amt, 2),
                "alert": "red" if abs(deviation) > 20 else ("orange" if abs(deviation) > 10 else "normal"),
            })

        # 单项对比
        all_items = set()
        for _, data in stages:
            for item in data.get("items", []):
                all_items.add(item.get("name", ""))

        item_comparison = []
        for name in all_items:
            row = {"name": name}
            for sname, sdata in stages:
                matched = next((it for it in sdata.get("items", []) if it.get("name") == name), None)
                row[sname] = float(matched.get("amount", 0)) if matched else 0
            # 概算到决算总偏差
            if row["概算"] > 0:
                row["total_deviation_pct"] = round((row["决算"] - row["概算"]) / row["概算"] * 100, 2)
            else:
                row["total_deviation_pct"] = 0
            if abs(row.get("total_deviation_pct", 0)) > 20:
                row["alert"] = "red"
            item_comparison.append(row)

        item_comparison.sort(key=lambda x: abs(x.get("total_deviation_pct", 0)), reverse=True)

        alert_count = sum(1 for t in transitions if t["alert"] != "normal")
        summary = f"四阶段穿透比对：概算→决算总偏差{transitions[-1]['deviation_pct']}%，{alert_count}个阶段预警"

        return {"status": "success", "data": {"transitions": transitions, "item_comparison": item_comparison[:20], "alert_count": alert_count}, "summary": summary}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ─── 工具2：待摊投资分摊校验 ──────────────────────────

def apportioned_investment_check(
    apportioned_items: List[Dict],
    asset_list: List[Dict],
) -> Dict[str, Any]:
    """
    待摊投资分摊合理性校验。
    apportioned_items: [{name, amount, allocation_method: 直接归属/比例分摊/不应分摊, allocated_to: [asset_names]}]
    asset_list: [{name, value}]
    """
    try:
        issues = []
        total_apportioned = 0
        total_assets = sum(float(a.get("value", 0)) for a in asset_list)

        for item in apportioned_items:
            name = item.get("name", "")
            amount = float(item.get("amount", 0))
            method = item.get("allocation_method", "")
            allocated_to = item.get("allocated_to", [])
            total_apportioned += amount

            if method == "不应分摊":
                issues.append({"item": name, "amount": amount, "issue": f"{name}不应纳入待摊投资", "risk": "high"})
            elif method == "直接归属":
                if not allocated_to:
                    issues.append({"item": name, "amount": amount, "issue": "直接归属但未指明受益对象", "risk": "high"})
            elif method == "比例分摊":
                if total_assets > 0 and amount / total_assets > 0.15:
                    issues.append({"item": name, "amount": amount, "issue": f"分摊比例异常偏高({amount/total_assets*100:.1f}%)", "risk": "medium"})
            else:
                issues.append({"item": name, "amount": amount, "issue": f"分摊方法不明确: {method}", "risk": "medium"})

        return {"status": "success", "data": {"issues": issues, "total_apportioned": total_apportioned, "total_assets": total_assets, "issue_count": len(issues)}, "summary": f"待摊投资{total_apportioned:,.0f}元分{len(apportioned_items)}项，{len(issues)}个问题"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ─── 工具3：交付资产-决算勾稽 ──────────────────────────

def delivery_asset_reconciliation(
    delivery_list: List[Dict],
    final_accounts: Dict[str, Any],
) -> Dict[str, Any]:
    """
    交付使用资产明细表 × 竣工决算报表 勾稽。
    delivery_list: [{name, spec, quantity, value}]
    final_accounts: {items: [{name, spec, quantity, value}]}
    """
    try:
        delivery_map = {d["name"]: d for d in delivery_list}
        account_items = final_accounts.get("items", [])
        account_map = {a["name"]: a for a in account_items}

        matched = []
        delivery_only = []
        accounts_only = []
        mismatches = []

        for name, d in delivery_map.items():
            if name in account_map:
                a = account_map[name]
                d_val = float(d.get("value", 0))
                a_val = float(a.get("value", 0))
                diff = abs(d_val - a_val)
                if diff > 0.01 and (a_val > 0):
                    mismatches.append({"name": name, "delivery_value": d_val, "account_value": a_val, "diff": round(diff, 2), "diff_pct": round(diff/a_val*100, 2)})
                matched.append({"name": name, "delivery_value": d_val, "account_value": a_val, "match": diff < 0.01})
            else:
                delivery_only.append({"name": name, "value": d.get("value", 0), "issue": "交付清单有但决算报表无"})

        for name, a in account_map.items():
            if name not in delivery_map:
                accounts_only.append({"name": name, "value": a.get("value", 0), "issue": "决算报表有但交付清单无"})

        return {"status": "success", "data": {
            "total_delivery": len(delivery_list), "total_accounts": len(account_items),
            "matched": len(matched), "delivery_only": delivery_only, "accounts_only": accounts_only,
            "mismatches": mismatches,
            "reconciliation_rate": round(len(matched)/max(len(delivery_map),1)*100, 1),
        }, "summary": f"勾稽率{len(matched)}/{max(len(delivery_map),1)}，差异{len(mismatches)}项，单方{len(delivery_only)+len(accounts_only)}项"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ─── MCP ────────────────────────────────────────────

def handle_request(method: str, params: dict) -> dict:
    tools = {
        "four_stage_penetration": lambda: four_stage_penetration(**{k: params.get(k, {}) for k in ["estimate","budget","settlement","final_accounts"]}),
        "apportioned_investment_check": lambda: apportioned_investment_check(params.get("apportioned_items",[]), params.get("asset_list",[])),
        "delivery_asset_reconciliation": lambda: delivery_asset_reconciliation(params.get("delivery_list",[]), params.get("final_accounts",{})),
    }
    if method in tools:
        return tools[method]()
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    # 测试四阶段穿透
    est = {"total_amount": 100000000, "items": [{"name": "建筑工程", "amount": 60000000}, {"name": "设备购置", "amount": 40000000}]}
    bud = {"total_amount": 95000000, "items": [{"name": "建筑工程", "amount": 58000000}, {"name": "设备购置", "amount": 37000000}]}
    stl = {"total_amount": 108000000, "items": [{"name": "建筑工程", "amount": 65000000}, {"name": "设备购置", "amount": 38000000}, {"name": "新增变更", "amount": 5000000}]}
    fac = {"total_amount": 112000000, "items": [{"name": "建筑工程", "amount": 66000000}, {"name": "设备购置", "amount": 38000000}, {"name": "新增变更", "amount": 8000000}]}

    r1 = four_stage_penetration(est, bud, stl, fac)
    assert r1["status"] == "success"
    assert r1["data"]["transitions"][-1]["deviation_pct"] > 10
    print("four_stage_penetration: OK")

    # 测试待摊投资
    apportioned = [
        {"name": "征地拆迁费", "amount": 5000000, "allocation_method": "直接归属", "allocated_to": ["建筑工程"]},
        {"name": "建设单位管理费", "amount": 2000000, "allocation_method": "比例分摊", "allocated_to": ["建筑工程", "设备购置"]},
        {"name": "生产经营相关费用", "amount": 300000, "allocation_method": "不应分摊", "allocated_to": []},
    ]
    assets = [{"name": "建筑工程", "value": 60000000}, {"name": "设备购置", "value": 40000000}]
    r2 = apportioned_investment_check(apportioned, assets)
    assert r2["data"]["issue_count"] >= 1
    print("apportioned_investment_check: OK")

    # 测试勾稽
    delivery = [{"name": "综合楼", "spec": "框架结构", "quantity": 1, "value": 50000000}, {"name": "门卫室", "spec": "砖混", "quantity": 1, "value": 200000}]
    accounts = {"items": [{"name": "综合楼", "spec": "框架结构", "quantity": 1, "value": 51000000}, {"name": "配电房", "spec": "框架", "quantity": 1, "value": 800000}]}
    r3 = delivery_asset_reconciliation(delivery, accounts)
    assert r3["data"]["mismatches"] or r3["data"]["delivery_only"] or r3["data"]["accounts_only"]
    print("delivery_asset_reconciliation: OK")

    print("\n✅ 工程竣工财务决算3工具全部通过")
