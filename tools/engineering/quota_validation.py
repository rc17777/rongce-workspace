"""
定额套用审查
============
检查分部分项清单的定额套用是否合理，识别未套定额、套用错误、高套定额嫌疑。

用法:
    python -m tools.engineering.quota_validation --input data.json --output result.json
"""

import json
import argparse
from dataclasses import dataclass, field
from typing import Optional
from difflib import SequenceMatcher

# ============================================================
# 可配置阈值
# ============================================================
NAME_SIMILARITY_THRESHOLD = 0.6       # 项目名称与定额名称相似度阈值（低于此值认为不匹配）
HIGH_QUOTA_RATIO_THRESHOLD = 0.9     # 高套嫌疑：选择了基价排名前X%的定额（默认前10%）
# ============================================================


@dataclass
class QuotaEntry:
    """定额条目"""
    code: str                       # 定额编号
    name: str                       # 定额名称
    unit: str                       # 单位
    base_price: float               # 基价（元）
    region: str = ""                # 适用地区
    year: int = 2024                # 定额版本年份
    status: str = "active"          # 状态: active/deprecated
    description: str = ""           # 项目特征描述


@dataclass
class WorkItem:
    """需要审查的分部分项清单项"""
    code: str                       # 清单编码
    name: str                       # 清单名称
    unit: str                       # 单位
    quantity: float                 # 工程量
    applied_quota_code: str = ""    # 已套定额编号（可为空）
    applied_quota_name: str = ""    # 已套定额名称
    feature_desc: str = ""          # 项目特征描述


@dataclass
class QuotaIssue:
    """定额套用问题"""
    severity: str                   # high/medium/low
    category: str                   # 问题类别
    work_item_code: str             # 关联清单编码
    work_item_name: str             # 清单名称
    detail: str                     # 问题描述
    suggestion: str = ""            # 建议


@dataclass
class QuotaResult:
    """定额审查完整结果"""
    project_name: str
    issues: list[QuotaIssue] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    pass_rate: float = 0.0

    def to_json(self) -> str:
        return json.dumps({
            "project_name": self.project_name,
            "summary": self.summary,
            "pass_rate": round(self.pass_rate, 4),
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "work_item_code": i.work_item_code,
                    "work_item_name": i.work_item_name,
                    "detail": i.detail,
                    "suggestion": i.suggestion
                }
                for i in self.issues
            ]
        }, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            f"# 定额套用审查报告 — {self.project_name}",
            "",
            "## 汇总",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 审查清单项数 | {self.summary.get('total_items', 0)} |",
            f"| 通过项数 | {self.summary.get('passed', 0)} |",
            f"| 问题项数 | {self.summary.get('issue_count', 0)} |",
            f"| 通过率 | {self.pass_rate:.1%} |",
            f"| 高风险 | {self.summary.get('high', 0)} |",
            f"| 中风险 | {self.summary.get('medium', 0)} |",
            f"| 低风险 | {self.summary.get('low', 0)} |",
            "",
            "## 问题明细",
        ]

        if not self.issues:
            lines.append("✅ 未发现问题。")
            return "\n".join(lines)

        # 按严重程度排序
        by_severity = {"high": [], "medium": [], "low": []}
        for iss in self.issues:
            by_severity[iss.severity].append(iss)

        for sev, label in [("high", "🔴 高风险"), ("medium", "🟡 中风险"), ("low", "🟢 低风险")]:
            if not by_severity[sev]:
                continue
            lines += ["", f"### {label}"]
            for iss in by_severity[sev]:
                lines += [
                    f"**{iss.category}** — {iss.work_item_code} {iss.work_item_name}",
                    f"> {iss.detail}",
                ]
                if iss.suggestion:
                    lines.append(f"> 建议: {iss.suggestion}")
                lines.append("")

        lines.append("---")
        lines.append("*本报告由融策工程咨询Agent自动生成，仅供专业人员参考。*")
        return "\n".join(lines)


def _name_similarity(name_a: str, name_b: str) -> float:
    """计算两个项目名称的文本相似度"""
    return SequenceMatcher(None, name_a, name_b).ratio()


def _find_matching_quotas(item: WorkItem, quota_lib: list[QuotaEntry]) -> list[QuotaEntry]:
    """在定额库中查找与清单项匹配的定额"""
    item_keywords = set(item.name) | set(item.feature_desc)
    matches = []
    for q in quota_lib:
        q_keywords = set(q.name) | set(q.description)
        # 简单关键词重叠检测
        overlap = len(item_keywords & q_keywords) / max(len(item_keywords), 1)
        name_sim = _name_similarity(item.name, q.name)
        if overlap > 0.3 or name_sim > 0.5:
            matches.append(q)

    # 按名称相似度排序
    matches.sort(key=lambda q: _name_similarity(item.name, q.name), reverse=True)
    return matches


def _check_high_quota(item: WorkItem, all_matches: list[QuotaEntry],
                      applied: Optional[QuotaEntry]) -> Optional[QuotaIssue]:
    """检查是否有高套定额嫌疑"""
    if not applied or not all_matches:
        return None

    # 按基价排序
    sorted_matches = sorted(all_matches, key=lambda q: q.base_price, reverse=True)
    high_cutoff = max(1, int(len(sorted_matches) * (1 - HIGH_QUOTA_RATIO_THRESHOLD)))
    top_priced = sorted_matches[:high_cutoff]

    if applied in top_priced and len(sorted_matches) > 1:
        median_idx = len(sorted_matches) // 2
        median_price = sorted_matches[median_idx].base_price if median_idx < len(sorted_matches) else applied.base_price
        if applied.base_price > median_price * 1.3:  # 超过中位数30%
            return QuotaIssue(
                severity="high",
                category="高套定额嫌疑",
                work_item_code=item.code,
                work_item_name=item.name,
                detail=f"当前套用定额 {applied.code} 基价 {applied.base_price:.2f}元，"
                       f"在同组可选定额中处于最高价位区间（前{HIGH_QUOTA_RATIO_THRESHOLD:.0%}），"
                       f"高于中位数 {median_price:.2f}元 {applied.base_price/median_price-1:.0%}。",
                suggestion=f"建议复核是否可套用中位定额（{sorted_matches[median_idx].code}，基价{median_price:.2f}元）。"
            )
    return None


def validate_quotas(
    work_items: list[WorkItem],
    quota_lib: list[QuotaEntry],
    project_name: str = "",
    current_year: int = 2026
) -> QuotaResult:
    """
    执行定额套用审查

    Args:
        work_items: 需审查的分部分项清单
        quota_lib: 地区定额库
        project_name: 项目名称
        current_year: 当前年份（用于判断定额是否过时）

    Returns:
        QuotaResult: 审查结果
    """
    issues: list[QuotaIssue] = []
    total_items = len(work_items)

    for item in work_items:
        # === 检查1: 未套定额 ===
        if not item.applied_quota_code:
            # 尝试推荐匹配定额
            suggestions = _find_matching_quotas(item, quota_lib)[:3]
            sug_text = "、".join(f"{q.code}({q.name})" for q in suggestions) if suggestions else "无匹配推荐"
            issues.append(QuotaIssue(
                severity="high",
                category="未套定额",
                work_item_code=item.code,
                work_item_name=item.name,
                detail=f"清单项 {item.code} 未套用任何定额。",
                suggestion=f"推荐定额: {sug_text}"
            ))
            continue

        # === 检查2: 定额是否存在 ===
        applied_quota = None
        for q in quota_lib:
            if q.code == item.applied_quota_code:
                applied_quota = q
                break

        if not applied_quota:
            issues.append(QuotaIssue(
                severity="high",
                category="定额不存在",
                work_item_code=item.code,
                work_item_name=item.name,
                detail=f"套用的定额编号 {item.applied_quota_code} 在定额库中不存在。",
                suggestion="请核实定额编号是否输入正确，或该定额是否已废止。"
            ))
            continue

        # === 检查3: 定额状态（是否已废止） ===
        if applied_quota.status == "deprecated":
            issues.append(QuotaIssue(
                severity="high",
                category="定额已废止",
                work_item_code=item.code,
                work_item_name=item.name,
                detail=f"套用的定额 {applied_quota.code}（{applied_quota.year}年版）已废止。",
                suggestion=f"请查阅 {current_year} 年最新版定额库，替换为现行有效定额。"
            ))

        # === 检查4: 定额版本过旧 ===
        if current_year - applied_quota.year >= 5:
            issues.append(QuotaIssue(
                severity="medium",
                category="定额版本过旧",
                work_item_code=item.code,
                work_item_name=item.name,
                detail=f"套用的定额为 {applied_quota.year} 年版，距今已 {current_year - applied_quota.year} 年。",
                suggestion="建议核实是否有新版定额替代。"
            ))

        # === 检查5: 项目特征不匹配 ===
        similarity = _name_similarity(item.name, applied_quota.name)
        if similarity < NAME_SIMILARITY_THRESHOLD:
            issues.append(QuotaIssue(
                severity="medium",
                category="项目特征不匹配",
                work_item_code=item.code,
                work_item_name=item.name,
                detail=f"清单项名称与定额名称相似度仅 {similarity:.1%}，可能存在套用错误。"
                       f"\n  清单: {item.name}\n  定额: {applied_quota.name}",
                suggestion=f"建议核实 {item.code} 是否应该套用其他定额。"
            ))

        # === 检查6: 单位不匹配（软检查） ===
        if item.unit and applied_quota.unit and item.unit != applied_quota.unit:
            issues.append(QuotaIssue(
                severity="low",
                category="单位不匹配",
                work_item_code=item.code,
                work_item_name=item.name,
                detail=f"清单单位'{item.unit}'与定额单位'{applied_quota.unit}'不一致，需确认是否需要换算。",
                suggestion="如需换算，请确认换算系数并在备注中说明。"
            ))

        # === 检查7: 高套定额嫌疑 ===
        all_matches = _find_matching_quotas(item, quota_lib)
        high_issue = _check_high_quota(item, all_matches, applied_quota)
        if high_issue:
            issues.append(high_issue)

    # 汇总统计
    item_issue_count: dict[str, set] = {}
    for iss in issues:
        item_issue_count.setdefault(iss.work_item_code, set()).add(iss.severity)

    # 取每个清单项的最高严重程度
    def _max_severity(sev_set: set[str]) -> str:
        if "high" in sev_set:
            return "high"
        if "medium" in sev_set:
            return "medium"
        return "low"

    sev_counts = {"high": 0, "medium": 0, "low": 0}
    for sev_set in item_issue_count.values():
        sev_counts[_max_severity(sev_set)] += 1

    issue_item_count = len(item_issue_count)
    passed_count = total_items - issue_item_count

    return QuotaResult(
        project_name=project_name,
        issues=issues,
        summary={
            "total_items": total_items,
            "passed": passed_count,
            "issue_count": issue_item_count,
            "total_issues": len(issues),
            **sev_counts
        },
        pass_rate=passed_count / total_items if total_items > 0 else 1.0
    )


# ============================================================
# CLI入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="定额套用审查")
    parser.add_argument("--input", required=True, help="输入JSON文件路径")
    parser.add_argument("--output", required=True, help="输出JSON文件路径")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    project_name = data.get("project_name", "")

    # 解析清单项
    work_items = [WorkItem(
        code=it["code"], name=it["name"], unit=it.get("unit", ""),
        quantity=float(it.get("quantity", 1)),
        applied_quota_code=it.get("applied_quota_code", ""),
        applied_quota_name=it.get("applied_quota_name", ""),
        feature_desc=it.get("feature_desc", "")
    ) for it in data.get("work_items", [])]

    # 解析定额库
    quota_lib = [QuotaEntry(
        code=q["code"], name=q["name"], unit=q.get("unit", ""),
        base_price=float(q.get("base_price", 0)),
        region=q.get("region", ""),
        year=int(q.get("year", 2024)),
        status=q.get("status", "active"),
        description=q.get("description", "")
    ) for q in data.get("quota_lib", [])]

    result = validate_quotas(work_items, quota_lib, project_name)

    if args.format in ("json", "both"):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.to_json())
        print(f"[✓] JSON结果已保存: {args.output}")

    if args.format in ("md", "both"):
        out_md = args.output.replace(".json", ".md")
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(result.to_markdown())
        print(f"[✓] Markdown报告已保存: {out_md}")

    print(f"\n{'='*50}")
    print(f"项目: {project_name}")
    print(f"审查项数: {result.summary['total_items']} | 通过: {result.summary['passed']} | 问题: {result.summary['issue_count']}")
    print(f"通过率: {result.pass_rate:.1%}")
    print(f"高/{result.summary['high']} 中/{result.summary['medium']} 低/{result.summary['low']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
