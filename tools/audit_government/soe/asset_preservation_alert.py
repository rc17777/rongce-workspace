"""
国有资产保值增值风险预警 — State Asset Preservation Alert System

核心功能：三维检测资产减值/低价处置/无偿划转风险。
适用场景：国有企业审计、国有资产监督管理、经责审计。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def analyze_asset_preservation(
    *,
    assets: List[Dict] = None,
    disposals: List[Dict] = None,
    transfers: List[Dict] = None,
    reference_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    国有资产保值增值三维风险检测。

    Args:
        assets: 资产台账 [{id, name, type, book_value, market_value, acquisition_date, usage_status,
                 impairment_indicators: [str], last_revaluation_date}]
        disposals: 处置记录 [{id, asset_name, book_value, appraised_value, disposal_price,
                   disposal_date, buyer_name, buyer_relation}]
        transfers: 无偿划转记录 [{id, asset_name, value, from_entity, to_entity,
                   to_entity_type, approval_date, sasac_approval_exist}]
        reference_date: 参考日期

    Returns:
        综合风险报告
    """
    try:
        results = {}
        total_risk_score = 0
        all_findings = []

        if assets:
            r = _check_impairment(assets, reference_date)
            results["impairment"] = r
            total_risk_score += r["risk_score"]
            all_findings.extend(r.get("findings", []))

        if disposals:
            r = _check_disposals(disposals)
            results["disposals"] = r
            total_risk_score += r["risk_score"]
            all_findings.extend(r.get("findings", []))

        if transfers:
            r = _check_transfers(transfers)
            results["transfers"] = r
            total_risk_score += r["risk_score"]
            all_findings.extend(r.get("findings", []))

        # 综合风险评级
        if total_risk_score >= 10:
            risk_level = "严重"
        elif total_risk_score >= 5:
            risk_level = "关注"
        elif total_risk_score >= 2:
            risk_level = "一般"
        else:
            risk_level = "正常"

        return {
            "status": "success",
            "data": {
                "categories": results,
                "total_risk_score": total_risk_score,
                "risk_level": risk_level,
                "all_findings": sorted(all_findings, key=lambda x: x.get("risk_score", 0), reverse=True),
            },
            "summary": f"国有资产保值增值风险评级[{risk_level}]，风险总分{total_risk_score}，共{len(all_findings)}项发现"
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"分析异常: {str(e)}"}


def _check_impairment(assets: List[Dict], reference_date: Optional[str]) -> Dict:
    """资产减值信号检测"""
    findings = []
    risk_score = 0
    ref_date = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()

    for a in assets:
        signals = []
        score = 0

        # 信号1：公允价值持续下跌
        book = float(a.get("book_value", 0))
        market = float(a.get("market_value", 0))
        if book > 0 and market < book * 0.8:
            decline_pct = (1 - market / book) * 100
            signals.append(f"公允价值下跌{decline_pct:.1f}%（账面{book:,.0f}→市场{market:,.0f}）")
            score += 3

        # 信号2：使用状态异常
        status = a.get("usage_status", "")
        if status in ["闲置", "停用", "待报废"]:
            signals.append(f"资产状态: {status}")
            score += 2

        # 信号3：技术淘汰风险
        indicators = a.get("impairment_indicators", [])
        for ind in indicators:
            if ind in ["技术淘汰", "市场萎缩", "法规限制"]:
                signals.append(f"减值迹象: {ind}")
                score += 1

        # 信号4：长期未重估
        last_reval = a.get("last_revaluation_date", "")
        if last_reval:
            try:
                reval_date = datetime.strptime(last_reval, "%Y-%m-%d")
                if (ref_date - reval_date).days > 365 * 3:
                    signals.append(f"距上次重估已超3年")
                    score += 1
            except ValueError:
                pass

        # 信号5：已终止使用项目
        if a.get("terminated", False):
            signals.append("项目已终止，资产可能减值")
            score += 2

        if signals:
            findings.append({
                "asset_id": a.get("id", ""),
                "asset_name": a.get("name", ""),
                "type": a.get("type", ""),
                "book_value": round(book, 2),
                "market_value": round(market, 2),
                "signals": signals,
                "risk_score": score,
            })
            risk_score += score

    return {"item_count": len(assets), "finding_count": len(findings), "risk_score": risk_score, "findings": findings}


def _check_disposals(disposals: List[Dict]) -> Dict:
    """低价处置检测：处置价 vs 评估价 vs 账面净值 三维比价"""
    findings = []
    risk_score = 0

    for d in disposals:
        book = float(d.get("book_value", 0))
        appraised = float(d.get("appraised_value", 0))
        price = float(d.get("disposal_price", 0))
        buyer_rel = d.get("buyer_relation", "")

        signals = []
        score = 0

        if appraised > 0 and price < appraised * 0.85:
            pct = (1 - price / appraised) * 100
            signals.append(f"处置价低于评估价{pct:.1f}%（评估{appraised:,.0f}→成交{price:,.0f}）")
            score += 3

        if book > 0 and price < book * 0.8:
            pct = (1 - price / book) * 100
            signals.append(f"处置价低于账面净值{pct:.1f}%（账面{book:,.0f}→成交{price:,.0f}）")
            score += 3

        if buyer_rel in ["关联方", "管理层亲属", "原股东", "内部人"]:
            signals.append(f"购买方为{buyer_rel}，存在利益输送风险")
            score += 4

        if signals:
            findings.append({"asset_name": d.get("asset_name", ""), "disposal_price": round(price, 2),
                             "book_value": round(book, 2), "appraised_value": round(appraised, 2),
                             "signals": signals, "risk_score": score})
            risk_score += score

    return {"item_count": len(disposals), "finding_count": len(findings), "risk_score": risk_score, "findings": findings}


def _check_transfers(transfers: List[Dict]) -> Dict:
    """无偿划转合规检测"""
    findings = []
    risk_score = 0

    for t in transfers:
        signals = []
        score = 0

        to_type = t.get("to_entity_type", "")
        if to_type not in ["国有企业", "国有独资", "国有控股"]:
            signals.append(f"接收方为非国有主体({to_type})，存在国有资产流失风险")
            score += 5

        if not t.get("sasac_approval_exist", False):
            signals.append("缺少国资委批准文件")
            score += 4

        value = float(t.get("value", 0))
        if value > 10000000 and not signals:  # 大额划转即使合规也需关注
            signals.append(f"大额划转({value:,.0f}元)，建议复核商业合理性")
            score += 1

        if signals:
            findings.append({"asset_name": t.get("asset_name", ""), "value": round(value, 2),
                             "to_entity": t.get("to_entity", ""), "signals": signals, "risk_score": score})
            risk_score += score

    return {"item_count": len(transfers), "finding_count": len(findings), "risk_score": risk_score, "findings": findings}


def handle_request(method: str, params: dict) -> dict:
    if method == "analyze_asset_preservation":
        return analyze_asset_preservation(
            assets=params.get("assets"),
            disposals=params.get("disposals"),
            transfers=params.get("transfers"),
            reference_date=params.get("reference_date"),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    assets = [
        {"id": "A001", "name": "闲置厂房", "type": "固定资产", "book_value": 5000000, "market_value": 3000000, "acquisition_date": "2018-01-01", "usage_status": "闲置", "impairment_indicators": ["市场萎缩"], "last_revaluation_date": "2019-12-31"},
        {"id": "A002", "name": "生产线设备", "type": "固定资产", "book_value": 8000000, "market_value": 7500000, "acquisition_date": "2023-06-01", "usage_status": "在用", "impairment_indicators": [], "last_revaluation_date": "2024-12-31"},
        {"id": "A003", "name": "旧办公楼", "type": "固定资产", "book_value": 3000000, "market_value": 1000000, "acquisition_date": "2005-01-01", "usage_status": "停用", "impairment_indicators": ["技术淘汰", "法规限制"], "last_revaluation_date": "2018-06-01"},
    ]

    disposals = [
        {"asset_name": "子公司股权", "book_value": 10000000, "appraised_value": 12000000, "disposal_price": 7000000, "disposal_date": "2025-05-01", "buyer_name": "XX投资公司", "buyer_relation": "关联方"},
        {"asset_name": "运输车辆", "book_value": 200000, "appraised_value": 180000, "disposal_price": 170000, "disposal_date": "2025-08-01", "buyer_name": "二手车商", "buyer_relation": "外部"},
    ]

    transfers = [
        {"asset_name": "土地使用权", "value": 20000000, "from_entity": "A国企", "to_entity": "B民营企业", "to_entity_type": "民营", "sasac_approval_exist": False},
    ]

    result = analyze_asset_preservation(assets=assets, disposals=disposals, transfers=transfers)
    print("=" * 60)
    print("国有资产保值增值风险预警")
    print("=" * 60)
    print(f"风险等级: {result['data']['risk_level']} (总分{result['data']['total_risk_score']})")

    for f in result["data"]["all_findings"]:
        print(f"\n  [{f['risk_score']}分] {f.get('asset_name','')}")
        for s in f["signals"]:
            print(f"    - {s}")

    assert result["status"] == "success"
    assert result["data"]["total_risk_score"] >= 8
    assert len(result["data"]["all_findings"]) >= 2

    print("\n✅ 全部测试通过")
    print(result["summary"])
