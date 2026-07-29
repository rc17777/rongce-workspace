"""
4步标准化审计文本分析流水线

步骤映射：
  Step 1: 数据归集统一格式 → data_collection
  Step 2: 规则配置对标风险 → rule_configuration
  Step 3: 批量分析疑点初筛 → data_analysis
  Step 4: 人机核验固化证据 → human_review

对应 LangGraph 工作流节点，支持独立运行或嵌入编排。
"""

import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .utils import (
    CoverageReport, AuditFinding, RiskFlag,
    infer_audit_type, infer_focus_areas,
)
from .hotword import TextHotwordAnalyzer
from .similarity import TextSimilarityComparator
from .contract import ContractFieldExtractor
from .personnel import PersonnelProfileChecker
from .budget import BudgetComplianceScanner
from .simulator_duality import SimulatorDualityEngine, generate_simulator_inferences
from .benford import BenfordAnalyzer
from .supplier_fingerprint import SupplierFingerprintEngine
from .timeline_anomaly import TimelineAnomalyDetector
from .contract_change_trajectory import ContractChangeTrajectoryAnalyzer
from .bid_rigging_detector import BidRiggingDetector
from .evidence_chain_graph import EvidenceChainGenerator, SummaryCardGenerator


@dataclass
class PipelineState:
    """流水线状态（对应LangGraph State）"""
    # 输入
    project_name: str = ""
    project_type: str = ""  # economic_responsibility | budget | project | subsidy | ...
    source_files: List[str] = field(default_factory=list)

    # Step 1: 数据归集
    raw_texts: Dict[str, List[str]] = field(default_factory=dict)  # type -> texts
    coverage: Optional[CoverageReport] = None

    # Step 2: 规则配置
    rule_set: Dict[str, Any] = field(default_factory=dict)
    audit_focus: List[str] = field(default_factory=list)

    # Step 3: 分析结果
    hotword_result: Optional[Dict] = None
    similarity_result: Optional[Dict] = None
    contract_result: Optional[Dict] = None
    personnel_result: Optional[Dict] = None
    budget_result: Optional[Dict] = None

    # v5: 模拟器推理
    simulator_inferences: Dict[str, List[Dict]] = field(default_factory=dict)

    # v7: 统计/行为分析结果
    benford_result: Optional[Dict] = None
    fingerprint_result: Optional[Dict] = None
    timeline_result: Optional[Dict] = None
    change_trajectory_result: Optional[Dict] = None

    # v9: 围标串标检测结果
    bid_rigging_result: Optional[Dict] = None
    evidence_chain_result: Optional[Dict] = None

    # Step 4: 人机核验
    risk_findings: List[AuditFinding] = field(default_factory=list)
    human_review_task: Optional[Dict] = None
    human_feedback: List[Dict] = field(default_factory=list)
    confirmed_evidence: List[Dict] = field(default_factory=list)
    false_positives: List[Dict] = field(default_factory=list)

    # 元信息
    current_step: str = "init"
    errors: List[str] = field(default_factory=list)


class AuditTextPipeline:
    """审计文本分析4步流水线"""

    def __init__(self, state: Optional[PipelineState] = None):
        self.state = state or PipelineState()
        self._hotword = TextHotwordAnalyzer()
        self._similarity = TextSimilarityComparator()
        self._contract = ContractFieldExtractor()
        self._personnel = PersonnelProfileChecker()
        self._budget = BudgetComplianceScanner()
        self._simulator = SimulatorDualityEngine()
        self._benford = BenfordAnalyzer()
        self._fingerprint = SupplierFingerprintEngine()
        self._timeline = TimelineAnomalyDetector()
        self._change_traj = ContractChangeTrajectoryAnalyzer()
        self._bid_rigging = BidRiggingDetector()
        self._evidence_chain = EvidenceChainGenerator()

    # ── Step 1: 数据归集 ──────────────────────────────────

    def step1_data_collection(
        self,
        source_files: List[str],
        project_name: str = "",
        project_type: str = "",
        expected_files: Optional[int] = None,
    ) -> CoverageReport:
        """
        Step 1: 数据归集统一格式

        读取源文件，分类为不同类型（会议纪要/合同/报销凭证/人员名单等），
        输出覆盖率报告。
        """
        self.state.current_step = "data_collection"
        self.state.project_name = project_name
        self.state.source_files = source_files

        # 文件分类
        categories = {
            "meeting_minutes": [],
            "contracts": [],
            "expense_records": [],
            "personnel_lists": [],
            "other": [],
        }

        for filepath in source_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(filepath, "r", encoding="gbk") as f:
                        content = f.read()
                except Exception as e:
                    self.state.errors.append(f"无法读取 {filepath}: {e}")
                    continue
            except FileNotFoundError:
                self.state.errors.append(f"文件不存在: {filepath}")
                continue

            # 自动分类
            category = self._classify_file(filepath, content)
            categories[category].append(content)

        self.state.raw_texts = {k: v for k, v in categories.items() if v}

        # 覆盖率报告
        actual = len(source_files)
        expected = expected_files or actual

        self.state.coverage = CoverageReport(
            expected_count=expected,
            actual_count=actual,
            coverage_pct=actual / expected * 100 if expected > 0 else 100,
            missing_items=[] if actual >= expected else [
                f"期望{expected}份，实收{actual}份"
            ],
            data_quality_issues=self.state.errors.copy(),
        )

        # 推断项目类型
        all_texts = []
        for texts in categories.values():
            all_texts.extend(texts)
        if not self.state.project_type and all_texts:
            self.state.project_type = project_type or infer_audit_type(all_texts)

        return self.state.coverage

    def _classify_file(self, filepath: str, content: str) -> str:
        """自动分类文件类型"""
        filename = Path(filepath).name.lower()

        if any(kw in filename for kw in ["会议", "纪要", "纪要", "meeting"]):
            return "meeting_minutes"
        if any(kw in filename for kw in ["合同", "协议", "contract"]):
            return "contracts"
        if any(kw in filename for kw in ["凭证", "报销", "发票", "expense", "付款"]):
            return "expense_records"
        if any(kw in filename for kw in ["名单", "人员", "花名册", "personnel", "员工"]):
            return "personnel_lists"

        # 内容特征分类
        if "合同编号" in content or "甲方" in content:
            return "contracts"
        if "报销" in content or "费用" in content:
            return "expense_records"
        if "会议" in content[:200]:
            return "meeting_minutes"
        if "姓名" in content and "身份证" in content:
            return "personnel_lists"

        return "other"

    # ── Step 2: 规则配置 ──────────────────────────────────

    def step2_rule_configuration(
        self,
        rule_set: Optional[Dict[str, Any]] = None,
        custom_rules: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Step 2: 规则配置对标风险

        根据审计项目类型，加载对应筛查规则。
        支持从AGR知识库检索（预留接口）或使用内置规则。
        """
        self.state.current_step = "rule_configuration"

        if not self.state.project_type:
            self.state.errors.append("项目类型未确定，使用通用规则")
            self.state.project_type = "general"

        self.state.audit_focus = infer_focus_areas(self.state.project_type)

        # 使用传入规则或默认规则
        if rule_set:
            self.state.rule_set = rule_set
        else:
            # 默认规则集（从budget_compliance_scan复用）
            self.state.rule_set = {
                "audit_type": self.state.project_type,
                "audit_focus": self.state.audit_focus,
                "custom_rules": custom_rules or {},
            }

        return self.state.rule_set

    # ── Step 3: 批量分析 ──────────────────────────────────

    def step3_data_analysis(
        self,
        enable_simulator: bool = True,
    ) -> Dict[str, Any]:
        """
        Step 3: 批量分析疑点初筛

        并行调用5个文本分析工具，聚合结果并标注风险等级。
        可选启用v5模拟器对偶推理。
        """
        self.state.current_step = "data_analysis"

        # 热词分析（会议纪要）
        if self.state.raw_texts.get("meeting_minutes"):
            hr = self._hotword.analyze(
                documents=self.state.raw_texts["meeting_minutes"],
                doc_type="meeting_minutes",
                audit_focus=self.state.project_type,
            )
            self.state.hotword_result = {
                "hotwords": [asdict(hw) for hw in hr.hotwords],
                "audit_focus": hr.audit_focus,
                "audit_type": hr.audit_type,
            }

        # 合同提取
        if self.state.raw_texts.get("contracts"):
            ct = self._contract.extract([
                (f"contract_{i}.txt", text)
                for i, text in enumerate(
                    self.state.raw_texts["contracts"]
                )
            ])
            self.state.contract_result = {
                "contracts": [
                    {"file": c.file, "fields": c.fields, "risk_flags": c.risk_flags}
                    for c in ct.contracts
                ],
                "total_files": ct.total_files,
                "risk_summary": ct.risk_summary,
            }

        # 预算合规扫描（报销凭证）
        if self.state.raw_texts.get("expense_records"):
            br = self._budget.scan(
                expense_texts=self.state.raw_texts["expense_records"],
            )
            self.state.budget_result = {
                "violations": [asdict(v) for v in br.violations],
                "violation_count": br.violation_count,
                "violation_by_severity": br.violation_by_severity,
            }

        # 相似度比对（全量文本两两比对，或按需触发）
        # 默认不执行全量相似度比对（计算量大），需要显式传入reference/check

        # 人员比对（需要参照名单，暂不在自动流水线中执行，由工具独立调用）

        # ── v7: 统计/行为分析工具 ──
        # Benford分析（从合同/报销中提取金额）
        if self.state.raw_texts.get("contracts") or self.state.raw_texts.get("expense_records"):
            amounts = self._extract_amounts_for_benford()
            if amounts and len(amounts) >= 30:
                br = self._benford.analyze(amounts, label="流水线全量数据")
                self.state.benford_result = {
                    "total_records": br.total_records,
                    "distribution": [
                        {"digit": d.digit, "actual_pct": f"{d.actual_pct*100:.1f}%",
                         "theoretical_pct": f"{d.theoretical_pct*100:.1f}%",
                         "deviation": f"{d.deviation*100:+.1f}%"}
                        for d in br.distribution
                    ],
                    "chi_square": br.chi_square,
                    "p_value": br.p_value,
                    "is_significant": br.is_significant,
                    "interpretation": br.interpretation,
                }

        # 供应商指纹（从合同数据中提取供应商特征）
        if self.state.raw_texts.get("contracts"):
            supplier_records = self._extract_supplier_records()
            if supplier_records and len(set(
                r.get("supplier_name", "") for r in supplier_records
            )) >= 5:
                fp_result = self._fingerprint.run(supplier_records)
                self.state.fingerprint_result = {
                    "total_suppliers": fp_result.total_suppliers,
                    "total_pairs": fp_result.total_pairs,
                    "high_similarity_count": len(fp_result.high_similarity_pairs),
                    "summary": fp_result.summary,
                }

        # 时间序列异常（从合同中检测先付后签）
        if self.state.raw_texts.get("contracts"):
            projects = self._extract_project_timeline()
            if projects:
                tl_result = self._timeline.detect(projects)
                self.state.timeline_result = {
                    "total_projects": tl_result.total_projects,
                    "anomaly_count": tl_result.anomaly_count,
                    "anomaly_rate": f"{tl_result.anomaly_rate:.1%}",
                    "total_anomaly_amount": tl_result.total_anomaly_amount,
                    "summary": tl_result.summary,
                }

        # 合同变更轨迹（需要变更记录数据，流水线中有变更信息时触发）
        changes_data = self._extract_change_records()
        if changes_data and self.state.raw_texts.get("contracts"):
            ct_result = self._change_traj.analyze(
                self._extract_contract_summaries(),
                changes_data,
            )
            self.state.change_trajectory_result = {
                "total_projects": ct_result.total_projects,
                "overall_change_rate": f"{ct_result.overall_change_rate:.1%}",
                "change_rate_deviation": f"{ct_result.change_rate_deviation*100:+.1f}%",
                "high_risk_count": len(ct_result.high_risk_projects),
                "summary": ct_result.summary,
            }

        # ── v5: 模拟器对偶推理 ──
        if enable_simulator:
            self.state.simulator_inferences = {}

            if self.state.hotword_result:
                risk_hotwords = [
                    hw for hw in self.state.hotword_result.get("hotwords", [])
                    if hw.get("risk_signal")
                ]
                if risk_hotwords:
                    self.state.simulator_inferences["hotword"] = (
                        generate_simulator_inferences(
                            "text_hotword_analysis",
                            risk_hotwords,
                            {"audit_type": self.state.project_type},
                        )
                    )

            if self.state.budget_result:
                violations = self.state.budget_result.get("violations", [])
                if violations:
                    self.state.simulator_inferences["budget"] = (
                        generate_simulator_inferences(
                            "budget_compliance_scan",
                            violations,
                        )
                    )

        # 聚合疑点
        self._aggregate_findings()

        return {
            "hotword": self.state.hotword_result,
            "contract": self.state.contract_result,
            "budget": self.state.budget_result,
            "benford": self.state.benford_result,
            "fingerprint": self.state.fingerprint_result,
            "timeline": self.state.timeline_result,
            "change_trajectory": self.state.change_trajectory_result,
            "simulator_inferences": self.state.simulator_inferences,
        }

    def _aggregate_findings(self):
        """聚合所有工具的疑点为统一的风险清单"""
        findings = []
        idx = 0

        # 热词风险
        if self.state.hotword_result:
            for hw in self.state.hotword_result.get("hotwords", []):
                if hw.get("risk_signal"):
                    idx += 1
                    findings.append(AuditFinding(
                        index=idx,
                        finding_type="hotword_risk",
                        source_file=f"[会议纪要] 关键词: {hw.get('word', '')}",
                        risk_flags=[
                            RiskFlag(
                                type="keyword_risk",
                                detail=f"风险信号词「{hw.get('word')}」"
                                      f"（权重{hw.get('weight', 0):.4f}）",
                                severity="medium",
                                evidence=hw.get("audit_relevance", ""),
                                simulator_inference=hw.get("simulator_inference"),
                            )
                        ],
                        severity="medium",
                    ))

        # 合同风险
        if self.state.contract_result:
            for ct in self.state.contract_result.get("contracts", []):
                for rf in ct.get("risk_flags", []):
                    idx += 1
                    findings.append(AuditFinding(
                        index=idx,
                        finding_type="contract_risk",
                        source_file=ct.get("file", ""),
                        risk_flags=[
                            RiskFlag(
                                type=rf.get("type", "unknown"),
                                detail=rf.get("detail", ""),
                                severity=rf.get("severity", "medium"),
                                simulator_inference=rf.get("simulator_inference"),
                            )
                        ],
                        severity=rf.get("severity", "medium"),
                    ))

        # 预算违规
        if self.state.budget_result:
            for v in self.state.budget_result.get("violations", []):
                idx += 1
                findings.append(AuditFinding(
                    index=idx,
                    finding_type="budget_violation",
                    source_file=f"[报销凭证 #{v.get('index', 0)}]",
                    risk_flags=[
                        RiskFlag(
                            type=v.get("violation_type", "unknown"),
                            detail=v.get("rule_description", ""),
                            severity=v.get("severity", "medium"),
                            evidence=v.get("original_text", "")[:200],
                            simulator_inference=v.get("simulator_inference"),
                        )
                    ],
                    severity=v.get("severity", "medium"),
                ))

        self.state.risk_findings = findings

    def _extract_amounts_for_benford(self) -> List[float]:
        """从合同/报销文本中提取金额用于Benford分析"""
        import re
        amounts = []
        for texts in [
            self.state.raw_texts.get("contracts", []),
            self.state.raw_texts.get("expense_records", []),
        ]:
            for text in texts:
                # 简单正则可以匹配大多数金额格式
                matches = re.findall(
                    r'[¥￥]?\s*(\d{3,}(?:,\d{3})*(?:\.\d{2})?)\s*(?:元|万元?)?',
                    text
                )
                for m in matches:
                    try:
                        val = float(m.replace(",", ""))
                        if val > 0:
                            amounts.append(val)
                    except ValueError:
                        pass
        return amounts

    def _extract_supplier_records(self) -> List[Dict]:
        """从合同文本中提取供应商记录"""
        import re
        records = []
        for text in self.state.raw_texts.get("contracts", []):
            # 尝试提取供应商名称和金额
            supplier_match = re.search(
                r'(?:乙方|供应商|承包方|中标人)[：:]\s*(.+?)(?:[\n，。])',
                text
            )
            amount_match = re.search(
                r'[¥￥]?\s*(\d{3,}(?:,\d{3})*(?:\.\d{2})?)\s*(?:元)',
                text
            )
            supplier_name = supplier_match.group(1).strip() if supplier_match else "未知"
            amount = 0.0
            if amount_match:
                try:
                    amount = float(amount_match.group(1).replace(",", ""))
                except ValueError:
                    pass
            records.append({
                "supplier_name": supplier_name,
                "supplier_id": supplier_name,
                "amount": amount,
                "project_category": self.state.project_type or "general",
                "unit_name": self.state.project_name or "未知单位",
                "is_winner": True,
            })
        return records

    def _extract_project_timeline(self) -> List[Dict]:
        """从合同文本中提取合同日期和付款日期"""
        import re
        projects = []
        for i, text in enumerate(self.state.raw_texts.get("contracts", [])):
            contract_date = re.search(
                r'(?:签订日期|合同日期|签约日期)[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                text
            )
            payment_date = re.search(
                r'(?:付款日期|支付日期|结算日期)[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                text
            )
            amount_match = re.search(
                r'[¥￥]?\s*(\d{3,}(?:,\d{3})*(?:\.\d{2})?)\s*(?:元)',
                text
            )
            amount = 0.0
            if amount_match:
                try:
                    amount = float(amount_match.group(1).replace(",", ""))
                except ValueError:
                    pass

            projects.append({
                "project_id": f"PIPE_{i:04d}",
                "contract_date": (
                    contract_date.group(1).replace("/", "-")
                    if contract_date else "2024-01-01"
                ),
                "payment_date": (
                    payment_date.group(1).replace("/", "-")
                    if payment_date else "2024-01-01"
                ),
                "contract_amount": amount,
                "payment_amount": amount,
                "handler": "流水线提取",
                "unit": self.state.project_name or "未知",
            })
        return projects

    def _extract_contract_summaries(self) -> List[Dict]:
        """从合同文本中提取合同摘要"""
        import re
        summaries = []
        for i, text in enumerate(self.state.raw_texts.get("contracts", [])):
            contract_date = re.search(
                r'(?:签订日期|合同日期)[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                text
            )
            amount_match = re.search(
                r'[¥￥]?\s*(\d{3,}(?:,\d{3})*(?:\.\d{2})?)\s*(?:元)',
                text
            )
            amount = 0.0
            if amount_match:
                try:
                    amount = float(amount_match.group(1).replace(",", ""))
                except ValueError:
                    pass
            summaries.append({
                "project_id": f"PIPE_{i:04d}",
                "contract_date": (
                    contract_date.group(1).replace("/", "-")
                    if contract_date else "2024-01-01"
                ),
                "completion_date": "2024-12-31",
                "contract_amount": amount,
            })
        return summaries

    def _extract_change_records(self) -> List[Dict]:
        """从文本中提取变更记录"""
        import re
        changes = []
        for text in self.state.raw_texts.get("other", []):
            if "变更" not in text:
                continue
            records = re.split(r'[\n；;]', text)
            for i, rec in enumerate(records):
                if "变更" not in rec:
                    continue
                ct = "other"
                if "金额" in rec and ("调减" in rec or "减少" in rec):
                    ct = "amount_decrease"
                elif "金额" in rec and ("调增" in rec or "增加" in rec):
                    ct = "amount_increase"
                elif "工期" in rec or "延期" in rec:
                    ct = "timeline_change"
                elif "范围" in rec or "内容" in rec:
                    ct = "scope_change"

                amount = 0.0
                am = re.search(r'[¥￥]?(\d+[\.\d]*)\s*(?:万)?元', rec)
                if am:
                    try:
                        amount = float(am.group(1).replace(",", ""))
                        if "减" in rec:
                            amount = -amount
                    except ValueError:
                        pass

                date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', rec)
                changes.append({
                    "project_id": f"PIPE_{i:04d}",
                    "change_date": (
                        date_match.group(1).replace("/", "-")
                        if date_match else "2024-06-15"
                    ),
                    "change_type": ct,
                    "change_amount": amount,
                    "change_description": rec.strip(),
                    "change_reason": "从文本提取",
                })
        return changes

    # ── Step 4: 人机核验 ──────────────────────────────────

    def step4_human_review(self) -> Dict[str, Any]:
        """
        Step 4: 人机核验固化证据

        将高风险疑点整理为人工复核任务清单，
        等待人工确认/驳回/修正后返回。
        """
        self.state.current_step = "human_review"

        findings = self.state.risk_findings

        high_risk = [
            {
                "index": f.index,
                "type": f.finding_type,
                "source": f.source_file,
                "severity": f.severity,
                "risk_flags": [
                    {
                        "type": rf.type,
                        "detail": rf.detail,
                        "evidence": rf.evidence[:300],
                        "simulator_inference": (
                            rf.simulator_inference.get("arbitration_reason", "")
                            if rf.simulator_inference else ""
                        ),
                    }
                    for rf in f.risk_flags
                ],
            }
            for f in findings
            if f.severity in ("high", "medium")
        ]

        low_risk = [
            {
                "index": f.index,
                "type": f.finding_type,
                "source": f.source_file,
            }
            for f in findings
            if f.severity == "low"
        ]

        self.state.human_review_task = {
            "total_findings": len(findings),
            "high_medium_risk_items": high_risk,
            "low_risk_items": low_risk,
            "high_risk_count": len(high_risk),
            "estimated_review_hours": len(high_risk) * 0.5 + len(low_risk) * 0.1,
            "status": "awaiting_review",
        }

        return self.state.human_review_task

    def submit_human_feedback(
        self, feedback: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        提交人工复核反馈

        feedback格式：
        [
            {
                "index": 1,
                "decision": "confirmed" | "rejected" | "modified",
                "note": "人工审核意见",
                "modified": {...}  # decision=modified时的修正内容
            },
            ...
        ]
        """
        self.state.human_feedback = feedback

        for item in feedback:
            idx = item.get("index", 0)
            decision = item.get("decision", "pending")

            # 更新对应的finding状态
            for finding in self.state.risk_findings:
                if finding.index == idx:
                    finding.human_review_status = decision
                    finding.human_review_note = item.get("note", "")

                    if decision == "confirmed":
                        self.state.confirmed_evidence.append({
                            "index": idx,
                            "type": finding.finding_type,
                            "source": finding.source_file,
                            "note": item.get("note", ""),
                        })
                    elif decision == "rejected":
                        self.state.false_positives.append({
                            "index": idx,
                            "type": finding.finding_type,
                            "reason": item.get("note", ""),
                        })
                    elif decision == "modified":
                        self.state.confirmed_evidence.append({
                            "index": idx,
                            "type": finding.finding_type,
                            "modified": item.get("modified", {}),
                            "note": item.get("note", ""),
                        })
                    break

        # 更新任务状态
        if self.state.human_review_task:
            self.state.human_review_task["status"] = "completed"
            self.state.human_review_task["confirmed"] = len(
                self.state.confirmed_evidence
            )
            self.state.human_review_task["rejected"] = len(
                self.state.false_positives
            )

        return {
            "status": "completed",
            "confirmed": len(self.state.confirmed_evidence),
            "rejected": len(self.state.false_positives),
            "total_reviewed": len(feedback),
        }

    # ── 完整流水线 ──────────────────────────────────────

    # ── v9: 围标串标检测 ───────────────────────────────

    def step3e_bid_rigging_detect(
        self,
        segments: List[Dict[str, Any]],
        industry: str = "default",
    ) -> Dict[str, Any]:
        """
        v9 Step 3e: 围标串标多维检测

        对招投标标段进行5维特征并行检测：
        IP/设备→报价规律→保证金同源→文件基因→时间扎堆

        Args:
            segments: 标段数据列表
            industry: 行业类型

        Returns:
            检测结果
        """
        self.state.current_step = "step3e_bid_rigging"
        result = self._bid_rigging.detect(segments, industry=industry)
        self.state.bid_rigging_result = {
            "total_segments": result.total_segments,
            "flagged_segments": result.flagged_segments,
            "risk_distribution": result.risk_distribution,
            "hit_rate_stats": result.hit_rate_stats,
            "cross_hit_matrix": result.cross_hit_matrix,
            "summary": result.summary,
        }

        # 将高风险标段加入risk_findings
        for risk in result.risks:
            if risk.risk_level in ("high", "medium"):
                self.state.risk_findings.append(AuditFinding(
                    index=len(self.state.risk_findings) + 1,
                    finding_type="bid_rigging",
                    source_file=f"segment://{risk.segment_id}",
                    description=f"标段{risk.segment_name}围标风险评分{risk.risk_score}/5.0",
                    severity=risk.risk_level,
                    evidence=risk.combined_evidence,
                    recommendation=risk.recommendation,
                ))

        return self.state.bid_rigging_result

    def step3f_evidence_chain_generate(
        self,
        min_risk_score: float = 2.0,
        export_html: bool = False,
    ) -> Dict[str, Any]:
        """
        v9 Step 3f: 证据链图谱生成

        基于围标检测结果为高风险标段生成力导向证据链图谱

        Args:
            min_risk_score: 最低风险评分阈值
            export_html: 是否导出HTML

        Returns:
            证据链结果
        """
        self.state.current_step = "step3f_evidence_chain"

        if not self.state.bid_rigging_result:
            return {"error": "需先执行 step3e_bid_rigging_detect"}

        # 从管道状态重建result（简化）
        from .bid_rigging_detector import detect_bid_rigging
        # 此处需要原始segments数据，从state获取
        # 简化处理：从已有结果生成
        result = self._evidence_chain.generate_all(
            self._build_rigging_result_proxy(),
            max_graphs=20,
            min_risk_score=min_risk_score,
        )

        self.state.evidence_chain_result = {
            "total_graphs": result.total_segments,
            "generated_at": result.generated_at,
            "graphs_summary": [
                {
                    "segment_id": g.segment_id,
                    "risk_score": g.risk_score,
                    "summary_text": g.summary_text[:200],
                }
                for g in result.graphs
            ],
        }

        return self.state.evidence_chain_result

    def _build_rigging_result_proxy(self) -> Any:
        """从pipeline state构建BidRiggingResult代理对象"""
        from .bid_rigging_detector import BidRiggingRisk, BidRiggingResult

        br = self.state.bid_rigging_result or {}
        risks = []
        for f in self.state.risk_findings:
            if f.finding_type == "bid_rigging":
                # 从finding来源提取segment_id
                seg_id = f.source_file.replace("segment://", "") if f.source_file else ""
                risk = BidRiggingRisk(
                    segment_id=seg_id,
                    segment_name=f.description.split("围标风险")[0].replace("标段", "") if f.description else "",
                    risk_score=0.0,
                    risk_level=f.severity,
                    combined_evidence=f.evidence or [],
                    recommendation=f.recommendation or "",
                )
                risks.append(risk)

        return BidRiggingResult(
            total_segments=br.get("total_segments", 0),
            flagged_segments=len(risks),
            risk_distribution=br.get("risk_distribution", {}),
            risks=risks,
            hit_rate_stats=br.get("hit_rate_stats", {}),
            cross_hit_matrix=br.get("cross_hit_matrix", {}),
            summary=br.get("summary", ""),
        )

    # ── 完整流水线 ──────────────────────────────────────

    def run(
        self,
        source_files: List[str],
        project_name: str = "",
        project_type: str = "",
        rule_set: Optional[Dict] = None,
        enable_simulator: bool = True,
        auto_approve_low: bool = True,
    ) -> Dict[str, Any]:
        """
        运行完整4步流水线

        Args:
            source_files: 源文件列表
            project_name: 项目名称
            project_type: 项目类型
            rule_set: 自定义规则集
            enable_simulator: 是否启用v5模拟器对偶
            auto_approve_low: 是否自动确认低风险疑点

        Returns:
            流水线完整结果
        """
        # Step 1
        coverage = self.step1_data_collection(
            source_files, project_name, project_type
        )

        # Step 2
        rules = self.step2_rule_configuration(rule_set)

        # Step 3
        analysis = self.step3_data_analysis(enable_simulator)

        # Step 4
        review_task = self.step4_human_review()

        return {
            "project_name": self.state.project_name,
            "project_type": self.state.project_type,
            "coverage": asdict(coverage) if coverage else None,
            "rules_configured": bool(rules),
            "analysis": analysis,
            "review_task": review_task,
            "total_findings": len(self.state.risk_findings),
            "high_risk_count": sum(
                1 for f in self.state.risk_findings
                if f.severity == "high"
            ),
            "medium_risk_count": sum(
                1 for f in self.state.risk_findings
                if f.severity == "medium"
            ),
            "low_risk_count": sum(
                1 for f in self.state.risk_findings
                if f.severity == "low"
            ),
            "errors": self.state.errors,
        }
