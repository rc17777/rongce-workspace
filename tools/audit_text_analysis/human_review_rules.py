"""
P2: human_review_rules — 人机复核量化规则 (v6, 2d)

在现有三级复核流程中嵌入量化抽检规则：
  L1（AI自动评分）：评分≥0.85且无扣分项 → 人工抽检5%
  L2（Agent交叉复核）：任一Agent触发异常标记 → 人工100%全检
  L3（独立质量复核）：全部100%全检

集成到 workpaper_scorer 和 pipeline Step4 中。
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ReviewLevel(str, Enum):
    L1_AI = "L1"        # AI自动评分
    L2_AGENT = "L2"     # Agent交叉复核
    L3_INDEPENDENT = "L3"  # 独立质量复核


class SamplingStrategy(str, Enum):
    NONE = "none"           # 不抽检
    SPOT_5PCT = "spot_5%"   # 5%随机抽检
    TARGETED_100PCT = "targeted_100%"  # 定向100%全检
    FULL_100PCT = "full_100%"  # 全部100%全检


@dataclass
class ReviewRule:
    """单条复核规则"""
    level: ReviewLevel
    condition: str                 # 触发条件描述
    sampling_strategy: SamplingStrategy
    sample_size_description: str   # "100%" / "5%（最少5份）"等


@dataclass
class ReviewPlan:
    """一个审计项目的复核计划"""
    total_items: int
    rules: List[ReviewRule]

    # 各级复核样本量
    l1_sample_count: int = 0
    l2_sample_count: int = 0
    l3_sample_count: int = 0

    # 异常触发统计
    l2_triggered_items: int = 0   # 有多少项触发了L2全检
    high_risk_items: int = 0       # 高危项数

    def summary(self) -> str:
        """生成复核计划摘要"""
        total = self.total_items
        l1_pct = self.l1_sample_count / total * 100 if total > 0 else 0
        l2_pct = self.l2_sample_count / total * 100 if total > 0 else 0
        l3_pct = self.l3_sample_count / total * 100 if total > 0 else 0

        return (
            f"复核计划：总计{total}项\n"
            f"  L1 AI评分抽检：{self.l1_sample_count}项（{l1_pct:.1f}%）\n"
            f"  L2 Agent异常全检：{self.l2_sample_count}项（{l2_pct:.1f}%）\n"
            f"  L3 独立质量复核：{self.l3_sample_count}项（{l3_pct:.1f}%）\n"
            f"  总复核量：{self.l1_sample_count + self.l2_sample_count + self.l3_sample_count}项"
        )


# ── 默认复核规则 ─────────────────────────────────────────────

DEFAULT_REVIEW_RULES = [
    ReviewRule(
        level=ReviewLevel.L1_AI,
        condition="AI评分 ≥ 0.85 且 无E/F/G类扣分项",
        sampling_strategy=SamplingStrategy.SPOT_5PCT,
        sample_size_description="5%（最少5份）随机抽检",
    ),
    ReviewRule(
        level=ReviewLevel.L1_AI,
        condition="AI评分 < 0.85 或 存在E/F/G类扣分项",
        sampling_strategy=SamplingStrategy.TARGETED_100PCT,
        sample_size_description="100%定向全检",
    ),
    ReviewRule(
        level=ReviewLevel.L2_AGENT,
        condition="任一Agent触发异常标记（severity=high）",
        sampling_strategy=SamplingStrategy.TARGETED_100PCT,
        sample_size_description="100%定向全检",
    ),
    ReviewRule(
        level=ReviewLevel.L2_AGENT,
        condition="多Agent交叉标记同一疑点（>=2个Agent独立检出）",
        sampling_strategy=SamplingStrategy.TARGETED_100PCT,
        sample_size_description="100%定向全检（多Agent一致=高可信度但仍需人工确认）",
    ),
    ReviewRule(
        level=ReviewLevel.L2_AGENT,
        condition="疑点涉及金额 > 重要性水平的5%",
        sampling_strategy=SamplingStrategy.TARGETED_100PCT,
        sample_size_description="100%定向全检（大额必查）",
    ),
    ReviewRule(
        level=ReviewLevel.L3_INDEPENDENT,
        condition="全部审计发现（不论评分高低）",
        sampling_strategy=SamplingStrategy.FULL_100PCT,
        sample_size_description="100%全量复核（独立质量复核岗）",
    ),
]


class ReviewPlanner:
    """复核计划生成器"""

    def __init__(self, rules: Optional[List[ReviewRule]] = None):
        self.rules = rules or DEFAULT_REVIEW_RULES

    def plan(
        self,
        total_items: int,
        ai_scores: Optional[List[float]] = None,
        high_risk_count: int = 0,
        l2_triggered_count: int = 0,
        materiality_threshold: float = 0.05,
    ) -> ReviewPlan:
        """
        生成复核计划

        Args:
            total_items: 审计发现总条数
            ai_scores: L1 AI评分列表（0-1分）
            high_risk_count: 高危发现数
            l2_triggered_count: L2 Agent触发的异常数
            materiality_threshold: 重要性水平阈值
        """
        plan = ReviewPlan(
            total_items=total_items,
            rules=self.rules,
            high_risk_items=high_risk_count,
            l2_triggered_items=l2_triggered_count,
        )

        # L1 抽样
        if ai_scores:
            # 评分≥0.85且无扣分项 → 抽检5%
            clean_count = sum(1 for s in ai_scores if s >= 0.85)
            plan.l1_sample_count = max(5, int(clean_count * 0.05))
            # 剩余项全部全检
            plan.l1_sample_count += sum(1 for s in ai_scores if s < 0.85)
        else:
            # 无评分数据 → 保守估计，全部视为需复核
            plan.l1_sample_count = total_items

        # L2 全检
        plan.l2_sample_count = max(high_risk_count, l2_triggered_count)

        # L3 全部全检
        plan.l3_sample_count = total_items

        # 去重：同一项在L1被标记→不计入L2重复
        plan.l2_sample_count = min(plan.l2_sample_count, total_items)

        return plan

    def calculate_review_workload(
        self,
        plan: ReviewPlan,
        minutes_per_item: float = 5.0,
    ) -> Dict[str, Any]:
        """计算复核工作量（人时）"""
        l1_hours = plan.l1_sample_count * minutes_per_item / 60
        l2_hours = plan.l2_sample_count * minutes_per_item / 60
        l3_hours = plan.l3_sample_count * minutes_per_item / 60
        total_hours = l1_hours + l2_hours + l3_hours

        return {
            "l1_review_hours": round(l1_hours, 1),
            "l2_review_hours": round(l2_hours, 1),
            "l3_review_hours": round(l3_hours, 1),
            "total_hours": round(total_hours, 1),
            "estimated_days": round(total_hours / 8, 1),
            "recommendation": self._staffing_recommendation(total_hours),
        }

    def _staffing_recommendation(self, total_hours: float) -> str:
        """人员配置建议"""
        if total_hours <= 8:
            return "1人可完成（建议半天内集中复核）"
        elif total_hours <= 24:
            return "建议1-2人（1-3天内完成）"
        elif total_hours <= 80:
            return "建议2-4人（1-2周内完成）"
        else:
            return f"建议至少{int(total_hours/40) + 1}人（按40h/周计算）"


# ── 业绩统计 ──────────────────────────────────────────────────

@dataclass
class ReviewStats:
    """复核统计"""
    total_reviewed: int = 0
    confirmed_positives: int = 0     # 确认为真实问题
    false_positives: int = 0          # 确认为误报
    modified_findings: int = 0        # 修正后发现（部分准确）
    l1_recall: float = 0.0            # L1召回率（L1标记中真实问题的比例）
    l2_recall: float = 0.0            # L2召回率
    l3_error_capture: float = 0.0     # L3捕获的L1/L2遗漏问题比率


def compute_review_stats(
    l1_flagged: int, l1_confirmed: int,
    l2_flagged: int, l2_confirmed: int,
    l3_caught_missed: int,
) -> ReviewStats:
    """计算复核绩效指标"""
    return ReviewStats(
        total_reviewed=l1_flagged + l2_flagged,
        confirmed_positives=l1_confirmed + l2_confirmed,
        false_positives=(l1_flagged - l1_confirmed) + (l2_flagged - l2_confirmed),
        l1_recall=l1_confirmed / l1_flagged if l1_flagged > 0 else 0,
        l2_recall=l2_confirmed / l2_flagged if l2_flagged > 0 else 0,
        l3_error_capture=l3_caught_missed / (l1_flagged + l2_flagged) if (l1_flagged + l2_flagged) > 0 else 0,
    )


# ── MCP工具接口 ──────────────────────────────────────────────

def generate_review_plan(
    total_items: int,
    ai_scores: Optional[List[float]] = None,
    high_risk_count: int = 0,
    l2_triggered_count: int = 0,
) -> dict:
    """生成人机复核计划"""
    planner = ReviewPlanner()
    plan = planner.plan(
        total_items=total_items,
        ai_scores=ai_scores,
        high_risk_count=high_risk_count,
        l2_triggered_count=l2_triggered_count,
    )
    workload = planner.calculate_review_workload(plan)

    return {
        "total_items": plan.total_items,
        "l1_sample_count": plan.l1_sample_count,
        "l2_sample_count": plan.l2_sample_count,
        "l3_sample_count": plan.l3_sample_count,
        "total_review_count": plan.l1_sample_count + plan.l2_sample_count + plan.l3_sample_count,
        "review_rate": f"{(plan.l1_sample_count + plan.l2_sample_count + plan.l3_sample_count) / plan.total_items * 100:.1f}%"
            if plan.total_items > 0 else "0%",
        "workload": workload,
        "summary": plan.summary(),
    }
