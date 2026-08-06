"""
内控五要素对标引擎 — COSO Five Elements Benchmarking Engine

核心功能：基于COSO框架五要素对制度文件进行覆盖度评估。
适用场景：内控制度审计、制度体系建设评估。

作者：融策审计智析Agent
日期：2026-07-22
"""

from __future__ import annotations
from typing import Dict, List, Any

# COSO五要素 → 18项原则 → 80+关注点
COSO_FRAMEWORK = {
    "控制环境": {
        "weight": 0.25,
        "principles": {
            "诚信与道德价值观": {
                "focus_points": ["行为准则制度", "利益冲突申报制度", "举报人保护制度", "职业道德培训记录", "违纪处分制度"],
            },
            "董事会与审计委员会独立性": {
                "focus_points": ["独立董事占比", "审计委员会章程", "审计委员会履职记录", "专业委员会设置"],
            },
            "组织结构与权责分配": {
                "focus_points": ["组织架构图", "授权审批矩阵", "岗位职责说明书", "汇报路线图"],
            },
            "人力资源政策": {
                "focus_points": ["招聘录用制度", "薪酬考核制度", "培训发展制度", "轮岗强制休假制度", "离职交接制度"],
            },
        }
    },
    "风险评估": {
        "weight": 0.2,
        "principles": {
            "风险识别机制": {
                "focus_points": ["风险清单/风险库", "风险识别流程", "风险分类标准", "外部环境监测机制"],
            },
            "风险评估方法": {
                "focus_points": ["风险评价标准", "风险矩阵/风险地图", "风险容忍度/承受度", "重大风险评估记录"],
            },
            "舞弊风险评估": {
                "focus_points": ["舞弊风险识别", "反舞弊制度", "舞弊举报渠道", "舞弊调查流程"],
            },
            "风险应对策略": {
                "focus_points": ["风险应对方案", "风险应急预案", "业务连续性计划", "剩余风险评估"],
            },
        }
    },
    "控制活动": {
        "weight": 0.3,
        "principles": {
            "不相容职务分离": {
                "focus_points": ["不相容职务清单", "授权审批控制", "系统权限管理", "关键岗位分离机制"],
            },
            "授权审批控制": {
                "focus_points": ["审批权限表", "重大事项审批流程", "特殊授权管理", "审批痕迹记录"],
            },
            "会计系统控制": {
                "focus_points": ["会计制度", "凭证管理规范", "账务处理流程", "对账制度", "会计档案管理"],
            },
            "资产保护控制": {
                "focus_points": ["资产管理制度", "盘点制度", "资产领用登记", "保险/担保管理", "资产处置流程"],
            },
            "预算控制": {
                "focus_points": ["预算管理制度", "预算编制流程", "预算执行监控", "预算调整审批", "预算考核制度"],
            },
            "信息系统控制": {
                "focus_points": ["系统权限管理", "数据备份制度", "信息安全制度", "系统变更管理", "业务连续性管理"],
            },
        }
    },
    "信息与沟通": {
        "weight": 0.15,
        "principles": {
            "信息获取与传递": {
                "focus_points": ["内部报告制度", "信息报送制度", "数据质量标准", "信息披露制度"],
            },
            "内部沟通机制": {
                "focus_points": ["会议制度", "报告路线", "沟通渠道", "跨部门协作机制"],
            },
            "外部沟通机制": {
                "focus_points": ["对外信息披露", "投资者关系管理", "舆情应对机制", "供应商/客户沟通渠道"],
            },
        }
    },
    "监督": {
        "weight": 0.1,
        "principles": {
            "持续监督": {
                "focus_points": ["日常监控指标", "异常报告机制", "自查自纠制度", "绩效考核与内控挂钩"],
            },
            "独立评估": {
                "focus_points": ["内部审计制度", "内审独立性保障", "内审计划与执行", "外部审计协调"],
            },
            "缺陷报告与整改": {
                "focus_points": ["内控缺陷认定标准", "缺陷报告流程", "整改跟踪机制", "缺陷汇总分析"],
            },
        }
    },
}


def evaluate_coso_coverage(
    documents: List[Dict[str, Any]],
    *,
    framework: Dict = None,
) -> Dict[str, Any]:
    """
    基于COSO框架评估制度文件的内控覆盖度。

    Args:
        documents: 制度文件列表 [{name, content_text, relevant_focus_points: [str]}]
        framework: 自定义COSO框架（默认使用内置框架）

    Returns:
        五要素覆盖度报告
    """
    try:
        if framework is None:
            framework = COSO_FRAMEWORK

        # 统计总关注点
        total_focus_points = 0
        for element, edata in framework.items():
            for princ, pdata in edata["principles"].items():
                total_focus_points += len(pdata["focus_points"])

        # 建立关注点→文件映射（基于文件名+内容关键词匹配）
        coverage_map: Dict[str, List[str]] = {}  # 关注点 → 覆盖它的文件列表

        for doc in documents:
            doc_name = doc.get("name", "")
            content = doc.get("content_text", "").lower()
            keywords = doc.get("keywords", [])
            relevant = doc.get("relevant_focus_points", [])

            for element, edata in framework.items():
                for princ, pdata in edata["principles"].items():
                    for fp in pdata["focus_points"]:
                        # 检查是否覆盖此关注点
                        covered = fp in relevant
                        if not covered:
                            # 关键词匹配
                            fp_lower = fp.lower()
                            if any(kw.lower() in content for kw in keywords):
                                if fp_lower in content:
                                    covered = True
                            if fp_lower in doc_name.lower():
                                covered = True

                        if covered:
                            if fp not in coverage_map:
                                coverage_map[fp] = []
                            coverage_map[fp].append(doc_name)

        # 计算各要素评分
        element_scores = {}
        total_score = 0.0
        all_gaps: List[Dict] = []

        for element, edata in framework.items():
            covered_count = 0
            total_count = 0
            element_gaps = []

            for princ, pdata in edata["principles"].items():
                for fp in pdata["focus_points"]:
                    total_count += 1
                    if fp in coverage_map and coverage_map[fp]:
                        covered_count += 1
                    else:
                        element_gaps.append({
                            "principle": princ,
                            "focus_point": fp,
                            "status": "未覆盖",
                        })

            coverage_rate = (covered_count / max(total_count, 1)) * 100
            element_scores[element] = {
                "covered": covered_count,
                "total": total_count,
                "coverage_rate": round(coverage_rate, 1),
                "weight": edata["weight"],
                "gaps": element_gaps,
                "rating": "优秀" if coverage_rate >= 90 else ("良好" if coverage_rate >= 70 else ("一般" if coverage_rate >= 50 else "不足")),
            }
            total_score += coverage_rate * edata["weight"]
            all_gaps.extend(element_gaps)

        return {
            "status": "success",
            "data": {
                "total_focus_points": total_focus_points,
                "covered_focus_points": len(coverage_map),
                "overall_coverage_rate": round(
                    len(coverage_map) / max(total_focus_points, 1) * 100, 1
                ),
                "weighted_score": round(total_score, 1),
                "element_scores": element_scores,
                "all_gaps": all_gaps,
                "coverage_map": {k: v for k, v in coverage_map.items()},
                "rating": "健全" if total_score >= 90 else ("基本健全" if total_score >= 70 else ("有待完善" if total_score >= 50 else "严重不足")),
            },
            "summary": f"COSO五要素加权评分{total_score:.1f}分，制度覆盖度{len(coverage_map)}/{total_focus_points}，评级：{'健全' if total_score >= 90 else ('基本健全' if total_score >= 70 else ('有待完善' if total_score >= 50 else '严重不足'))}",
        }

    except Exception as e:
        return {"status": "error", "data": None, "summary": f"评估异常: {str(e)}"}


def handle_request(method: str, params: dict) -> dict:
    if method == "evaluate_coso_coverage":
        return evaluate_coso_coverage(
            params.get("documents", []),
            framework=params.get("framework"),
        )
    return {"status": "error", "data": None, "summary": f"未知方法: {method}"}


if __name__ == "__main__":
    docs = [
        {"name": "财务管理制度", "content_text": "会计制度、凭证管理、对账制度、预算管理、审批流程...", "keywords": ["财务", "会计", "凭证", "预算", "审批"], "relevant_focus_points": ["会计制度", "凭证管理规范", "对账制度"]},
        {"name": "人力资源管理制度", "content_text": "招聘录用、薪酬考核、培训发展、岗位职责...", "keywords": ["招聘", "薪酬", "培训", "岗位"], "relevant_focus_points": ["招聘录用制度", "薪酬考核制度", "岗位职责说明书"]},
        {"name": "内部审计制度", "content_text": "内部审计、缺陷报告、整改跟踪、审计计划...", "keywords": ["审计", "缺陷", "整改"], "relevant_focus_points": ["内部审计制度", "内审计划与执行", "缺陷报告流程"]},
        {"name": "授权管理制度", "content_text": "审批权限、授权矩阵、重大事项审批...", "keywords": ["审批", "授权", "权限"], "relevant_focus_points": ["审批权限表", "重大事项审批流程", "授权审批矩阵"]},
    ]

    result = evaluate_coso_coverage(docs)
    print("=" * 60)
    print("COSO五要素制度覆盖度评估")
    print("=" * 60)
    print(f"加权评分: {result['data']['weighted_score']}分 [{result['data']['rating']}]")
    print(f"覆盖关注点: {result['data']['covered_focus_points']}/{result['data']['total_focus_points']} ({result['data']['overall_coverage_rate']}%)")

    for element, scores in result["data"]["element_scores"].items():
        bar = "█" * int(scores["coverage_rate"] / 10) + "░" * (10 - int(scores["coverage_rate"] / 10))
        print(f"\n  {element} (权重{scores['weight']}): {scores['coverage_rate']}% [{scores['rating']}] {scores['covered']}/{scores['total']}")
        print(f"  {bar}")
        if scores["gaps"]:
            print(f"  制度空白（前5）:")
            for g in scores["gaps"][:5]:
                print(f"    - [{g['principle']}] {g['focus_point']}")

    print(f"\n{result['summary']}")
    assert result["status"] == "success"
    assert result["data"]["weighted_score"] < 50  # 4份文档只能覆盖少量

    print("\n✅ 全部测试通过")
