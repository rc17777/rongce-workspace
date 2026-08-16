"""
审计风险排序模型 (Audit Risk Ranking Model)
===========================================
综合多维度评分，对审计对象/项目进行风险排序。
支持自定义权重，输出优先级清单。

评分维度（7维）：
  1. 财务舞弊风险（25%）
  2. 预算执行偏差（20%）
  3. 内控制度缺陷（15%）
  4. 历史审计问题（15%）
  5. 资金规模（10%）
  6. 社会关注度（10%）
  7. 整改落实情况（05%）

使用方式：
  py audit_risk_ranking.py --sample        # 示例数据
  py audit_risk_ranking.py --file 对象数据.json --output 排序结果.json
  py audit_risk_ranking.py --weights 0.3 0.15 0.15 0.15 0.1 0.1 0.05  # 自定义权重
"""

import json
import sys
import math
from datetime import datetime

# ========== 默认权重 ==========

DEFAULT_WEIGHTS = {
    "financial_fraud": 0.25,       # 财务舞弊风险
    "budget_deviation": 0.20,      # 预算执行偏差
    "internal_control": 0.15,      # 内控制度缺陷
    "history_issues": 0.15,        # 历史审计问题
    "fund_scale": 0.10,            # 资金规模
    "public_concern": 0.10,        # 社会关注度
    "rectification": 0.05,         # 整改落实情况
}


# ========== 评分函数 ==========

def score_dimension(value, thresholds, max_score=100):
    """
    通用维度评分
    thresholds = [(lower, upper, score), ...]
    示例：thresholds=[(0,50,20), (50,80,50), (80,101,90)]
    表示 0-50%得20分，50-80%得50分，80%+得90分
    """
    for lo, hi, score in thresholds:
        if lo <= value < hi:
            return score
    return 0


def score_financial_fraud(fraud_score):
    """财务舞弊风险评分（0-100）"""
    return min(fraud_score, 100)


def score_budget_deviation(execution_rate):
    """预算执行偏差评分（0-100）"""
    if execution_rate <= 0:
        return 100  # 完全未执行
    if execution_rate < 0.5:
        return 80   # 执行严重不足
    if execution_rate > 1.2:
        return 70   # 超预算
    if execution_rate > 1.0:
        return 40   # 略超
    return 10       # 正常


def score_internal_control(defect_count):
    """内控制度缺陷评分（0-100）"""
    return min(defect_count * 20, 100)


def score_history_issues(issue_count, severity_factor=1.0):
    """历史审计问题评分（0-100）"""
    return min(issue_count * 15 * severity_factor, 100)


def score_fund_scale(total_amount):
    """资金规模评分（0-100）"""
    if total_amount >= 100_000_000:   # 1亿+
        return 100
    if total_amount >= 10_000_000:    # 1000万+
        return 80
    if total_amount >= 1_000_000:     # 100万+
        return 50
    if total_amount >= 100_000:       # 10万+
        return 20
    return 10


def score_public_concern(media_reports=0, public_complaints=0):
    """社会关注度评分（0-100）"""
    score = min(media_reports * 10 + public_complaints * 5, 100)
    return score


def score_rectification(past_rectification_rate):
    """整改落实情况评分（0-100）"""
    rate = past_rectification_rate  # 0.0-1.0
    if rate >= 0.9:
        return 10    # 整改好，风险低
    if rate >= 0.7:
        return 30
    if rate >= 0.5:
        return 50
    if rate >= 0.3:
        return 70
    return 100  # 整改极差 → 高风险


def calculate_risk(entity, weights=None):
    """
    对单个审计对象计算综合风险分

    输入 entity = {
        'id': 'U001',
        'name': 'XX局',
        'financial_fraud_score': 85,         # 0-100
        'budget_execution_rate': 0.35,        # 0.0-2.0
        'internal_control_defects': 3,        # 整数
        'history_issue_count': 5,             # 整数
        'history_issue_severity': 1.2,        # 乘数
        'fund_total': 5000000,                # 总资金
        'media_reports': 8,                   # 媒体报道数
        'public_complaints': 3,               # 投诉数
        'rectification_rate': 0.4,            # 0.0-1.0
    }

    输出: { entity info + dimensional scores + total score }
    """
    w = weights or DEFAULT_WEIGHTS

    s1 = entity.get("financial_fraud_score", 0)
    s2 = score_budget_deviation(entity.get("budget_execution_rate", 0.5))
    s3 = score_internal_control(entity.get("internal_control_defects", 0))
    s4 = score_history_issues(entity.get("history_issue_count", 0),
                              entity.get("history_issue_severity", 1.0))
    s5 = score_fund_scale(entity.get("fund_total", 0))
    s6 = score_public_concern(entity.get("media_reports", 0),
                              entity.get("public_complaints", 0))
    s7 = score_rectification(entity.get("rectification_rate", 0.5))

    scores = {
        "财务舞弊风险": round(s1, 1),
        "预算执行偏差": round(s2, 1),
        "内控制度缺陷": round(s3, 1),
        "历史审计问题": round(s4, 1),
        "资金规模": round(s5, 1),
        "社会关注度": round(s6, 1),
        "整改落实情况": round(s7, 1),
    }

    total = (s1 * w["financial_fraud"] +
             s2 * w["budget_deviation"] +
             s3 * w["internal_control"] +
             s4 * w["history_issues"] +
             s5 * w["fund_scale"] +
             s6 * w["public_concern"] +
             s7 * w["rectification"])

    # 风险等级
    if total >= 80:
        level = "🔴 极高风险"
    elif total >= 60:
        level = "🟡 高风险"
    elif total >= 40:
        level = "🔵 中风险"
    else:
        level = "🟢 低风险"

    # 主要风险点（取top3最高分维度）
    sorted_dims = sorted(scores.items(), key=lambda x: -x[1])
    top_risks = [d[0] for d in sorted_dims[:3] if d[1] >= 50]

    return {
        "id": entity.get("id", "?"),
        "name": entity.get("name", "未命名"),
        "total_score": round(total, 1),
        "level": level,
        "dimensional_scores": scores,
        "top_risks": top_risks if top_risks else ["整体风险可控"],
    }


def rank_entities(entities, weights=None, top_n=20):
    """
    对多个审计对象进行风险排序

    输入: [entity1, entity2, ...]
    输出: sorted list with ranking
    """
    results = []
    for e in entities:
        r = calculate_risk(e, weights)
        results.append(r)

    results.sort(key=lambda x: -x["total_score"])

    # 附排序号
    for i, r in enumerate(results, 1):
        r["rank"] = i

    # 汇总
    summary = {
        "total": len(results),
        "极高风险": len([r for r in results if "极高" in r["level"]]),
        "高风险": len([r for r in results if "高" in r["level"] and "极高" not in r["level"]]),
        "中风险": len([r for r in results if "中" in r["level"]]),
        "低风险": len([r for r in results if "低" in r["level"]]),
        "top3_avg_score": round(sum(r["total_score"] for r in results[:3]) / 3, 1) if len(results) >= 3 else 0,
    }

    return {"ranked_entities": results[:top_n], "full_count": len(results), "summary": summary}


def print_report(result):
    """打印风险排序报告"""
    s = result["summary"]
    print("=" * 65)
    print(f"  审计风险排序报告")
    print(f"  评估对象数: {s['total']}")
    print(f"  显示前 {len(result['ranked_entities'])} 名")
    print("=" * 65)
    print(f"  🔴 极高风险: {s['极高风险']} 个")
    print(f"  🟡 高风险:   {s['高风险']} 个")
    print(f"  🔵 中风险:   {s['中风险']} 个")
    print(f"  🟢 低风险:   {s['低风险']} 个")
    print(f"  TOP3 平均分: {s['top3_avg_score']}")
    print("=" * 65)

    for r in result["ranked_entities"]:
        icon = r["level"][:2]
        print(f"\n  {icon} #{r['rank']:2d} {r['name']:15s} | 总分:{r['total_score']:>5.1f} | {r['level']}")
        dims = " | ".join(f"{k}:{v:.0f}" for k, v in r["dimensional_scores"].items() if v > 10)
        print(f"     {'':15s} 维度: {dims}")
        if r["top_risks"]:
            print(f"     {'':15s} ⚠️  {', '.join(r['top_risks'])}")


# ========== 示例数据 ==========

SAMPLE_ENTITIES = [
    {"id": "U001", "name": "XX局机关", "financial_fraud_score": 85, "budget_execution_rate": 0.35,
     "internal_control_defects": 3, "history_issue_count": 5, "history_issue_severity": 1.2,
     "fund_total": 50000000, "media_reports": 8, "public_complaints": 3, "rectification_rate": 0.4},
    {"id": "U002", "name": "XX中心", "financial_fraud_score": 60, "budget_execution_rate": 1.45,
     "internal_control_defects": 2, "history_issue_count": 3, "history_issue_severity": 1.0,
     "fund_total": 20000000, "media_reports": 3, "public_complaints": 1, "rectification_rate": 0.6},
    {"id": "U003", "name": "XX项目办", "financial_fraud_score": 30, "budget_execution_rate": 0.15,
     "internal_control_defects": 5, "history_issue_count": 8, "history_issue_severity": 1.5,
     "fund_total": 100000000, "media_reports": 12, "public_complaints": 5, "rectification_rate": 0.2},
    {"id": "U004", "name": "XX研究院", "financial_fraud_score": 20, "budget_execution_rate": 0.85,
     "internal_control_defects": 0, "history_issue_count": 1, "history_issue_severity": 0.8,
     "fund_total": 8000000, "media_reports": 0, "public_complaints": 0, "rectification_rate": 0.9},
    {"id": "U005", "name": "XX学校", "financial_fraud_score": 45, "budget_execution_rate": 0.98,
     "internal_control_defects": 1, "history_issue_count": 2, "history_issue_severity": 0.9,
     "fund_total": 30000000, "media_reports": 2, "public_complaints": 0, "rectification_rate": 0.7},
    {"id": "U006", "name": "XX执法支队", "financial_fraud_score": 75, "budget_execution_rate": 1.35,
     "internal_control_defects": 4, "history_issue_count": 6, "history_issue_severity": 1.1,
     "fund_total": 15000000, "media_reports": 0, "public_complaints": 0, "rectification_rate": 0.5},
    {"id": "U007", "name": "XX局附属A", "financial_fraud_score": 95, "budget_execution_rate": 0.05,
     "internal_control_defects": 6, "history_issue_count": 10, "history_issue_severity": 1.8,
     "fund_total": 250000000, "media_reports": 15, "public_complaints": 8, "rectification_rate": 0.1},
    {"id": "U008", "name": "XX卫生中心", "financial_fraud_score": 55, "budget_execution_rate": 1.05,
     "internal_control_defects": 2, "history_issue_count": 4, "history_issue_severity": 1.0,
     "fund_total": 12000000, "media_reports": 1, "public_complaints": 0, "rectification_rate": 0.8},
    {"id": "U009", "name": "XX社区", "financial_fraud_score": 15, "budget_execution_rate": 0.75,
     "internal_control_defects": 0, "history_issue_count": 0, "history_issue_severity": 0.0,
     "fund_total": 5000000, "media_reports": 0, "public_complaints": 0, "rectification_rate": 0.0},
    {"id": "U010", "name": "XX养老服务中心", "financial_fraud_score": 40, "budget_execution_rate": 0.60,
     "internal_control_defects": 3, "history_issue_count": 2, "history_issue_severity": 1.0,
     "fund_total": 80000000, "media_reports": 6, "public_complaints": 4, "rectification_rate": 0.3},
]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="审计风险排序模型")
    parser.add_argument("--file", help="审计对象数据文件(.json)")
    parser.add_argument("--output", help="输出文件(.json)")
    parser.add_argument("--sample", action="store_true", help="使用示例数据")
    parser.add_argument("--top", type=int, default=20, help="显示前N个")
    parser.add_argument("--weights", nargs=7, type=float,
                        help="7个权重值（财务舞弊 预算偏差 内控 历史问题 资金规模 社会关注 整改落实）")
    args = parser.parse_args()

    data = None
    if args.sample:
        data = SAMPLE_ENTITIES
        print(f"使用内置示例数据（{len(data)}个）")
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"加载文件: {args.file}, {len(data)}个审计对象")
    else:
        data = SAMPLE_ENTITIES
        print(f"未指定输入文件，使用示例数据")

    weights = None
    if args.weights and len(args.weights) == 7:
        keys = ["financial_fraud", "budget_deviation", "internal_control",
                "history_issues", "fund_scale", "public_concern", "rectification"]
        weights = dict(zip(keys, args.weights))
        s = sum(weights.values())
        if abs(s - 1.0) > 0.001:
            print(f"⚠️  权重和为 {s:.3f}，不等于1，将自动归一化")
            for k in weights:
                weights[k] /= s

    result = rank_entities(data, weights=weights, top_n=args.top)
    print_report(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            # 去掉emoji便于其他工具处理
            clean_result = {
                "ranked_entities": [{
                    **r,
                    "level": r["level"].replace("🔴 ", "").replace("🟡 ", "").replace("🔵 ", "").replace("🟢 ", "")
                } for r in result["ranked_entities"]],
                "full_count": result["full_count"],
                "summary": result["summary"],
            }
            json.dump(clean_result, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n结果已保存至: {args.output}")
