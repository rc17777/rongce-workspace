"""
混合所有制改革资产流失检测 — Mixed Reform Asset Check

核心功能：混改进程中的资产定价公允性、利润隐藏、关联受让方检测。
适用场景：国有企业审计、混合所有制改革监督。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Any, Optional


def check_mixed_reform_assets(
    reforms: List[Dict[str, Any]],
    *,
    related_party_db: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    混改资产流失风险检测。

    Args:
        reforms: 混改项目列表 [{id, entity_name, appraisal_date, appraised_value, transaction_date,
                  transaction_price, pre_reform_profits: [{year, amount}], post_reform_profits: [{year, amount}],
                  buyer_name, buyer_relationship, management_involvement: bool}]
        related_party_db: 已知关联方名单（用于交叉验证）

    Returns:
        混改风险报告
    """
    try:
        findings = []
        total_risk_score = 0

        for ref in reforms:
            item_findings = []
            score = 0
            entity = ref.get("entity_name", "")
            buyer = ref.get("buyer_name", "")

            # 检测1：评估价 vs 成交价偏差
            appraised = float(ref.get("appraised_value", 0))
            trans_price = float(ref.get("transaction_price", 0))
            if appraised > 0:
                deviation = (1 - trans_price / appraised) * 100
                if deviation > 20:
                    item_findings.append(f"成交价低于评估价{deviation:.1f}%（评估{appraised:,.0f}→成交{trans_price:,.0f}），定价严重偏离")
                    score += 5
                elif deviation > 10:
                    item_findings.append(f"成交价低于评估价{deviation:.1f}%，需关注定价依据")
                    score += 2
                elif deviation < -10:
                    item_findings.append(f"成交价高于评估价{abs(deviation):.1f}%，需关注是否有利益输送意图")
                    score += 1

            # 检测2：评估基准日到成交日之间的资产变化（隐藏利润）
            appraisal_date = ref.get("appraisal_date", "")
            transaction_date = ref.get("transaction_date", "")
            if appraisal_date and transaction_date:
                try:
                    ad = datetime.strptime(appraisal_date, "%Y-%m-%d")
                    td = datetime.strptime(transaction_date, "%Y-%m-%d")
                    gap_days = (td - ad).days
                    if gap_days > 180:
                        # 间隔超过半年，检查期间利润
                        pre_profits = ref.get("pre_reform_profits", [])
                        post_profits = ref.get("post_reform_profits", [])
                        # 如果混改前利润显著低于混改后利润，可能隐藏利润压低估值
                        avg_pre = sum(float(p.get("amount", 0)) for p in pre_profits) / max(len(pre_profits), 1)
                        avg_post = sum(float(p.get("amount", 0)) for p in post_profits) / max(len(post_profits), 1)
                        if avg_pre > 0 and avg_post > avg_pre * 2:
                            item_findings.append(f"混改后利润骤增{avg_post/avg_pre:.1f}倍（前{avg_pre:,.0f}→后{avg_post:,.0f}），疑隐藏利润压低评估价")
                            score += 5
                        elif avg_pre < avg_post * 0.5:
                            item_findings.append(f"混改后利润显著改善，需核实评估基准日会计处理公允性")
                            score += 2
                except ValueError:
                    pass

            # 检测3：受让方关联关系
            relationship = ref.get("buyer_relationship", "")
            if relationship in ["管理层", "管理层亲属", "原股东关联方", "内部人控制"]:
                item_findings.append(f"受让方({buyer})与原管理层存在关联({relationship})，存在利益输送重大风险")
                score += 5
            elif relationship in ["关联方", "一致行动人"]:
                item_findings.append(f"受让方({buyer})为关联方，需审查定价公允性")
                score += 3

            # 交叉验证关联方数据库
            if related_party_db and buyer in related_party_db:
                item_findings.append(f"受让方({buyer})在关联方监控名单中")
                score += 4

            # 检测4：管理层参与受让
            mgmt = ref.get("management_involvement", False)
            if mgmt:
                item_findings.append("管理层成员直接或间接参与受让，存在自我交易风险")
                score += 4

            # 检测5：混改后快速转让
            resale_date = ref.get("resale_date", "")
            resale_price = ref.get("resale_price")
            if resale_date and transaction_date and resale_price:
                try:
                    td = datetime.strptime(transaction_date, "%Y-%m-%d")
                    rd = datetime.strptime(resale_date, "%Y-%m-%d")
                    if (rd - td).days < 365 and float(resale_price) > trans_price * 1.5:
                        item_findings.append(f"混改后不足1年即以{resale_price:,.0f}元转让（买入{trans_price:,.0f}元），存在贱卖嫌疑")
                        score += 5
                except ValueError:
                    pass

            if item_findings:
                findings.append({
                    "reform_id": ref.get("id", ""),
                    "entity_name": entity,
                    "appraised_value": round(appraised, 2),
                    "transaction_price": round(trans_price, 2),
                    "buyer_name": buyer,
                    "findings": item_findings,
                    "risk_score": score,
                    "risk_level": "严重" if score >= 10 else ("高度关注" if score >= 6 else ("关注" if score >= 3 else "一般")),
                })
                total_risk_score += score

        overall_risk = "严重" if total_risk_score >= 15 else ("高度关注" if total_risk_score >= 8 else ("关注" if total_risk_score >= 3 else "正常"))

        return {
            "status": "success",
            "data": {
                "reform_items": len(reforms),
                "abnormal_items": len(findings),
                "findings": sorted(findings, key=lambda x: x["risk_score"], reverse=True),
                "total_risk_score": total_risk_score,
                "overall_risk": overall_risk,
            },
            "summary": f"共{len(reforms)}项混改：{len(findings)}项存在风险信号，综合风险评级[{overall_risk}]（风险分{total_risk_score}）"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"检测异常: {str(e)}"}


def handle_request(method: str, params: dict) -> dict:
    if method == "check_mixed_reform_assets":
        return check_mixed_reform_assets(
            params.get("reforms", []),
            related_party_db=params.get("related_party_db"),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    reforms = [
        {"id": "M001", "entity_name": "某市自来水公司", "appraisal_date": "2024-06-30", "appraised_value": 50000000,
         "transaction_date": "2025-01-15", "transaction_price": 32000000,
         "pre_reform_profits": [{"year": 2022, "amount": 500000}, {"year": 2023, "amount": 400000}, {"year": 2024, "amount": 300000}],
         "post_reform_profits": [{"year": 2025, "amount": 8000000}],
         "buyer_name": "某投资有限公司", "buyer_relationship": "管理层", "management_involvement": True, "resale_date": "", "resale_price": None},
        {"id": "M002", "entity_name": "某市公交集团", "appraisal_date": "2025-03-15", "appraised_value": 30000000,
         "transaction_date": "2025-09-01", "transaction_price": 28000000,
         "pre_reform_profits": [{"year": 2023, "amount": 6000000}, {"year": 2024, "amount": 6500000}],
         "post_reform_profits": [{"year": 2025, "amount": 7000000}],
         "buyer_name": "某交通集团", "buyer_relationship":  "", "management_involvement": False,
         "resale_date": "2026-03-01", "resale_price": 60000000},
    ]

    result = check_mixed_reform_assets(reforms, related_party_db=["某投资有限公司"])
    print("=" * 60)
    print("混合所有制改革资产流失检测")
    print("=" * 60)
    print(f"混改项目: {result['data']['reform_items']}项")
    print(f"异常项目: {result['data']['abnormal_items']}项")
    print(f"风险评级: {result['data']['overall_risk']} (总分{result['data']['total_risk_score']})")

    for f in result["data"]["findings"]:
        print(f"\n  [{f['risk_level']}] {f['entity_name']} (评分{f['risk_score']})")
        print(f"    评估价: {f['appraised_value']:,.0f} → 成交价: {f['transaction_price']:,.0f}")
        print(f"    受让方: {f['buyer_name']}")
        for ff in f["findings"]:
            print(f"    - {ff}")

    assert result["status"] == "success"
    assert result["data"]["abnormal_items"] >= 1
    m001 = next(f for f in result["data"]["findings"] if f.get("reform_id") == "M001")
    assert m001["risk_score"] >= 8

    print("\n✅ 全部测试通过")
    print(result["summary"])
