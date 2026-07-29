"""
工具9：contract_change_trajectory — 合同变更轨迹分析器

场景：采购/工程审计中，通过横向投影分析合同变更类型分布，
     对标行业基准值，检测异常变更率及变更时间点模式。

技术：变更类型汇总 → 行业基准比对 → 时间点聚焦 → 审减率联动
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import csv


# ── 行业基准值（可配置）─────────────────────────────────────

INDUSTRY_BENCHMARKS = {
    "procurement": {
        "total_change_rate": 0.05,  # 总变更率
        "amount_increase_rate": 0.03,  # 金额调增率
        "amount_decrease_rate": 0.01,  # 金额调减率
        "scope_change_rate": 0.02,
        "timeline_change_rate": 0.03,
        "description": "采购合同行业基准（政府/央企采购）",
    },
    "project_construction": {
        "total_change_rate": 0.10,  # 工程变更率通常更高
        "amount_increase_rate": 0.06,
        "amount_decrease_rate": 0.02,
        "scope_change_rate": 0.05,
        "timeline_change_rate": 0.04,
        "description": "工程建设行业基准",
    },
    "general": {
        "total_change_rate": 0.05,
        "amount_increase_rate": 0.03,
        "amount_decrease_rate": 0.01,
        "scope_change_rate": 0.02,
        "timeline_change_rate": 0.03,
        "description": "通用基准",
    },
}

# 变更类型枚举
CHANGE_TYPES = [
    "amount_increase",   # 金额调增
    "amount_decrease",   # 金额调减
    "scope_change",      # 范围变更
    "timeline_change",   # 工期变更
    "party_change",      # 主体变更
    "other",             # 其他
]


# ── 数据结构 ──────────────────────────────────────────────────

@dataclass
class ChangeRecord:
    """单条变更记录"""
    project_id: str
    change_date: str
    change_type: str  # amount_increase | amount_decrease | scope_change | ...
    change_amount: float = 0.0  # 变更金额（正=增/负=减）
    change_description: str = ""
    change_reason: str = ""


@dataclass
class ChangeTypeStats:
    """某类变更的统计"""
    change_type: str
    count: int
    total_amount: float
    pct_of_total: float  # 占总变更数的%
    industry_benchmark: float  # 行业基准率
    deviation: float  # 偏离（百分比点）
    is_abnormal: bool = False  # 是否异常偏高


@dataclass
class TimeCluster:
    """变更时间聚集"""
    period_label: str  # "合同签订前" "履行期" "验收前" "验收后" "质保期"
    count: int
    total_amount: float
    pct_of_total: float
    risk_level: str  # high/medium/low


@dataclass
class TrajectoryResult:
    """变更轨迹分析完整结果"""
    total_projects: int
    projects_with_changes: int
    overall_change_rate: float
    industry_benchmark: float
    change_rate_deviation: float
    change_type_stats: List[ChangeTypeStats]
    time_clusters: List[TimeCluster]
    high_risk_projects: List[Dict[str, Any]]
    summary: str


class ContractChangeTrajectoryAnalyzer:
    """合同变更轨迹分析器"""

    def __init__(self, industry: str = "general"):
        self.industry = industry
        self.benchmarks = INDUSTRY_BENCHMARKS.get(
            industry, INDUSTRY_BENCHMARKS["general"]
        )

    def analyze(
        self,
        contracts: List[Dict[str, Any]],
        changes: List[Dict[str, Any]],
    ) -> TrajectoryResult:
        """
        分析合同变更轨迹

        Args:
            contracts: 合同列表 [{"project_id": "...", "contract_date": "...",
                        "completion_date": "...", "contract_amount": 10000, ...}, ...]
            changes: 变更记录 [{"project_id": "...", "change_date": "...",
                      "change_type": "amount_decrease", "change_amount": -5000, ...}, ...]
        """
        total_n = len(contracts) or 1

        # 合同索引
        contract_map = {}
        for c in contracts:
            pid = str(c.get("project_id", ""))
            if pid:
                contract_map[pid] = c

        # 统计有变更的合同数
        changed_pids = set(ch.get("project_id", "") for ch in changes)
        changed_n = len(changed_pids)
        overall_rate = changed_n / total_n

        # 变更类型统计
        type_counter = Counter()
        type_amount: Dict[str, float] = defaultdict(float)
        for ch in changes:
            ct = ch.get("change_type", "other")
            if ct not in CHANGE_TYPES:
                ct = "other"
            type_counter[ct] += 1
            try:
                type_amount[ct] += float(ch.get("change_amount", 0))
            except (ValueError, TypeError):
                pass

        total_changes = len(changes) or 1

        change_type_stats = []
        for ct in CHANGE_TYPES:
            cnt = type_counter.get(ct, 0)
            # 变更率 = 该类变更数 / 合同总数
            rate = cnt / total_n
            benchmark_key = self._benchmark_key(ct)
            benchmark = self.benchmarks.get(benchmark_key, 0.05)
            deviation = rate - benchmark
            is_abnormal = deviation > 0.02  # 超过基准2个百分点=异常

            change_type_stats.append(ChangeTypeStats(
                change_type=ct,
                count=cnt,
                total_amount=type_amount.get(ct, 0),
                pct_of_total=round(cnt / total_changes, 3) if cnt > 0 else 0,
                industry_benchmark=round(benchmark, 3),
                deviation=round(deviation, 3),
                is_abnormal=is_abnormal,
            ))

        # 时间点聚集分析
        time_clusters = self._analyze_time_clusters(
            changes, contract_map
        )

        # 高风险项目
        high_risk = self._identify_high_risk(
            changes, contract_map, change_type_stats, time_clusters
        )

        # 摘要
        summary = self._summarize(
            changed_n, total_n, overall_rate,
            change_type_stats, time_clusters, high_risk,
        )

        return TrajectoryResult(
            total_projects=total_n,
            projects_with_changes=changed_n,
            overall_change_rate=round(overall_rate, 3),
            industry_benchmark=self.benchmarks["total_change_rate"],
            change_rate_deviation=round(
                overall_rate - self.benchmarks["total_change_rate"], 3
            ),
            change_type_stats=change_type_stats,
            time_clusters=time_clusters,
            high_risk_projects=high_risk[:20],
            summary=summary,
        )

    def _benchmark_key(self, change_type: str) -> str:
        """变更类型 → 基准值key"""
        mapping = {
            "amount_increase": "amount_increase_rate",
            "amount_decrease": "amount_decrease_rate",
            "scope_change": "scope_change_rate",
            "timeline_change": "timeline_change_rate",
        }
        return mapping.get(change_type, "total_change_rate")

    def _analyze_time_clusters(
        self,
        changes: List[Dict],
        contract_map: Dict[str, Dict],
    ) -> List[TimeCluster]:
        """
        分析变更发生的时间点分布

        时间窗口定义：
        - 合同签订前：change_date < contract_date
        - 履行期：contract_date ≤ change_date < completion_date - 30天
        - 验收前（30天窗口）：completion_date - 30天 ≤ change_date < completion_date
        - 验收后：completion_date ≤ change_date < completion_date + 90天
        - 质保期后：change_date ≥ completion_date + 90天
        """
        clusters: Dict[str, Dict[str, Any]] = {
            "合同签订前": {"count": 0, "total_amount": 0.0, "risk": "low"},
            "履行期": {"count": 0, "total_amount": 0.0, "risk": "low"},
            "验收前(30天)": {"count": 0, "total_amount": 0.0, "risk": "medium"},
            "验收后(90天内)": {"count": 0, "total_amount": 0.0, "risk": "high"},
            "质保期后": {"count": 0, "total_amount": 0.0, "risk": "medium"},
        }

        for ch in changes:
            pid = str(ch.get("project_id", ""))
            contract = contract_map.get(pid, {})
            change_date_str = str(ch.get("change_date", ""))

            try:
                change_date = datetime.strptime(
                    change_date_str.strip(), "%Y-%m-%d"
                )
            except ValueError:
                continue

            try:
                contract_date = datetime.strptime(
                    str(contract.get("contract_date", "")).strip(), "%Y-%m-%d"
                )
            except ValueError:
                contract_date = None

            try:
                completion_date = datetime.strptime(
                    str(contract.get("completion_date", "")).strip(), "%Y-%m-%d"
                )
            except ValueError:
                # 无完工日期则使用验收日期或合同日期+365天
                try:
                    acceptance = str(contract.get("acceptance_date", "")).strip()
                    completion_date = datetime.strptime(acceptance, "%Y-%m-%d")
                except (ValueError, KeyError):
                    if contract_date:
                        completion_date = contract_date + __import__("datetime").timedelta(days=365)
                    else:
                        completion_date = None

            amount = 0.0
            try:
                amount = abs(float(ch.get("change_amount", 0)))
            except (ValueError, TypeError):
                pass

            period = self._classify_period(
                change_date, contract_date, completion_date
            )

            clusters[period]["count"] += 1
            clusters[period]["total_amount"] += amount

        total = sum(c["count"] for c in clusters.values()) or 1
        result = []
        for period, data in clusters.items():
            result.append(TimeCluster(
                period_label=period,
                count=data["count"],
                total_amount=data["total_amount"],
                pct_of_total=round(data["count"] / total, 3),
                risk_level=data["risk"],
            ))

        return sorted(result, key=lambda c: c.count, reverse=True)

    def _classify_period(
        self, change_date: datetime,
        contract_date: Optional[datetime],
        completion_date: Optional[datetime],
    ) -> str:
        """分类变更时间点"""
        if contract_date and change_date < contract_date:
            return "合同签订前"
        if completion_date and change_date >= completion_date + timedelta(days=90):
            return "质保期后"
        if completion_date and change_date >= completion_date:
            return "验收后(90天内)"
        if completion_date and change_date >= completion_date - timedelta(days=30):
            return "验收前(30天)"
        return "履行期"

    def _identify_high_risk(
        self,
        changes: List[Dict],
        contract_map: Dict[str, Dict],
        type_stats: List[ChangeTypeStats],
        time_clusters: List[TimeCluster],
    ) -> List[Dict[str, Any]]:
        """
        识别高风险项目

        风险规则：
        1. 验收后金额调减 → 高风险（结算水分）
        2. 验收前密集变更 → 中风险（赶工/补手续）
        3. 金额调减且无明确理由 → 高风险
        4. 单个项目变更次数>3 → 中风险
        """
        # 按项目聚合
        project_changes: Dict[str, List[Dict]] = defaultdict(list)
        for ch in changes:
            pid = str(ch.get("project_id", ""))
            project_changes[pid].append(ch)

        high_risk = []
        for pid, pchanges in project_changes.items():
            contract = contract_map.get(pid, {})
            risk_score = 0
            risk_reasons = []

            # 规则1: 验收后金额调减
            post_completion_decrease = [
                c for c in pchanges
                if c.get("change_type") == "amount_decrease"
            ]
            # 简化判断：只要有金额调减记录
            if post_completion_decrease:
                risk_score += 3
                risk_reasons.append(
                    "验收后金额调减——疑似结算水分/原始合同价格虚高"
                )

            # 规则2: 变更次数>3
            if len(pchanges) > 3:
                risk_score += 2
                risk_reasons.append(f"变更次数异常（{len(pchanges)}次）")

            # 规则3: 金额调减且变更理由为空
            no_reason_decrease = [
                c for c in pchanges
                if c.get("change_type") == "amount_decrease"
                and not c.get("change_reason", "").strip()
            ]
            if no_reason_decrease:
                risk_score += 2
                risk_reasons.append(
                    f"{len(no_reason_decrease)}次金额调减无明确理由"
                )

            # 规则4: 调减金额占比大
            total_decrease = sum(
                abs(float(c.get("change_amount", 0)))
                for c in post_completion_decrease
            )
            contract_amt = float(contract.get("contract_amount", 0))
            if contract_amt > 0 and total_decrease / contract_amt > 0.10:
                risk_score += 2
                risk_reasons.append(
                    f"调减金额占合同额{total_decrease/contract_amt:.0%}"
                )

            if risk_score >= 2:
                high_risk.append({
                    "project_id": pid,
                    "change_count": len(pchanges),
                    "risk_score": risk_score,
                    "risk_level": (
                        "high" if risk_score >= 5
                        else "medium" if risk_score >= 3
                        else "low"
                    ),
                    "risk_reasons": risk_reasons,
                    "total_decrease_amount": total_decrease if post_completion_decrease else 0,
                })

        return sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)

    def _summarize(
        self, changed_n: int, total_n: int, overall_rate: float,
        type_stats: List[ChangeTypeStats],
        time_clusters: List[TimeCluster],
        high_risk: List[Dict],
    ) -> str:
        """生成摘要"""
        benchmark_rate = self.benchmarks["total_change_rate"]
        parts = []

        # 总体变更率
        if overall_rate > benchmark_rate * 2:
            parts.append(
                f"🔴 合同变更率{overall_rate:.1%}，是行业基准（{benchmark_rate:.0%}）的"
                f"{overall_rate/benchmark_rate:.1f}倍，整体变更管控存在严重问题。"
            )
        elif overall_rate > benchmark_rate * 1.5:
            parts.append(
                f"🟠 合同变更率{overall_rate:.1%}，显著高于行业基准（{benchmark_rate:.0%}），"
                f"需关注变更管控流程。"
            )
        else:
            parts.append(
                f"✅ 合同变更率{overall_rate:.1%}，接近行业基准（{benchmark_rate:.0%}）。"
            )

        # 异常变更类型
        abnormal_types = [s for s in type_stats if s.is_abnormal]
        if abnormal_types:
            type_names = {
                "amount_decrease": "金额调减",
                "amount_increase": "金额调增",
                "scope_change": "范围变更",
                "timeline_change": "工期变更",
            }
            parts.append(
                f"异常变更类型："
                + "、".join(
                    f"{type_names.get(s.change_type, s.change_type)}"
                    f"（{s.deviation*100:+.0f}%偏离基准）"
                    for s in abnormal_types
                )
                + "。"
            )

        # 时间聚集
        post = next(
            (c for c in time_clusters if "验收后" in c.period_label), None
        )
        if post and post.count > 0:
            rate = post.pct_of_total
            parts.append(
                f"验收后变更占比{rate:.0%}，涉及金额{post.total_amount:,.0f}元，"
                f"高度可疑——正常项目验收后不应有大量变更。"
            )

        # 高风险项目
        if high_risk:
            parts.append(
                f"识别出{len(high_risk)}个高风险项目，建议逐项核查变更原因和审批流程。"
            )

        return "".join(parts)


# ── MCP工具接口 ──────────────────────────────────────────────

def contract_change_trajectory(
    contracts: List[Dict[str, Any]],
    changes: List[Dict[str, Any]],
    industry: str = "general",
    csv_contracts: Optional[str] = None,
    csv_changes: Optional[str] = None,
) -> dict:
    """
    合同变更轨迹分析

    Args:
        contracts: 合同列表 [{"project_id": "P001", "contract_date": "2024-01-01", ...}, ...]
        changes: 变更记录 [{"project_id": "P001", "change_date": "2024-03-15",
                  "change_type": "amount_decrease", "change_amount": -5000}, ...]
        industry: 行业基准类型（procurement/project_construction/general）
        csv_contracts: 合同CSV路径
        csv_changes: 变更记录CSV路径

    Returns:
        分析结果dict
    """
    # CSV加载
    if csv_contracts and not contracts:
        loaded = []
        with open(csv_contracts, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["contract_amount"] = float(
                        row.get("contract_amount", "0").replace(",", "")
                    )
                except (ValueError, KeyError):
                    row["contract_amount"] = 0
                loaded.append(row)
        contracts = loaded

    if csv_changes and not changes:
        loaded = []
        with open(csv_changes, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["change_amount"] = float(
                        row.get("change_amount", "0").replace(",", "")
                    )
                except (ValueError, KeyError):
                    row["change_amount"] = 0
                loaded.append(row)
        changes = loaded

    analyzer = ContractChangeTrajectoryAnalyzer(industry=industry)
    result = analyzer.analyze(contracts or [], changes or [])

    # 变更类型标签
    type_labels = {
        "amount_increase": "金额调增",
        "amount_decrease": "金额调减",
        "scope_change": "范围变更",
        "timeline_change": "工期变更",
        "party_change": "主体变更",
        "other": "其他",
    }

    return {
        "total_projects": result.total_projects,
        "projects_with_changes": result.projects_with_changes,
        "overall_change_rate": f"{result.overall_change_rate:.1%}",
        "industry_benchmark": f"{result.industry_benchmark:.0%}",
        "change_rate_deviation": f"{result.change_rate_deviation*100:+.1f}%",
        "deviation_label": (
            "🔴 严重偏离（>2倍基准）" if result.change_rate_deviation > result.industry_benchmark
            else "🟠 显著偏离（>1.5倍基准）" if result.change_rate_deviation > result.industry_benchmark * 0.5
            else "🟡 略高" if result.change_rate_deviation > 0.02
            else "✅ 正常范围"
        ),
        "change_types": [
            {
                "type": s.change_type,
                "type_label": type_labels.get(s.change_type, s.change_type),
                "count": s.count,
                "pct": f"{s.pct_of_total:.0%}",
                "rate_vs_total": f"{s.count/result.total_projects:.1%}",
                "industry_benchmark": f"{s.industry_benchmark:.1%}",
                "deviation": f"{s.deviation*100:+.1f}%",
                "is_abnormal": s.is_abnormal,
                "total_amount": s.total_amount,
            }
            for s in result.change_type_stats
        ],
        "time_clusters": [
            {
                "period": c.period_label,
                "count": c.count,
                "pct": f"{c.pct_of_total:.0%}",
                "total_amount": c.total_amount,
                "risk_level": c.risk_level,
            }
            for c in result.time_clusters
        ],
        "high_risk_projects": result.high_risk_projects,
        "high_risk_count": len(result.high_risk_projects),
        "summary": result.summary,
    }
