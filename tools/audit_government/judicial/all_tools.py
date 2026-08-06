"""
P2：司法审计 + 监督检查 + 清单编制 工具集

作者：融策审计智析Agent | 日期：2026-07-22
"""

from typing import Dict, List, Any
from datetime import datetime


# ═══════════ 司法审计 ═══════════

def fund_trace_visualizer(
    transactions: List[Dict],
    *,
    target_account: str = None,
    max_depth: int = 5,
) -> Dict[str, Any]:
    """
    资金追踪可视化（司法标准）。
    transactions: [{id, from_account, to_account, amount, date, summary}]
    """
    try:
        # 构建追踪树
        nodes = {}
        edges = []

        for tx in transactions:
            frm = tx.get("from_account", "")
            to = tx.get("to_account", "")
            amt = float(tx.get("amount", 0))
            date = tx.get("date", "")
            summary = tx.get("summary", "")

            for acc in [frm, to]:
                if acc not in nodes and acc:
                    nodes[acc] = {"account": acc, "inflow": 0, "outflow": 0, "tx_count": 0}

            if frm in nodes:
                nodes[frm]["outflow"] += amt
                nodes[frm]["tx_count"] += 1
            if to in nodes:
                nodes[to]["inflow"] += amt
                nodes[to]["tx_count"] += 1

            edges.append({"from": frm, "to": to, "amount": amt, "date": date, "summary": summary[:80]})

        # 找出关键路径（金额最大的链路）
        edges.sort(key=lambda x: x["amount"], reverse=True)
        total_flow = sum(e["amount"] for e in edges)

        # 中间账户（既是 inflow 也是 outflow）
        intermediary = [n for n in nodes.values() if n["inflow"] > 0 and n["outflow"] > 0]
        # 终点账户
        endpoints = [n for n in nodes.values() if n["inflow"] > 0 and n["outflow"] == 0]

        return {"status": "success", "data": {
            "nodes": list(nodes.values()), "edges": edges[:50], "total_flow": round(total_flow, 2),
            "intermediary_accounts": intermediary, "endpoint_accounts": endpoints,
            "key_paths": [_find_key_paths(edges, target_account or "")],
            "account_count": len(nodes), "edge_count": len(edges),
        }, "summary": f"资金网络：{len(nodes)}个账户，{len(edges)}笔交易，{len(intermediary)}个中转账户"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def _find_key_paths(edges: List[Dict], target: str, depth: int = 3) -> List[Dict]:
    """找到目标账户的关键出入路径"""
    flows_in = [e for e in edges if e["to"] == target]
    flows_out = [e for e in edges if e["from"] == target]
    return {"target": target, "inflows": sorted(flows_in, key=lambda x: x["amount"], reverse=True)[:5],
            "outflows": sorted(flows_out, key=lambda x: x["amount"], reverse=True)[:5]}


def loss_quantification_model(
    loss_items: List[Dict],
) -> Dict[str, Any]:
    """
    损失金额计算模型。
    loss_items: [{type: 虚增成本/虚减收入/关联非公允/资产侵占, params: {...}}]
    """
    try:
        results = []
        total_loss = 0.0

        for item in loss_items:
            loss_type = item.get("type", "")
            params = item.get("params", {})

            if loss_type == "虚增成本":
                inflated = float(params.get("inflated_amount", 0))
                reasonable_rate = float(params.get("reasonable_profit_rate", 0.05))
                loss = inflated * (1 + reasonable_rate)
                legal = "《会计法》第二十六条：不得虚列支出"

            elif loss_type == "虚减收入":
                unrecorded = float(params.get("unrecorded_revenue", 0))
                loss = unrecorded
                legal = "《会计法》第二十六条：不得隐匿收入"

            elif loss_type == "关联非公允":
                fair_price = float(params.get("fair_price", 0))
                actual_price = float(params.get("actual_price", 0))
                volume = float(params.get("transaction_volume", 1))
                loss = (fair_price - actual_price) * volume
                legal = "《企业国有资产法》第四十四条：不得以不公平价格与关联方交易"

            elif loss_type == "资产侵占":
                book_value = float(params.get("book_value", 0))
                recoverable = float(params.get("recoverable_value", 0))
                loss = book_value - recoverable
                legal = "《刑法》第二百七十一条：职务侵占罪"

            else:
                loss = 0
                legal = ""

            if loss > 0:
                results.append({"type": loss_type, "loss_amount": round(loss, 2), "description": params.get("description", ""),
                               "legal_basis": legal, "params": params})
                total_loss += loss

        return {"status": "success", "data": {"loss_items": results, "total_loss": round(total_loss, 2), "item_count": len(results)},
                "summary": f"{len(results)}项损失，合计{total_loss:,.2f}元"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ═══════════ 监督检查 ═══════════

def risk_based_inspection_planner(
    history_issues: List[Dict],
    fund_distribution: List[Dict],
    policy_priorities: List[Dict],
) -> Dict[str, Any]:
    """
    风险导向检查计划生成。三维排序：历史问题密度(30%) + 资金规模(30%) + 政策优先级(40%)
    """
    try:
        # 历史问题密度
        issue_density: Dict[str, Dict] = {}
        for h in history_issues:
            dept = h.get("dept", "")
            if dept not in issue_density:
                issue_density[dept] = {"count": 0, "total_amount": 0}
            issue_density[dept]["count"] += 1
            issue_density[dept]["total_amount"] += float(h.get("amount", 0))

        max_issues = max((v["count"] for v in issue_density.values()), default=1)

        # 资金规模
        fund_map = {f.get("dept", ""): float(f.get("amount", 0)) for f in fund_distribution}
        max_fund = max(fund_map.values(), default=1)

        # 政策优先级
        policy_map = {p.get("dept", ""): float(p.get("priority_score", 5)) for p in policy_priorities}

        # 所有部门
        all_depts = set(list(issue_density.keys()) + list(fund_map.keys()) + list(policy_map.keys()))
        scores = []

        for dept in all_depts:
            issue_score = (issue_density.get(dept, {}).get("count", 0) / max_issues * 30) if max_issues > 0 else 0
            fund_score = (fund_map.get(dept, 0) / max_fund * 30) if max_fund > 0 else 0
            policy_score = policy_map.get(dept, 5) / 10 * 40

            total = issue_score + fund_score + policy_score
            scores.append({
                "dept": dept,
                "score": round(total, 1),
                "breakdown": {"历史问题": round(issue_score, 1), "资金规模": round(fund_score, 1), "政策优先级": round(policy_score, 1)},
                "suggested_sample_pct": 100 if total > 70 else (50 if total > 40 else 20),
                "priority": "P0" if total > 70 else ("P1" if total > 40 else "P2"),
            })

        scores.sort(key=lambda x: x["score"], reverse=True)
        return {"status": "success", "data": {"plan": scores, "p0_count": sum(1 for s in scores if s["priority"] == "P0")},
                "summary": f"检查计划：{len(scores)}个部门排序完成，P0级{sum(1 for s in scores if s['priority']=='P0')}个"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def rectification_tracker(
    issues: List[Dict],
    rectification_reports: List[Dict],
    *,
    reference_date: str = None,
) -> Dict[str, Any]:
    """
    整改销号管理 + 同类问题跨项目归因。
    issues: [{id, description, type, dept, project, find_date, responsible, deadline}]
    rectification_reports: [{issue_id, report_date, status: 已整改/整改中/未整改, evidence}]
    """
    try:
        ref_date = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()
        report_map = {r["issue_id"]: r for r in rectification_reports}

        tracked = []
        overdue = []
        completed = []
        pending = []

        for iss in issues:
            iid = iss.get("id", "")
            deadline = iss.get("deadline", "")
            report = report_map.get(iid, {})

            # 判定状态
            if report.get("status") == "已整改":
                status = "已完成"
                completed.append(iid)
            elif report.get("status") == "整改中":
                # 检查是否逾期
                if deadline:
                    try:
                        dl = datetime.strptime(deadline, "%Y-%m-%d")
                        status = "逾期未完成" if ref_date > dl else "整改中"
                    except ValueError:
                        status = "整改中"
                else:
                    status = "整改中"
                if status == "逾期未完成":
                    overdue.append(iid)
                else:
                    pending.append(iid)
            else:
                if deadline:
                    try:
                        dl = datetime.strptime(deadline, "%Y-%m-%d")
                        status = "超期未整改" if ref_date > dl else "待整改"
                    except ValueError:
                        status = "待整改"
                else:
                    status = "待整改"
                if "超期" in status:
                    overdue.append(iid)
                else:
                    pending.append(iid)

            tracked.append({"issue_id": iid, "description": iss.get("description", "")[:100],
                           "status": status, "deadline": deadline, "report_date": report.get("report_date", "")})

        # 同类问题归因（同类型+同部门+不同项目）
        from collections import defaultdict
        pattern_map = defaultdict(list)
        for iss in issues:
            key = f"{iss.get('type','')}_{iss.get('dept','')}"
            pattern_map[key].append(iss.get("id", ""))

        systemic_risks = []
        for key, ids in pattern_map.items():
            if len(ids) >= 3:
                systemic_risks.append({"pattern_key": key, "issue_count": len(ids), "issue_ids": ids,
                                      "assessment": "同部门多次出现同类问题，可能存在系统性管理缺陷"})

        total = len(tracked)
        completion_rate = len(completed) / max(total, 1) * 100

        return {"status": "success", "data": {"tracked": tracked, "completed": len(completed), "overdue": len(overdue),
                "pending": len(pending), "completion_rate": round(completion_rate, 1), "systemic_risks": systemic_risks,
                "total": total},
                "summary": f"整改跟踪：完成{len(completed)}、逾期{len(overdue)}、待整改{len(pending)}，完成率{completion_rate:.0f}%"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ═══════════ 清单编制 ═══════════

def boq_omission_detector(
    design_items: List[Dict],
    boq_items: List[Dict],
) -> Dict[str, Any]:
    """
    工程量清单漏项检测。
    design_items: [{name, spec, estimated_qty, unit}]
    boq_items: [{code, name, unit, quantity}]
    """
    try:
        boq_names = {b.get("name", "") for b in boq_items}
        omissions = []

        for d in design_items:
            name = d.get("name", "")
            if name not in boq_names:
                # 模糊匹配
                matched = False
                for bn in boq_names:
                    if name in bn or bn in name:
                        matched = True
                        break
                if not matched:
                    omissions.append({"name": name, "estimated_qty": d.get("estimated_qty", 0),
                                     "unit": d.get("unit", ""), "spec": d.get("spec", ""),
                                     "risk": "high" if d.get("estimated_qty", 0) > 100 else "medium"})

        return {"status": "success", "data": {"omissions": omissions, "omission_count": len(omissions)},
                "summary": f"检测到{len(omissions)}项疑似漏项"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def unit_price_benchmark(
    current_prices: List[Dict],
    historical_prices: List[Dict],
    *,
    max_deviation_pct: float = 20.0,
) -> Dict[str, Any]:
    """
    综合单价合理性多维度对比。
    current/historical: [{code, name, unit_price, project_name, date}]
    """
    try:
        hist_map: Dict[str, List[float]] = {}
        for h in historical_prices:
            code = h.get("code", "")
            if code not in hist_map:
                hist_map[code] = []
            hist_map[code].append(float(h.get("unit_price", 0)))

        anomalies = []
        for c in current_prices:
            code = c.get("code", "")
            price = float(c.get("unit_price", 0))
            hist_prices = hist_map.get(code, [])
            if hist_prices:
                avg = sum(hist_prices) / len(hist_prices)
                std = (sum((p - avg) ** 2 for p in hist_prices) / len(hist_prices)) ** 0.5
                if avg > 0:
                    dev = (price - avg) / avg * 100
                    if abs(dev) > max_deviation_pct:
                        anomalies.append({"code": code, "name": c.get("name", ""), "current_price": price,
                                         "hist_avg": round(avg, 2), "hist_std": round(std, 2),
                                         "deviation_pct": round(dev, 2), "sample_count": len(hist_prices),
                                         "position": "偏高" if dev > 0 else "偏低"})

        anomalies.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)
        return {"status": "success", "data": {"anomalies": anomalies, "anomaly_count": len(anomalies)},
                "summary": f"{len(anomalies)}项综合单价偏离历史均价超过{max_deviation_pct}%"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ─── MCP ────────────────────────────────────────────

def handle_request(method: str, params: dict) -> dict:
    tools = {
        "fund_trace_visualizer": lambda: fund_trace_visualizer(params.get("transactions",[]), target_account=params.get("target_account"), max_depth=params.get("max_depth",5)),
        "loss_quantification_model": lambda: loss_quantification_model(params.get("loss_items",[])),
        "risk_based_inspection_planner": lambda: risk_based_inspection_planner(params.get("history_issues",[]), params.get("fund_distribution",[]), params.get("policy_priorities",[])),
        "rectification_tracker": lambda: rectification_tracker(params.get("issues",[]), params.get("rectification_reports",[]), reference_date=params.get("reference_date")),
        "boq_omission_detector": lambda: boq_omission_detector(params.get("design_items",[]), params.get("boq_items",[])),
        "unit_price_benchmark": lambda: unit_price_benchmark(params.get("current_prices",[]), params.get("historical_prices",[]), max_deviation_pct=params.get("max_deviation_pct",20.0)),
    }
    if method in tools:
        return tools[method]()
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    # 资金追踪
    r1 = fund_trace_visualizer([
        {"id": "T1", "from_account": "财政专户", "to_account": "A公司", "amount": 5000000, "date": "2025-01-15", "summary": "补贴款"},
        {"id": "T2", "from_account": "A公司", "to_account": "B个人", "amount": 4500000, "date": "2025-01-20", "summary": "备用金"},
    ])
    assert r1["data"]["account_count"] >= 3
    print("fund_trace_visualizer: OK")

    # 损失计算
    r2 = loss_quantification_model([
        {"type": "虚增成本", "params": {"inflated_amount": 2000000, "reasonable_profit_rate": 0.05, "description": "虚列材料采购"}},
        {"type": "关联非公允", "params": {"fair_price": 100, "actual_price": 60, "transaction_volume": 50000, "description": "低价关联交易"}},
    ])
    assert r2["data"]["total_loss"] > 0
    print("loss_quantification_model: OK")

    # 检查计划
    r3 = risk_based_inspection_planner(
        [{"dept": "住建局", "amount": 5000000}, {"dept": "交通局", "amount": 3000000}],
        [{"dept": "住建局", "amount": 100000000}, {"dept": "教育局", "amount": 50000000}],
        [{"dept": "住建局", "priority_score": 9}, {"dept": "教育局", "priority_score": 7}])
    assert len(r3["data"]["plan"]) >= 2
    print("risk_based_inspection_planner: OK")

    # 整改跟踪
    r4 = rectification_tracker(
        [{"id": "I001", "description": "预算执行超支", "type": "预算", "dept": "住建局", "find_date": "2025-06-01", "deadline": "2025-12-31"},
         {"id": "I002", "description": "无预算支出", "type": "预算", "dept": "住建局", "find_date": "2025-06-01", "deadline": "2025-09-30"}],
        [{"issue_id": "I001", "report_date": "2025-11-01", "status": "已整改"}])
    assert r4["data"]["completion_rate"] == 50
    print("rectification_tracker: OK")

    # 漏项检测
    r5 = boq_omission_detector(
        [{"name": "混凝土基础", "spec": "C30", "estimated_qty": 500, "unit": "m3"}, {"name": "防水层", "spec": "SBS", "estimated_qty": 2000, "unit": "m2"}],
        [{"code": "010501", "name": "混凝土基础", "unit": "m3", "quantity": 500}])
    assert r5["data"]["omission_count"] >= 1
    print("boq_omission_detector: OK")

    # 单价对比
    r6 = unit_price_benchmark(
        [{"code": "010101", "name": "挖土方", "unit_price": 45}],
        [{"code": "010101", "name": "挖土方", "unit_price": 25}, {"code": "010101", "name": "挖土方", "unit_price": 28}])
    assert r6["data"]["anomaly_count"] >= 1
    print("unit_price_benchmark: OK")

    print("\n✅ P2司法+监督+清单6工具全部通过")
