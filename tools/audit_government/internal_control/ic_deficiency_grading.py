"""
内控缺陷分级模型 — Internal Control Deficiency Grading Model

核心功能：定量+定性双维度加权评分，重大/重要/一般三级输出。
适用场景：内控制度审计、内控评价报告。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from typing import Dict, List, Any


def grade_deficiencies(
    deficiencies: List[Dict[str, Any]],
    *,
    quantitative_weight: float = 0.5,
    qualitative_weight: float = 0.5,
) -> Dict[str, Any]:
    """
    内控缺陷分级。

    Args:
        deficiencies: 缺陷清单 [{id, description, amount_involved, scope_count, frequency,
                       is_systematic, is_intentional, caused_loss, financial_statement_impact,
                       category, source}]
        quantitative_weight: 定量维度权重
        qualitative_weight: 定性维度权重

    Returns:
        缺陷分级报告
    """
    try:
        graded = []
        stats = {"重大": 0, "重要": 0, "一般": 0}

        for d in deficiencies:
            # ── 定量评分（0-50分）──
            q_score = 0
            amount = float(d.get("amount_involved", 0))
            scope = int(d.get("scope_count", 1))
            freq = d.get("frequency", "偶尔")

            # 金额维度（0-20）
            if amount > 5000000:
                q_score += 20
            elif amount > 1000000:
                q_score += 15
            elif amount > 500000:
                q_score += 10
            elif amount > 100000:
                q_score += 5

            # 影响范围（0-15）
            if scope >= 10:
                q_score += 15
            elif scope >= 5:
                q_score += 10
            elif scope >= 2:
                q_score += 5

            # 发生频率（0-15）
            freq_map = {"持续": 15, "频繁": 10, "多次": 7, "偶尔": 3, "单次": 0}
            q_score += freq_map.get(freq, 3)

            # ── 定性评分（0-50分）──
            l_score = 0

            # 系统性问题（0-15）
            if d.get("is_systematic", False):
                l_score += 15

            # 故意性（0-15）
            if d.get("is_intentional", False):
                l_score += 15

            # 已造成损失（0-10）
            if d.get("caused_loss", False):
                loss_amount = float(d.get("loss_amount", 0))
                if loss_amount > 1000000:
                    l_score += 10
                elif loss_amount > 100000:
                    l_score += 7
                else:
                    l_score += 4

            # 财报影响（0-10）
            fs_impact = d.get("financial_statement_impact", "无影响")
            fs_map = {"重大错报": 10, "重要错报": 7, "一般调整": 4, "无影响": 0}
            l_score += fs_map.get(fs_impact, 0)

            # ── 综合评分 ──
            total = q_score * quantitative_weight + l_score * qualitative_weight

            # 分级
            if total >= 30:
                grade = "重大"
            elif total >= 15:
                grade = "重要"
            else:
                grade = "一般"

            stats[grade] += 1

            graded.append({
                "id": d.get("id", ""),
                "description": d.get("description", "")[:200],
                "category": d.get("category", ""),
                "quantitative_score": round(q_score, 1),
                "qualitative_score": round(l_score, 1),
                "total_score": round(total, 1),
                "grade": grade,
                "source": d.get("source", ""),
                "remediation_priority": "立即整改" if grade == "重大" else ("限期整改" if grade == "重要" else "计划整改"),
                # 具体打分明细
                "score_breakdown": {
                    "amount_risk": "高" if amount > 1000000 else ("中" if amount > 100000 else "低"),
                    "scope_risk": "高" if scope >= 5 else ("中" if scope >= 2 else "低"),
                    "systematic": d.get("is_systematic", False),
                    "intentional": d.get("is_intentional", False),
                    "caused_loss": d.get("caused_loss", False),
                }
            })

        # 排序
        graded.sort(key=lambda x: x["total_score"], reverse=True)

        # 风险评估
        high_ratio = stats["重大"] / max(len(graded), 1) * 100
        if high_ratio > 30:
            verdict = "内控存在系统性重大缺陷，需立即全面整改"
        elif stats["重大"] > 0:
            verdict = f"存在{stats['重大']}个重大缺陷，需重点整改"
        elif stats["重要"] > 0:
            verdict = f"存在{stats['重要']}个重要缺陷，建议限期整改"
        else:
            verdict = "内控缺陷总体可控"

        return {
            "status": "success",
            "data": {
                "deficiencies": graded,
                "total_count": len(graded),
                "stats": stats,
                "verdict": verdict,
                "top_issues": graded[:5],
                "remediation_plan": _generate_remediation_plan(graded),
            },
            "summary": f"共{len(graded)}个缺陷：重大{stats['重大']}、重要{stats['重要']}、一般{stats['一般']}。{verdict}"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"分级异常: {str(e)}"}


def _generate_remediation_plan(graded: List[Dict]) -> List[Dict]:
    """生成整改建议"""
    plan = []
    for g in graded:
        actions = []
        if g["grade"] == "重大":
            actions = ["立即报告管理层和审计委员会", "成立专项整改工作组", "制度修订+流程重塑", "对相关责任人问责"]
        elif g["grade"] == "重要":
            actions = ["纳入整改台账，明确责任人和完成时限", "修订相关制度流程", "加强监督检查频率"]
        else:
            actions = ["列入改进计划", "定期复查"]

        plan.append({
            "deficiency_id": g["id"],
            "grade": g["grade"],
            "actions": actions,
            "suggested_deadline": "7天" if g["grade"] == "重大" else ("30天" if g["grade"] == "重要" else "90天"),
        })
    return plan


def handle_request(method: str, params: dict) -> dict:
    if method == "grade_deficiencies":
        return grade_deficiencies(
            params.get("deficiencies", []),
            quantitative_weight=params.get("quantitative_weight", 0.5),
            qualitative_weight=params.get("qualitative_weight", 0.5),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    deficiencies = [
        {"id": "D001", "description": "采购审批权限未按金额分级，单笔500万以上采购无董事会审批", "amount_involved": 20000000, "scope_count": 15, "frequency": "频繁", "is_systematic": True, "is_intentional": False, "caused_loss": True, "loss_amount": 3000000, "financial_statement_impact": "重要错报", "category": "控制活动", "source": "穿行测试"},
        {"id": "D002", "description": "出纳兼记账，违反不相容职务分离原则", "amount_involved": 500000, "scope_count": 1, "frequency": "持续", "is_systematic": False, "is_intentional": False, "caused_loss": False, "financial_statement_impact": "一般调整", "category": "控制活动", "source": "职务分离检测"},
        {"id": "D003", "description": "固定资产盘点制度缺失，连续3年未全面盘点", "amount_involved": 8000000, "scope_count": 8, "frequency": "持续", "is_systematic": True, "is_intentional": False, "caused_loss": True, "loss_amount": 500000, "financial_statement_impact": "重要错报", "category": "控制活动", "source": "COSO评估"},
        {"id": "D004", "description": "个别员工报销缺少审批单", "amount_involved": 5000, "scope_count": 1, "frequency": "偶尔", "is_systematic": False, "is_intentional": False, "caused_loss": False, "financial_statement_impact": "无影响", "category": "控制活动", "source": "穿行测试"},
    ]

    result = grade_deficiencies(deficiencies)
    print("=" * 60)
    print("内控缺陷分级报告")
    print("=" * 60)
    print(f"总计: {result['data']['total_count']}个缺陷")
    print(f"分级: 重大{result['data']['stats']['重大']} / 重要{result['data']['stats']['重要']} / 一般{result['data']['stats']['一般']}")

    for d in result["data"]["deficiencies"]:
        emoji = {"重大": "[!!]", "重要": "[!] ", "一般": "[·]"}.get(d["grade"], "")
        print(f"\n  {emoji} [{d['grade']}] {d['id']}: {d['description'][:80]}...")
        print(f"      定量{d['quantitative_score']} + 定性{d['qualitative_score']} = {d['total_score']}分 | {d['remediation_priority']}")
        print(f"      风险因子: {d['score_breakdown']}")

    print(f"\n整改计划:")
    for rp in result["data"]["remediation_plan"]:
        print(f"  {rp['deficiency_id']} [{rp['grade']}]: 时限{rp['suggested_deadline']} — {' → '.join(rp['actions'])}")

    assert result["status"] == "success"
    assert result["data"]["stats"]["重大"] >= 2
    assert result["data"]["stats"]["一般"] >= 1
    # D001应该是最高的
    assert result["data"]["deficiencies"][0]["id"] == "D001"

    print(f"\n{result['summary']}")
    print("\n✅ 全部测试通过")
