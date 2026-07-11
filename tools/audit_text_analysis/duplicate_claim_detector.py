"""
P2: duplicate_claim_detector — 三维联合去重检测器 (v8, 3d)

在现有 timeline_anomaly 基础上，新增三维联合去重模式：
- 维度1：报销人（字符串匹配，支持近似匹配）
- 维度2：金额（±tolerance_pct%浮动容忍度）
- 维度3：时间窗口（可配置，默认3天）

数据来源：费用报销记录的 报销人+金额+日期 三个字段
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta


@dataclass
class DuplicatePair:
    """去重检测对"""
    record_a: Dict[str, Any]
    record_b: Dict[str, Any]
    similarity_score: float  # 0-1，越高越可疑
    match_dimensions: List[str]  # 命中的维度
    duplicate_type: str  # exact_duplicate | amount_variant | time_variant | partial


@dataclass
class DuplicateCluster:
    """重复记录簇（3条及以上）"""
    records: List[Dict[str, Any]]
    cluster_size: int
    total_amount: float
    duplicate_pairs: List[DuplicatePair]
    risk_level: str  # high | medium | low


@dataclass
class DuplicateDetectionResult:
    """去重检测完整结果"""
    total_records: int
    duplicate_pairs: List[DuplicatePair]
    clusters: List[DuplicateCluster]
    unique_claimants: int
    duplicate_rate: float  # 涉及重复的记录比例
    summary: str


class DuplicateClaimDetector:
    """三维联合去重检测器"""

    def __init__(
        self,
        amount_tolerance_pct: float = 5.0,
        time_window_days: int = 3,
        min_similarity: float = 0.7,
    ):
        self.amount_tolerance_pct = amount_tolerance_pct
        self.time_window_days = time_window_days
        self.min_similarity = min_similarity

    def detect(
        self,
        expense_records: List[Dict[str, Any]],
        claimant_field: str = "claimant",
        amount_field: str = "amount",
        date_field: str = "date",
        date_format: str = "%Y-%m-%d",
    ) -> DuplicateDetectionResult:
        """
        三维联合去重检测

        Args:
            expense_records: 费用报销记录 [{"claimant": "张三", "amount": 5000, "date": "2024-01-15"}, ...]
            claimant_field: 报销人字段名
            amount_field: 金额字段名
            date_field: 日期字段名
            date_format: 日期格式
        """
        n = len(expense_records)
        pairs = []
        seen_pairs = set()

        for i in range(n):
            rec_a = expense_records[i]
            name_a = str(rec_a.get(claimant_field, "")).strip()
            amount_a = self._safe_float(rec_a.get(amount_field, 0))
            date_a = self._safe_date(rec_a.get(date_field, ""), date_format)

            for j in range(i + 1, n):
                pair_key = (min(i, j), max(i, j))
                if pair_key in seen_pairs:
                    continue

                rec_b = expense_records[j]
                name_b = str(rec_b.get(claimant_field, "")).strip()
                amount_b = self._safe_float(rec_b.get(amount_field, 0))
                date_b = self._safe_date(rec_b.get(date_field, ""), date_format)

                # 三维匹配检测
                dims = []
                score = 0.0

                # 维度1：报销人匹配（0.40权重）
                name_match = self._name_similarity(name_a, name_b)
                if name_match >= 0.80:
                    dims.append("claimant")
                    score += 0.40 * name_match

                # 维度2：金额匹配（0.35权重）
                amount_match = self._amount_similarity(amount_a, amount_b)
                if amount_match >= 0.90:
                    dims.append("amount")
                    score += 0.35 * amount_match

                # 维度3：时间窗口（0.25权重）
                if date_a and date_b:
                    days_diff = abs((date_b - date_a).days)
                    if days_diff <= self.time_window_days:
                        dims.append("time")
                        time_score = 1.0 - (days_diff / max(self.time_window_days, 1))
                        score += 0.25 * time_score

                if score >= self.min_similarity:
                    seen_pairs.add(pair_key)
                    duplicate_type = self._classify_type(dims)
                    pairs.append(DuplicatePair(
                        record_a=rec_a,
                        record_b=rec_b,
                        similarity_score=round(score, 3),
                        match_dimensions=dims,
                        duplicate_type=duplicate_type,
                    ))

        # 聚类（找出3条以上的重复簇）
        clusters = self._build_clusters(expense_records, pairs)

        # 涉及重复的记录数
        duplicate_indices = set()
        for p in pairs:
            duplicate_indices.add(id(p.record_a))
            duplicate_indices.add(id(p.record_b))
        duplicate_rate = len(duplicate_indices) / n if n > 0 else 0

        summary = self._summarize(pairs, clusters, n)

        return DuplicateDetectionResult(
            total_records=n,
            duplicate_pairs=pairs,
            clusters=clusters,
            unique_claimants=len(set(
                str(r.get(claimant_field, "")) for r in expense_records
            )),
            duplicate_rate=round(duplicate_rate, 3),
            summary=summary,
        )

    def _safe_float(self, val: Any) -> float:
        try:
            return float(str(val).replace(",", "").replace(" ", ""))
        except (ValueError, TypeError):
            return 0.0

    def _safe_date(self, val: Any, fmt: str) -> Optional[datetime]:
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except (ValueError, TypeError):
            return None

    def _name_similarity(self, a: str, b: str) -> float:
        """姓名相似度（简单Jaccard）"""
        if a == b:
            return 1.0
        if not a or not b:
            return 0.0
        set_a = set(a)
        set_b = set(b)
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0

    def _amount_similarity(self, a: float, b: float) -> float:
        """金额相似度（基于百分比容差）"""
        if a == 0 and b == 0:
            return 1.0
        if a == 0 or b == 0:
            return 0.0
        diff_pct = abs(a - b) / max(abs(a), abs(b))
        # 在容差范围内 = 高相似度
        if diff_pct <= self.amount_tolerance_pct / 100:
            return 1.0 - diff_pct / (self.amount_tolerance_pct / 100 * 2)
        else:
            return max(0.0, 1.0 - diff_pct)

    def _classify_type(self, dims: List[str]) -> str:
        """分类重复类型"""
        if len(dims) >= 3:
            return "完全匹配（三维修全中）"
        if "claimant" in dims and "amount" in dims:
            return "同人同金额不同时间"
        if "claimant" in dims and "time" in dims:
            return "同人相近时间不同金额"
        if "amount" in dims and "time" in dims:
            return "同金额相近时间不同人"
        return "部分匹配"

    def _build_clusters(
        self, records: List[Dict], pairs: List[DuplicatePair]
    ) -> List[DuplicateCluster]:
        """构建重复簇（并查集）"""
        # 记录索引 → 所属组
        parent = {}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            parent[find(x)] = find(y)

        # 初始化
        for r in records:
            parent[id(r)] = id(r)

        # 连接重复对
        for p in pairs:
            union(id(p.record_a), id(p.record_b))

        # 分组
        groups = defaultdict(list)
        for r in records:
            groups[find(id(r))].append(r)

        # 构建簇（3条及以上）
        clusters = []
        for group_records in groups.values():
            if len(group_records) >= 3:
                cluster_pairs = [
                    p for p in pairs
                    if p.record_a in group_records and p.record_b in group_records
                ]
                total_amount = sum(
                    self._safe_float(r.get("amount", 0))
                    for r in group_records
                )
                clusters.append(DuplicateCluster(
                    records=group_records,
                    cluster_size=len(group_records),
                    total_amount=total_amount,
                    duplicate_pairs=cluster_pairs,
                    risk_level=(
                        "high" if len(group_records) >= 5
                        else "medium" if len(group_records) >= 3
                        else "low"
                    ),
                ))

        return sorted(clusters, key=lambda c: c.cluster_size, reverse=True)

    def _summarize(
        self, pairs: List[DuplicatePair],
        clusters: List[DuplicateCluster],
        total_n: int,
    ) -> str:
        """生成摘要"""
        n_pairs = len(pairs)
        if n_pairs == 0:
            return "未发现重复报销记录。"

        exact = sum(1 for p in pairs if p.duplicate_type.startswith("完全匹配"))
        high_risk_clusters = [c for c in clusters if c.risk_level == "high"]

        parts = [f"共发现{n_pairs}对重复报销记录。"]

        if exact > 0:
            parts.append(f"其中{exact}对为三维修全中的完全匹配，高度可疑。")

        if high_risk_clusters:
            total_amount = sum(c.total_amount for c in high_risk_clusters)
            parts.append(
                f"检测到{len(high_risk_clusters)}个高危重复簇（5条以上），"
                f"涉及金额{total_amount:,.0f}元。"
            )

        parts.append(
            f"建议对完全匹配的记录逐条核实原始凭证，"
            f"对高危簇启动专项稽查。"
        )

        return "".join(parts)


# ── MCP工具接口 ──────────────────────────────────────────────

def detect_duplicate_claims(
    records: List[Dict[str, Any]],
    amount_tolerance_pct: float = 5.0,
    time_window_days: int = 3,
) -> dict:
    """
    三维联合去重检测（报销人×金额×时间）

    Args:
        records: 费用报销记录 [{"claimant": "...", "amount": 5000, "date": "2024-01-15"}, ...]
        amount_tolerance_pct: 金额容差百分比（默认5%）
        time_window_days: 时间窗口天数（默认3天）

    Returns:
        检测结果dict
    """
    detector = DuplicateClaimDetector(
        amount_tolerance_pct=amount_tolerance_pct,
        time_window_days=time_window_days,
    )
    result = detector.detect(records)

    pairs_data = []
    for p in result.duplicate_pairs[:50]:
        pairs_data.append({
            "record_a_claimant": p.record_a.get("claimant", ""),
            "record_b_claimant": p.record_b.get("claimant", ""),
            "amount_a": p.record_a.get("amount", 0),
            "amount_b": p.record_b.get("amount", 0),
            "date_a": p.record_a.get("date", ""),
            "date_b": p.record_b.get("date", ""),
            "similarity": p.similarity_score,
            "match_dimensions": p.match_dimensions,
            "duplicate_type": p.duplicate_type,
        })

    clusters_data = []
    for c in result.clusters[:10]:
        clusters_data.append({
            "cluster_size": c.cluster_size,
            "claimants": list(set(r.get("claimant", "") for r in c.records)),
            "total_amount": c.total_amount,
            "risk_level": c.risk_level,
            "record_count": len(c.records),
        })

    return {
        "total_records": result.total_records,
        "duplicate_pairs_count": len(result.duplicate_pairs),
        "clusters_count": len(result.clusters),
        "unique_claimants": result.unique_claimants,
        "duplicate_rate": f"{result.duplicate_rate:.1%}",
        "pairs": pairs_data,
        "clusters": clusters_data,
        "summary": result.summary,
    }
