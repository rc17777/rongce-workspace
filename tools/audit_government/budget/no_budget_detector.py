"""
无预算支出检测器 — No-Budget Expenditure Detector

核心功能：扫描实际支出中无预算安排的科目，按金额和风险分级。
适用场景：预算执行情况审计、财政纪律检查。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from typing import Dict, List, Any


def detect_no_budget_expenditure(
    budget_data: Dict[str, Dict[str, Any]],
    execution_data: Dict[str, Dict[str, Any]],
    *,
    threshold: float = 10000.0,
    include_suspicious_transfers: bool = True,
) -> Dict[str, Any]:
    """
    检测无预算安排的支出。

    Args:
        budget_data: 预算批复表 {科目代码: {"name": str, "budget": float, ...}}
        execution_data: 执行报表 {科目代码: {"name": str, "actual": float, ...}}
        threshold: 金额阈值(元)，低于此金额的忽略
        include_suspicious_transfers: 是否检测可疑的科目间转移

    Returns:
        {
            "status": "success"/"error",
            "data": {
                "no_budget_items": [...],
                "total_no_budget_amount": float,
                "total_execution": float,
                "ratio_pct": float,
                "suspicious_transfers": [...]  (如果启用)
            },
            "summary": str
        }
    """
    try:
        budget_codes = set(budget_data.keys())
        exec_codes = set(execution_data.keys())

        # 无预算但有支出的科目
        no_budget_codes = exec_codes - budget_codes

        total_execution = sum(float(e.get("actual", 0)) for e in execution_data.values())

        no_budget_items: List[Dict[str, Any]] = []
        total_no_budget = 0.0

        for code in no_budget_codes:
            item = execution_data[code]
            actual = float(item.get("actual", 0))
            if actual < threshold:
                continue

            # 判断疑似类型
            suspicious_type = _classify_no_budget_type(code, item, budget_data)

            no_budget_items.append({
                "code": code,
                "name": item.get("name", ""),
                "amount": round(actual, 2),
                "category": item.get("category", ""),
                "economic": item.get("economic", ""),
                "dept": item.get("dept", ""),
                "suspicious_type": suspicious_type,
                "risk_level": "high" if actual > 500000 else ("medium" if actual > 100000 else "low"),
            })
            total_no_budget += actual

        # 按金额降序
        no_budget_items.sort(key=lambda x: x["amount"], reverse=True)

        ratio = (total_no_budget / total_execution * 100) if total_execution > 0 else 0.0

        result = {
            "no_budget_items": no_budget_items,
            "total_no_budget_amount": round(total_no_budget, 2),
            "total_execution": round(total_execution, 2),
            "ratio_pct": round(ratio, 2),
            "item_count": len(no_budget_items),
        }

        if include_suspicious_transfers:
            result["suspicious_transfers"] = _detect_suspicious_transfers(budget_data, execution_data)

        summary = f"检出{len(no_budget_items)}项无预算支出，合计{total_no_budget:,.2f}元（占总支出的{ratio:.2f}%）"
        if ratio > 5:
            summary += " — ⚠️ 占比超过5%，需重点关注"

        return {"status": "success", "data": result, "summary": summary}

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"检测异常: {str(e)}"}


def _classify_no_budget_type(
    code: str, item: Dict, budget_data: Dict
) -> str:
    """判断无预算支出的疑似类型"""
    name = item.get("name", "")
    dept = item.get("dept", "")
    economic = item.get("economic", "")
    amount = float(item.get("actual", 0))

    # 检查是否可能是科目串用（同名科目在其他代码下有预算）
    similar_in_budget = False
    for bc, bv in budget_data.items():
        if bv.get("name", "") == name and bc != code:
            similar_in_budget = True
            break

    if similar_in_budget:
        return "科目串用可能 — 该名称在预算表其他科目代码下存在"

    # 应急类关键词
    emergency_keywords = ["应急", "突发", "抢险", "救灾", "防疫"]
    if any(kw in name for kw in emergency_keywords):
        return "应急支出 — 确认是否已履行预算追加程序"

    # 大额检测
    if amount > 2000000:
        return "大额无预算支出 — 需追溯审批流程"
    if amount > 500000:
        return "无预算支出 — 建议核实是否为预算外项目"

    return "无预算支出 — 建议核实"


def _detect_suspicious_transfers(
    budget_data: Dict, execution_data: Dict
) -> List[Dict[str, Any]]:
    """
    检测可疑的科目间资金转移：
    有些科目预算大幅减少（actual << budget），同时另一些同名科目出现无预算支出，
    可能是资金在科目间违规调剂。
    """
    transfers = []
    for code, bv in budget_data.items():
        budget_amt = float(bv.get("budget", 0))
        if code in execution_data:
            actual_amt = float(execution_data[code].get("actual", 0))
        else:
            actual_amt = 0.0

        if budget_amt == 0:
            continue

        usage_rate = actual_amt / budget_amt * 100
        if usage_rate < 30 and budget_amt > 50000:
            # 这个科目预算几乎没用——查是否转到了其他地方
            dept = bv.get("dept", "")
            # 找同部门下无预算但有支出的科目
            for ec, ev in execution_data.items():
                if ec not in budget_data and ev.get("dept", "") == dept:
                    transfers.append({
                        "from_code": code,
                        "from_name": bv.get("name", ""),
                        "from_budget": budget_amt,
                        "from_actual": actual_amt,
                        "to_code": ec,
                        "to_name": ev.get("name", ""),
                        "to_actual": float(ev.get("actual", 0)),
                        "risk": "可能存在科目间违规调剂资金",
                    })

    return transfers


# ─── MCP 接口 ──────────────────────────────────────────

def handle_request(method: str, params: dict) -> dict:
    if method == "detect_no_budget_expenditure":
        return detect_no_budget_expenditure(
            params.get("budget_data", {}),
            params.get("execution_data", {}),
            threshold=params.get("threshold", 10000.0),
            include_suspicious_transfers=params.get("include_suspicious_transfers", True),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


# ─── 测试 ─────────────────────────────────────────────

if __name__ == "__main__":
    budget = {
        "2010101": {"name": "行政运行-人员经费", "budget": 5000000, "category": "一般公共服务", "economic": "工资福利", "dept": "市财政局"},
        "2050201": {"name": "学前教育-生均拨款", "budget": 8000000, "category": "教育", "economic": "对个人和家庭的补助", "dept": "市教育局"},
    }

    execution = {
        "2010101": {"name": "行政运行-人员经费", "actual": 200000, "category": "一般公共服务", "economic": "工资福利", "dept": "市财政局"},
        "2050201": {"name": "学前教育-生均拨款", "actual": 7500000, "category": "教育", "economic": "对个人和家庭的补助", "dept": "市教育局"},
        "3029901": {"name": "其他商品和服务支出-会议费", "actual": 600000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市财政局"},
        "2140101": {"name": "交通运输-突发事件处置", "actual": 800000, "category": "交通运输", "economic": "商品和服务", "dept": "市交通局"},
        "2299901": {"name": "其他支出-设备采购", "actual": 1500000, "category": "其他支出", "economic": "资本性支出", "dept": "市交通局"},
        "2010301": {"name": "小额杂项", "actual": 5000, "category": "一般公共服务", "economic": "商品和服务", "dept": "市财政局"},
    }

    result = detect_no_budget_expenditure(budget, execution)
    print("=" * 60)
    print("无预算支出检测")
    print("=" * 60)

    for item in result["data"]["no_budget_items"]:
        risk_emoji = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(item["risk_level"], "⚪")
        print(f"  {risk_emoji} [{item['risk_level']}] {item['name']}: {item['amount']:,.0f}元 — {item['suspicious_type']}")

    print(f"\n无预算支出合计: {result['data']['total_no_budget_amount']:,.0f}元 (占比{result['data']['ratio_pct']}%)")

    if result["data"].get("suspicious_transfers"):
        print("\n⚠️ 可疑科目间调剂:")
        for t in result["data"]["suspicious_transfers"]:
            print(f"  {t['from_name']}(预算{t['from_budget']:,.0f}→实际{t['from_actual']:,.0f}) → {t['to_name']}({t['to_actual']:,.0f}元) — {t['risk']}")

    # 断言
    assert result["status"] == "success"
    assert len(result["data"]["no_budget_items"]) >= 3  # 3个大额无预算
    # 5000元的小额应该被过滤
    codes = [i["code"] for i in result["data"]["no_budget_items"]]
    assert "2010301" not in codes
    # 检测到可疑科目间转移
    assert len(result["data"].get("suspicious_transfers", [])) >= 1

    print("\n✅ 全部测试通过")
    print(result["summary"])
