"""
工具11：bid_rigging_detector — 招投标围标串标多维检测引擎

v9新增，基于「数审视界」《招投标围标串标，5个数据特征一抓一个准》。

5大数据特征：
  特征1：同IP/同设备投标 — IP C段匹配 + MAC前缀 + CA证书
  特征2：报价规律性雷同 — 尾数分布 + 整数一致性 + 差额稳定性 + 贴边
  特征3：保证金来源同源 — 账号匹配 + 转账时间聚类 + 摘要相似度
  特征4：投标文件基因相似 — 文本相似度 + 行业基准加权
  特征5：时间窗口扎堆 — 提交间隔聚类 + 末段比例 + 秒级批量

每个标段输出0-5分围标风险评分（每特征1分，交叉加权）。
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime
import re
import math
import csv


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class IPDeviceSignal:
    """特征1：同IP/同设备投标信号"""
    segment_id: str
    suspected_bidders: List[str]
    ip_c_segment: str = ""
    mac_prefix_match: bool = False
    ca_same_day: bool = False
    hit_count: int = 0
    total_bidders_in_segment: int = 0
    hit_ratio: float = 0.0
    evidence: str = ""


@dataclass
class PricePatternSignal:
    """特征2：报价规律性雷同信号"""
    segment_id: str
    suspected_bidders: List[str]
    decimal_pattern: str = ""           # 尾数模式描述
    integer_consistency: float = 0.0    # 整数位一致性（0-1）
    gap_stability: float = 0.0          # 差额稳定性（CV越小越异常）
    edge_ratio: float = 0.0             # 贴边比例
    all_bids: List[float] = field(default_factory=list)
    evidence: str = ""


@dataclass
class DepositSourceSignal:
    """特征3：保证金来源同源信号"""
    segment_id: str
    suspected_bidders: List[str]
    shared_account: str = ""
    time_cluster_window_min: int = 0
    summary_similarity: float = 0.0
    evidence: str = ""


@dataclass
class DocumentGeneSignal:
    """特征4：投标文件基因相似信号"""
    segment_id: str
    suspected_bidders: List[str]
    max_similarity: float = 0.0
    avg_similarity: float = 0.0
    similarity_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    industry_baseline: float = 0.0
    evidence: str = ""


@dataclass
class TimeClusterSignal:
    """特征5：时间窗口扎堆信号"""
    segment_id: str
    suspected_bidders: List[str]
    last_window_count: int = 0
    last_window_max_interval_sec: int = 0
    last_window_min_interval_sec: int = 0
    total_bidders: int = 0
    last_window_ratio: float = 0.0
    batch_upload_detected: bool = False
    evidence: str = ""


@dataclass
class BidRiggingRisk:
    """单个标段的完整围标风险评估"""
    segment_id: str
    segment_name: str = ""
    total_bidders: int = 0
    risk_score: float = 0.0            # 0-5 总分
    feature_flags: Dict[str, bool] = field(default_factory=dict)  # 各特征命中
    feature_details: Dict[str, Any] = field(default_factory=dict)

    # 各特征详细信号
    ip_device: Optional[IPDeviceSignal] = None
    price_pattern: Optional[PricePatternSignal] = None
    deposit_source: Optional[DepositSourceSignal] = None
    document_gene: Optional[DocumentGeneSignal] = None
    time_cluster: Optional[TimeClusterSignal] = None

    combined_evidence: List[str] = field(default_factory=list)
    risk_level: str = "low"             # high / medium / low
    recommendation: str = ""


@dataclass
class BidRiggingResult:
    """围标检测完整结果"""
    total_segments: int
    flagged_segments: int
    risk_distribution: Dict[str, int]   # high/medium/low → count
    risks: List[BidRiggingRisk]
    hit_rate_stats: Dict[str, float]    # 各特征独立命中率
    cross_hit_matrix: Dict[str, Dict[str, float]]  # 特征交叉命中
    summary: str


# ═══════════════════════════════════════════════════════════════
# 特征1：同IP/同设备投标检测器
# ═══════════════════════════════════════════════════════════════

class IPDeviceClusterDetector:
    """
    检测不同投标人使用同一IP段/设备投标的行为。

    信号：
    - IP C段相同（前3段相同）
    - MAC地址前24位相同（同批次网卡或虚拟机）
    - CA证书同一天签发
    """

    @staticmethod
    def _extract_c_segment(ip: str) -> str:
        """提取IP C段（前3段）"""
        parts = ip.strip().split(".")
        if len(parts) >= 3:
            return ".".join(parts[:3])
        return ip

    @staticmethod
    def _extract_mac_prefix(mac: str, length: int = 24) -> str:
        """提取MAC地址前缀"""
        clean = re.sub(r'[:-]', '', mac.strip().upper())
        return clean[:length // 4]

    def detect(
        self,
        segments: List[Dict[str, Any]],
    ) -> Dict[str, List[IPDeviceSignal]]:
        """
        检测同IP/设备投标

        Args:
            segments: 标段数据列表，每条含：
                segment_id, bidders: [
                    {bidder_id, bidder_name, ip, mac, ca_issue_date, ca_issuer}
                ]

        Returns:
            {segment_id: [IPDeviceSignal, ...]}
        """
        results: Dict[str, List[IPDeviceSignal]] = {}

        for seg in segments:
            seg_id = seg.get("segment_id", "")
            bidders = seg.get("bidders", [])

            if len(bidders) < 2:
                continue

            signals = []

            # 1. IP C段聚类
            ip_c_groups = defaultdict(list)
            for b in bidders:
                ip = b.get("ip", "")
                if ip:
                    c_seg = self._extract_c_segment(ip)
                    ip_c_groups[c_seg].append(b)

            for c_seg, group in ip_c_groups.items():
                if len(group) >= 3:  # 至少3家同C段
                    signals.append(IPDeviceSignal(
                        segment_id=seg_id,
                        suspected_bidders=[b.get("bidder_name", b.get("bidder_id", "")) for b in group],
                        ip_c_segment=c_seg,
                        hit_count=len(group),
                        total_bidders_in_segment=len(bidders),
                        hit_ratio=len(group) / len(bidders),
                        evidence=f"{len(group)}家投标人IP在同一个C段({c_seg}.x)"
                    ))

            # 2. MAC前缀匹配
            mac_groups = defaultdict(list)
            for b in bidders:
                mac = b.get("mac", "")
                if mac:
                    prefix = self._extract_mac_prefix(mac)
                    mac_groups[prefix].append(b)

            for prefix, group in mac_groups.items():
                if len(group) >= 2:
                    bidder_names = [b.get("bidder_name", b.get("bidder_id", "")) for b in group]
                    signals.append(IPDeviceSignal(
                        segment_id=seg_id,
                        suspected_bidders=bidder_names,
                        mac_prefix_match=True,
                        hit_count=len(group),
                        total_bidders_in_segment=len(bidders),
                        hit_ratio=len(group) / len(bidders),
                        evidence=f"{len(group)}家投标人MAC地址前24位相同({prefix})"
                    ))

            # 3. CA证书同天签发
            ca_groups = defaultdict(list)
            for b in bidders:
                issuer = b.get("ca_issuer", "")
                issue_date = b.get("ca_issue_date", "")
                if issuer and issue_date:
                    key = (issuer, issue_date)
                    ca_groups[key].append(b)

            for (issuer, date), group in ca_groups.items():
                if len(group) >= 2:
                    bidder_names = [b.get("bidder_name", b.get("bidder_id", "")) for b in group]
                    signals.append(IPDeviceSignal(
                        segment_id=seg_id,
                        suspected_bidders=bidder_names,
                        ca_same_day=True,
                        hit_count=len(group),
                        total_bidders_in_segment=len(bidders),
                        hit_ratio=len(group) / len(bidders),
                        evidence=f"{len(group)}家投标人CA证书由{issuer}在{date}同天签发"
                    ))

            if signals:
                results[seg_id] = signals

        return results


# ═══════════════════════════════════════════════════════════════
# 特征2：报价规律性雷同检测器
# ═══════════════════════════════════════════════════════════════

class PricePatternDetector:
    """
    检测投标报价的规律性雷同。

    信号：
    - 尾数集中在 .88 / .99 / .66 等"伪随机"偏好数字
    - 整数位完全一致，仅小数不同
    - 报价差额高度稳定（CV<0.3）
    - 报价贴边（限价1%内或基准价±0.5%）
    """

    _PSEUDO_RANDOM_DECIMALS = {0.88, 0.99, 0.66, 0.88, 0.00, 0.50}

    def _check_decimal_pattern(self, bids: List[float]) -> Tuple[bool, str]:
        """检查尾数模式"""
        if len(bids) < 3:
            return False, ""

        decimals = []
        for b in bids:
            decimals.append(round(b - int(b), 2))

        pseudo_count = sum(1 for d in decimals if d in self._PSEUDO_RANDOM_DECIMALS)
        pseudo_ratio = pseudo_count / len(decimals)

        if pseudo_ratio >= 0.6:
            return True, f"报价尾数{int(pseudo_ratio*100)}%集中在伪随机数字(.88/.99/.66等)"
        return False, ""

    def _check_integer_consistency(self, bids: List[float]) -> Tuple[float, str]:
        """检查整数位一致性"""
        if len(bids) < 3:
            return 0.0, ""

        int_parts = [int(b) for b in bids]
        # 去掉"万"位以比较整数部分一致性
        trunc = [ip // 1000 for ip in int_parts]
        unique = len(set(trunc))
        consistency = 1.0 - (unique - 1) / max(len(bids) - 1, 1)

        if consistency >= 0.85:
            return consistency, f"报价整数位高度一致(一致性={consistency:.1%})"
        return consistency, ""

    def _check_gap_stability(self, bids: List[float]) -> Tuple[float, str]:
        """检查报价差额稳定性（CV越小→越规律→越可疑）"""
        if len(bids) < 3:
            return 1.0, ""

        sorted_bids = sorted(bids)
        gaps = [sorted_bids[i+1] - sorted_bids[i] for i in range(len(sorted_bids)-1)]

        mean_gap = sum(gaps) / len(gaps)
        if mean_gap == 0:
            return 0.0, "报价差额为0（完全相同）"

        variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        std = math.sqrt(variance)
        cv = std / abs(mean_gap)  # 变异系数

        if cv < 0.3:
            return cv, f"报价差额高度稳定(CV={cv:.2f}，人工排列特征明显)"
        return cv, ""

    def _check_edge_clustering(self, bids: List[float], max_price: Optional[float] = None, base_price: Optional[float] = None) -> Tuple[float, str]:
        """检查报价是否贴边（限价/基准价）"""
        edge_count = 0
        for b in bids:
            if max_price and abs(b - max_price) / max_price <= 0.01:
                edge_count += 1
            if base_price and abs(b - base_price) / base_price <= 0.005:
                edge_count += 1

        edge_ratio = edge_count / len(bids) if bids else 0.0

        if edge_ratio >= 0.5:
            return edge_ratio, f"报价贴边比例{edge_ratio:.0%}（限价1%内或基准价±0.5%）"
        return edge_ratio, ""

    def detect(
        self,
        segments: List[Dict[str, Any]],
    ) -> Dict[str, PricePatternSignal]:
        """
        检测报价规律雷同

        Args:
            segments: 标段列表，每条含：
                segment_id, bidders: [{bidder_id, bid_amount}],
                max_price (最高限价), base_price (基准价, 可选)

        Returns:
            {segment_id: PricePatternSignal}
        """
        results: Dict[str, PricePatternSignal] = {}

        for seg in segments:
            seg_id = seg.get("segment_id", "")
            bidders = seg.get("bidders", [])
            max_price = seg.get("max_price")
            base_price = seg.get("base_price")

            if len(bidders) < 3:
                continue

            bids = [b.get("bid_amount", 0) for b in bidders if b.get("bid_amount")]
            if not bids:
                continue

            evidence_parts = []
            signal_count = 0

            # 尾数模式
            decimal_hit, dec_ev = self._check_decimal_pattern(bids)
            if decimal_hit:
                evidence_parts.append(dec_ev)
                signal_count += 1

            # 整数一致性
            consistency, int_ev = self._check_integer_consistency(bids)
            if consistency >= 0.85:
                evidence_parts.append(int_ev)
                signal_count += 1

            # 差额稳定性
            cv, gap_ev = self._check_gap_stability(bids)
            if cv < 0.3:
                evidence_parts.append(gap_ev)
                signal_count += 1

            # 贴边
            edge_ratio, edge_ev = self._check_edge_clustering(bids, max_price, base_price)
            if edge_ratio >= 0.5:
                evidence_parts.append(edge_ev)
                signal_count += 1

            if signal_count >= 2:  # 至少2个信号才认定
                results[seg_id] = PricePatternSignal(
                    segment_id=seg_id,
                    suspected_bidders=[b.get("bidder_name", b.get("bidder_id", "")) for b in bidders],
                    decimal_pattern=dec_ev if decimal_hit else "",
                    integer_consistency=consistency,
                    gap_stability=cv if cv < 0.3 else 1.0,
                    edge_ratio=edge_ratio if edge_ratio >= 0.5 else 0.0,
                    all_bids=bids,
                    evidence="; ".join(evidence_parts)
                )

        return results


# ═══════════════════════════════════════════════════════════════
# 特征3：保证金来源同源检测器
# ═══════════════════════════════════════════════════════════════

class DepositSourceDetector:
    """
    检测不同投标人的保证金是否来自同一银行账户。

    信号：
    - 同一对公账户为多家投标人代缴
    - 转账时间集中（同一小时内）
    - 转账摘要文字格式高度一致
    """

    def _check_summary_similarity(self, summaries: List[str]) -> float:
        """检查转账摘要相似度（基于文本编辑距离的简化版）"""
        if len(summaries) < 2:
            return 0.0

        def _jaccard_chars(s1: str, s2: str) -> float:
            if not s1 or not s2:
                return 0.0
            set1, set2 = set(s1), set(s2)
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0

        similarities = []
        for i in range(len(summaries)):
            for j in range(i+1, len(summaries)):
                similarities.append(_jaccard_chars(summaries[i], summaries[j]))

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _check_time_cluster(self, times: List[str], window_min: int = 60) -> Tuple[bool, int]:
        """检查转账时间是否集中"""
        if len(times) < 2:
            return False, 0

        try:
            timestamps = [datetime.fromisoformat(t) for t in times]
        except (ValueError, TypeError):
            return False, 0

        timestamps.sort()
        cluster_count = 0
        for i in range(len(timestamps) - 1):
            diff = (timestamps[i+1] - timestamps[i]).total_seconds()
            if diff <= window_min * 60:
                cluster_count += 1

        return cluster_count >= len(timestamps) // 2, int(cluster_count)

    def detect(
        self,
        segments: List[Dict[str, Any]],
    ) -> Dict[str, DepositSourceSignal]:
        """
        检测保证金来源同源

        Args:
            segments: 标段列表，每条含：
                segment_id, deposits: [
                    {bidder_id, bidder_name, from_account, transfer_time, summary}
                ]

        Returns:
            {segment_id: DepositSourceSignal}
        """
        results: Dict[str, DepositSourceSignal] = {}

        for seg in segments:
            seg_id = seg.get("segment_id", "")
            deposits = seg.get("deposits", [])

            if len(deposits) < 2:
                continue

            # 账号聚类
            account_groups = defaultdict(list)
            for d in deposits:
                acct = d.get("from_account", "")
                if acct:
                    account_groups[acct].append(d)

            for acct, group in account_groups.items():
                if len(group) >= 2:
                    bidder_names = [g.get("bidder_name", g.get("bidder_id", "")) for g in group]
                    summaries = [g.get("summary", "") for g in group]
                    times = [g.get("transfer_time", "") for g in group]

                    time_clustered, cluster_window = self._check_time_cluster(times)
                    summary_sim = self._check_summary_similarity(summaries)

                    evidence_parts = [f"{len(group)}家投标人保证金来自同一账户({acct})"]

                    if time_clustered:
                        evidence_parts.append(f"转账时间集中在{cluster_window}分钟窗口内")
                    if summary_sim >= 0.7:
                        evidence_parts.append(f"转账摘要格式高度一致(相似度{summary_sim:.1%})")

                    results[seg_id] = DepositSourceSignal(
                        segment_id=seg_id,
                        suspected_bidders=bidder_names,
                        shared_account=acct,
                        time_cluster_window_min=cluster_window if time_clustered else 0,
                        summary_similarity=summary_sim,
                        evidence="; ".join(evidence_parts)
                    )

        return results


# ═══════════════════════════════════════════════════════════════
# 特征4：投标文件基因相似检测器
# ═══════════════════════════════════════════════════════════════

class DocumentGeneDetector:
    """
    检测不同投标人投标文件的内容相似度。

    复用 v4 text_similarity_compare 的SimHash/MinHash能力，
    增加行业基准值加权和马甲关联推断。
    """

    # 行业基准相似度（同行业技术方案天然相似度）
    INDUSTRY_BASELINES = {
        "construction": 0.55,       # 建筑施工
        "it_service": 0.45,         # IT服务
        "equipment": 0.35,          # 设备采购
        "consulting": 0.50,         # 咨询服务
        "epc": 0.40,                # EPC总承包
        "design": 0.45,             # 设计服务
        "default": 0.40,
    }

    def _get_baseline(self, industry: str) -> float:
        return self.INDUSTRY_BASELINES.get(industry, self.INDUSTRY_BASELINES["default"])

    def detect(
        self,
        segments: List[Dict[str, Any]],
        industry: str = "default",
    ) -> Dict[str, DocumentGeneSignal]:
        """
        检测投标文件基因相似

        Args:
            segments: 标段列表，每条含：
                segment_id, bidders: [{bidder_id, bidder_name, doc_text}]
            industry: 行业类型（用于基准值加权）

        Returns:
            {segment_id: DocumentGeneSignal}
        """
        baseline = self._get_baseline(industry)
        results: Dict[str, DocumentGeneSignal] = {}

        for seg in segments:
            seg_id = seg.get("segment_id", "")
            bidders = seg.get("bidders", [])

            if len(bidders) < 2:
                continue

            # 简化的文本相似度计算（Jaccard字符级）
            texts = {}
            for b in bidders:
                bid = b.get("bidder_id", b.get("bidder_name", ""))
                text = b.get("doc_text", b.get("technical_proposal", ""))
                if text:
                    texts[bid] = text

            if len(texts) < 2:
                continue

            # 计算两两相似度
            similarity_matrix: Dict[str, Dict[str, float]] = {}
            similarities = []
            bidder_ids = list(texts.keys())

            for i in range(len(bidder_ids)):
                a = bidder_ids[i]
                similarity_matrix[a] = {}
                for j in range(i+1, len(bidder_ids)):
                    b = bidder_ids[j]

                    # 简化Jaccard相似度（字符级bigram）
                    def _jaccard_similarity(t1: str, t2: str) -> float:
                        if not t1 or not t2:
                            return 0.0
                        bigrams1 = {t1[k:k+2] for k in range(len(t1)-1)}
                        bigrams2 = {t2[k:k+2] for k in range(len(t2)-1)}
                        if not bigrams1 or not bigrams2:
                            return 0.0
                        intersection = len(bigrams1 & bigrams2)
                        union = len(bigrams1 | bigrams2)
                        return intersection / union if union > 0 else 0.0

                    sim = _jaccard_similarity(texts[a], texts[b])
                    similarity_matrix[a][b] = sim
                    similarities.append(sim)

            avg_sim = sum(similarities) / len(similarities) if similarities else 0.0
            max_sim = max(similarities) if similarities else 0.0

            # 行业基准值加权：超出基准值越多越可疑
            weighted_signal = max(0.0, avg_sim - baseline)

            if weighted_signal >= 0.25:  # 超出行业基准25%以上
                evidence = (
                    f"投标文件平均相似度{avg_sim:.1%}，超出行业基准({baseline:.0%})"
                    f"{weighted_signal:.0%}，最高相似度{max_sim:.1%}"
                )
                results[seg_id] = DocumentGeneSignal(
                    segment_id=seg_id,
                    suspected_bidders=list(texts.keys()),
                    max_similarity=max_sim,
                    avg_similarity=avg_sim,
                    similarity_matrix=similarity_matrix,
                    industry_baseline=baseline,
                    evidence=evidence
                )

        return results


# ═══════════════════════════════════════════════════════════════
# 特征5：时间窗口扎堆检测器
# ═══════════════════════════════════════════════════════════════

class TimeClusterDetector:
    """
    检测投标文件提交时间是否集中在最后时刻。

    信号：
    - 提交集中在开标前30分钟
    - 多家提交间隔<5分钟
    - 秒级批量上传（同一秒内多份）
    """

    def detect(
        self,
        segments: List[Dict[str, Any]],
        last_window_min: int = 30,
        batch_threshold_sec: int = 5,
    ) -> Dict[str, TimeClusterSignal]:
        """
        检测时间窗口扎堆

        Args:
            segments: 标段列表，每条含：
                segment_id, deadline (开标截止时间),
                bidders: [{bidder_id, bidder_name, submit_time}]
            last_window_min: 末段窗口（分钟）
            batch_threshold_sec: 批量上传阈值（秒）

        Returns:
            {segment_id: TimeClusterSignal}
        """
        results: Dict[str, TimeClusterSignal] = {}

        for seg in segments:
            seg_id = seg.get("segment_id", "")
            deadline_str = seg.get("deadline", "")
            bidders = seg.get("bidders", [])

            if len(bidders) < 2:
                continue

            try:
                deadline = datetime.fromisoformat(deadline_str)
            except (ValueError, TypeError):
                continue

            # 提取有效提交时间
            valid_times = []
            for b in bidders:
                try:
                    t = datetime.fromisoformat(b.get("submit_time", ""))
                    valid_times.append((b.get("bidder_name", b.get("bidder_id", "")), t))
                except (ValueError, TypeError):
                    continue

            if not valid_times:
                continue

            # 末段窗口计数
            last_window_times = [
                (name, t) for name, t in valid_times
                if (deadline - t).total_seconds() <= last_window_min * 60
            ]

            last_window_ratio = len(last_window_times) / len(valid_times) if valid_times else 0

            # 间隔计算
            sorted_times = sorted([t for _, t in last_window_times])
            intervals = []
            batch_detected = False
            for i in range(len(sorted_times) - 1):
                gap = (sorted_times[i+1] - sorted_times[i]).total_seconds()
                intervals.append(int(gap))
                if gap <= batch_threshold_sec:
                    batch_detected = True

            min_interval = min(intervals) if intervals else 999999
            max_interval = max(intervals) if intervals else 0

            # 判定信号
            if last_window_ratio >= 0.6:
                evidence_parts = [
                    f"{len(last_window_times)}/{len(valid_times)}({last_window_ratio:.0%})投标在开标前{last_window_min}分钟内提交"
                ]
                if min_interval <= 60:
                    evidence_parts.append(f"最短提交间隔{min_interval}秒")
                if batch_detected:
                    evidence_parts.append(f"检测到批量上传（间隔≤{batch_threshold_sec}秒）")
                    evidence_parts[0] += "，涉嫌批量上传"

                results[seg_id] = TimeClusterSignal(
                    segment_id=seg_id,
                    suspected_bidders=[name for name, _ in last_window_times],
                    last_window_count=len(last_window_times),
                    last_window_max_interval_sec=max_interval,
                    last_window_min_interval_sec=min_interval,
                    total_bidders=len(valid_times),
                    last_window_ratio=last_window_ratio,
                    batch_upload_detected=batch_detected,
                    evidence="; ".join(evidence_parts)
                )

        return results


# ═══════════════════════════════════════════════════════════════
# 主引擎：围标串标多维检测器
# ═══════════════════════════════════════════════════════════════

class BidRiggingDetector:
    """
    围标串标多维检测引擎

    并行运行5个特征检测器，交叉验证加权评分。

    评分规则：
        - 每个特征命中=1分
        - 特征3（保证金同源）命中=额外+0.5（高特异性补偿）
        - 特征4（文件基因）相似度>0.95=额外+0.5（极高相似度补偿）
        - 4个以上特征命中=额外+0.5（多特征交叉强信号）
        - 总分范围0-5，≥2.5=高风险，≥1.5=中风险，<1.5=低风险
    """

    def __init__(self):
        self.ip_detector = IPDeviceClusterDetector()
        self.price_detector = PricePatternDetector()
        self.deposit_detector = DepositSourceDetector()
        self.gene_detector = DocumentGeneDetector()
        self.time_detector = TimeClusterDetector()

    def detect(
        self,
        segments: List[Dict[str, Any]],
        industry: str = "default",
        verbose: bool = False,
    ) -> BidRiggingResult:
        """
        主检测入口

        Args:
            segments: 标段数据列表，每条可含：
                - segment_id, segment_name, bidders (必填)
                - bidders 每条含: bidder_id, bidder_name, ip, mac, ca_issue_date,
                  ca_issuer, bid_amount, doc_text/technical_proposal, submit_time
                - deposits: [{bidder_id, from_account, transfer_time, summary}]
                - deadline, max_price, base_price (可选)

        Returns:
            BidRiggingResult 含全部检测结果、交叉矩阵、汇总
        """
        risks: List[BidRiggingRisk] = []
        hit_counts = {f"feature_{i}": 0 for i in range(1, 6)}

        for seg in segments:
            seg_id = seg.get("segment_id", "")
            seg_name = seg.get("segment_name", "")
            bidders = seg.get("bidders", [])

            if not bidders:
                continue

            # 并行运行5个特征检测器
            ip_results = self.ip_detector.detect([seg])
            price_results = self.price_detector.detect([seg])
            deposit_results = self.deposit_detector.detect([seg])
            gene_results = self.gene_detector.detect([seg], industry)
            time_results = self.time_detector.detect([seg])

            f1_hit = seg_id in ip_results
            f2_hit = seg_id in price_results
            f3_hit = seg_id in deposit_results
            f4_hit = seg_id in gene_results
            f5_hit = seg_id in time_results

            feature_flags = {
                "f1_ip_device": f1_hit,
                "f2_price_pattern": f2_hit,
                "f3_deposit_source": f3_hit,
                "f4_document_gene": f4_hit,
                "f5_time_cluster": f5_hit,
            }

            # 计分
            score = sum(1 for v in feature_flags.values() if v)
            if f3_hit:
                score += 0.5  # 保证金同源高特异性
            if f4_hit and gene_results[seg_id].max_similarity >= 0.95:
                score += 0.5  # 极高相似度
            if score >= 4:
                score += 0.5  # 多特征交叉

            score = min(5.0, score)

            if score >= 1.5:  # 至少中风险才纳入
                # 记录命中统计
                for k in feature_flags:
                    if feature_flags[k]:
                        hit_counts[k] = hit_counts.get(k, 0) + 1

                # 组合证据
                combined_evidence = []
                if f1_hit:
                    for ip_sig in ip_results[seg_id]:
                        combined_evidence.append(f"[IP/设备] {ip_sig.evidence}")
                if f2_hit:
                    combined_evidence.append(f"[报价规律] {price_results[seg_id].evidence}")
                if f3_hit:
                    combined_evidence.append(f"[保证金] {deposit_results[seg_id].evidence}")
                if f4_hit:
                    combined_evidence.append(f"[文件基因] {gene_results[seg_id].evidence}")
                if f5_hit:
                    combined_evidence.append(f"[时间扎堆] {time_results[seg_id].evidence}")

                # 风险等级
                if score >= 2.5:
                    risk_level = "high"
                    recommendation = "多特征交叉验证，围标嫌疑较重，建议立即启动人工核查+工商穿透"
                elif score >= 1.5:
                    risk_level = "medium"
                    recommendation = "存在异常信号，建议结合工商信息和历史投标记录进一步分析"
                else:
                    risk_level = "low"
                    recommendation = "单一弱信号，列入持续观察列表"

                risk = BidRiggingRisk(
                    segment_id=seg_id,
                    segment_name=seg_name,
                    total_bidders=len(bidders),
                    risk_score=round(score, 1),
                    feature_flags=feature_flags,
                    feature_details={
                        "ip_device": ip_results.get(seg_id),
                        "price_pattern": price_results.get(seg_id),
                        "deposit_source": deposit_results.get(seg_id),
                        "document_gene": gene_results.get(seg_id),
                        "time_cluster": time_results.get(seg_id),
                    },
                    ip_device=ip_results.get(seg_id, [None])[0] if ip_results.get(seg_id) else None,
                    price_pattern=price_results.get(seg_id),
                    deposit_source=deposit_results.get(seg_id),
                    document_gene=gene_results.get(seg_id),
                    time_cluster=time_results.get(seg_id),
                    combined_evidence=combined_evidence,
                    risk_level=risk_level,
                    recommendation=recommendation,
                )
                risks.append(risk)

        # 排序：高风险优先
        risks.sort(key=lambda r: r.risk_score, reverse=True)

        # 分布统计
        dist = Counter(r.risk_level for r in risks)

        # 各特征独立命中率（相对总标段数）
        total = len(segments)
        hit_rate_stats = {
            "f1_ip_device": hit_counts.get("f1_ip_device", 0) / total if total else 0,
            "f2_price_pattern": hit_counts.get("f2_price_pattern", 0) / total if total else 0,
            "f3_deposit_source": hit_counts.get("f3_deposit_source", 0) / total if total else 0,
            "f4_document_gene": hit_counts.get("f4_document_gene", 0) / total if total else 0,
            "f5_time_cluster": hit_counts.get("f5_time_cluster", 0) / total if total else 0,
        }

        # 交叉命中矩阵
        cross_hit_matrix = self._build_cross_matrix(risks)

        # 汇总
        high_count = dist.get("high", 0)
        medium_count = dist.get("medium", 0)
        summary = (
            f"招投标围标串标检测完成：共{total}个标段，"
            f"检出高风险{high_count}个、中风险{medium_count}个。"
            f"建议优先核查高风险标段并生成证据链图谱。"
        )

        return BidRiggingResult(
            total_segments=total,
            flagged_segments=len(risks),
            risk_distribution=dict(dist),
            risks=risks,
            hit_rate_stats=hit_rate_stats,
            cross_hit_matrix=cross_hit_matrix,
            summary=summary,
        )

    def _build_cross_matrix(self, risks: List[BidRiggingRisk]) -> Dict[str, Dict[str, float]]:
        """构建特征交叉命中矩阵"""
        feature_keys = [
            "f1_ip_device", "f2_price_pattern", "f3_deposit_source",
            "f4_document_gene", "f5_time_cluster"
        ]

        matrix: Dict[str, Dict[str, float]] = {}
        for f1 in feature_keys:
            matrix[f1] = {}
            for f2 in feature_keys:
                if f1 == f2:
                    matrix[f1][f2] = 1.0
                    continue

                both = sum(1 for r in risks
                          if r.feature_flags.get(f1) and r.feature_flags.get(f2))
                either = sum(1 for r in risks
                            if r.feature_flags.get(f1) or r.feature_flags.get(f2))
                matrix[f1][f2] = both / either if either else 0.0

        return matrix


# ═══════════════════════════════════════════════════════════════
# 便捷导出函数
# ═══════════════════════════════════════════════════════════════

def detect_bid_rigging(
    segments: List[Dict[str, Any]],
    industry: str = "default",
) -> BidRiggingResult:
    """
    便捷接口：围标串标检测

    Args:
        segments: 标段数据列表
        industry: 行业类型

    Returns:
        BidRiggingResult
    """
    detector = BidRiggingDetector()
    return detector.detect(segments, industry=industry)


def export_risks_to_csv(result: BidRiggingResult, output_path: str) -> None:
    """导出风险列表到CSV"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "标段ID", "标段名称", "投标人数", "风险评分",
            "风险等级", "IP/设备", "报价规律", "保证金同源",
            "文件基因", "时间扎堆", "建议"
        ])
        for r in result.risks:
            flags = r.feature_flags
            writer.writerow([
                r.segment_id,
                r.segment_name,
                r.total_bidders,
                r.risk_score,
                r.risk_level,
                "✓" if flags.get("f1_ip_device") else "✗",
                "✓" if flags.get("f2_price_pattern") else "✗",
                "✓" if flags.get("f3_deposit_source") else "✗",
                "✓" if flags.get("f4_document_gene") else "✗",
                "✓" if flags.get("f5_time_cluster") else "✗",
                r.recommendation,
            ])
    print(f"已导出{len(result.risks)}条围标风险记录到 {output_path}")
