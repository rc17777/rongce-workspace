"""
P2: throughput_benchmark — 批量文档处理吞吐量基准 (v6, 2d)

为 contract_field_extract 和 text_similarity_compare 增加批量模式SLA：
- 50份合同 ≤ 30分钟
- 100条报销记录 ≤ 10分钟
- 1000条记录 ≤ 60分钟

输出批量处理报告（含每批耗时、吞吐量、SLA达标率）。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time


# ── SLA定义 ──────────────────────────────────────────────────

BATCH_SLA = {
    "contract_extract": {
        "name": "合同字段提取",
        "small": {"max_items": 10, "max_ms": 30_000},      # ≤10份: 30秒
        "medium": {"max_items": 50, "max_ms": 300_000},    # ≤50份: 5分钟
        "large": {"max_items": 200, "max_ms": 1_800_000},  # ≤200份: 30分钟
        "unit": "份",
    },
    "text_similarity": {
        "name": "文本相似度比对",
        "small": {"max_items": 20, "max_ms": 60_000},
        "medium": {"max_items": 100, "max_ms": 600_000},
        "large": {"max_items": 500, "max_ms": 3_600_000},
        "unit": "对",
    },
    "budget_compliance": {
        "name": "预算合规扫描",
        "small": {"max_items": 50, "max_ms": 10_000},
        "medium": {"max_items": 500, "max_ms": 60_000},
        "large": {"max_items": 5000, "max_ms": 600_000},
        "unit": "条",
    },
    "benford_analysis": {
        "name": "Benford分析",
        "small": {"max_items": 100, "max_ms": 5_000},
        "medium": {"max_items": 1000, "max_ms": 30_000},
        "large": {"max_items": 10000, "max_ms": 300_000},
        "unit": "条",
    },
    "supplier_fingerprint": {
        "name": "供应商指纹分析",
        "small": {"max_items": 10, "max_ms": 10_000},
        "medium": {"max_items": 50, "max_ms": 60_000},
        "large": {"max_items": 200, "max_ms": 300_000},
        "unit": "家",
    },
    "timeline_anomaly": {
        "name": "时间序列异常检测",
        "small": {"max_items": 100, "max_ms": 5_000},
        "medium": {"max_items": 1000, "max_ms": 30_000},
        "large": {"max_items": 10000, "max_ms": 300_000},
        "unit": "条",
    },
    "contract_change_trajectory": {
        "name": "合同变更轨迹分析",
        "small": {"max_items": 20, "max_ms": 10_000},
        "medium": {"max_items": 100, "max_ms": 60_000},
        "large": {"max_items": 500, "max_ms": 300_000},
        "unit": "条",
    },
}


@dataclass
class BatchRun:
    """单次批量运行记录"""
    tool_name: str
    item_count: int
    elapsed_ms: int
    throughput: float  # 条/秒
    sla_met: bool
    sla_threshold_ms: int
    timestamp: str = ""


@dataclass
class ThroughputReport:
    """吞吐量报告"""
    tool_name: str
    total_items: int
    total_batches: int
    total_time_ms: int
    avg_throughput: float     # 平均吞吐量（条/秒）
    sla_violations: int       # SLA违规次数
    sla_compliance_rate: float  # SLA达标率
    runs: List[BatchRun]


class ThroughputTracker:
    """吞吐量跟踪器"""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.runs: List[BatchRun] = []
        self._start_time: Optional[float] = None

    def start_batch(self):
        """开始计时"""
        self._start_time = time.time()

    def end_batch(self, item_count: int) -> BatchRun:
        """结束计时，记录批次"""
        elapsed_ms = int((time.time() - (self._start_time or time.time())) * 1000)
        self._start_time = None

        sla = BATCH_SLA.get(self.tool_name)
        if sla:
            # 选择最接近的SLA档位
            if item_count <= sla["small"]["max_items"]:
                threshold = sla["small"]["max_ms"]
            elif item_count <= sla["medium"]["max_items"]:
                threshold = sla["medium"]["max_ms"]
            else:
                threshold = sla["large"]["max_ms"]
            sla_met = elapsed_ms <= threshold
        else:
            threshold = 0
            sla_met = True

        throughput = item_count / (elapsed_ms / 1000) if elapsed_ms > 0 else 0

        run = BatchRun(
            tool_name=self.tool_name,
            item_count=item_count,
            elapsed_ms=elapsed_ms,
            throughput=round(throughput, 2),
            sla_met=sla_met,
            sla_threshold_ms=threshold,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.runs.append(run)
        return run

    def report(self) -> ThroughputReport:
        """生成吞吐量报告"""
        total_items = sum(r.item_count for r in self.runs)
        total_time = sum(r.elapsed_ms for r in self.runs)
        avg_tp = total_items / (total_time / 1000) if total_time > 0 else 0
        violations = sum(1 for r in self.runs if not r.sla_met)
        total_runs = len(self.runs) or 1

        return ThroughputReport(
            tool_name=self.tool_name,
            total_items=total_items,
            total_batches=len(self.runs),
            total_time_ms=total_time,
            avg_throughput=round(avg_tp, 2),
            sla_violations=violations,
            sla_compliance_rate=round(1 - violations / total_runs, 2),
            runs=self.runs,
        )

    def report_dict(self) -> dict:
        """导出为dict"""
        r = self.report()
        sla = BATCH_SLA.get(self.tool_name, {})
        return {
            "tool": self.tool_name,
            "tool_label": sla.get("name", self.tool_name),
            "total_items": r.total_items,
            "total_batches": r.total_batches,
            "total_time_ms": r.total_time_ms,
            "total_time_label": f"{r.total_time_ms/1000:.1f}秒",
            "avg_throughput": r.avg_throughput,
            "throughput_label": f"{r.avg_throughput:.1f}条/秒",
            "sla_violations": r.sla_violations,
            "sla_compliance_rate": f"{r.sla_compliance_rate:.0%}",
            "sla_status": (
                "✅ 达标" if r.sla_compliance_rate >= 0.95
                else "⚠️ 部分达标" if r.sla_compliance_rate >= 0.80
                else "🔴 不达标"
            ),
            "last_run": {
                "items": r.runs[-1].item_count if r.runs else 0,
                "elapsed_ms": r.runs[-1].elapsed_ms if r.runs else 0,
                "sla_met": r.runs[-1].sla_met if r.runs else True,
            } if r.runs else None,
        }


def get_all_sla_summary() -> dict:
    """获取所有工具的SLA定义摘要"""
    summary = {}
    for tool_name, sla in BATCH_SLA.items():
        summary[tool_name] = {
            "name": sla["name"],
            "small": f"≤{sla['small']['max_items']}{sla['unit']} → {sla['small']['max_ms']/1000:.0f}秒",
            "medium": f"≤{sla['medium']['max_items']}{sla['unit']} → {sla['medium']['max_ms']/1000:.0f}秒",
            "large": f"≤{sla['large']['max_items']}{sla['unit']} → {sla['large']['max_ms']/1000:.0f}秒",
        }
    return summary
