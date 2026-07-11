"""
workpaper_scorer.models — 数据模型与常量定义

所有评分相关的数据结构、枚举和关键词库集中管理。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── 审计专业常量 ─────────────────────────────────────────────

AUDIT_ASSERTIONS: List[str] = [
    "存在", "发生",
    "完整性",
    "准确性",
    "截止",
    "计价", "分摊", "计价和分摊",
    "权利", "义务", "权利和义务",
    "列报", "披露",
]

SAMPLING_METHODS: List[str] = [
    "随机抽样", "分层抽样", "大额优先", "PPS抽样",
    "系统抽样", "金额降序", "按金额", "选取", "抽取",
    "等距抽样", "货币单位抽样", "整群抽样",
]

TEST_PROCEDURE_VERBS: List[str] = [
    "获取", "核对", "检查", "验证", "比较",
    "重新计算", "函证", "盘点", "观察", "询问",
    "分析性复核", "重新执行", "扫描", "审阅",
]

DOCUMENT_TYPES: List[str] = [
    "合同", "发票", "出库单", "签收单", "入库单",
    "银行对账单", "凭证", "明细账", "总账",
    "权证", "评估报告", "验收单", "付款申请单",
    "采购订单", "销售订单", "对账单",
]

EVIDENCE_KEYWORDS: List[str] = [
    "依据", "证据", "支撑", "经检查", "经核查",
    "经抽查", "来源", "详见索引", "参照", "根据",
    "证明", "证实", "确认", "核实",
]

ASSERTION_KEYWORDS: List[str] = [
    "认定", "验证", "目标", "程序目标",
    "审计目标", "测试目标",
]

EXCEPTION_KEYWORDS: List[str] = [
    "差异", "异常", "不符", "例外", "偏差",
    "不一致", "超过", "低于", "偏离",
]

# ── 枚举 ──────────────────────────────────────────────────────

class Grade(str, Enum):
    """底稿质量等级"""
    A = "A"  # 优秀 ≥90
    B = "B"  # 良好 80-89
    C = "C"  # 合格 70-79
    D = "D"  # 不足 60-69
    F = "F"  # 不合格 <60


class ScoreDimension(str, Enum):
    """评分维度"""
    TARGET_CLARITY = "A_目标明确性"
    PROCESS_CLARITY = "B_过程清晰性"
    EVIDENCE_SUFFICIENCY = "C_证据充分性"
    INDEX_COMPLETENESS = "D_索引完整性"


class PenaltyCode(str, Enum):
    """扣分项代码"""
    NUMBERS_WITHOUT_ANALYSIS = "E_有数无说"
    CONCLUSION_WITHOUT_EVIDENCE = "F_有论无据"
    COPYCAT_SUSPICION = "G_照抄嫌疑"


# ── 输入数据模型 ──────────────────────────────────────────────

@dataclass
class WorkpaperField:
    """
    底稿的结构化字段内容。
    当 Agent 按结构化 JSON 输出时使用此模型。
    """
    target: str = ""
    """程序目标：写明验证哪项/哪些认定"""

    sampling_method: str = ""
    """抽样方法描述"""

    selection_logic: str = ""
    """选取逻辑说明"""

    sample_size: int = 0
    """样本量"""

    coverage_ratio: str = ""
    """覆盖比例，如 '72%'"""

    test_procedures: List[str] = field(default_factory=list)
    """测试步骤列表"""

    documents_reviewed: List[str] = field(default_factory=list)
    """已核查的文件类型"""

    conclusion_statement: str = ""
    """结论文字"""

    evidence_refs: List[str] = field(default_factory=list)
    """证据索引列表"""

    exceptions: List[Dict[str, str]] = field(default_factory=list)
    """例外事项: [{description, resolution, impact}]"""

    cross_refs: List[str] = field(default_factory=list)
    """交叉引用索引列表"""

    ledger_ref: str = ""
    """明细表索引"""

    contract_refs: List[str] = field(default_factory=list)
    """合同索引"""


@dataclass
class Workpaper:
    """
    单张审计底稿的完整输入。

    支持两种输入模式：
    1. 结构化模式：填充 `fields` (WorkpaperField)
    2. 非结构化模式：填充 `raw_content` (全文 Markdown/纯文本)
       + 尽量填充 `target`, `process`, `conclusion` 三个关键字段

    两种模式可混合使用 —— scorer 内部会优先使用结构化字段，
    缺失时回退到 raw_content 文本分析。
    """
    id: str
    """底稿编号，如 'WP-2026-001'"""

    title: str = ""
    """底稿标题 / 程序名称"""

    # 结构化字段（优先级高）
    fields: Optional[WorkpaperField] = None
    """结构化输出字段"""

    # 半结构化关键字段（raw_content 之外的快捷填充）
    target: str = ""
    """程序目标段"""

    process: str = ""
    """过程描述段"""

    conclusion: str = ""
    """结论段"""

    # 全文本（兜底）
    raw_content: str = ""
    """底稿全文（Markdown / 纯文本）"""

    # 索引
    cross_refs: List[str] = field(default_factory=list)
    """交叉引用列表（合并自 fields.cross_refs 或手动指定）"""

    # 元信息
    metadata: Dict[str, Any] = field(default_factory=dict)
    """扩展元信息（科目、项目、年度等）"""

    def get_full_text(self) -> str:
        """返回用于文本分析的完整内容"""
        parts = []
        if self.target:
            parts.append(f"【目标】{self.target}")
        if self.process:
            parts.append(f"【过程】{self.process}")
        if self.conclusion:
            parts.append(f"【结论】{self.conclusion}")
        if self.fields:
            parts.append(json.dumps(self.fields.__dict__, ensure_ascii=False, default=str))
        if self.raw_content:
            parts.append(self.raw_content)
        return "\n".join(parts)

    def get_evidence_refs(self) -> List[str]:
        """合并所有来源的证据引用"""
        refs = list(self.cross_refs)
        if self.fields:
            refs.extend(self.fields.evidence_refs)
            refs.extend(self.fields.cross_refs)
        return list(set(refs))


@dataclass
class PreviousYearWorkpaper:
    """上年度同项目底稿（用于照抄检测）"""
    id: str
    raw_content: str
    year: str


# ── 输出数据模型 ──────────────────────────────────────────────

@dataclass
class RiskFlag:
    """风险标记"""
    code: str
    """风险代码"""
    level: str  # "high" | "medium" | "low"
    message: str
    """风险描述"""
    suggestion: str = ""
    """改进建议"""


@dataclass
class PenaltyItem:
    """扣分项详情"""
    code: PenaltyCode
    points_deducted: float  # 负数
    reason: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ImprovementItem:
    """改进事项"""
    priority: str  # "high" | "medium" | "low"
    dimension: ScoreDimension
    item: str
    """改进内容"""
    action: str
    """建议操作"""


@dataclass
class ScoreReport:
    """
    底稿质量评分报告（完整输出）

    提供 to_dict() / to_json() 用于序列化到 LangGraph Checkpoint。
    """

    # 基础信息
    workpaper_id: str
    workpaper_title: str = ""

    # 总分
    final_score: float = 0.0
    grade: Grade = Grade.F
    passed_l1: bool = False
    """L1 复核通过（≥70分）"""

    # 维度得分
    dimension_scores: Dict[str, float] = field(default_factory=lambda: {
        "A_目标明确性": 0,
        "B_过程清晰性": 0,
        "C_证据充分性": 0,
        "D_索引完整性": 0,
    })

    # 扣分明细
    penalties: List[PenaltyItem] = field(default_factory=list)

    # 风险与改进
    risk_flags: List[RiskFlag] = field(default_factory=list)
    improvement_checklist: List[ImprovementItem] = field(default_factory=list)

    # 年对年对比（可选）
    yoy_report: Optional[YoYReport] = None

    # 元信息
    scorer_version: str = "1.0.0"
    scored_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（适合 JSON / LangGraph Checkpoint 存储）"""
        return {
            "workpaper_id": self.workpaper_id,
            "workpaper_title": self.workpaper_title,
            "final_score": self.final_score,
            "grade": self.grade.value,
            "passed_l1": self.passed_l1,
            "dimension_scores": self.dimension_scores,
            "penalties": [
                {
                    "code": p.code.value,
                    "points_deducted": p.points_deducted,
                    "reason": p.reason,
                    "details": p.details,
                }
                for p in self.penalties
            ],
            "risk_flags": [
                {"code": r.code, "level": r.level, "message": r.message, "suggestion": r.suggestion}
                for r in self.risk_flags
            ],
            "improvement_checklist": [
                {"priority": i.priority, "dimension": i.dimension.value, "item": i.item, "action": i.action}
                for i in self.improvement_checklist
            ],
            "yoy_report": self.yoy_report.to_dict() if self.yoy_report else None,
            "scorer_version": self.scorer_version,
            "scored_at": self.scored_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def summary(self) -> str:
        """生成人类可读的评分摘要"""
        lines = [
            f"底稿编号: {self.workpaper_id}",
            f"底稿标题: {self.workpaper_title}",
            f"最终得分: {self.final_score:.1f} / 100",
            f"质量等级: {self.grade.value}",
            f"L1通过:   {'✅ 通过' if self.passed_l1 else '❌ 退回修改'}",
            "",
            "维度得分:",
        ]
        for dim, score in self.dimension_scores.items():
            bar = "█" * int(score / 5) + "░" * (5 - int(score / 5))
            lines.append(f"  {dim}: {score:.0f}/25 {bar}")

        if self.penalties:
            lines.append("")
            lines.append("扣分项:")
            for p in self.penalties:
                lines.append(f"  {p.code.value}: {p.points_deducted:.0f}分 — {p.reason}")

        if self.risk_flags:
            lines.append("")
            lines.append("风险标记:")
            for r in self.risk_flags:
                icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(r.level, "⚪")
                lines.append(f"  {icon} [{r.level}] {r.message}")

        if self.improvement_checklist:
            lines.append("")
            lines.append("改进清单:")
            for i in self.improvement_checklist:
                icon = {"high": "❗", "medium": "⚠️", "low": "💡"}.get(i.priority, "•")
                lines.append(f"  {icon} {i.item} → {i.action}")

        return "\n".join(lines)


@dataclass
class YoYReport:
    """年度对比报告（防照抄检测）"""
    similarity_score: float
    """文本相似度 0.0-1.0"""
    has_program_changes: bool
    """程序是否有变化"""
    risk_mismatch_detected: bool
    """是否存在风险评估变化但程序未变的不匹配"""
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "similarity_score": self.similarity_score,
            "has_program_changes": self.has_program_changes,
            "risk_mismatch_detected": self.risk_mismatch_detected,
            "details": self.details,
        }
