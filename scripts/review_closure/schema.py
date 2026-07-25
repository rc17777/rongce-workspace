# -*- coding: utf-8 -*-
"""
审盾闭环层 - 数据模型 v1.0
============================
核心数据结构：
  - ReasoningTrail: 每条发现的推演过程
  - ReviewFinding: 带推理链的复核发现
  - QCReviewItem: 质控审核记录
  - QCPipeline: 整个质控管道状态
"""

from __future__ import annotations
import json, hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Literal
from enum import Enum

TZ = timezone(timedelta(hours=8))

# ============================================================
# 推演过程 - 一条发现怎么来的
# ============================================================

class ReasoningStepType(str, Enum):
    """推理步骤类型"""
    DATA_LOAD = "数据加载"          # 加载了哪份数据
    RULE_MATCH = "规则匹配"         # 命中了什么规则/模式
    RAG_QUERY = "知识库查询"        # 查了RAG的什么内容
    CALCULATION = "计算推演"        # 中间计算过程
    AI_JUDGMENT = "AI判断"         # AI推理判断
    CROSS_VERIFY = "交叉验证"      # 多来源交叉验证
    HUMAN_INPUT = "人工输入"       # 人工补充的信息
    FP_SUPPRESS = "误报抑制"       # 误报规则命中记录


class ReasoningStep:
    """推理链中的一步"""
    
    def __init__(self, 
                 step_type: ReasoningStepType,
                 description: str,
                 input_data: Any = None,
                 output_data: Any = None,
                 rule_ref: Optional[str] = None,
                 source_ref: Optional[str] = None,
                 confidence: Optional[float] = None):
        self.step_type = step_type
        self.description = description
        self.input_data = input_data          # 输入了什么
        self.output_data = output_data        # 输出了什么
        self.rule_ref = rule_ref              # 引用的规则编号
        self.source_ref = source_ref          # 数据来源引用
        self.confidence = confidence          # 本步置信度 0-1
        self.timestamp = datetime.now(TZ).isoformat()
    
    def to_dict(self) -> Dict:
        d = {
            "step_type": self.step_type.value,
            "description": self.description,
            "timestamp": self.timestamp,
        }
        if self.input_data is not None:
            d["input_data"] = self._safe_str(self.input_data)
        if self.output_data is not None:
            d["output_data"] = self._safe_str(self.output_data)
        if self.rule_ref:
            d["rule_ref"] = self.rule_ref
        if self.source_ref:
            d["source_ref"] = self.source_ref
        if self.confidence is not None:
            d["confidence"] = round(self.confidence, 2)
        return d
    
    @staticmethod
    def _safe_str(v: Any, max_len: int = 500) -> str:
        s = str(v)
        if len(s) > max_len:
            return s[:max_len] + f"...[截断, 原文{len(s)}字符]"
        return s


class ReasoningTrail:
    """完整推演过程 - 一条发现的完整推导链条"""
    
    def __init__(self, finding_id: str):
        self.finding_id = finding_id
        self.steps: List[ReasoningStep] = []
        self.data_sources: List[str] = []       # 引用的数据源
        self.rules_applied: List[str] = []      # 应用的规则列表
        self.rag_references: List[str] = []     # RAG知识库引用
        self.fp_checks: List[str] = []          # 误报抑制检查记录
        self.overall_confidence: Optional[float] = None
    
    @property
    def step_count(self) -> int:
        return len(self.steps)
    
    def add_step(self, step: ReasoningStep):
        """添加一步推理"""
        self.steps.append(step)
        if step.rule_ref and step.rule_ref not in self.rules_applied:
            self.rules_applied.append(step.rule_ref)
        if step.source_ref and step.source_ref not in self.data_sources:
            self.data_sources.append(step.source_ref)
        if step.step_type == ReasoningStepType.RAG_QUERY and step.output_data:
            ref = str(step.output_data)[:100]
            if ref not in self.rag_references:
                self.rag_references.append(ref)
        if step.step_type == ReasoningStepType.FP_SUPPRESS:
            self.fp_checks.append(step.description)
    
    def add_data_load(self, source: str, description: str):
        """记录数据加载步骤"""
        self.add_step(ReasoningStep(
            ReasoningStepType.DATA_LOAD, description,
            source_ref=source
        ))
    
    def add_rule_match(self, rule: str, description: str, input_data=None, output_data=None):
        """记录规则匹配步骤"""
        self.add_step(ReasoningStep(
            ReasoningStepType.RULE_MATCH, description,
            rule_ref=rule, input_data=input_data, output_data=output_data
        ))
    
    def add_rag_query(self, query: str, result: str, source: str):
        """记录知识库查询"""
        self.add_step(ReasoningStep(
            ReasoningStepType.RAG_QUERY, f"知识库查询: {query}",
            input_data=query, output_data=result[:200],
            source_ref=source
        ))
    
    def add_calculation(self, description: str, formula: str, result: str):
        """记录计算过程"""
        self.add_step(ReasoningStep(
            ReasoningStepType.CALCULATION, description,
            input_data=formula, output_data=result
        ))
    
    def add_judgment(self, description: str, input_data: Any, output_data: Any, confidence: float = None):
        """记录AI判断"""
        self.add_step(ReasoningStep(
            ReasoningStepType.AI_JUDGMENT, description,
            input_data=input_data, output_data=output_data,
            confidence=confidence
        ))
    
    def add_cross_verify(self, description: str, source_a: str, source_b: str, result: str):
        """记录交叉验证"""
        self.add_step(ReasoningStep(
            ReasoningStepType.CROSS_VERIFY, description,
            input_data=f"来源A: {source_a} | 来源B: {source_b}",
            output_data=result
        ))
    
    def add_fp_check(self, rule: str, description: str, result: str):
        """记录误报抑制检查"""
        self.add_step(ReasoningStep(
            ReasoningStepType.FP_SUPPRESS, description,
            rule_ref=rule, output_data=result
        ))
    
    def set_confidence(self, confidence: float):
        """设置整体置信度"""
        self.overall_confidence = round(confidence, 2)
    
    def to_dict(self) -> Dict:
        d = {
            "finding_id": self.finding_id,
            "steps": [s.to_dict() for s in self.steps],
            "step_count": self.step_count,
            "data_sources": self.data_sources,
            "rules_applied": self.rules_applied,
            "rag_references": self.rag_references,
            "fp_checks": self.fp_checks,
        }
        if self.overall_confidence is not None:
            d["overall_confidence"] = self.overall_confidence
        return d
    
    def to_markdown(self) -> str:
        """生成可读的推演过程Markdown"""
        lines = [
            f"## 🔍 推演过程: {self.finding_id}",
            f"",
            f"**步骤数**: {len(self.steps)} | **置信度**: {self.overall_confidence or 'N/A'}",
            f"",
        ]
        
        if self.data_sources:
            lines.append("**引用数据源**:")
            for s in self.data_sources:
                lines.append(f"- 📄 {s}")
            lines.append("")
        
        if self.rules_applied:
            lines.append("**应用规则**:")
            for r in self.rules_applied:
                lines.append(f"- ⚙️ {r}")
            lines.append("")
        
        if self.rag_references:
            lines.append("**RAG知识库引用**:")
            for r in self.rag_references[:5]:
                lines.append(f"- 📚 {r}")
            if len(self.rag_references) > 5:
                lines.append(f"  ...还有{len(self.rag_references)-5}条")
            lines.append("")
        
        if self.fp_checks:
            lines.append("**误报抑制检查**:")
            for f in self.fp_checks:
                lines.append(f"- ✅ {f}")
            lines.append("")
        
        lines.append("**推理步骤**:")
        lines.append("")
        for i, step in enumerate(self.steps, 1):
            sd = step.to_dict()
            lines.append(f"### 步骤 {i}: {sd['step_type']}")
            lines.append(f"**描述**: {sd['description']}")
            if 'input_data' in sd:
                lines.append(f"**输入**: {sd['input_data'][:200]}")
            if 'output_data' in sd:
                lines.append(f"**输出**: {sd['output_data'][:200]}")
            if 'rule_ref' in sd:
                lines.append(f"**规则**: {sd['rule_ref']}")
            if 'source_ref' in sd:
                lines.append(f"**来源**: {sd['source_ref']}")
            if 'confidence' in sd:
                lines.append(f"**本步置信度**: {sd['confidence']}")
            lines.append("")
        
        return '\n'.join(lines)


# ============================================================
# 带推理链的复核发现
# ============================================================

class ReviewFinding:
    """带完整推理链的复核发现"""
    
    def __init__(self,
                 finding_id: str,
                 dimension: str,
                 severity: Literal["P0", "P1", "P2"],
                 message: str,
                 category: str = "正文复核",
                 location: str = "",
                 suggestion: str = "",
                 amount: Optional[float] = None,
                 ):
        self.finding_id = finding_id
        self.dimension = dimension
        self.severity = severity
        self.message = message
        self.category = category
        self.location = location
        self.suggestion = suggestion
        self.amount = amount
        self.trail = ReasoningTrail(finding_id)
        self.timestamp = datetime.now(TZ).isoformat()
        self.qc_status: QCStatus = QCStatus.PENDING
        self.qc_comment: Optional[str] = None
        self.qc_reviewer: Optional[str] = None
        self.qc_reviewed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        d = {
            "finding_id": self.finding_id,
            "dimension": self.dimension,
            "severity": self.severity,
            "message": self.message,
            "category": self.category,
            "location": self.location,
            "suggestion": self.suggestion,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "trail": self.trail.to_dict(),
            "qc_status": self.qc_status.value,
        }
        if self.qc_comment:
            d["qc_comment"] = self.qc_comment
        if self.qc_reviewer:
            d["qc_reviewer"] = self.qc_reviewer
        if self.qc_reviewed_at:
            d["qc_reviewed_at"] = self.qc_reviewed_at
        return d


# ============================================================
# 质控状态
# ============================================================

class QCStatus(str, Enum):
    PENDING = "待审核"          # 刚生成，等待质控
    IN_REVIEW = "审核中"        # 正在被质控人员审查
    ACCEPTED = "已确认"         # 质控确认问题有效
    REJECTED = "已驳回"         # 质控认为这是误报
    MODIFIED = "已修改"         # 质控修改了问题描述
    ARCHIVED = "已归档"         # 最终归档


# ============================================================
# 质控管道状态
# ============================================================

class QCPipeline:
    """整个质控管道"""
    
    def __init__(self, report_name: str, pipeline_id: str = None):
        self.pipeline_id = pipeline_id or self._gen_id()
        self.report_name = report_name
        self.findings: List[ReviewFinding] = []
        self.status: QCStatus = QCStatus.PENDING
        self.created_at = datetime.now(TZ).isoformat()
        self.updated_at = self.created_at
        self.completed_at: Optional[str] = None
        self.report_path: Optional[str] = None
        self.raw_report_path: Optional[str] = None
        self.metadata: Dict = {}
    
    @staticmethod
    def _gen_id() -> str:
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        h = hashlib.md5(ts.encode()).hexdigest()[:6]
        return f"QC-{ts}-{h}"
    
    def add_finding(self, finding: ReviewFinding):
        self.findings.append(finding)
        self.updated_at = datetime.now(TZ).isoformat()
    
    def add_findings(self, findings: List[ReviewFinding]):
        self.findings.extend(findings)
        self.updated_at = datetime.now(TZ).isoformat()
    
    def get_summary(self) -> Dict:
        summary = {
            "pipeline_id": self.pipeline_id,
            "report_name": self.report_name,
            "status": self.status.value,
            "total_findings": len(self.findings),
            "severity_breakdown": {"P0": 0, "P1": 0, "P2": 0},
            "qc_status_breakdown": {},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        for f in self.findings:
            s = f.severity
            summary["severity_breakdown"][s] = summary["severity_breakdown"].get(s, 0) + 1
            qs = f.qc_status.value
            summary["qc_status_breakdown"][qs] = summary["qc_status_breakdown"].get(qs, 0) + 1
        return summary
    
    def to_dict(self) -> Dict:
        return {
            "pipeline_id": self.pipeline_id,
            "report_name": self.report_name,
            "status": self.status.value,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.get_summary(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "report_path": self.report_path,
            "raw_report_path": self.raw_report_path,
            "metadata": self.metadata,
        }