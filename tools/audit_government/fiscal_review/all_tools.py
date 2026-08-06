"""
P2：财政评审 + 全过程工程咨询 + 专项审计/内部审计补充

作者：融策审计智析Agent | 日期：2026-07-22
"""

from typing import Dict, List, Any
from datetime import datetime
import math


# ═══════════ 财政评审 ═══════════

def estimate_reasonableness(
    estimate: Dict[str, Any],
    *,
    construction_standards: Dict[str, Any] = None,
    cost_index: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    概算合理性评审。estimate: {total, items: [{name, area_sqm, unit_cost, standard}], project_type}
    construction_standards: {项目类型: {面积上限, 单价上限}}
    cost_index: {项目类型: 行业均价}
    """
    try:
        issues = []
        project_type = estimate.get("project_type", "")

        for item in estimate.get("items", []):
            name = item.get("name", "")
            area = float(item.get("area_sqm", 0))
            unit_cost = float(item.get("unit_cost", 0))

            # 建设标准对标
            if construction_standards and project_type in construction_standards:
                std = construction_standards[project_type]
                area_cap = float(std.get("area_cap", float("inf")))
                cost_cap = float(std.get("unit_cost_cap", float("inf")))
                if area > area_cap:
                    issues.append({"item": name, "type": "面积超标", "actual": area, "limit": area_cap, "excess": round(area - area_cap, 2)})
                if unit_cost > cost_cap:
                    issues.append({"item": name, "type": "单价超标", "actual": unit_cost, "limit": cost_cap, "excess_pct": round((unit_cost/cost_cap-1)*100, 2)})

            # 行业造价对标
            if cost_index and project_type in cost_index:
                benchmark = cost_index[project_type]
                if benchmark > 0:
                    dev = (unit_cost - benchmark) / benchmark * 100
                    if abs(dev) > 20:
                        issues.append({"item": name, "type": "偏离行业均价", "actual": unit_cost, "benchmark": benchmark, "deviation_pct": round(dev, 2)})

        total_issues = len(issues)
        return {"status": "success", "data": {"issues": issues, "total_items": len(estimate.get("items", [])),
                "issue_count": total_issues, "risk": "严重" if total_issues >= 3 else ("需关注" if total_issues >= 1 else "合理")},
                "summary": f"概算{len(estimate.get('items',[]))}项中{total_issues}项存在不合理"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def investment_control_evaluation(
    projects: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    投资控制效果评价。projects: [{name, estimate, budget, settlement, final_accounts}]
    """
    try:
        results = []

        for p in projects:
            est = float(p.get("estimate", 0))
            bud = float(p.get("budget", 0))
            stl = float(p.get("settlement", 0))
            fac = float(p.get("final_accounts", 0))

            compression = _safe_pct(est, bud, "compression")
            savings = _safe_pct(bud, stl, "savings")
            variation = _safe_pct(stl, fac, "variation")

            scores = {
                "概算→预算压缩率": _score(compression, 5, 15),  # 理想范围5-15%
                "预算→结算节约率": _score(savings, 0, 10),       # 正值为节约，理想0-10%
                "结算→决算变化率": _score(variation, -5, 5),    # 理想范围±5%
            }

            total_score = sum(scores.values())
            results.append({
                "name": p.get("name", ""),
                "estimate": est, "budget": bud, "settlement": stl, "final_accounts": fac,
                "compression_pct": round(compression, 2), "savings_pct": round(savings, 2), "variation_pct": round(variation, 2),
                "scores": scores, "total_score": round(total_score, 1),
                "rating": "优秀" if total_score >= 80 else ("良好" if total_score >= 60 else ("合格" if total_score >= 40 else "不足")),
            })

        return {"status": "success", "data": {"projects": results},
                "summary": f"{len(results)}个项目投资控制效果评价完成"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def _safe_pct(frm: float, to: float, name: str) -> float:
    if frm > 0:
        return (to - frm) / frm * 100
    return 0


def _score(pct: float, low_ideal: float, high_ideal: float) -> float:
    """评分：在理想区间内满分，偏离则扣分"""
    if low_ideal <= pct <= high_ideal:
        return 100
    dist = min(abs(pct - low_ideal), abs(pct - high_ideal))
    return max(0, 100 - dist * 2)


# ═══════════ 全过程工程咨询 ═══════════

def evm_auto_analyzer(
    plan_data: Dict[str, float],
    actual_data: Dict[str, float],
    *,
    period: str = "",
) -> Dict[str, Any]:
    """
    挣值管理(EVM)自动分析。
    plan_data: {PV(计划价值), BAC(完工预算)}
    actual_data: {EV(挣值), AC(实际成本)}
    """
    try:
        pv = float(plan_data.get("PV", 0))
        bac = float(plan_data.get("BAC", 0))
        ev = float(actual_data.get("EV", 0))
        ac = float(actual_data.get("AC", 0))

        sv = ev - pv  # 进度偏差
        cv = ev - ac  # 成本偏差
        spi = ev / pv if pv > 0 else 1  # 进度绩效指数
        cpi = ev / ac if ac > 0 else 1  # 成本绩效指数

        # 完工估算 EAC
        if cpi > 0:
            eac = ac + (bac - ev) / cpi
        else:
            eac = bac

        # 完工偏差
        vac = bac - eac

        # 诊断
        diagnosis = []
        if spi < 0.8:
            diagnosis.append(f"进度严重滞后(SPI={spi:.2f})")
        elif spi < 0.95:
            diagnosis.append(f"进度轻度滞后(SPI={spi:.2f})")
        elif spi > 1.1:
            diagnosis.append(f"进度超前(SPI={spi:.2f})")

        if cpi < 0.8:
            diagnosis.append(f"成本严重超支(CPI={cpi:.2f})")
        elif cpi < 0.95:
            diagnosis.append(f"成本轻度超支(CPI={cpi:.2f})")
        elif cpi > 1.1:
            diagnosis.append(f"成本节约(CPI={cpi:.2f})")

        risk = "严重" if (spi < 0.8 or cpi < 0.8) else ("关注" if (spi < 0.95 or cpi < 0.95) else "正常")

        return {"status": "success", "data": {
            "PV": round(pv, 2), "EV": round(ev, 2), "AC": round(ac, 2), "BAC": round(bac, 2),
            "SV": round(sv, 2), "CV": round(cv, 2), "SPI": round(spi, 3), "CPI": round(cpi, 3),
            "EAC": round(eac, 2), "VAC": round(vac, 2), "diagnosis": diagnosis, "risk": risk,
        }, "summary": f"SPI={spi:.2f}, CPI={cpi:.2f}, EAC={eac:,.0f}, 风险: {risk}"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def contract_performance_monitor(
    contracts: List[Dict[str, Any]],
    *,
    reference_date: str = None,
) -> Dict[str, Any]:
    """
    合同履约风险动态监测。
    contracts: [{id, name, milestones: [{name, planned_date, actual_date}], key_personnel_changes: [{role, from_person, to_person}],
                material_deviations: [{item, contract_spec, actual_spec}], cumulative_changes_amount, contract_amount}]
    """
    try:
        ref_date = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()
        risks = []

        for c in contracts:
            contract_risks = []
            risk_score = 0

            # 里程碑逾期
            for ms in c.get("milestones", []):
                planned = ms.get("planned_date", "")
                actual = ms.get("actual_date") or ""
                if planned:
                    try:
                        pd = datetime.strptime(planned, "%Y-%m-%d")
                        if not actual and pd < ref_date:
                            contract_risks.append(f"里程碑'{ms.get('name','')}'已逾期({planned})")
                            risk_score += 3
                        elif actual:
                            ad = datetime.strptime(actual, "%Y-%m-%d")
                            if ad > pd:
                                delay = (ad - pd).days
                                contract_risks.append(f"里程碑'{ms.get('name','')}'延迟{delay}天")
                                risk_score += 2 if delay > 30 else 1
                    except ValueError:
                        pass

            # 关键人员变更
            for kp in c.get("key_personnel_changes", []):
                contract_risks.append(f"关键人员变更: {kp.get('role','')} {kp.get('from_person','')}→{kp.get('to_person','')}")
                risk_score += 2

            # 材料异常
            for md in c.get("material_deviations", []):
                contract_risks.append(f"材料与合同不符: {md.get('item','')}")
                risk_score += 2

            # 变更膨胀
            changes = float(c.get("cumulative_changes_amount", 0))
            contract_amt = float(c.get("contract_amount", 1))
            change_pct = changes / contract_amt * 100
            if change_pct > 15:
                contract_risks.append(f"累计变更占比{change_pct:.1f}%，超过15%警戒线")
                risk_score += 3
            elif change_pct > 10:
                contract_risks.append(f"累计变更占比{change_pct:.1f}%，接近警戒线")
                risk_score += 1

            if contract_risks:
                risks.append({
                    "contract_id": c.get("id", ""), "contract_name": c.get("name", ""),
                    "risks": contract_risks, "risk_score": risk_score,
                    "risk_level": "high" if risk_score >= 6 else ("medium" if risk_score >= 3 else "low"),
                })

        risks.sort(key=lambda x: x["risk_score"], reverse=True)
        return {"status": "success", "data": {"risks": risks, "total_contracts": len(contracts),
                "risky_contracts": len(risks), "high_risk_count": sum(1 for r in risks if r["risk_level"] == "high")},
                "summary": f"{len(contracts)}个合同，{len(risks)}个存在履约风险，高风险{sum(1 for r in risks if r['risk_level']=='high')}个"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


def document_chain_trace(
    documents: List[Dict[str, Any]],
    *,
    required_docs_per_phase: Dict[str, List[str]] = None,
) -> Dict[str, Any]:
    """
    全过程文档链自动化追溯。
    documents: [{name, phase(决策/设计/招标/施工/竣工), date, ref_doc_ids: [str]}]
    required_docs_per_phase: {阶段: [必需文档名称]}
    """
    try:
        if required_docs_per_phase is None:
            required_docs_per_phase = {
                "决策": ["项目建议书", "可行性研究报告", "立项批复"],
                "设计": ["初步设计", "施工图设计", "设计审查意见"],
                "招标": ["招标文件", "中标通知书", "施工合同"],
                "施工": ["开工报告", "施工组织设计", "监理日志"],
                "竣工": ["竣工报告", "竣工验收证书", "竣工图", "结算报告"],
            }

        docs_by_phase: Dict[str, List[Dict]] = {}
        for d in documents:
            phase = d.get("phase", "")
            if phase not in docs_by_phase:
                docs_by_phase[phase] = []
            docs_by_phase[phase].append(d)

        missing_docs = []
        time_logic_issues = []

        # 检查必需文档
        for phase, required in required_docs_per_phase.items():
            existing_names = [d.get("name", "") for d in docs_by_phase.get(phase, [])]
            for req in required:
                if not any(req in en for en in existing_names):
                    missing_docs.append({"phase": phase, "required_doc": req})

        # 时间逻辑检查
        phase_order = ["决策", "设计", "招标", "施工", "竣工"]
        for i in range(1, len(phase_order)):
            prev_docs = docs_by_phase.get(phase_order[i-1], [])
            curr_docs = docs_by_phase.get(phase_order[i], [])
            if prev_docs and curr_docs:
                prev_max_date = max((d.get("date", "0000-00-00") for d in prev_docs), default="0000-00-00")
                curr_min_date = min((d.get("date", "9999-99-99") for d in curr_docs), default="9999-99-99")
                if prev_max_date > curr_min_date:
                    time_logic_issues.append({
                        "from_phase": phase_order[i-1], "to_phase": phase_order[i],
                        "from_max_date": prev_max_date, "to_min_date": curr_min_date,
                        "issue": f"{phase_order[i]}阶段文档日期早于{phase_order[i-1]}阶段文档"
                    })

        completeness = (1 - len(missing_docs) / sum(len(v) for v in required_docs_per_phase.values())) * 100

        return {"status": "success", "data": {
            "total_docs": len(documents), "phases_covered": len(docs_by_phase),
            "missing_docs": missing_docs, "time_logic_issues": time_logic_issues,
            "completeness_pct": round(completeness, 1),
            "assessment": "完整" if completeness >= 90 else ("基本完整" if completeness >= 70 else "存在缺失"),
        }, "summary": f"{len(documents)}份文档，缺失{len(missing_docs)}份必需文档，完整度{completeness:.0f}%"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ═══════════ 专项审计补充：方案自动生成 ═══════════

def audit_plan_generator(
    audit_objective: str,
    fund_amount: float,
    *,
    history_issues: List[Dict] = None,
) -> Dict[str, Any]:
    """专项审计方案自动生成器"""
    try:
        # 工具推荐映射
        tool_map = {
            "预算执行": ["budget_deviation_engine", "no_budget_detector", "carryover_compliance"],
            "采购": ["supplier_fingerprint", "bid_rigging_detector", "contract_field_extract"],
            "资金": ["fund_trace_visualizer", "benford_analysis", "three_flow_checker"],
            "工程": ["four_stage_penetration", "boq_vs_actual_quantity_check", "change_order_reasonableness"],
            "内控": ["coso_five_elements", "segregation_duties_check", "walkthrough_test_engine"],
            "绩效": ["multi_source_scoring", "performance_benchmark"],
        }

        # 匹配工具
        recommended_tools = []
        for keyword, tools in tool_map.items():
            if keyword in audit_objective:
                recommended_tools.extend(tools)

        if not recommended_tools:
            recommended_tools = ["analyze_budget_deviation", "detect_no_budget_expenditure"]

        # 抽样策略
        if fund_amount > 100000000:
            sample_pct = 20
            sample_strategy = "重点全额+其余随机抽样"
        elif fund_amount > 10000000:
            sample_pct = 30
            sample_strategy = "分层抽样（高金额100%+中金额50%+低金额10%）"
        else:
            sample_pct = 50
            sample_strategy = "不低于50%随机抽样"

        # 历史问题关注
        focus_areas = []
        if history_issues:
            from collections import Counter
            types = Counter(h.get("type", "") for h in history_issues)
            focus_areas = [f"{t}(历史{count}次)" for t, count in types.most_common(3)]

        return {"status": "success", "data": {
            "audit_objective": audit_objective,
            "recommended_tools": list(set(recommended_tools)),
            "sample_strategy": sample_strategy,
            "sample_pct": sample_pct,
            "focus_areas": focus_areas,
            "estimated_days": max(5, int(fund_amount / 5000000)),
        }, "summary": f"生成审计方案：{len(recommended_tools)}个工具，抽样比例{sample_pct}%"}
    except Exception as e:
        return {"status": "error", "data": None, "summary": str(e)}


# ─── MCP ────────────────────────────────────────────

def handle_request(method: str, params: dict) -> dict:
    tools = {
        "estimate_reasonableness": lambda: estimate_reasonableness(params.get("estimate",{}), construction_standards=params.get("construction_standards"), cost_index=params.get("cost_index")),
        "investment_control_evaluation": lambda: investment_control_evaluation(params.get("projects",[])),
        "evm_auto_analyzer": lambda: evm_auto_analyzer(params.get("plan_data",{}), params.get("actual_data",{}), period=params.get("period","")),
        "contract_performance_monitor": lambda: contract_performance_monitor(params.get("contracts",[]), reference_date=params.get("reference_date")),
        "document_chain_trace": lambda: document_chain_trace(params.get("documents",[]), required_docs_per_phase=params.get("required_docs_per_phase")),
        "audit_plan_generator": lambda: audit_plan_generator(params.get("audit_objective",""), params.get("fund_amount",0), history_issues=params.get("history_issues")),
    }
    if method in tools:
        return tools[method]()
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    # 概算评审
    r1 = estimate_reasonableness(
        {"project_type": "办公楼", "items": [{"name": "建筑主体", "area_sqm": 8000, "unit_cost": 4500}]},
        construction_standards={"办公楼": {"area_cap": 5000, "unit_cost_cap": 4000}},
        cost_index={"办公楼": 3800})
    assert r1["data"]["issue_count"] >= 1
    print("estimate_reasonableness: OK")

    # 投资管控
    r2 = investment_control_evaluation([
        {"name": "项目X", "estimate": 100000000, "budget": 92000000, "settlement": 88000000, "final_accounts": 91000000},
    ])
    assert r2["data"]["projects"][0]["rating"] != ""
    print("investment_control_evaluation: OK")

    # EVM
    r3 = evm_auto_analyzer({"PV": 5000000, "BAC": 20000000}, {"EV": 4500000, "AC": 5200000})
    assert 0 < r3["data"]["SPI"] < 1.5
    print("evm_auto_analyzer: OK")

    # 合同履约
    r4 = contract_performance_monitor([
        {"id": "C001", "name": "施工总承包", "milestones": [{"name": "主体封顶", "planned_date": "2025-06-30", "actual_date": ""}],
         "key_personnel_changes": [{"role": "项目经理", "from_person": "张三", "to_person": "李四"}],
         "material_deviations": [], "cumulative_changes_amount": 2500000, "contract_amount": 10000000},
    ], reference_date="2026-07-22")
    assert r4["data"]["high_risk_count"] >= 1
    print("contract_performance_monitor: OK")

    # 文档链
    r5 = document_chain_trace([
        {"name": "可行性研究报告", "phase": "决策", "date": "2025-01-15"},
        {"name": "施工图设计", "phase": "设计", "date": "2025-06-01"},
        {"name": "施工合同", "phase": "招标", "date": "2025-05-15"},
        {"name": "开工报告", "phase": "施工", "date": "2025-11-01"},
    ])
    assert len(r5["data"]["time_logic_issues"]) >= 1 or len(r5["data"]["missing_docs"]) >= 1
    print("document_chain_trace: OK")

    # 审计方案
    r6 = audit_plan_generator("财政预算执行和专项资金审计", 50000000, history_issues=[{"type": "超预算支出"}, {"type": "超预算支出"}, {"type": "结转超期"}])
    assert len(r6["data"]["recommended_tools"]) >= 1
    print("audit_plan_generator: OK")

    print("\n✅ P2财政评审+全过程咨询+补充工具6个全部通过")
