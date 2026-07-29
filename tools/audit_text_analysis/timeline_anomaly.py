"""
工具8：timeline_anomaly — 时间序列异常检测器

场景：采购审计中检测付款时间早于合同签订时间的异常项目，
     识别金额偏离、经办人聚集等模式。

技术：时滞检测 + 金额偏离率 + 经办人聚焦统计
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import csv


# ── 数据结构 ──────────────────────────────────────────────────

@dataclass
class TimelineAnomaly:
    """单个时间序列异常"""
    index: int
    project_id: str = ""
    contract_date: str = ""
    payment_date: str = ""
    contract_amount: float = 0.0
    payment_amount: float = 0.0
    lead_days: int = 0  # 付款领先天数（正数=先付款后签合同）
    amount_deviation_pct: float = 0.0  # 金额偏离率
    handler: str = ""
    unit: str = ""
    severity: str = "medium"  # high/medium/low
    anomaly_type: str = ""  # prepayment | amount_mismatch | both


@dataclass
class HandlerCluster:
    """经办人聚集分析"""
    handler_name: str
    anomaly_count: int
    total_projects: int
    anomaly_rate: float
    total_amount: float
    avg_lead_days: float
    risk_rank: int = 0


@dataclass
class TimelineResult:
    """时间序列异常检测完整结果"""
    total_projects: int
    anomalies: List[TimelineAnomaly]
    anomaly_count: int
    anomaly_rate: float
    total_anomaly_amount: float
    handler_clusters: List[HandlerCluster]
    summary: str


class TimelineAnomalyDetector:
    """时间序列异常检测器"""

    def __init__(self, max_lead_days_before_flag: int = 0):
        """
        Args:
            max_lead_days_before_flag: 允许的最大提前付款天数（默认0=不允许提前）
        """
        self.max_lead_days_before_flag = max_lead_days_before_flag

    def detect(
        self,
        projects: List[Dict[str, Any]],
        date_format: str = "%Y-%m-%d",
    ) -> TimelineResult:
        """
        检测时间序列异常

        Args:
            projects: 项目记录列表，每条含：
                project_id, contract_date(合同签订日), payment_date(付款日),
                contract_amount(合同金额), payment_amount(付款金额),
                handler(经办人), unit(单位)
            date_format: 日期格式
        """
        anomalies = []
        handler_projects: Dict[str, int] = defaultdict(int)

        for idx, proj in enumerate(projects):
            handler = proj.get("handler", "未知")
            handler_projects[handler] += 1

            contract_date_str = str(proj.get("contract_date", ""))
            payment_date_str = str(proj.get("payment_date", ""))

            if not contract_date_str or not payment_date_str:
                continue

            try:
                contract_date = datetime.strptime(
                    contract_date_str.strip(), date_format
                )
                payment_date = datetime.strptime(
                    payment_date_str.strip(), date_format
                )
            except ValueError:
                continue

            # 时滞计算
            delta = payment_date - contract_date
            lead_days = -delta.days  # 正数=付款领先
            is_prepayment = lead_days > self.max_lead_days_before_flag

            # 金额偏离
            contract_amt = float(proj.get("contract_amount", 0))
            payment_amt = float(proj.get("payment_amount", 0))
            amount_deviation = 0.0
            if contract_amt > 0:
                amount_deviation = abs(payment_amt - contract_amt) / contract_amt

            is_amount_mismatch = amount_deviation > 0.10  # 超过10%偏离

            if is_prepayment or is_amount_mismatch:
                # 确定严重级别和类型
                if is_prepayment and is_amount_mismatch:
                    severity = "high"
                    atype = "both"
                elif is_prepayment:
                    severity = "high" if lead_days > 30 else "medium"
                    atype = "prepayment"
                else:
                    severity = "medium"
                    atype = "amount_mismatch"

                anomalies.append(TimelineAnomaly(
                    index=idx,
                    project_id=str(proj.get("project_id", idx)),
                    contract_date=contract_date_str,
                    payment_date=payment_date_str,
                    contract_amount=contract_amt,
                    payment_amount=payment_amt,
                    lead_days=lead_days,
                    amount_deviation_pct=round(amount_deviation * 100, 1),
                    handler=handler,
                    unit=str(proj.get("unit", "")),
                    severity=severity,
                    anomaly_type=atype,
                ))

        # 排序：高危先付>中危先付>金额偏离
        anomalies.sort(
            key=lambda a: (
                {"high": 0, "medium": 1, "low": 2}[a.severity],
                -a.lead_days,
            )
        )

        # 经办人聚焦
        handler_anomalies: Dict[str, List[TimelineAnomaly]] = defaultdict(list)
        for a in anomalies:
            handler_anomalies[a.handler].append(a)

        handler_clusters = []
        for h_name, h_anoms in handler_anomalies.items():
            total_proj = handler_projects.get(h_name, len(h_anoms))
            cluster = HandlerCluster(
                handler_name=h_name,
                anomaly_count=len(h_anoms),
                total_projects=max(total_proj, len(h_anoms)),
                anomaly_rate=len(h_anoms) / max(total_proj, 1),
                total_amount=sum(a.payment_amount for a in h_anoms),
                avg_lead_days=(
                    sum(max(0, a.lead_days) for a in h_anoms) / len(h_anoms)
                    if h_anoms else 0
                ),
            )
            handler_clusters.append(cluster)

        handler_clusters.sort(key=lambda c: c.anomaly_count, reverse=True)
        for i, c in enumerate(handler_clusters):
            c.risk_rank = i + 1

        # 统计
        total = len(projects) or 1
        anomaly_amount = sum(a.payment_amount for a in anomalies)

        summary = self._summarize(anomalies, handler_clusters)

        return TimelineResult(
            total_projects=len(projects),
            anomalies=anomalies,
            anomaly_count=len(anomalies),
            anomaly_rate=round(len(anomalies) / total, 3),
            total_anomaly_amount=anomaly_amount,
            handler_clusters=handler_clusters,
            summary=summary,
        )

    def _summarize(
        self,
        anomalies: List[TimelineAnomaly],
        handler_clusters: List[HandlerCluster],
    ) -> str:
        """生成摘要"""
        n = len(anomalies)
        if n == 0:
            return "未发现时间序列异常（先付款后签合同或金额显著偏离）。"

        prepay = [a for a in anomalies if a.anomaly_type in ("prepayment", "both")]
        amount = [a for a in anomalies if a.anomaly_type in ("amount_mismatch", "both")]
        high_sev = [a for a in anomalies if a.severity == "high"]

        parts = [
            f"共发现{n}个时间序列异常项目，其中：",
            f"先付款后签合同{len(prepay)}个（高危{len([a for a in prepay if a.severity=='high'])}个），",
            f"金额偏离>10%{len(amount)}个，",
            f"总涉及金额{sum(a.payment_amount for a in anomalies):,.0f}元。",
        ]

        if handler_clusters:
            top_handler = handler_clusters[0]
            if top_handler.anomaly_rate > 0.5:
                parts.append(
                    f"经办人'{top_handler.handler_name}'集中了{top_handler.anomaly_count}个异常"
                    f"（占总项目数的{top_handler.anomaly_rate:.0%}），高度可疑。"
                )

        parts.append(
            "建议：(1)对先付款后签合同项目逐项核实审批依据 "
            "(2)对经办人聚焦度高的人员进行专项审计 "
            "(3)结合合同变更轨迹分析，判断是否存在结算水分。"
        )

        return "".join(parts)


# ── MCP工具接口 ──────────────────────────────────────────────

def timeline_anomaly(
    projects: List[Dict[str, Any]],
    date_format: str = "%Y-%m-%d",
    max_lead_days: int = 0,
    csv_file: Optional[str] = None,
) -> dict:
    """
    时间序列异常检测（先付款后签合同 / 金额偏离）

    Args:
        projects: 项目/合同记录数组 [{"contract_date": "2024-01-15", ...}, ...]
        date_format: 日期格式
        max_lead_days: 允许的最大提前付款天数（0=严格禁止）
        csv_file: CSV文件路径（与projects二选一）

    CSV列要求：project_id, contract_date, payment_date,
               contract_amount, payment_amount, handler, unit

    Returns:
        分析结果dict
    """
    if csv_file and not projects:
        loaded = []
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for key in ("contract_amount", "payment_amount"):
                    try:
                        row[key] = float(row.get(key, "0").replace(",", ""))
                    except (ValueError, KeyError):
                        row[key] = 0
                loaded.append(row)
        projects = loaded

    detector = TimelineAnomalyDetector(
        max_lead_days_before_flag=max_lead_days,
    )
    result = detector.detect(projects or [], date_format=date_format)

    anomaly_items = []
    for a in result.anomalies[:50]:  # 只返回前50条详情
        anomaly_items.append({
            "project_id": a.project_id,
            "contract_date": a.contract_date,
            "payment_date": a.payment_date,
            "lead_days": a.lead_days,
            "lead_label": f"提前{a.lead_days}天付款" if a.lead_days > 0 else "正常",
            "contract_amount": a.contract_amount,
            "payment_amount": a.payment_amount,
            "amount_deviation": f"{a.amount_deviation_pct:+.1f}%",
            "handler": a.handler,
            "unit": a.unit,
            "severity": a.severity,
            "anomaly_type": a.anomaly_type,
        })

    handler_items = []
    for c in result.handler_clusters:
        handler_items.append({
            "handler": c.handler_name,
            "anomaly_count": c.anomaly_count,
            "total_projects": c.total_projects,
            "anomaly_rate": f"{c.anomaly_rate:.0%}",
            "total_amount": c.total_amount,
            "avg_lead_days": round(c.avg_lead_days, 1),
            "risk_rank": c.risk_rank,
            "risk_label": (
                "🔴 高度可疑（异常率>50%）" if c.anomaly_rate > 0.5
                else "🟠 中等风险（异常率25-50%）" if c.anomaly_rate > 0.25
                else "🟡 关注（异常率10-25%）" if c.anomaly_rate > 0.10
                else "⚪ 分散分布"
            ),
        })

    return {
        "total_projects": result.total_projects,
        "anomaly_count": result.anomaly_count,
        "anomaly_rate": f"{result.anomaly_rate:.1%}",
        "total_anomaly_amount": result.total_anomaly_amount,
        "total_anomaly_amount_label": f"{result.total_anomaly_amount/1e8:.2f}亿"
            if result.total_anomaly_amount > 1e8
            else f"{result.total_anomaly_amount/1e4:.0f}万",
        "breakdown": {
            "prepayment": len([
                a for a in result.anomalies
                if a.anomaly_type in ("prepayment", "both")
            ]),
            "amount_mismatch": len([
                a for a in result.anomalies
                if a.anomaly_type in ("amount_mismatch", "both")
            ]),
            "high_severity": len([
                a for a in result.anomalies if a.severity == "high"
            ]),
        },
        "anomalies": anomaly_items,
        "handler_clusters": handler_items,
        "summary": result.summary,
    }
