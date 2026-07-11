"""
工具7：supplier_fingerprint — 供应商行为指纹相似度引擎

场景：采购审计中，通过提取供应商多维行为特征形成向量，
     计算供应商对之间的行为相似度，发现表面无关联但行为模式高度一致的供应商组。

技术：多维特征提取 → 标准化 → 余弦相似度 → Top-N异常对
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter
import math
import csv


# ── 数据结构 ──────────────────────────────────────────────────

@dataclass
class SupplierFeature:
    """供应商行为特征向量"""
    supplier_id: str
    supplier_name: str
    total_projects: int = 0
    total_amount: float = 0.0
    median_amount: float = 0.0
    avg_amount: float = 0.0
    std_amount: float = 0.0
    win_rate: float = 0.0  # 中标率
    unit_diversity: float = 0.0  # 参与单位多样性（熵）
    category_diversity: float = 0.0  # 项目类别多样性（熵）
    amount_band_dist: Dict[str, float] = field(default_factory=dict)  # 金额区间分布
    time_pattern: str = ""  # 投标时间模式（morning/afternoon/evening/night/mixed）


@dataclass
class SupplierPairMatch:
    """相似供应商对"""
    supplier_a: str
    supplier_b: str
    similarity: float
    contributing_dimensions: List[Dict[str, Any]]  # 各维度贡献度
    risk_signals: List[str]
    recommendation: str


@dataclass
class FingerprintResult:
    """指纹分析完整结果"""
    total_suppliers: int
    total_pairs: int
    high_similarity_pairs: List[SupplierPairMatch]
    threshold: float
    summary: str


class SupplierFingerprintEngine:
    """供应商行为指纹引擎"""

    def __init__(self, threshold: float = 0.80):
        self.threshold = threshold

    def extract_features(
        self,
        records: List[Dict[str, Any]],
    ) -> Dict[str, SupplierFeature]:
        """
        从采购记录中提取供应商特征向量

        Args:
            records: 采购记录列表，每条含：
                supplier_name, supplier_id, amount, project_category,
                unit_name, bid_time, is_winner

        Returns:
            {supplier_id: SupplierFeature}
        """
        # 按供应商聚合
        supplier_data: Dict[str, List[Dict]] = {}
        for r in records:
            sid = r.get("supplier_id") or r.get("supplier_name", "")
            if sid not in supplier_data:
                supplier_data[sid] = []
            supplier_data[sid].append(r)

        features = {}
        for sid, recs in supplier_data.items():
            name = recs[0].get("supplier_name", sid)
            amounts = sorted([
                float(r.get("amount", 0))
                for r in recs
                if r.get("amount")
            ])
            n = len(amounts)
            total = sum(amounts)

            # 金额特征
            avg = total / n if n > 0 else 0
            median = amounts[n // 2] if n > 0 else 0
            std = (
                math.sqrt(sum((a - avg) ** 2 for a in amounts) / n)
                if n > 1 else 0
            )

            # 中标率
            wins = sum(1 for r in recs if r.get("is_winner"))
            total_bids = sum(1 for r in recs if r.get("bid_time"))
            win_rate = wins / total_bids if total_bids > 0 else 0

            # 参与单位多样性（熵）
            unit_counter = Counter(
                r.get("unit_name", "") for r in recs if r.get("unit_name")
            )
            total_participations = len(recs)
            unit_entropy = self._entropy(unit_counter, total_participations)

            # 项目类别多样性（熵）
            cat_counter = Counter(
                r.get("project_category", "") for r in recs if r.get("project_category")
            )
            category_entropy = self._entropy(cat_counter, total_participations)

            # 金额区间分布
            bands = self._amount_bands(amounts, total)

            # 投标时间模式
            time_pattern = self._time_mode([
                r.get("bid_time", "") for r in recs if r.get("bid_time")
            ])

            features[sid] = SupplierFeature(
                supplier_id=sid,
                supplier_name=name,
                total_projects=len(recs),
                total_amount=total,
                median_amount=median,
                avg_amount=round(avg, 2),
                std_amount=round(std, 2),
                win_rate=round(win_rate, 3),
                unit_diversity=round(unit_entropy, 3),
                category_diversity=round(category_entropy, 3),
                amount_band_dist=bands,
                time_pattern=time_pattern,
            )

        return features

    def compute_similarity(
        self,
        features: Dict[str, SupplierFeature],
    ) -> List[SupplierPairMatch]:
        """
        计算供应商对之间的余弦相似度

        Args:
            features: 供应商特征向量字典

        Returns:
            相似度高于阈值的供应商对
        """
        ids = list(features.keys())
        matches = []

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                fa = features[ids[i]]
                fb = features[ids[j]]
                sim, contribs = self._cosine_similarity(fa, fb)

                if sim >= self.threshold:
                    signals = self._risk_signals(fa, fb, contribs)
                    matches.append(SupplierPairMatch(
                        supplier_a=f"{fa.supplier_name}({fa.supplier_id})",
                        supplier_b=f"{fb.supplier_name}({fb.supplier_id})",
                        similarity=round(sim, 4),
                        contributing_dimensions=contribs,
                        risk_signals=signals,
                        recommendation=self._recommend(sim, signals),
                    ))

        # 按相似度降序
        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches

    def run(
        self,
        records: List[Dict[str, Any]],
        threshold: Optional[float] = None,
    ) -> FingerprintResult:
        """
        完整指纹分析流程

        Args:
            records: 采购记录列表
            threshold: 相似度阈值（可选，覆盖实例默认值）
        """
        if threshold is not None:
            self.threshold = threshold

        features = self.extract_features(records)
        matches = self.compute_similarity(features)

        # 生成摘要
        summary = self._summary(features, matches)

        return FingerprintResult(
            total_suppliers=len(features),
            total_pairs=len(features) * (len(features) - 1) // 2,
            high_similarity_pairs=matches,
            threshold=self.threshold,
            summary=summary,
        )

    # ── 内部方法 ──────────────────────────────────────────

    def _entropy(self, counter: Counter, total: int) -> float:
        """计算信息熵（归一化到0-1）"""
        if total == 0 or len(counter) <= 1:
            return 0.0
        max_entropy = math.log(len(counter))
        if max_entropy == 0:
            return 0.0
        entropy = sum(
            -(c / total) * math.log(c / total)
            for c in counter.values()
        )
        return entropy / max_entropy

    def _amount_bands(
        self, amounts: List[float], total: float
    ) -> Dict[str, float]:
        """金额区间分布"""
        if total == 0 or not amounts:
            return {}
        bands = {"小额(<10万)": 0, "中额(10-100万)": 0, "大额(>100万)": 0}
        for a in amounts:
            if a < 100000:
                bands["小额(<10万)"] += a
            elif a < 1000000:
                bands["中额(10-100万)"] += a
            else:
                bands["大额(>100万)"] += a
        return {k: round(v / total, 3) for k, v in bands.items()}

    def _time_mode(self, times: List[str]) -> str:
        """投标时间模式识别"""
        if not times:
            return "unknown"
        hours = []
        for t in times:
            try:
                # 假设格式 HH:MM 或 YYYY-MM-DD HH:MM
                parts = t.strip().split()
                time_part = parts[-1] if parts else t
                h = int(time_part.split(":")[0])
                hours.append(h)
            except (ValueError, IndexError):
                continue
        if not hours:
            return "unknown"
        avg_h = sum(hours) / len(hours)
        if avg_h < 9:
            return "清晨(6-9点)"
        elif avg_h < 12:
            return "上午(9-12点)"
        elif avg_h < 14:
            return "午间(12-14点)"
        elif avg_h < 18:
            return "下午(14-18点)"
        else:
            return "晚间(18+点)"

    def _cosine_similarity(
        self, fa: SupplierFeature, fb: SupplierFeature
    ) -> Tuple[float, List[Dict]]:
        """
        计算两个供应商的余弦相似度

        特征维度权重：
        - 参与单位分布: 0.30 (最高，反映围标模式)
        - 项目类别分布: 0.25 (反映业务重合)
        - 金额分布: 0.20 (反映定价模式)
        - 中标率: 0.10
        - 投标时间模式: 0.10
        - 项目数量规模: 0.05
        """
        dims = []

        # 1. 金额区段分布相似度 (0.20)
        bands_sim = self._dict_cosine(
            fa.amount_band_dist, fb.amount_band_dist
        )
        dims.append({
            "dimension": "金额区段分布",
            "weight": 0.20,
            "similarity": round(bands_sim, 3),
            "contribution": round(bands_sim * 0.20, 3),
        })

        # 2. 参与单位多样性 — 用熵差(0.30)
        unit_sim = 1.0 - min(abs(fa.unit_diversity - fb.unit_diversity), 1.0)
        dims.append({
            "dimension": "参与单位多样性",
            "weight": 0.30,
            "similarity": round(unit_sim, 3),
            "contribution": round(unit_sim * 0.30, 3),
        })

        # 3. 项目类别多样性 (0.25)
        cat_sim = 1.0 - min(abs(fa.category_diversity - fb.category_diversity), 1.0)
        dims.append({
            "dimension": "项目类别多样性",
            "weight": 0.25,
            "similarity": round(cat_sim, 3),
            "contribution": round(cat_sim * 0.25, 3),
        })

        # 4. 中标率相似度 (0.10)
        wr_sim = 1.0 - min(abs(fa.win_rate - fb.win_rate), 1.0)
        dims.append({
            "dimension": "中标率",
            "weight": 0.10,
            "similarity": round(wr_sim, 3),
            "contribution": round(wr_sim * 0.10, 3),
        })

        # 5. 投标时间模式 (0.10)
        time_sim = 1.0 if fa.time_pattern == fb.time_pattern else 0.0
        dims.append({
            "dimension": "投标时间模式",
            "weight": 0.10,
            "similarity": round(time_sim, 3),
            "contribution": round(time_sim * 0.10, 3),
        })

        # 6. 项目数量规模 (0.05)
        max_n = max(fa.total_projects, fb.total_projects, 1)
        n_sim = 1.0 - abs(fa.total_projects - fb.total_projects) / max_n
        dims.append({
            "dimension": "项目数量规模",
            "weight": 0.05,
            "similarity": round(n_sim, 3),
            "contribution": round(n_sim * 0.05, 3),
        })

        total_sim = sum(d["contribution"] for d in dims)
        return total_sim, dims

    def _dict_cosine(self, d1: Dict, d2: Dict) -> float:
        """字典余弦相似度"""
        all_keys = set(d1.keys()) | set(d2.keys())
        v1 = [d1.get(k, 0) for k in all_keys]
        v2 = [d2.get(k, 0) for k in all_keys]
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 1.0 if norm1 == norm2 else 0.0
        return dot / (norm1 * norm2)

    def _risk_signals(
        self, fa: SupplierFeature, fb: SupplierFeature,
        contribs: List[Dict],
    ) -> List[str]:
        """生成风险信号"""
        signals = []
        high_contrib = [c for c in contribs if c["similarity"] > 0.85]

        for c in high_contrib:
            dim = c["dimension"]
            if dim == "参与单位多样性":
                signals.append(
                    "⚠️ 参与单位高度重合——同一批采购单位的固定搭档组合，围标嫌疑"
                )
            elif dim == "投标时间模式":
                if fa.time_pattern == fb.time_pattern and fa.time_pattern != "上午(9-12点)":
                    signals.append(
                        f"⚠️ 投标时间高度一致（{fa.time_pattern}）——可能同一操作人"
                    )
            elif dim == "金额区段分布":
                signals.append(
                    "⚠️ 金额分布高度相似——可能采用相同的定价/分拆策略"
                )
            elif dim == "项目类别多样性":
                signals.append(
                    "⚠️ 项目类别分布一致——业务范围高度重合，但表面无关联=陪标嫌疑"
                )

        if abs(fa.win_rate - fb.win_rate) < 0.05 and fa.win_rate > 0.7:
            signals.append(
                f"⚠️ 双方中标率均高（{fa.win_rate:.0%} vs {fb.win_rate:.0%}）——"
                f"疑似轮流中标/围标联盟"
            )

        if not signals:
            signals.append("行为模式高度相似，建议人工核查是否存在隐性关联关系")

        return signals

    def _recommend(self, sim: float, signals: List[str]) -> str:
        """生成建议"""
        if sim > 0.95:
            return (
                "🔴 极高相似度（>95%）——强烈建议立即启动关联关系尽职调查，"
                "核查实控人、股东、高管之间的亲属/利益关系。"
            )
        elif sim > 0.90:
            return (
                "🟠 高度相似（90-95%）——建议纳入重点核查名单，"
                "核实投标文件编制风格、IP地址、联系人信息等。"
            )
        else:
            return (
                "🟡 较高相似度（80-90%）——建议作为线索留存，"
                "结合其他异常信号（如Benford异常、时间序列异常）综合研判。"
            )

    def _summary(
        self, features: Dict[str, SupplierFeature],
        matches: List[SupplierPairMatch],
    ) -> str:
        """生成摘要"""
        n_suppliers = len(features)
        n_matches = len(matches)
        if n_matches == 0:
            return (
                f"共分析{n_suppliers}家供应商，未发现行为模式高度相似的供应商对"
                f"（相似度阈值{self.threshold:.0%}）。"
            )
        top_sim = matches[0].similarity
        return (
            f"共分析{n_suppliers}家供应商，发现{n_matches}对行为模式高度相似的供应商"
            f"（阈值{self.threshold:.0%}），最高相似度{top_sim:.1%}。"
            f"建议优先核查相似度>90%的供应商对。"
        )


# ── MCP工具接口 ──────────────────────────────────────────────

def supplier_fingerprint(
    records: List[Dict[str, Any]],
    threshold: Optional[float] = None,
    csv_file: Optional[str] = None,
) -> dict:
    """
    供应商行为指纹相似度分析

    Args:
        records: 采购记录列表 [{"supplier_name": "...", "amount": 10000, ...}, ...]
        threshold: 相似度阈值（默认0.80）
        csv_file: CSV文件路径（与records二选一）

    CSV列要求：supplier_name, supplier_id(可选), amount, project_category,
               unit_name, bid_time(可选), is_winner(可选)

    Returns:
        分析结果dict
    """
    if csv_file and not records:
        loaded = []
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["amount"] = float(row.get("amount", "0").replace(",", ""))
                except (ValueError, KeyError):
                    row["amount"] = 0
                # is_winner: 支持 1/0, True/False, yes/no
                w = str(row.get("is_winner", "")).lower()
                row["is_winner"] = w in ("1", "true", "yes", "是")
                loaded.append(row)
        records = loaded

    threshold_val = threshold if threshold is not None else 0.80
    engine = SupplierFingerprintEngine(threshold=threshold_val)
    result = engine.run(records or [])

    pairs_data = []
    for pair in result.high_similarity_pairs:
        pairs_data.append({
            "supplier_a": pair.supplier_a,
            "supplier_b": pair.supplier_b,
            "similarity": pair.similarity,
            "similarity_pct": f"{pair.similarity*100:.1f}%",
            "contributing_dimensions": [
                {
                    "dimension": c["dimension"],
                    "weight": c["weight"],
                    "similarity": c["similarity"],
                }
                for c in sorted(
                    pair.contributing_dimensions,
                    key=lambda x: x["contribution"],
                    reverse=True,
                )[:3]
            ],
            "risk_signals": pair.risk_signals,
            "recommendation": pair.recommendation,
        })

    return {
        "total_suppliers": result.total_suppliers,
        "total_pairs": result.total_pairs,
        "high_similarity_count": len(result.high_similarity_pairs),
        "threshold": result.threshold,
        "pairs": pairs_data,
        "summary": result.summary,
        "next_steps": (
            f"发现{len(result.high_similarity_pairs)}对高相似供应商。"
            f"建议：(1)对相似度>90%的供应商对进行工商信息穿透查询 "
            f"(2)提取双方投标文件的元数据（作者/IP/创建时间）进行比对 "
            f"(3)与Benford分析和时间序列异常交叉验证，确认是否为系统性围标。"
            if result.high_similarity_pairs
            else "未发现高相似供应商对。如仍有围标怀疑，建议降低阈值重新分析，或结合时间序列异常检测。"
        ),
    }
