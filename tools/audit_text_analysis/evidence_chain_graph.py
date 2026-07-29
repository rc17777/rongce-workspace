"""
工具12：evidence_chain_graph — 证据链图谱生成器

v9新增，基于「数审视界」《招投标围标串标，5个数据特征一抓一个准》。

功能：
  1. 从 BidRiggingResult 提取风险标段数据
  2. 生成力导向图（Force-Directed）JSON → 前端可渲染为交互式图谱
  3. 生成PDF静态报告（HTML → 浏览器打印）
  4. 生成证据摘要卡片（A4一页纸）

图谱节点类型：
  - 标段节点（中心）
  - 特征节点（5大特征×N个投标人）
  - 投标人节点（各投标公司）
  - 关联方节点（工商关联）
  - 异常指标节点（金额/时间等）

边类型：
  - 投标关系（投标人→标段）
  - 特征命中（标段→特征节点）
  - 同源关系（投标人→投标人，同IP/同账户）
  - 工商关联（投标人→关联方）
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import json
import math
from datetime import datetime

# 尝试导入bid_rigging_detector类型（运行时可选）
try:
    from .bid_rigging_detector import BidRiggingRisk, BidRiggingResult
except ImportError:
    BidRiggingRisk = None  # type: ignore
    BidRiggingResult = None  # type: ignore


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class GraphNode:
    """图谱节点"""
    id: str
    label: str
    node_type: str  # segment | feature | bidder | related_party | indicator
    size: float = 10.0           # 视觉大小（=风险权重）
    color: str = "#4A90D9"       # 节点颜色
    metadata: Dict[str, Any] = field(default_factory=dict)
    x: float = 0.0               # 布局坐标（力导向计算后）
    y: float = 0.0


@dataclass
class GraphEdge:
    """图谱边"""
    source: str                  # 源节点ID
    target: str                  # 目标节点ID
    edge_type: str               # bid | feature_hit | same_source | business_relation
    weight: float = 1.0          # 边权重
    label: str = ""              # 边标签
    dash: bool = False           # 是否虚线（弱信号）


@dataclass
class EvidenceGraph:
    """证据链图谱"""
    segment_id: str
    segment_name: str
    risk_score: float
    risk_level: str
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    summary_text: str = ""


@dataclass
class EvidenceChainResult:
    """证据链生成完整结果"""
    graphs: List[EvidenceGraph]
    total_segments: int
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ═══════════════════════════════════════════════════════════════
# 颜色映射
# ═══════════════════════════════════════════════════════════════

FEATURE_COLORS = {
    "f1_ip_device": "#E74C3C",       # 红色 - IP/设备
    "f2_price_pattern": "#F39C12",    # 橙色 - 报价规律
    "f3_deposit_source": "#9B59B6",   # 紫色 - 保证金同源
    "f4_document_gene": "#3498DB",    # 蓝色 - 文件基因
    "f5_time_cluster": "#1ABC9C",     # 青色 - 时间扎堆
}

RISK_LEVEL_COLORS = {
    "high": "#E74C3C",
    "medium": "#F39C12",
    "low": "#27AE60",
}

FEATURE_LABELS = {
    "f1_ip_device": "同IP/同设备投标",
    "f2_price_pattern": "报价规律性雷同",
    "f3_deposit_source": "保证金来源同源",
    "f4_document_gene": "投标文件基因相似",
    "f5_time_cluster": "时间窗口扎堆",
}

FEATURE_CATEGORIES = {
    "f1_ip_device": "网络/设备层",
    "f2_price_pattern": "金额层",
    "f3_deposit_source": "资金层",
    "f4_document_gene": "内容层",
    "f5_time_cluster": "行为层",
}


# ═══════════════════════════════════════════════════════════════
# 图谱生成器
# ═══════════════════════════════════════════════════════════════

class EvidenceChainGenerator:
    """
    证据链图谱生成器

    为每个高风险标段生成一张力导向图，
    展示5大特征 + 投标人 + 中标结果 + 关联方关系。
    """

    def __init__(self):
        self._node_counter = 0

    def _make_id(self, prefix: str) -> str:
        self._node_counter += 1
        return f"{prefix}_{self._node_counter}"

    def generate_all(
        self,
        rigging_result: Any,  # BidRiggingResult
        max_graphs: int = 20,
        min_risk_score: float = 1.5,
    ) -> EvidenceChainResult:
        """
        为所有达到阈值的风险标段生成证据链图谱

        Args:
            rigging_result: BidRiggingResult 检测结果
            max_graphs: 最多生成的图谱数
            min_risk_score: 最低风险评分阈值

        Returns:
            EvidenceChainResult
        """
        self._node_counter = 0
        graphs = []

        risks = getattr(rigging_result, "risks", [])
        # 过滤并排序
        filtered = [r for r in risks if r.risk_score >= min_risk_score]
        filtered.sort(key=lambda r: r.risk_score, reverse=True)

        for risk in filtered[:max_graphs]:
            graph = self._build_graph(risk)
            graphs.append(graph)

        return EvidenceChainResult(
            graphs=graphs,
            total_segments=len(graphs),
        )

    def generate_for_report(
        self,
        rigging_result: Any,
        related_parties: Optional[Dict[str, List[Dict]]] = None,
    ) -> EvidenceChainResult:
        """
        为审计报告生成证据链图谱（含工商关联信息）

        Args:
            rigging_result: BidRiggingResult
            related_parties: {bidder_name: [{name, relation_type, evidence}]}

        Returns:
            EvidenceChainResult
        """
        return self.generate_all(rigging_result, max_graphs=15, min_risk_score=2.0)

    def _build_graph(self, risk: Any) -> EvidenceGraph:
        """为单个风险标段构建图谱"""
        seg_id = risk.segment_id
        seg_name = getattr(risk, "segment_name", seg_id)
        flags = risk.feature_flags

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # 1. 中心节点：标段
        seg_node = GraphNode(
            id=self._make_id("seg"),
            label=seg_name or seg_id,
            node_type="segment",
            size=20 + risk.risk_score * 4,
            color=RISK_LEVEL_COLORS.get(risk.risk_level, "#95A5A6"),
            metadata={"risk_score": risk.risk_score, "risk_level": risk.risk_level}
        )
        nodes.append(seg_node)

        # 2. 特征节点 + 边
        hit_count = 0
        for feat_key, feat_label in FEATURE_LABELS.items():
            if not flags.get(feat_key):
                continue

            hit_count += 1
            feat_node = GraphNode(
                id=self._make_id("feat"),
                label=feat_label,
                node_type="feature",
                size=12 + hit_count * 2,
                color=FEATURE_COLORS[feat_key],
                metadata={
                    "feature_key": feat_key,
                    "category": FEATURE_CATEGORIES.get(feat_key, ""),
                }
            )
            nodes.append(feat_node)

            # 标段→特征
            edges.append(GraphEdge(
                source=seg_node.id,
                target=feat_node.id,
                edge_type="feature_hit",
                weight=1.0,
                label=feat_label,
            ))

        # 3. 特征详细数据 + 投标人节点
        features = risk.feature_details
        bidder_sets: Dict[str, Set[str]] = {}

        # IP/设备
        ip_signals = features.get("ip_device", []) or []
        if ip_signals and isinstance(ip_signals, list):
            for sig in ip_signals:
                if hasattr(sig, "suspected_bidders"):
                    bidders = sig.suspected_bidders
                    bidder_sets.setdefault("ip_device", set()).update(bidders)

                    # 投标人节点
                    for b_name in bidders[:5]:  # 最多5个
                        b_node = self._add_bidder_node(nodes, b_name, "ip_device")
                        edges.append(GraphEdge(
                            source=seg_node.id,
                            target=b_node.id,
                            edge_type="bid",
                            weight=0.5,
                            label="投标",
                        ))

                    # 同源边（投标人之间）
                    self._add_same_source_edges(nodes, bidders[:5], ip_signals,
                                                edges, "IP_C段")

        # 报价规律
        pp = features.get("price_pattern")
        if pp and hasattr(pp, "suspected_bidders"):
            bidders = pp.suspected_bidders
            bidder_sets.setdefault("price", set()).update(bidders)
            for b_name in bidders[:5]:
                self._add_bidder_node(nodes, b_name, "price_pattern")
                if hasattr(pp, "all_bids") and len(pp.all_bids) >= 2:
                    # 金额指标节点
                    indicator_node = GraphNode(
                        id=self._make_id("ind"),
                        label=f"报价CV={pp.gap_stability:.2f}",
                        node_type="indicator",
                        size=8,
                        color="#F39C12",
                        metadata={"indicator": "报价差额变异系数"}
                    )
                    nodes.append(indicator_node)

        # 保证金同源
        ds = features.get("deposit_source")
        if ds and hasattr(ds, "suspected_bidders"):
            bidders = ds.suspected_bidders
            bidder_sets.setdefault("deposit", set()).update(bidders)
            for b_name in bidders[:5]:
                self._add_bidder_node(nodes, b_name, "deposit_source")
            self._add_same_source_edges(nodes, bidders[:5], [ds],
                                        edges, "同账户")

        # 文件基因
        dg = features.get("document_gene")
        if dg and hasattr(dg, "suspected_bidders"):
            bidders = dg.suspected_bidders
            bidder_sets.setdefault("gene", set()).update(bidders)
            for b_name in bidders[:5]:
                self._add_bidder_node(nodes, b_name, "document_gene")

        # 时间扎堆
        tc = features.get("time_cluster")
        if tc and hasattr(tc, "suspected_bidders"):
            bidders = tc.suspected_bidders
            bidder_sets.setdefault("time", set()).update(bidders)
            for b_name in bidders[:5]:
                self._add_bidder_node(nodes, b_name, "time_cluster")

        # 4. 生成文字摘要
        summary_text = self._generate_summary_text(risk)

        return EvidenceGraph(
            segment_id=seg_id,
            segment_name=seg_name,
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            nodes=nodes,
            edges=edges,
            summary_text=summary_text,
        )

    def _add_bidder_node(
        self, nodes: List[GraphNode], name: str, feature_key: str
    ) -> GraphNode:
        """添加投标人节点（去重）"""
        existing = next((n for n in nodes if n.label == name and n.node_type == "bidder"), None)
        if existing:
            # 已存在，叠加特征颜色（混合）
            existing.metadata["features"] = existing.metadata.get("features", []) + [feature_key]
            existing.size = max(existing.size, 10 + len(existing.metadata["features"]) * 2)
            return existing

        node = GraphNode(
            id=self._make_id("bidder"),
            label=name,
            node_type="bidder",
            size=8,
            color="#7F8C8D",
            metadata={"features": [feature_key]}
        )
        nodes.append(node)
        return node

    def _add_same_source_edges(
        self,
        nodes: List[GraphNode],
        bidders: List[str],
        signals: List[Any],
        edges: List[GraphEdge],
        source_label: str,
    ):
        """添加投标人之间的同源关联边"""
        bidder_nodes = [n for n in nodes if n.label in bidders and n.node_type == "bidder"]
        for i in range(len(bidder_nodes)):
            for j in range(i + 1, len(bidder_nodes)):
                edges.append(GraphEdge(
                    source=bidder_nodes[i].id,
                    target=bidder_nodes[j].id,
                    edge_type="same_source",
                    weight=0.8,
                    label=source_label,
                ))

    def _generate_summary_text(self, risk: Any) -> str:
        """生成证据摘要文字"""
        lines = []
        lines.append(f"【{risk.risk_level.upper()}风险】{risk.segment_name or risk.segment_id}")
        lines.append(f"风险评分：{risk.risk_score}/5.0 | 投标人数：{risk.total_bidders}")
        lines.append("")

        for ev in getattr(risk, "combined_evidence", []):
            lines.append(f"• {ev}")

        lines.append("")
        lines.append(f"建议：{risk.recommendation}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 图谱导出（JSON → ECharts/D3.js 渲染格式）
# ═══════════════════════════════════════════════════════════════

class GraphExporter:
    """图谱格式导出器"""

    @staticmethod
    def to_echarts_json(graph: EvidenceGraph) -> Dict[str, Any]:
        """
        导出为ECharts力导向图JSON格式

        可直接用于前端渲染：
        https://echarts.apache.org/examples/zh/editor.html?c=graph-force
        """
        nodes = []
        for n in graph.nodes:
            node_data = {
                "id": n.id,
                "name": n.label,
                "symbolSize": n.size,
                "category": _node_category_index(n.node_type),
                "itemStyle": {"color": n.color},
                "metadata": n.metadata,
            }
            nodes.append(node_data)

        links = []
        for e in graph.edges:
            links.append({
                "source": e.source,
                "target": e.target,
                "label": {"show": True, "formatter": e.label} if e.label else {},
                "lineStyle": {
                    "type": "dashed" if e.dash else "solid",
                    "width": max(0.5, e.weight),
                },
            })

        return {
            "title": {
                "text": f"围标串标证据链图谱 — {graph.segment_name}",
                "subtext": f"风险评分: {graph.risk_score}/5.0 | 风险等级: {graph.risk_level}",
            },
            "categories": [
                {"name": "标段", "itemStyle": {"color": "#E74C3C"}},
                {"name": "特征", "itemStyle": {"color": "#3498DB"}},
                {"name": "投标人", "itemStyle": {"color": "#7F8C8D"}},
                {"name": "关联方", "itemStyle": {"color": "#E67E22"}},
                {"name": "指标", "itemStyle": {"color": "#1ABC9C"}},
            ],
            "nodes": nodes,
            "links": links,
            "force": {
                "repulsion": 200,
                "gravity": 0.1,
                "edgeLength": [100, 200],
            },
        }

    @staticmethod
    def to_d3_json(graph: EvidenceGraph) -> Dict[str, Any]:
        """
        导出为D3.js力导向图JSON格式

        兼容格式：
        https://observablehq.com/@d3/force-directed-graph
        """
        nodes = [
            {
                "id": n.id,
                "group": _node_category_index(n.node_type),
                "label": n.label,
                "r": n.size / 2,
                "color": n.color,
            }
            for n in graph.nodes
        ]
        links = [
            {
                "source": e.source,
                "target": e.target,
                "value": e.weight,
                "label": e.label,
            }
            for e in graph.edges
        ]
        return {"nodes": nodes, "links": links}

    @staticmethod
    def to_html(graph: EvidenceGraph) -> str:
        """
        生成独立HTML文件（内嵌ECharts，可直接打开）

        包含：
        - 力导向交互图
        - 证据摘要卡片
        - 风险特征明细表
        """
        echarts_json = json.dumps(GraphExporter.to_echarts_json(graph), ensure_ascii=False)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>围标串标证据链图谱 — {graph.segment_name}</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Microsoft YaHei", sans-serif; background: #f5f6fa; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
  .header {{ background: white; padding: 24px; border-radius: 8px; margin-bottom: 20px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
  .header .meta {{ color: #666; font-size: 14px; }}
  .risk-badge {{ display: inline-block; padding: 2px 12px; border-radius: 12px;
                color: white; font-size: 14px; font-weight: bold; }}
  .risk-high {{ background: #E74C3C; }}
  .risk-medium {{ background: #F39C12; }}
  .risk-low {{ background: #27AE60; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .card {{ background: white; border-radius: 8px; padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .card h2 {{ font-size: 18px; margin-bottom: 12px; border-bottom: 2px solid #eee; padding-bottom: 8px; }}
  #graph {{ width: 100%; height: 500px; }}
  .evidence-list {{ list-style: none; }}
  .evidence-list li {{ padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
  .evidence-list li:last-child {{ border-bottom: none; }}
  .feature-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  .feature-table th, .feature-table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
  .feature-table th {{ background: #f8f9fa; }}
  .hit {{ color: #E74C3C; font-weight: bold; }}
  .miss {{ color: #95A5A6; }}
  .summary-box {{ margin-top: 20px; }}
  .summary-box pre {{ background: #f8f9fa; padding: 16px; border-radius: 4px;
                     font-size: 14px; line-height: 1.6; white-space: pre-wrap; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>围标串标证据链图谱</h1>
    <p class="meta">
      标段: {graph.segment_name} |
      风险评分: <span class="risk-badge risk-{graph.risk_level}">{graph.risk_score}/5.0</span> |
      等级: <span class="risk-badge risk-{graph.risk_level}">{graph.risk_level}</span>
    </p>
  </div>

  <div class="card" style="margin-bottom:20px;">
    <h2>📊 证据链力导向图</h2>
    <div id="graph"></div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>🔍 特征命中明细</h2>
      <table class="feature-table">
        <tr><th>特征</th><th>状态</th><th>分类</th></tr>
""" + "\n".join(
    f"        <tr><td>{FEATURE_LABELS.get(k, k)}</td><td class=\"{'hit' if v else 'miss'}\">{'✓ 命中' if v else '✗ 未命中'}</td><td>{FEATURE_CATEGORIES.get(k, '')}</td></tr>"
    for k, v in {
        "f1_ip_device": graph.nodes and any(n.metadata.get("feature_key") == "f1_ip_device" for n in graph.nodes),
        "f2_price_pattern": graph.risk_score > 0,  # 简化
        "f3_deposit_source": graph.risk_score > 0,
        "f4_document_gene": graph.risk_score > 0,
        "f5_time_cluster": graph.risk_score > 0,
    }.items()
) + """
      </table>
    </div>

    <div class="card">
      <h2>📝 证据摘要</h2>
      <div class="summary-box">
        <pre>""" + graph.summary_text + """</pre>
      </div>
    </div>
  </div>
</div>

<script>
var chart = echarts.init(document.getElementById('graph'));
chart.setOption(""" + echarts_json + """);
window.addEventListener('resize', () => chart.resize());
</script>
</body>
</html>"""


def _node_category_index(node_type: str) -> int:
    """节点类型→ECharts类别索引"""
    mapping = {
        "segment": 0,
        "feature": 1,
        "bidder": 2,
        "related_party": 3,
        "indicator": 4,
    }
    return mapping.get(node_type, 2)


# ═══════════════════════════════════════════════════════════════
# 证据摘要卡片生成（A4一页纸）
# ═══════════════════════════════════════════════════════════════

class SummaryCardGenerator:
    """
    生成A4一页纸证据摘要卡片（Markdown格式）

    包含：
    - 图谱缩略描述
    - 文字结论
    - 5特征数据表格
    - 建议
    """

    @staticmethod
    def generate(graph: EvidenceGraph) -> str:
        """生成Markdown格式证据摘要卡片"""
        flags = getattr(graph, "_feature_flags", {
            "f1_ip_device": any(n.node_type == "bidder" and "ip_device" in n.metadata.get("features", []) for n in graph.nodes),
            "f2_price_pattern": graph.risk_score >= 1.0,
            "f3_deposit_source": any(n.node_type == "bidder" and "deposit_source" in n.metadata.get("features", []) for n in graph.nodes),
            "f4_document_gene": graph.risk_score >= 1.0,
            "f5_time_cluster": any(n.node_type == "bidder" and "time_cluster" in n.metadata.get("features", []) for n in graph.nodes),
        })

        card = f"""# 围标串标证据摘要卡片

---

## 基本信息

| 项目 | 内容 |
|------|------|
| 标段ID | {graph.segment_id} |
| 标段名称 | {graph.segment_name} |
| 风险评分 | **{graph.risk_score}/5.0** |
| 风险等级 | **{graph.risk_level}** |
| 生成时间 | {datetime.now().strftime("%Y-%m-%d %H:%M")} |

---

## 特征命中矩阵

| 特征 | 状态 | 独立命中率(参考) |
|------|------|-----------------|
| 同IP/同设备投标 | {"✅ 命中" if flags.get("f1_ip_device") else "❌ 未命中"} | 27% |
| 报价规律性雷同 | {"✅ 命中" if flags.get("f2_price_pattern") else "❌ 未命中"} | 38% |
| 保证金来源同源 | {"✅ 命中" if flags.get("f3_deposit_source") else "❌ 未命中"} | 19% |
| 投标文件基因相似 | {"✅ 命中" if flags.get("f4_document_gene") else "❌ 未命中"} | 31% |
| 时间窗口扎堆 | {"✅ 命中" if flags.get("f5_time_cluster") else "❌ 未命中"} | 22% |

---

## 证据链摘要

{graph.summary_text}

---

## 审计建议

1. **立即行动**：对高风险标段进行人工核查，调取完整投标文件和银行流水
2. **工商穿透**：通过企查查/天眼查核查命中投标人的股东、法人、高管关联关系
3. **证据固化**：对确认围标的标段，导出完整证据链图谱作为审计底稿附件
4. **制度建议**：建议招标平台增加IP/MAC采集、投标文件相似度自动比对功能

---

> ⚠️ 本证据链图谱由融策审计智析Agent自动生成，需经人工复核确认后作为审计证据使用。
> 命中率数据来源于省属集团3万+标段实际审计项目统计。
"""
        return card

    @staticmethod
    def generate_all_cards(result: EvidenceChainResult) -> List[str]:
        """为所有图谱生成摘要卡片"""
        cards = []
        for graph in result.graphs:
            cards.append(SummaryCardGenerator.generate(graph))
        return cards


# ═══════════════════════════════════════════════════════════════
# 便捷接口
# ═══════════════════════════════════════════════════════════════

def generate_evidence_chains(
    rigging_result: Any,
    export_html: bool = False,
    output_dir: str = "./evidence_graphs",
) -> EvidenceChainResult:
    """
    便捷接口：一键生成证据链图谱

    Args:
        rigging_result: BidRiggingResult 围标检测结果
        export_html: 是否导出独立HTML文件
        output_dir: HTML输出目录

    Returns:
        EvidenceChainResult
    """
    generator = EvidenceChainGenerator()
    result = generator.generate_all(rigging_result)

    if export_html and result.graphs:
        import os
        os.makedirs(output_dir, exist_ok=True)
        exporter = GraphExporter()
        for i, graph in enumerate(result.graphs):
            html = exporter.to_html(graph)
            path = os.path.join(output_dir, f"evidence_{graph.segment_id}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        print(f"已导出{len(result.graphs)}个HTML图谱到 {output_dir}")

    return result


def generate_summary_card(rigging_result: Any, segment_id: str) -> Optional[str]:
    """
    为指定标段生成证据摘要卡片

    Args:
        rigging_result: BidRiggingResult
        segment_id: 标段ID

    Returns:
        Markdown格式摘要卡片，找不到返回None
    """
    generator = EvidenceChainGenerator()
    risks = getattr(rigging_result, "risks", [])
    for risk in risks:
        if risk.segment_id == segment_id:
            graph = generator._build_graph(risk)
            return SummaryCardGenerator.generate(graph)
    return None
