"""
Agent输出结构化 — 统一审计发现的标准输出格式

所有分析Agent（5个准则专家 + 数据分析层）的输出
必须符合统一的四段式JSON Schema：
  target    — 目标：本程序对应哪个认定，验证什么
  process   — 过程：抽样方法、测试步骤、覆盖比例
  conclusion — 结论：审计发现、证据索引、例外事项
  cross_refs — 索引：与其他底稿/文件的交叉引用

同时提供 Schema 校验和自动补全功能。
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime


# ── 枚举定义 ──────────────────────────────────────────────

class AssertionType(Enum):
    """审计认定类型"""
    EXISTENCE = "存在性"        # 资产/负债/交易是否真实存在
    COMPLETENESS = "完整性"     # 是否完整记录，无遗漏
    ACCURACY = "准确性"         # 金额/数量是否准确
    CUTOFF = "截止"             # 是否归属于正确期间
    VALUATION = "计价"          # 计价/分摊是否恰当
    RIGHTS = "权利"             # 权利和义务归属
    CLASSIFICATION = "列报"     # 报表列报和披露


class SamplingMethod(Enum):
    """抽样方法"""
    RANDOM = "随机抽样"
    STRATIFIED = "分层抽样"
    TOP_AMOUNT = "大额优先"
    PPS = "PPS抽样"
    SYSTEMATIC = "系统抽样"
    DESCENDING = "金额降序"
    JUDGMENT = "判断抽样"
    FULL = "全量检查"


class RiskLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── 输出数据结构 ───────────────────────────────────────────

@dataclass
class StructuredTarget:
    """目标段"""
    assertions: List[str]         # 对应的认定列表
    objective: str                # 具体验证目标
    audit_program_ref: str = ""   # 审计程序索引号


@dataclass
class StructuredProcess:
    """过程段"""
    sampling_method: str          # 抽样方法
    selection_logic: str          # 选取依据
    sample_size: int = 0
    population_size: int = 0
    coverage_ratio: str = ""      # 如 "72%"
    test_procedures: List[str] = field(default_factory=list)
    documents_reviewed: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    execution_date: str = ""


@dataclass
class ExceptionItem:
    """例外事项"""
    description: str
    resolution: str
    impact: str                   # 对结论的影响（如"不影响整体结论"）
    severity: str = "medium"
    cross_ref: str = ""


@dataclass
class StructuredConclusion:
    """结论段"""
    statement: str                # 结论文字
    evidence_refs: List[str] = field(default_factory=list)
    exceptions: List[ExceptionItem] = field(default_factory=list)
    overall_opinion: str = ""     # "无异常" / "存在例外但不影响结论" / "存在重大异常"


@dataclass
class StructuredCrossRefs:
    """交叉引用段"""
    ledger_ref: str = ""          # 明细表索引
    contract_refs: List[str] = field(default_factory=list)
    related_wps: List[str] = field(default_factory=list)
    report_refs: List[str] = field(default_factory=list)
    policy_refs: List[str] = field(default_factory=list)


@dataclass
class AgentStructuredOutput:
    """Agent完整结构化输出"""
    # 元信息
    agent_name: str               # 产出Agent名称
    audit_project: str            # 审计项目
    audit_period: str             # 审计期间
    generated_at: str = ""

    # 四段式
    target: StructuredTarget = field(default_factory=StructuredTarget)
    process: StructuredProcess = field(default_factory=StructuredProcess)
    conclusion: StructuredConclusion = field(default_factory=StructuredConclusion)
    cross_refs: StructuredCrossRefs = field(default_factory=StructuredCrossRefs)

    # 工具分析结果（附加）
    tool_results: Dict[str, Any] = field(default_factory=dict)
    simulator_inferences: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    quality_checks_passed: List[str] = field(default_factory=list)
    quality_checks_failed: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


# ── 输出校验器 ─────────────────────────────────────────────

class OutputValidator:
    """Agent输出结构校验器"""

    # 标准认定术语
    ASSERTION_TERMS = [
        "存在", "存在性", "完整性", "准确性", "计价", "分摊",
        "截止", "权利", "义务", "列报", "披露", "认定",
    ]

    # 抽样方法关键词
    SAMPLING_TERMS = [
        "随机抽样", "分层抽样", "大额优先", "PPS抽样",
        "系统抽样", "金额降序", "判断抽样", "全量检查",
        "选取", "抽取", "抽样",
    ]

    # 测试步骤关键词
    TEST_PROCEDURE_TERMS = [
        "获取", "核对", "检查", "验证", "比较", "重新计算",
        "函证", "盘点", "观察", "询问", "分析", "追踪",
        "交叉比对", "复核", "测试",
    ]

    # 证据关键词
    EVIDENCE_TERMS = [
        "依据", "证据", "支撑", "经检查", "经核查", "经抽查",
        "来源", "详见索引", "参照", "根据", "参见",
    ]

    # 文件类型关键词
    DOCUMENT_TYPE_TERMS = [
        "合同", "发票", "出库单", "签收单", "银行对账单",
        "凭证", "明细账", "权证", "评估报告", "验收单",
        "审批单", "付款申请", "结算单", "变更单", "签证单",
    ]

    def validate(self, output: AgentStructuredOutput) -> Tuple[bool, List[str], List[str]]:
        """
        校验结构化输出

        Returns:
            (is_valid, passed_checks, failed_checks)
        """
        passed = []
        failed = []

        # ── 目标段检查 ──
        if not output.target.objective:
            failed.append("目标缺失：未填写具体验证目标")
        elif len(output.target.objective) < 20:
            failed.append("目标过于简短：验证目标描述不充分")
        else:
            passed.append("目标明确")

        if not output.target.assertions:
            failed.append("认定缺失：未对应任何审计认定")
        else:
            has_standard_term = any(
                term in " ".join(output.target.assertions)
                for term in self.ASSERTION_TERMS
            )
            if has_standard_term:
                passed.append("认定术语规范")
            else:
                failed.append("认定术语不规范：未使用标准认定术语")

        # ── 过程段检查 ──
        if output.process.sampling_method:
            has_sampling = any(
                term in output.process.sampling_method
                for term in self.SAMPLING_TERMS
            )
            if has_sampling:
                passed.append("抽样方法清晰")
            else:
                failed.append("抽样方法不清晰：未使用标准抽样术语")
        else:
            failed.append("抽样方法缺失：未说明如何选取样本")

        if output.process.test_procedures:
            passed.append("测试步骤完整")
        elif not output.process.documents_reviewed:
            failed.append("过程描述不完整：无测试步骤也无文件清单")

        if output.process.coverage_ratio:
            passed.append("覆盖比例明确")
        else:
            failed.append("覆盖比例缺失：未标注抽样覆盖比例")

        # ── 结论段检查 ──
        if not output.conclusion.statement:
            failed.append("结论缺失：无审计结论")
        elif len(output.conclusion.statement) < 10:
            failed.append("结论过于简短")
        else:
            passed.append("结论完整")

        if output.conclusion.evidence_refs:
            passed.append("证据索引完整")
        else:
            failed.append("证据索引缺失：结论无对应证据引用")

        if output.conclusion.exceptions:
            has_handled = all(
                e.resolution and e.impact
                for e in output.conclusion.exceptions
            )
            if has_handled:
                passed.append("例外处理完整")
            else:
                failed.append("例外处理不完整：有例外但缺少处理方式或影响评估")

        # ── 交叉引用段检查 ──
        has_refs = (
            output.cross_refs.ledger_ref
            or output.cross_refs.contract_refs
            or output.cross_refs.related_wps
        )
        if has_refs:
            passed.append("交叉引用存在")
        else:
            failed.append("交叉引用缺失：无可追溯引用")

        # ── 数量溢出检查（有数无说预检） ──
        numeric_ratio = self._calc_numeric_ratio(output)
        if numeric_ratio["numeric_ratio"] > 0.7:
            failed.append(
                f"数据占比过高（{numeric_ratio['numeric_ratio']:.0%}），疑似有数无说"
            )

        is_valid = len(failed) == 0
        return is_valid, passed, failed

    def _calc_numeric_ratio(
        self, output: AgentStructuredOutput
    ) -> Dict[str, Any]:
        """计算输出中数字内容占比"""
        text = " ".join([
            output.target.objective,
            output.process.selection_logic,
            output.conclusion.statement,
            *[e.description for e in output.conclusion.exceptions],
        ])

        if not text:
            return {"numeric_ratio": 0, "total_chars": 0, "numeric_chars": 0}

        total = len(text)
        numeric = len(re.findall(r"\d", text))
        return {
            "numeric_ratio": numeric / total if total > 0 else 0,
            "total_chars": total,
            "numeric_chars": numeric,
        }


# ── 输出构建器：从工具结果快速生成结构化输出 ────────────────

class OutputBuilder:
    """从文本分析工具结果构建结构化输出"""

    def from_hotword(
        self,
        agent_name: str,
        project: str,
        period: str,
        hotword_result: Dict[str, Any],
    ) -> AgentStructuredOutput:
        """从热词分析结果构建结构化输出"""
        risk_words = [
            hw for hw in hotword_result.get("hotwords", [])
            if hw.get("risk_signal")
        ]

        objective = (
            f"通过TF-IDF热词分析，对{hotword_result.get('doc_count', 0)}份会议纪要"
            f"进行关键词提取，识别高频决策事项和潜在审计风险领域"
        )

        conclusion_text = (
            f"经分析，共提取{len(hotword_result.get('hotwords', []))}个热词，"
            f"其中{len(risk_words)}个为风险信号词"
        ) if risk_words else (
            f"经分析，共提取{len(hotword_result.get('hotwords', []))}个热词，"
            f"未发现明显风险信号词"
        )

        exceptions = []
        for hw in risk_words:
            si = hw.get("simulator_inference", {})
            exceptions.append(ExceptionItem(
                description=f"风险信号词「{hw['word']}」"
                           f"（权重{hw.get('weight', 0):.4f}）",
                resolution=si.get("recommended_action", "需进一步核查"),
                impact=si.get("arbitration_reason", "待确认"),
                severity=si.get("severity", "medium"),
                cross_ref=f"[热词分析] {hw['word']}",
            ))

        return AgentStructuredOutput(
            agent_name=agent_name,
            audit_project=project,
            audit_period=period,
            target=StructuredTarget(
                assertions=["存在性", "完整性"],
                objective=objective,
            ),
            process=StructuredProcess(
                sampling_method="全量检查",
                selection_logic=f"对{hotword_result.get('doc_count', 0)}份会议纪要"
                               f"进行全量TF-IDF分析",
                sample_size=hotword_result.get("doc_count", 0),
                test_procedures=["TF-IDF热词提取", "风险词库匹配"],
                tools_used=["text_hotword_analysis"],
            ),
            conclusion=StructuredConclusion(
                statement=conclusion_text,
                exceptions=exceptions,
                overall_opinion=(
                    "存在风险信号" if risk_words else "无异常"
                ),
            ),
            tool_results={"hotword": hotword_result},
        )

    def from_budget_scan(
        self,
        agent_name: str,
        project: str,
        period: str,
        budget_result: Dict[str, Any],
    ) -> AgentStructuredOutput:
        """从预算合规扫描结果构建结构化输出"""
        violations = budget_result.get("violations", [])
        high_risk = [v for v in violations if v.get("severity") == "high"]

        objective = (
            f"对{budget_result.get('total_expenses', 0)}条报销记录进行全量合规扫描，"
            f"识别超标接待、私车公养、违规采购等违规行为"
        )

        conclusion_text = (
            f"经扫描，共发现{budget_result.get('violation_count', 0)}条违规记录"
            f"（高危{len(high_risk)}条）"
        ) if violations else "经扫描，未发现违规记录"

        exceptions = []
        for v in violations[:10]:  # 最多10条
            si = v.get("simulator_inference", {})
            exceptions.append(ExceptionItem(
                description=f"[{v.get('severity', '')}] {v.get('rule_description', '')}",
                resolution=si.get("recommended_action", "需人工核实"),
                impact=v.get("original_text", "")[:100],
                severity=v.get("severity", "medium"),
            ))

        return AgentStructuredOutput(
            agent_name=agent_name,
            audit_project=project,
            audit_period=period,
            target=StructuredTarget(
                assertions=["存在性", "准确性", "列报"],
                objective=objective,
            ),
            process=StructuredProcess(
                sampling_method="全量检查",
                selection_logic=f"对{budget_result.get('total_expenses', 0)}条记录全量扫描",
                sample_size=budget_result.get("total_expenses", 0),
                test_procedures=["关键词扫描", "正则模式匹配", "限额规则校验"],
                tools_used=["budget_compliance_scan"],
            ),
            conclusion=StructuredConclusion(
                statement=conclusion_text,
                exceptions=exceptions,
                overall_opinion=(
                    "存在重大异常" if len(high_risk) >= 3
                    else "存在例外但不影响整体" if violations
                    else "无异常"
                ),
            ),
            tool_results={"budget": budget_result},
        )

    def from_contract_extract(
        self,
        agent_name: str,
        project: str,
        period: str,
        contract_result: Dict[str, Any],
    ) -> AgentStructuredOutput:
        """从合同提取结果构建结构化输出"""
        contracts = contract_result.get("contracts", [])
        risk_summary = contract_result.get("risk_summary", {})

        objective = (
            f"对{contract_result.get('total_files', 0)}份合同进行字段提取和"
            f"财务数据交叉比对，识别付款违规、履约超期等风险"
        )

        conclusion_text = (
            f"共处理{len(contracts)}份合同，发现"
            f"高危{risk_summary.get('high', 0)}条、"
            f"中危{risk_summary.get('medium', 0)}条风险"
        )

        exceptions = []
        for ct in contracts:
            for rf in ct.get("risk_flags", []):
                exceptions.append(ExceptionItem(
                    description=f"[{ct.get('file', '')}] {rf.get('detail', '')}",
                    resolution="需核查原始凭证和审批文件",
                    impact=rf.get('type', ''),
                    severity=rf.get("severity", "medium"),
                ))

        return AgentStructuredOutput(
            agent_name=agent_name,
            audit_project=project,
            audit_period=period,
            target=StructuredTarget(
                assertions=["存在性", "准确性", "权利"],
                objective=objective,
            ),
            process=StructuredProcess(
                sampling_method="全量检查",
                selection_logic=f"对{len(contracts)}份合同全量处理",
                sample_size=len(contracts),
                test_procedures=["合同字段提取", "金额标准化", "财务交叉比对"],
                tools_used=["contract_field_extract"],
            ),
            conclusion=StructuredConclusion(
                statement=conclusion_text,
                exceptions=exceptions,
                overall_opinion=(
                    "存在重大异常" if risk_summary.get("high", 0) > 0
                    else "存在例外" if risk_summary.get("medium", 0) > 0
                    else "无异常"
                ),
            ),
            tool_results={"contract": contract_result},
        )

    def from_personnel_check(
        self,
        agent_name: str,
        project: str,
        period: str,
        personnel_result: Dict[str, Any],
    ) -> AgentStructuredOutput:
        """从人员比对结果构建结构化输出"""
        violations = personnel_result.get("violations", [])

        objective = (
            f"对{personnel_result.get('total_applicants', 0)}名申报人进行"
            f"身份比对，筛查财政供养人员、死亡人员、重复申领等违规"
        )

        conclusion_text = (
            f"共核查{personnel_result.get('total_applicants', 0)}人，"
            f"发现{personnel_result.get('matched_count', 0)}人存在违规，"
            f"{personnel_result.get('clean_count', 0)}人通过"
        )

        exceptions = []
        for v in violations:
            exceptions.append(ExceptionItem(
                description=f"{v.get('name', '')}：{v.get('evidence', '')}",
                resolution="需追缴违规领取资金并追究经办人责任",
                impact=v.get('violation_type', ''),
                severity=v.get("severity", "high"),
            ))

        return AgentStructuredOutput(
            agent_name=agent_name,
            audit_project=project,
            audit_period=period,
            target=StructuredTarget(
                assertions=["存在性", "完整性"],
                objective=objective,
            ),
            process=StructuredProcess(
                sampling_method="全量检查",
                selection_logic="对全部申报人进行身份比对",
                sample_size=personnel_result.get("total_applicants", 0),
                test_procedures=["财政供养人员比对", "死亡人员比对",
                               "重复申领检测", "政策一致性检测"],
                tools_used=["personnel_profile_check"],
            ),
            conclusion=StructuredConclusion(
                statement=conclusion_text,
                exceptions=exceptions,
                overall_opinion=(
                    "存在重大异常" if personnel_result.get("matched_count", 0) > 0
                    else "无异常"
                ),
            ),
            tool_results={"personnel": personnel_result},
        )


# ── 便捷函数 ─────────────────────────────────────────────

def validate_output(output: AgentStructuredOutput) -> Tuple[bool, List[str], List[str]]:
    """校验Agent输出结构"""
    validator = OutputValidator()
    return validator.validate(output)


def build_from_tool_result(
    agent_name: str,
    project: str,
    period: str,
    tool_name: str,
    tool_result: Dict[str, Any],
) -> AgentStructuredOutput:
    """从工具结果快速构建结构化输出"""
    builder = OutputBuilder()
    builders = {
        "text_hotword_analysis": builder.from_hotword,
        "budget_compliance_scan": builder.from_budget_scan,
        "contract_field_extract": builder.from_contract_extract,
        "personnel_profile_check": builder.from_personnel_check,
    }
    fn = builders.get(tool_name)
    if fn:
        return fn(agent_name, project, period, tool_result)

    # 默认通用构建
    return AgentStructuredOutput(
        agent_name=agent_name,
        audit_project=project,
        audit_period=period,
        tool_results={tool_name: tool_result},
    )
