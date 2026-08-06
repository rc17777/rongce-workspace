"""
Text Quality Filter (文本质控滤波器)

Evaluates audit report prose quality against the 10-dimension checklist
from 浙江省审计厅《撰写出彩的审计报告，应重点关注的十项内容》.

Architecture:
  - Rule definitions load from text_quality_rules.yaml
  - Accepts structured report text (sections identified by header patterns)
  - Runs four layers: forbidden_word_scan → pattern_match → structure_check → cross_consistency
  - Produces TextQualityCheckResult compatible with ReviewReportGenerator

Companion module to ReviewFilter (arithmetic FP filter).
"""

from __future__ import annotations

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class TextQualityRule:
    """A single text quality check rule."""
    rule_id: str
    dimension: str       # 1-10 e.g. "1"
    dimension_name: str   # e.g. "审计评价的恰当性"
    check_item: str       # Short description
    severity: str = "warning"
    detect_type: str = "forbidden_word"
    pattern: str = ""
    anti_pattern: str = ""
    required: str = ""
    check_fn: str = ""
    wei_score: float = 1.0
    description: str = ""
    categories: str = "all"  # "all" | "government_audit" | "cpa_attestation" | "government_audit,cpa_attestation" etc.

    def __post_init__(self):
        if not self.description:
            self.description = self.check_item

    def applies_to(self, category: str) -> bool:
        """Check if this rule applies to a given report category."""
        if self.categories == "all":
            return True
        allowed = set(c.strip() for c in self.categories.split(","))
        return category in allowed


@dataclass
class TextQualityResult:
    """Single text quality check result, compatible with CheckResult downstream."""
    rule_id: str
    check_type: str = "text_quality"
    domain: str = "报告文本质控"
    description: str = ""
    dimension: str = ""
    dimension_name: str = ""
    severity: str = "info"
    passed: bool = True
    requires_human_review: bool = False
    page_ref: str = ""
    excerpt: str = ""          # The matched text excerpt
    section: str = ""          # Which section of the report
    detail: str = ""
    suggestion: str = ""       # Remediation suggestion
    false_positive: bool = False
    false_positive_reason: str = ""

    # For compatibility with ReviewReportGenerator
    @property
    def expected(self): return None
    @property
    def actual(self): return None
    @property
    def diff(self): return None
    @property
    def tolerance(self): return 0.0


# ---------------------------------------------------------------------------
# Built-in Forbidden Word Lists
# ---------------------------------------------------------------------------

# 主观评价禁止词（一、审计评价恰当性）
FORBIDDEN_SUBJECTIVE_EVAL = [
    "全心全意", "千方百计", "呕心沥血", "殚精竭虑",
    "任劳任怨", "兢兢业业", "恪尽职守", "不遗余力",
    "苦干实干", "埋头苦干", "废寝忘食",
]

# 模糊/不确定禁止词（三、事实表述清晰性）
FORBIDDEN_VAGUE_WORDS = [
    "看起来好像", "看起来似乎是", "可能是由于", "可能是",
    "大概是由于", "似乎是因为", "也许因为", "或许是",
]

# 主观判断禁止词（三、事实表述清晰性）
FORBIDDEN_SUBJECTIVE_JUDGMENT = [
    "审计认为",
]

# 程度强调禁止词（三、事实表述清晰性）
FORBIDDEN_DEGREE_WORDS = [
    "严重亏损", "非常缓慢", "极其严重", "十分恶劣",
    "特别突出", "相当糟糕", "极度", "极为",
]

# 绝对化禁止词（三、事实表述清晰性）
FORBIDDEN_ABSOLUTE_WORDS = [
    "完全没有", "所有都", "从来没有", "从未发生",
    "毫无例外", "无一例外",
]

# 定性无实质区别词（二、问题定性准确性）
FORBIDDEN_VAGUE_DINGXING = [
    "不到位", "不够到位", "还不够到位",
    "有待加强", "尚需完善", "需要进一步",
    "建议式",  # "建议式定性"
]

# 应知应会/空洞建议词（七、审计建议操作性）
FORBIDDEN_HOLLOW_SUGGESTIONS = [
    "遵守财经纪律", "加强财务管理", "提高思想认识",
    "高度重视", "认真对待", "切实落实",
    "严格执行", "加强管理",
]

# 建议式定性标志（二、问题定性准确性）
DINGXING_SUGGESTION_PATTERN = re.compile(
    r'(建议|应当|应该|需要)(加强|完善|改进|提高|规范|强化|进一步)'
)


# ---------------------------------------------------------------------------
# Pattern definitions for structure checks
# ---------------------------------------------------------------------------

# 内容矛盾检测（一、十）
CONTRADICTION_PATTERNS = [
    (r'总体.*较好.*但.*严重', '评价正面但问题负面程度冲突'),
    (r'基本合规.*但.*重大违规', '评价"基本合规"与"重大违规"矛盾'),
    (r'较好.*同时.*存在问题', '正面评价后直接接问题（需确认是否合理过渡）'),
]

# 八种责任界限缺失关键词检测（六）
RESPONSIBILITY_BOUNDARY_KEYWORDS = {
    "集体决策与个人主张": ["集体决策", "个人主张", "个人决定"],
    "决策与监管": ["决策责任", "监管责任", "监督责任"],
    "决策失误与管理不力": ["决策失误", "管理不力", "管理不善"],
    "决策责任与执行责任": ["决策责任", "执行责任"],
    "工作失职与工作失误": ["工作失职", "工作失误"],
    "主观故意与客观过失": ["主观故意", "客观制约", "无意过失"],
    "党委与行政": ["党委", "行政"],
    "前任与后任": ["前任", "后任"],
}

# 救济途径关键词（五、十）
REMEDY_KEYWORDS = [
    "行政复议", "行政诉讼", "申请复议", "提起诉讼",
    "救济途径", "救济期限",
]

# 整改公告关键词（十）
RECTIFICATION_KEYWORDS = [
    "整改", "公告", "整改情况",
]


# ---------------------------------------------------------------------------
# Section Detection
# ---------------------------------------------------------------------------

SECTION_PATTERNS = {
    "审计评价": re.compile(r'(审计评价|评价意见|综合评价)'),
    "审计发现|问题": re.compile(r'(审计发现|存在的问题|主要问题|问题定性)'),
    "审计建议": re.compile(r'(审计建议|意见建议|建议)'),
    "责任界定": re.compile(r'(责任认定|责任界定|应承担|领导责任|直接责任)'),
    "处理处罚": re.compile(r'(处理处罚|处理意见|处罚意见)'),
    "依据引用": re.compile(r'([依据根据].*规定|法律法规|政策依据)'),
    "基本情况": re.compile(r'(基本情况|被审计单位|单位概况)'),
    "整改要求": re.compile(r'(整改|整改要求|整改期限)'),
}


# ---------------------------------------------------------------------------
# Text Quality Filter
# ---------------------------------------------------------------------------

class TextQualityFilter:
    """
    Evaluates audit report text quality against the 10-dimension checklist.

    Usage:
        tqf = TextQualityFilter()
        results = tqf.evaluate(report_text, sections=parsed_sections)
        classified = tqf.classify(results)
        score = tqf.score(results)
    """

    def __init__(self, rules_path: Optional[str] = None,
                 report_category: str = "government_audit"):
        """
        Args:
            rules_path: path to YAML rules file. If None, uses built-in rules.
            report_category: 'government_audit' | 'cpa_attestation' | 'internal_audit'
                Controls which rules are active. CPA reports skip 处理处罚/责任界定/第三人称 rules.
        """
        self.report_category = report_category
        self.rules: list[TextQualityRule] = []
        self._load_rules(rules_path)

    def _load_rules(self, rules_path: Optional[str] = None) -> None:
        """Load rules from YAML or use built-in defaults."""
        if rules_path:
            path = Path(rules_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                if raw and "rules" in raw:
                    for r in raw["rules"]:
                        rule = TextQualityRule(**r)
                        if rule.applies_to(self.report_category):
                            self.rules.append(rule)
                return

        # Built-in rules
        self._register_builtin_rules()

    def _register_builtin_rules(self) -> None:
        """Register all 10 dimensions of built-in rules."""
        rules = []

        # ================================================================
        # Dimension 1: 审计评价恰当性 (8 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-1.1", "1", "审计评价的恰当性",
                "检查评价中是否有主观难取证词汇", severity="error",
                detect_type="forbidden_word",
                pattern="|".join(FORBIDDEN_SUBJECTIVE_EVAL),
                wei_score=1.0),
            TextQualityRule("TQ-1.2", "1", "审计评价的恰当性",
                "检查是否评价了党建、人事任命等越权事项", severity="error",
                detect_type="forbidden_word",
                pattern="(党建|人事任命|干部选拔|民主生活会|组织生活)",
                categories="government_audit"),
            TextQualityRule("TQ-1.3", "1", "审计评价的恰当性",
                "检查评价与问题是否矛盾（正面评价后紧跟负面问题）", severity="warning",
                detect_type="cross_check",
                check_fn="check_eval_problem_contradiction",
                wei_score=1.0),
            TextQualityRule("TQ-1.4", "1", "审计评价的恰当性",
                "检查是否只有定性评价无定量指标", severity="warning",
                detect_type="structure",
                check_fn="check_qualitative_only_eval",
                wei_score=0.8),
            TextQualityRule("TQ-1.5", "1", "审计评价的恰当性",
                "检查是否有静态/历史数据简单定量评价（仅有增长/下降百分比无分析）", severity="info",
                detect_type="pattern",
                pattern=r'(同比增长|环比增长|比上年|较去年同期)[^。]*?(?![，,].*?[原因由于因为])',
                wei_score=0.5),
        ])

        # ================================================================
        # Dimension 2: 问题定性准确性 (11 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-2.1", "2", "问题定性的准确性",
                "检查定性小标题是否含'不到位''不够到位'等无实质区别词", severity="error",
                detect_type="forbidden_word",
                pattern="|".join(FORBIDDEN_VAGUE_DINGXING),
                wei_score=1.5),
            TextQualityRule("TQ-2.2", "2", "问题定性的准确性",
                "检查是否存在'建议式'定性（用建议代替定性）", severity="error",
                detect_type="pattern",
                check_fn="check_suggestion_as_dingxing",
                wei_score=1.5),
            TextQualityRule("TQ-2.3", "2", "问题定性的准确性",
                "检查定性小标题是否为'性质+数量金额比例'写实结构", severity="warning",
                detect_type="structure",
                check_fn="check_dingxing_title_format",
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-2.4", "2", "问题定性的准确性",
                "检查有无越权定性（如超编、出国绕道等非审计职责事项）", severity="error",
                detect_type="pattern",
                pattern=r'(超人员编制|出国.*绕道|未集中保管.*护照|因私护照)',
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-2.5", "2", "问题定性的准确性",
                "检查是否存在小题大做/避重就轻/以偏概全的风险标志", severity="warning",
                detect_type="pattern",
                pattern=r'(比计划延迟\d+天|测试数据.*未.*删除|固定资产.*账实不符.*管理不规范)',
                wei_score=0.8),
        ])

        # ================================================================
        # Dimension 3: 事实表述清晰性 (10 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-3.1", "3", "事实表述的清晰性",
                "检查是否有'审计认为'等主观判断词", severity="error",
                detect_type="forbidden_word",
                pattern="|".join(FORBIDDEN_SUBJECTIVE_JUDGMENT),
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-3.2", "3", "事实表述的清晰性",
                "检查是否有程度强调词（严重亏损/非常缓慢等）", severity="warning",
                detect_type="forbidden_word",
                pattern="|".join(FORBIDDEN_DEGREE_WORDS),
                wei_score=1.0),
            TextQualityRule("TQ-3.3", "3", "事实表述的清晰性",
                "检查是否有模糊/不确定表述", severity="error",
                detect_type="forbidden_word",
                pattern="|".join(FORBIDDEN_VAGUE_WORDS),
                wei_score=1.0),
            TextQualityRule("TQ-3.4", "3", "事实表述的清晰性",
                "检查是否有绝对化表述", severity="warning",
                detect_type="forbidden_word",
                pattern="|".join(FORBIDDEN_ABSOLUTE_WORDS),
                wei_score=1.0),
            TextQualityRule("TQ-3.5", "3", "事实表述的清晰性",
                "检查问题事实是否包含时间（六要素之时间）", severity="warning",
                detect_type="structure",
                check_fn="check_time_presence_in_issues",
                wei_score=0.8),
            TextQualityRule("TQ-3.6", "3", "事实表述的清晰性",
                "检查问题事实是否明确相关人员身份责任", severity="warning",
                detect_type="structure",
                check_fn="check_person_responsibility_mention",
                categories="government_audit",
                wei_score=0.8),
            TextQualityRule("TQ-3.7", "3", "事实表述的清晰性",
                "检查是否有'流水式'表述（超过300字无分段且无数据）", severity="info",
                detect_type="structure",
                check_fn="check_verbose_prose",
                wei_score=0.5),
        ])

        # ================================================================
        # Dimension 4: 依据引用合理性 (12 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-4.1", "4", "依据引用的合理性",
                "检查是否引用'处罚处分条例'作为定性依据", severity="error",
                detect_type="pattern",
                pattern=r'(财政违法行为处罚处分条例|处分条例|处罚条例).*?定性',
                categories="government_audit",
                wei_score=1.5),
            TextQualityRule("TQ-4.2", "4", "依据引用的合理性",
                "检查是否引用处理处罚种类条文作为定性依据（审计法第45/46条）", severity="error",
                detect_type="pattern",
                pattern=r'(审计法.*第[四四]十[五六]条).*?定性',
                categories="government_audit",
                wei_score=1.5),
            TextQualityRule("TQ-4.3", "4", "依据引用的合理性",
                "检查是否有'参照执行'引用但未说明前提条件", severity="warning",
                detect_type="pattern",
                pattern=r'参照执行',
                wei_score=1.0),
            TextQualityRule("TQ-4.4", "4", "依据引用的合理性",
                "检查是否可能用现行依据衡量过去事项", severity="info",
                detect_type="cross_check",
                check_fn="check_temporal_basis_mismatch",
                wei_score=0.5),
            TextQualityRule("TQ-4.5", "4", "依据引用的合理性",
                "检查是否引用了非执法主体法规作为处理处罚依据", severity="error",
                detect_type="pattern",
                pattern=r'(招标投标法|土地管理法).*?处理处罚',
                categories="government_audit",
                wei_score=1.5),
        ])

        # ================================================================
        # Dimension 5: 处理处罚合法性 (11 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-5.1", "5", "处理处罚的合法性",
                "检查是否有越权处罚（责令停业/暂扣吊销许可证等）", severity="error",
                detect_type="pattern",
                pattern=r'(责令停业|暂扣.*许可证|吊销.*许可证|降低收费标准|追究.*党纪.*责任|追究.*政务.*责任)',
                categories="government_audit",
                wei_score=2.0),
            TextQualityRule("TQ-5.2", "5", "处理处罚的合法性",
                "检查是否用'将出具审计决定'代替处理处罚意见", severity="error",
                detect_type="pattern",
                pattern=r'将出具审计决定|拟出具审计决定',
                categories="government_audit",
                wei_score=1.5),
            TextQualityRule("TQ-5.3", "5", "处理处罚的合法性",
                "检查救济途径和期限是否完整", severity="error",
                detect_type="structure",
                check_fn="check_remedy_completeness",
                categories="government_audit",
                wei_score=1.5),
            TextQualityRule("TQ-5.4", "5", "处理处罚的合法性",
                "检查是否以审计处理代替审计处罚（或反之）", severity="warning",
                detect_type="cross_check",
                check_fn="check_handle_penalty_confusion",
                categories="government_audit",
                wei_score=1.0),
        ])

        # ================================================================
        # Dimension 6: 责任界定科学性 (16 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-6.1", "6", "责任界定的科学性",
                "检查责任认定是否厘清八大界限", severity="warning",
                detect_type="structure",
                check_fn="check_responsibility_boundaries",
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-6.2", "6", "责任界定的科学性",
                "检查是否简单以主持会议/签批文件/直接分管作为定责标准", severity="warning",
                detect_type="pattern",
                pattern=r'(主持.*会议|签批.*文件|直接分管).*?承担.*责任',
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-6.3", "6", "责任界定的科学性",
                "检查是否有'由事及人'的说理性表述", severity="info",
                detect_type="structure",
                check_fn="check_event_to_person_reasoning",
                categories="government_audit",
                wei_score=0.5),
        ])

        # ================================================================
        # Dimension 7: 审计建议操作性 (10 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-7.1", "7", "审计建议的操作性",
                "检查建议是否以应知应会空洞内容代替", severity="warning",
                detect_type="forbidden_word",
                pattern="|".join(FORBIDDEN_HOLLOW_SUGGESTIONS),
                wei_score=1.0),
            TextQualityRule("TQ-7.2", "7", "审计建议的操作性",
                "检查是否用审计建议代替揭示问题", severity="error",
                detect_type="cross_check",
                check_fn="check_suggestion_instead_of_issue",
                categories="government_audit",
                wei_score=1.5),
            TextQualityRule("TQ-7.3", "7", "审计建议的操作性",
                "检查是否用审计建议代替处理处罚", severity="error",
                detect_type="cross_check",
                check_fn="check_suggestion_instead_of_penalty",
                categories="government_audit",
                wei_score=1.5),
            TextQualityRule("TQ-7.4", "7", "审计建议的操作性",
                "检查建议数量是否在3-5条范围内", severity="info",
                detect_type="structure",
                check_fn="check_suggestion_count",
                wei_score=0.5),
            TextQualityRule("TQ-7.5", "7", "审计建议的操作性",
                "检查建议是否超越审计职权（如建议修改预算法的表述）", severity="error",
                detect_type="pattern",
                pattern=r'(建议.*修改.*预算法|建议.*增加.*编制|建议.*增加.*投资)',
                categories="government_audit",
                wei_score=1.5),
        ])

        # ================================================================
        # Dimension 8: 采纳意见合理性 (10 checks) - mostly manual
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-8.1", "8", "采纳意见的合理性",
                "检查签证/反馈/审理意见采纳记录是否完整", severity="info",
                detect_type="structure",
                check_fn="check_adoption_record_completeness",
                categories="government_audit",
                wei_score=0.5),
        ])

        # ================================================================
        # Dimension 9: 同类问题一致性 (8 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-9.1", "9", "同类问题的一致性",
                "检查同类问题定性标题是否表述一致", severity="warning",
                detect_type="cross_check",
                check_fn="check_similar_issue_title_consistency",
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-9.2", "9", "同类问题的一致性",
                "检查同类问题处理处罚是否一致", severity="warning",
                detect_type="cross_check",
                check_fn="check_similar_issue_penalty_consistency",
                categories="government_audit",
                wei_score=1.0),
        ])

        # ================================================================
        # Dimension 10: 报告格式规范性 (16 checks)
        # ================================================================
        rules.extend([
            TextQualityRule("TQ-10.1", "10", "报告格式的规范性",
                "检查是否以第三人称撰写（避免第一人称'我局''我们'）", severity="error",
                detect_type="pattern",
                pattern=r'我局|我们|我厅',
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-10.2", "10", "报告格式的规范性",
                "检查问题排序是否符合规范（资产流失/财政损失在前）", severity="warning",
                detect_type="structure",
                check_fn="check_issue_ordering",
                categories="government_audit",
                wei_score=1.0),
            TextQualityRule("TQ-10.3", "10", "报告格式的规范性",
                "检查报告中简称、单位、日期表述是否前后一致", severity="warning",
                detect_type="cross_check",
                check_fn="check_terminology_consistency",
                wei_score=1.0),
            TextQualityRule("TQ-10.4", "10", "报告格式的规范性",
                "检查小数点是否保留2位（金额类数字）", severity="info",
                detect_type="pattern",
                check_fn="check_decimal_places",
                wei_score=0.5),
            TextQualityRule("TQ-10.5", "10", "报告格式的规范性",
                "检查经济责任审计报告是否含救济途径和期限", severity="error",
                detect_type="structure",
                check_fn="check_remedy_in_econ_accountability",
                categories="government_audit",
                wei_score=1.5),
            TextQualityRule("TQ-10.6", "10", "报告格式的规范性",
                "检查报告中是否有整改和公告相关表述", severity="warning",
                detect_type="structure",
                check_fn="check_rectification_statement",
                wei_score=1.0),
            TextQualityRule("TQ-10.7", "10", "报告格式的规范性",
                "检查是否按会计要素（资产/负债/损益）分类问题（不推荐）", severity="info",
                detect_type="structure",
                check_fn="check_accounting_element_classification",
                wei_score=0.5),
        ])

        # Filter by report category
        self.rules = [r for r in rules if r.applies_to(self.report_category)]

    # ================================================================
    # Main evaluation pipeline
    # ================================================================

    def evaluate(self, report_text: str,
                 sections: Optional[dict[str, str]] = None,
                 report_type: str = "general") -> list[TextQualityResult]:
        """
        Evaluate report text against all registered rules.

        Args:
            report_text: Full report text
            sections: Pre-parsed sections {section_name: text}
            report_type: 'general' | 'econ_accountability' | 'natural_resources'

        Returns:
            List of TextQualityResult objects
        """
        if sections is None:
            sections = self._parse_sections(report_text)

        results = []
        for rule in self.rules:
            res = self._evaluate_rule(rule, report_text, sections, report_type)
            if res is not None:
                results.append(res)

        return results

    def _parse_sections(self, text: str) -> dict[str, str]:
        """Heuristic section parser based on common audit report headers."""
        sections: dict[str, str] = {"_full": text}

        # Common section header patterns in Chinese audit reports
        header_pattern = re.compile(
            r'(?:^|\n)\s*(?:[一二三四五六七八九十]+[、．.]\s*)?'
            r'(被审计单位基本情况|基本情况|审计评价|审计评价意见|'
            r'审计发现|审计发现的主要问题|存在的问题|主要问题|'
            r'审计调查发现的主要问题|'
            r'审计建议|意见建议|审计处理处罚意见|处理意见|处罚意见|'
            r'责任认定|责任界定|'
            r'审计处理情况|'
            r'整改要求|整改情况|'
            r'其他需要说明的问题|其他需要反映的情况)'
            r'[：:]',
            re.MULTILINE,
        )

        matches = list(header_pattern.finditer(text))
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_name = m.group(1).strip()
            sections[section_name] = text[start:end].strip()

        return sections

    def _evaluate_rule(self, rule: TextQualityRule,
                       text: str, sections: dict[str, str],
                       report_type: str) -> Optional[TextQualityResult]:
        """Evaluate a single rule and return a result."""
        if rule.detect_type == "forbidden_word":
            return self._check_forbidden_word(rule, text, sections)
        elif rule.detect_type == "pattern":
            return self._check_pattern(rule, text, sections)
        elif rule.detect_type == "structure":
            # Delegate to named check function
            if rule.check_fn and hasattr(self, rule.check_fn):
                fn = getattr(self, rule.check_fn)
                return fn(rule, text, sections, report_type)
        elif rule.detect_type == "cross_check":
            if rule.check_fn and hasattr(self, rule.check_fn):
                fn = getattr(self, rule.check_fn)
                return fn(rule, text, sections, report_type)
        return None

    def _check_forbidden_word(self, rule: TextQualityRule,
                              text: str, sections: dict[str, str]) -> TextQualityResult:
        """Scan for forbidden words in text."""
        pattern = re.compile(rule.pattern) if rule.pattern else None
        if not pattern:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=True, detail="无匹配模式"
            )

        matches = list(pattern.finditer(text))
        if not matches:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=True, detail="未发现违禁词"
            )

        # Build excerpt from first few matches
        excerpts = []
        for m in matches[:5]:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 20)
            ctx = text[start:end].replace("\n", " ")
            excerpts.append(f"...{ctx}...")

        match_word = m.group() if matches else ""
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=False,
            excerpt="\n".join(excerpts),
            section=self._locate_section(matches[0].start(), sections),
            detail=f"发现 {len(matches)} 处匹配: {match_word}",
            suggestion=f"请修改或删除违禁词'{match_word}'",
        )

    def _check_pattern(self, rule: TextQualityRule,
                       text: str, sections: dict[str, str]) -> TextQualityResult:
        """Check against a regex pattern."""
        if not rule.pattern:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=True, detail="无匹配模式"
            )

        pattern = re.compile(rule.pattern)
        matches = list(pattern.finditer(text))

        if not matches:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=True, detail="未发现模式匹配"
            )

        excerpts = []
        for m in matches[:5]:
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            ctx = text[start:end].replace("\n", " ")
            excerpts.append(f"...{ctx}...")

        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=False,
            excerpt="\n".join(excerpts),
            section=self._locate_section(matches[0].start(), sections),
            detail=f"发现 {len(matches)} 处风险匹配",
            suggestion=f"请检查模式: {rule.pattern[:80]}...",
        )

    # ================================================================
    # Named check functions (structure / cross_check types)
    # ================================================================

    def check_eval_problem_contradiction(self, rule, text, sections, report_type):
        """检测评价与问题是否前后矛盾（一、十）"""
        eval_section = ""
        problem_section = ""
        for key, val in sections.items():
            if "评价" in key:
                eval_section = val
            if "问题" in key or "发现" in key:
                problem_section = val

        passed = True
        detail = ""
        if eval_section and problem_section:
            # Check for positive evaluation + serious problem co-occurrence
            positive_in_eval = re.findall(r'(较好|良好|规范|合规|正常|健全|完善)', eval_section)
            serious_in_problem = re.findall(r'(严重|重大|巨大|巨额|违规|违法|犯罪)', problem_section)
            if positive_in_eval and serious_in_problem:
                passed = False
                detail = f"审计评价含正面词({','.join(positive_in_eval[:3])})，但问题部分含严重词({','.join(serious_in_problem[:3])})，需确认是否矛盾"

        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=passed, detail=detail or "未发现矛盾",
            requires_human_review=not passed,
        )

    def check_qualitative_only_eval(self, rule, text, sections, report_type):
        """检测评价是否只有定性无定量数据"""
        eval_section = ""
        for key, val in sections.items():
            if "评价" in key:
                eval_section = val
                break
        if not eval_section:
            eval_section = text

        has_numbers = bool(re.search(r'\d+\.?\d*万?亿?元?%?', eval_section))
        has_qualitative = bool(re.search(r'(较好|良好|规范|合规|健全|完善|有效)', eval_section))

        if has_qualitative and not has_numbers:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail="审计评价有定性表述但缺乏定量数据支撑",
                suggestion="建议增加具体数据指标（比率、金额、数量等）",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="评价包含定量数据"
        )

    def check_suggestion_as_dingxing(self, rule, text, sections, report_type):
        """检测是否以建议式表述作为问题定性"""
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break

        matches = list(DINGXING_SUGGESTION_PATTERN.finditer(problem_section or text))
        if matches:
            excerpts = []
            for m in matches[:3]:
                start = max(0, m.start() - 20)
                end = min(len(text), m.end() + 20)
                excerpts.append(text[start:end].replace("\n", " "))
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                excerpt="\n".join(excerpts),
                detail=f"发现 {len(matches)} 处建议式定性",
                suggestion="请将建议式表述改为'性质+数量金额比例'写实定性",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="未发现建议式定性"
        )

    def check_dingxing_title_format(self, rule, text, sections, report_type):
        """检测定性小标题是否为'性质+数量金额比例'写实结构"""
        # Look for problem titles in the problem section
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break
        if not problem_section:
            problem_section = text

        # Find potential issue titles (numbered items)
        title_pattern = re.compile(
            r'(?:^|\n)\s*(?:\d+[\.、．)]\s*|（[一二三四五六七八九十]+）\s*)'
            r'([^\n]{10,60})',
            re.MULTILINE,
        )
        titles = title_pattern.findall(problem_section)

        bad_titles = []
        for t in titles[:10]:
            has_number = bool(re.search(r'\d+\.?\d*万?亿?元?%?', t))
            has_nature = bool(re.search(
                r'(违规|违法|挤占|挪用|虚列|套取|截留|滞留|闲置|'
                r'少计|多计|漏记|未按规定|未执行|未履行)', t
            ))
            if not (has_nature or has_number):
                bad_titles.append(t)

        if bad_titles:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                excerpt="\n".join(bad_titles[:3]),
                detail=f"{len(bad_titles)}个定性标题缺乏'性质+数量金额比例'结构",
                suggestion="定性小标题应包含问题性质和数量金额比例",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="定性标题格式基本合规"
        )

    def check_time_presence_in_issues(self, rule, text, sections, report_type):
        """检测问题事实是否包含时间"""
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break
        if not problem_section:
            problem_section = text

        # Split into individual issues (by numbered items)
        issues = re.split(r'\n\s*(?:\d+[\.、．)]|\（[一二三四五六七八九十]+）)', problem_section)
        issues = [i.strip() for i in issues if len(i.strip()) > 50]

        missing_time = 0
        for issue in issues:
            has_time = bool(re.search(
                r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月|\d{4}年|'
                r'\d{4}-\d{2}-\d{2}|\d{4}\.\d{2}\.\d{2}',
                issue
            ))
            if not has_time:
                missing_time += 1

        if missing_time > 0:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False if missing_time > len(issues) * 0.3 else True,
                detail=f"{missing_time}/{len(issues)}个问题未明确发生时间",
                suggestion="问题事实应包含明确的发生时间",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="问题时间要素齐全"
        )

    def check_person_responsibility_mention(self, rule, text, sections, report_type):
        """检测问题是否明确相关人员身份责任"""
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break
        if not problem_section:
            problem_section = text

        has_person_mention = bool(re.search(
            r'(直接责任|领导责任|主体责任|监督责任|管理责任|'
            r'国家工作人员|国家机关工作人员|相关责任人)',
            problem_section
        ))

        if not has_person_mention:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail="问题部分未明确相关人员身份和责任",
                suggestion="应在问题事实中明确相关人员身份（国家工作人员/国家机关工作人员）和责任类型",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="已明确相关人员责任"
        )

    def check_verbose_prose(self, rule, text, sections, report_type):
        """检测是否有流水式表述"""
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break

        long_paragraphs = re.findall(r'[^。\n]{300,}', problem_section or text)
        if long_paragraphs:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail=f"发现 {len(long_paragraphs)} 处超过300字无分段的流水式表述",
                suggestion="请精简表述，过滤无关干扰因素，突出关键信息",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="表述简洁"
        )

    def check_temporal_basis_mismatch(self, rule, text, sections, report_type):
        """检测是否可能用现行依据衡量过去事项"""
        # Heuristic: check if there are old dates + new regulation references
        old_dates = re.findall(r'(201\d|202[0-2])\D', text)
        new_regs = re.findall(
            r'(202[3-6]年.*?[法规条例办法通知规定])|'
            r'(最新.*?规定|新.*?条例|新修订)',
            text
        )
        if old_dates and new_regs:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail=f"发现问题涉及较早日期({old_dates[:3]})同时引用较新法规，请核实是否适用",
                suggestion="不能用现行依据简单衡量过去的事项",
                requires_human_review=True,
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="未发现时间与依据不匹配"
        )

    def check_remedy_completeness(self, rule, text, sections, report_type):
        """检测救济途径和期限是否完整"""
        if report_type in ("econ_accountability", "natural_resources"):
            has_remedy = any(kw in text for kw in REMEDY_KEYWORDS)
            if not has_remedy:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail="经济责任/自然资源资产审计报告缺少救济途径和期限",
                    suggestion="请在报告结尾增加行政复议、行政诉讼等救济途径和期限说明",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="救济途径完整"
        )

    def check_handle_penalty_confusion(self, rule, text, sections, report_type):
        """检测处理与处罚是否混用"""
        # Heuristic: check if same paragraph mentions both 处理 and 处罚 interchangeably
        both = re.findall(r'(审计处理|审计处罚)', text)
        unique = set(both)
        if len(unique) == 2:
            # Count occurrences
            handle_count = both.count("审计处理")
            penalty_count = both.count("审计处罚")
            if abs(handle_count - penalty_count) <= 2:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail="报告中'审计处理'与'审计处罚'术语混用，请区分",
                    suggestion="审计处理限于审计法第45条种类，审计处罚限于警告、罚款、没收违法所得，二者不可相互替代",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="处理处罚术语使用规范"
        )

    def check_responsibility_boundaries(self, rule, text, sections, report_type):
        """检测责任界定是否厘清八大界限"""
        responsibility_section = ""
        for key, val in sections.items():
            if "责任" in key:
                responsibility_section = val
                break
        if not responsibility_section:
            responsibility_section = text

        missing_boundaries = []
        for boundary_name, keywords in RESPONSIBILITY_BOUNDARY_KEYWORDS.items():
            found = any(kw in responsibility_section for kw in keywords)
            if not found:
                missing_boundaries.append(boundary_name)

        if len(missing_boundaries) > 4:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail=f"责任界定部分缺少以下界限的辨析: {', '.join(missing_boundaries[:4])}",
                suggestion="责任认定需厘清八大界限：集体决策/个人主张、决策/监管、决策失误/管理不力、决策责任/执行责任、工作失职/工作失误、主观故意/客观过失、党委/行政、前任/后任",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="责任界限辨析基本完整"
        )

    def check_event_to_person_reasoning(self, rule, text, sections, report_type):
        """检测是否有由事及人的说理性表述"""
        responsibility_section = ""
        for key, val in sections.items():
            if "责任" in key:
                responsibility_section = val
                break
        if not responsibility_section:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=True, detail="未找到责任认定章节"
            )

        # Check for reasoning patterns
        has_reasoning = bool(re.search(
            r'(经查|经审计|经核实|综上所述|综上|因此|故|鉴于|考虑到)',
            responsibility_section
        ))
        if not has_reasoning:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail="责任认定部分缺少'由事及人'的说理性表述",
                suggestion="责任认定应有充分的证据，进行由事及人的说理性表述",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="有由事及人的说理"
        )

    def check_suggestion_instead_of_issue(self, rule, text, sections, report_type):
        """检测是否用审计建议代替揭示问题"""
        suggestion_section = ""
        for key, val in sections.items():
            if "建议" in key:
                suggestion_section = val
                break

        if suggestion_section:
            # Check if suggestion section contains problem-revealing language
            problem_like = re.findall(r'(发现|存在|问题|违规|违法)', suggestion_section)
            if problem_like:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail="审计建议部分含问题揭示性语言，疑似用建议代替揭示问题",
                    suggestion="审计建议应针对已揭示的问题提出整改措施，不应在此处再次揭示新问题",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="建议与问题揭示分离"
        )

    def check_suggestion_instead_of_penalty(self, rule, text, sections, report_type):
        """检测是否用审计建议代替处理处罚"""
        suggestion_section = ""
        for key, val in sections.items():
            if "建议" in key:
                suggestion_section = val
                break

        if suggestion_section:
            penalty_like = re.findall(
                r'(罚款|收缴|没收|退还|责令|警告)',
                suggestion_section
            )
            if penalty_like:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail="审计建议部分含处理处罚性语言，疑似用建议代替处理处罚",
                    suggestion="处理处罚应在专门章节明确，不应以建议形式提出",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="建议与处理处罚分离"
        )

    def check_suggestion_count(self, rule, text, sections, report_type):
        """检测建议数量是否在3-5条"""
        suggestion_section = ""
        for key, val in sections.items():
            if "建议" in key:
                suggestion_section = val
                break

        if suggestion_section:
            count = len(re.findall(r'\n\s*(?:\d+[\.、．)]|\（[一二三四五六七八九十]+）)', suggestion_section))
            if count == 0:
                count = len(re.findall(r'[。；]\s*(?:\d+[\.、．)])', suggestion_section))
            if count > 5:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail=f"审计建议共{count}条，超过建议的3-5条范围，可能不够聚焦",
                    suggestion="建议精简至3-5条核心建议",
                )
            elif count < 3:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail=f"审计建议仅{count}条，可能覆盖不足",
                    suggestion="建议扩充至3-5条，覆盖主要问题",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="建议数量合适"
        )

    def check_adoption_record_completeness(self, rule, text, sections, report_type):
        """检测采意记录完整度（标记需人工复核）"""
        # This is mostly a manual check - flag for human review
        has_adoption_mention = bool(re.search(
            r'(反馈意见|签证意见|审理意见|采纳|反馈|征求意见)',
            text
        ))
        if not has_adoption_mention:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail="报告中未发现采纳反馈/审理意见的记录",
                suggestion="报告应包含被审计对象反馈意见和审理意见的采纳情况",
                requires_human_review=True,
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="有采纳记录"
        )

    def check_similar_issue_title_consistency(self, rule, text, sections, report_type):
        """检测同类问题定性标题一致性（标记需人工复核）"""
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break
        if not problem_section:
            problem_section = text

        # Extract issue titles
        titles = re.findall(
            r'(?:^|\n)\s*(?:\d+[\.、．)]|（[一二三四五六七八九十]+）)\s*([^\n]{5,50})',
            problem_section,
            re.MULTILINE
        )
        unique_titles = set(t.strip() for t in titles)

        if len(unique_titles) < len(titles) * 0.5:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail="同类问题标题可能存在表述不一致",
                suggestion="同类问题定性标题应保持一致，不同问题应具体分析差异化原因并在报告中说明",
                requires_human_review=True,
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="标题一致性良好"
        )

    def check_similar_issue_penalty_consistency(self, rule, text, sections, report_type):
        """检测同类问题处理处罚一致性（标记需人工复核）"""
        # Flag for human review - hard to automate without deep semantic analysis
        penalty_count = len(re.findall(
            r'(罚款|收缴|没收|退还|责令|警告|移送)',
            text
        ))
        if penalty_count > 0:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=True, detail=f"检测到{penalty_count}处处理处罚表述，请人工确认一致性",
                requires_human_review=True,
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="无处罚事项"
        )

    def check_issue_ordering(self, rule, text, sections, report_type):
        """检测问题排序是否符合规范"""
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break

        if problem_section:
            # Check for accounting-element classification (not recommended)
            element_headers = re.findall(
                r'(资产.*问题|负债.*问题|损益.*问题|收入.*问题|支出.*问题)',
                problem_section
            )
            if element_headers:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail=f"问题按会计要素分类: {', '.join(element_headers[:3])}，建议改为按重要性排序",
                    suggestion="问题应按重要性排序（国有资产流失/财政损失→实质处理处罚→移送追责→本级问题→下属问题→共性问题→个性问题→定责问题→督查整改），不建议按会计要素分类",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="问题排序基本合规"
        )

    def check_terminology_consistency(self, rule, text, sections, report_type):
        """检测术语/简称/单位一致性"""
        # Check for abbreviation definitions: (XXX, 下称 YYY) or （XXX，简称YYY）
        abbr_patterns = [
            r'\(([^)]*(?:简称|下称)[^)]*)\)',
            r'\uff08([^\uff09]*(?:简称|下称)[^\uff09]*)\uff09',
        ]
        abbreviations = []
        for pat in abbr_patterns:
            abbreviations.extend(re.findall(pat, text))

        if len(abbreviations) > 1:
            for abbr in abbreviations:
                abbr_name = re.sub(r'(简称|下称)', '', abbr).strip()
                if abbr_name and len(abbr_name) > 2:
                    # Check if abbreviation is used consistently
                    full_count = text.count(abbr_name)
                    if full_count > 0:
                        prefix = abbr_name[:2]
                        short_forms = re.findall(
                            re.escape(prefix) + r'[\w\u4e00-\u9fff]{1,4}',
                            text
                        )
                        if short_forms and len(set(short_forms)) > 1:
                            return TextQualityResult(
                                rule_id=rule.rule_id, dimension=rule.dimension,
                                dimension_name=rule.dimension_name,
                                description=rule.description, severity=rule.severity,
                                passed=False,
                                detail=f'简称 "{abbr_name}" 在全文中使用不一致',
                                suggestion="简称、单位、日期表述应前后一致",
                                requires_human_review=True,
                            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="术语使用基本一致"
        )

    def check_decimal_places(self, rule, text, sections, report_type):
        """检测金额类数字小数位数"""
        # Find monetary amounts with wrong decimal places
        amounts = re.findall(r'(\d+\.\d{3,})\s*(万元|元|亿元)', text)
        amounts_bad = [a for a in amounts if '.' in a[0] and len(a[0].split('.')[1]) != 2]

        # Also check for amounts with only 1 decimal or no decimals in a context where others have 2
        amounts_1dp = re.findall(r'(\d+\.\d)\s*(万元|元|亿元)', text)

        bad_count = len(amounts_bad) + len(amounts_1dp)
        if bad_count > 3:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail=f"发现 {bad_count} 处金额小数位数不规范（应为2位）",
                suggestion="金额类数字小数点后保留2位",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="小数位数规范"
        )

    def check_remedy_in_econ_accountability(self, rule, text, sections, report_type):
        """检测经济责任审计报告是否含救济途径"""
        if report_type == "econ_accountability":
            has_remedy = any(kw in text for kw in REMEDY_KEYWORDS)
            if not has_remedy:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail="经济责任审计报告未包含救济途径和期限",
                    suggestion="经济责任审计报告结尾应包含行政复议、行政诉讼等救济途径和期限",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="已包含救济途径"
        )

    def check_rectification_statement(self, rule, text, sections, report_type):
        """检测报告中是否有整改和公告相关表述"""
        has_rectify = any(kw in text for kw in RECTIFICATION_KEYWORDS)
        if not has_rectify:
            return TextQualityResult(
                rule_id=rule.rule_id, dimension=rule.dimension,
                dimension_name=rule.dimension_name,
                description=rule.description, severity=rule.severity,
                passed=False,
                detail="报告未包含整改和公告的相关表述",
                suggestion="报告结尾应包含关于整改情况和结果公告的文字表述",
            )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="已包含整改公告表述"
        )

    def check_accounting_element_classification(self, rule, text, sections, report_type):
        """检测是否按会计要素分类问题"""
        problem_section = ""
        for key, val in sections.items():
            if "问题" in key or "发现" in key:
                problem_section = val
                break

        if problem_section:
            element_headers = re.findall(
                r'(?:资产|负债|所有者权益|收入|费用|损益|成本|支出)类?问题',
                problem_section
            )
            if element_headers:
                return TextQualityResult(
                    rule_id=rule.rule_id, dimension=rule.dimension,
                    dimension_name=rule.dimension_name,
                    description=rule.description, severity=rule.severity,
                    passed=False,
                    detail=f"问题按会计要素分类: {', '.join(element_headers[:3])}",
                    suggestion="不建议按会计要素分类问题，会降低报告揭示问题的深度。建议按重要性排序",
                )
        return TextQualityResult(
            rule_id=rule.rule_id, dimension=rule.dimension,
            dimension_name=rule.dimension_name,
            description=rule.description, severity=rule.severity,
            passed=True, detail="非会计要素分类"
        )

    # ================================================================
    # Classification & Scoring
    # ================================================================

    def classify(self, results: list[TextQualityResult]) -> dict[str, list]:
        """
        Classify results into confirmed / needs_review categories.
        (Text quality checks typically don't have false positives in the same way)
        """
        errors = []
        warnings = []
        infos = []
        needs_review = []

        for r in results:
            if r.requires_human_review:
                needs_review.append(r)
            elif r.severity == "error" and not r.passed:
                errors.append(r)
            elif r.severity == "warning" and not r.passed:
                warnings.append(r)
            else:
                infos.append(r)

        return {
            "errors": errors,
            "warnings": warnings,
            "info": infos,
            "needs_human_review": needs_review,
            "passed": [r for r in results if r.passed],
        }

    def score(self, results: list[TextQualityResult]) -> dict[str, Any]:
        """
        Calculate weighted quality score (0-100).

        Weights are dynamically normalized: if a dimension has no active rules
        (e.g. dimension 5-6 disabled for CPA reports), its weight is
        redistributed proportionally to the remaining active dimensions.

        Default weights per dimension:
          维度1 (评价): 10%, 维度2 (定性): 15%, 维度3 (表述): 12%,
          维度4 (依据): 12%, 维度5 (处理): 12%, 维度6 (责任): 12%,
          维度7 (建议): 10%, 维度8 (采纳): 5%,  维度9 (一致): 5%,
          维度10 (格式): 7%
        """
        default_weights = {
            "1": 0.10, "2": 0.15, "3": 0.12, "4": 0.12, "5": 0.12,
            "6": 0.12, "7": 0.10, "8": 0.05, "9": 0.05, "10": 0.07,
        }

        # Find active dimensions (those with at least one rule)
        active_dims = set(r.dimension for r in results)

        # Normalize weights: redistribute inactive dimensions proportionally
        active_total_weight = sum(default_weights.get(d, 0.0) for d in active_dims)
        if active_total_weight > 0:
            dimension_weights = {
                d: default_weights.get(d, 0.0) / active_total_weight
                for d in active_dims
            }
        else:
            dimension_weights = {d: 1.0 / len(active_dims) for d in active_dims} if active_dims else default_weights

        dim_scores: dict[str, dict] = {}
        for r in results:
            dim = r.dimension
            if dim not in dim_scores:
                dim_scores[dim] = {"total": 0, "passed": 0, "passed_weighted": 0.0}

            rule = next((rl for rl in self.rules if rl.rule_id == r.rule_id), None)
            weight = rule.wei_score if rule else 1.0

            dim_scores[dim]["total"] += weight
            if r.passed:
                dim_scores[dim]["passed_weighted"] += weight

        dim_details = {}
        total_weighted_score = 0.0

        for dim, scores in dim_scores.items():
            if scores["total"] > 0:
                dim_pct = scores["passed_weighted"] / scores["total"] * 100
            else:
                dim_pct = 100.0
            weight = dimension_weights.get(dim, 0.05)
            dim_details[f"维度{dim}"] = {
                "score": round(dim_pct, 1),
                "weight": round(weight, 3),
                "weighted": round(dim_pct * weight, 1),
            }
            total_weighted_score += dim_pct * weight

        overall = round(total_weighted_score, 1)

        # Grade
        if overall >= 90:
            grade = "优秀"
        elif overall >= 80:
            grade = "良好"
        elif overall >= 70:
            grade = "合格"
        elif overall >= 60:
            grade = "需修改"
        else:
            grade = "退回重写"

        return {
            "overall_score": overall,
            "grade": grade,
            "dimension_scores": dim_details,
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r.passed),
            "failed_checks": sum(1 for r in results if not r.passed),
            "needs_human_review": sum(1 for r in results if r.requires_human_review),
        }

    # ================================================================
    # Utility
    # ================================================================

    def _locate_section(self, pos: int, sections: dict[str, str]) -> str:
        """Locate which section a character position falls in."""
        accumulated = 0
        for name, content in sections.items():
            if name == "_full":
                continue
            section_start = accumulated
            section_end = accumulated + len(content)
            if section_start <= pos <= section_end:
                return name
            accumulated = section_end + 1
        return "未知章节"

    def generate_review_report(self, results: list[TextQualityResult],
                                report_type: str = "general") -> str:
        """Generate a Markdown text quality review report."""
        score_data = self.score(results)
        classified = self.classify(results)

        lines = [
            f"# 审计报告文本质控复核报告",
            f"",
            f"**生成时间**：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**报告类型**：{report_type}",
            f"",
            f"## 综合评分",
            f"",
            f"**总分：{score_data['overall_score']} / 100　|　等级：{score_data['grade']}**",
            f"",
            f"| 维度 | 得分 | 权重 | 加权 |",
            f"|------|------|------|------|",
        ]

        for dim, info in sorted(score_data["dimension_scores"].items()):
            dim_name = {
                "维度1": "审计评价恰当性", "维度2": "问题定性准确性",
                "维度3": "事实表述清晰性", "维度4": "依据引用合理性",
                "维度5": "处理处罚合法性", "维度6": "责任界定科学性",
                "维度7": "审计建议操作性", "维度8": "采纳意见合理性",
                "维度9": "同类问题一致性", "维度10": "报告格式规范性",
            }.get(dim, dim)
            lines.append(
                f"| {dim_name} | {info['score']} | {info['weight']:.0%} | {info['weighted']} |"
            )

        lines.extend([
            f"",
            f"## 检查概要",
            f"",
            f"- 检查总数：{score_data['total_checks']}",
            f"- 通过：{score_data['passed_checks']}",
            f"- 未通过：{score_data['failed_checks']}",
            f"- 需人工复核：{score_data['needs_human_review']}",
            f"",
        ])

        # Errors
        if classified["errors"]:
            lines.append(f"## 🔴 错误项（{len(classified['errors'])}项）")
            lines.append("")
            for r in classified["errors"]:
                lines.append(f"- **[{r.rule_id}]** {r.description}")
                if r.excerpt:
                    lines.append(f"  > 原文：{r.excerpt[:100]}...")
                if r.suggestion:
                    lines.append(f"  > 💡 {r.suggestion}")
            lines.append("")

        # Warnings
        if classified["warnings"]:
            lines.append(f"## 🟡 警告项（{len(classified['warnings'])}项）")
            lines.append("")
            for r in classified["warnings"]:
                lines.append(f"- **[{r.rule_id}]** {r.description}")
                if r.excerpt:
                    lines.append(f"  > 原文：{r.excerpt[:100]}...")
                if r.suggestion:
                    lines.append(f"  > 💡 {r.suggestion}")
            lines.append("")

        # Needs human review
        if classified["needs_human_review"]:
            lines.append(f"## 🟠 需人工复核（{len(classified['needs_human_review'])}项）")
            lines.append("")
            for r in classified["needs_human_review"]:
                lines.append(f"- **[{r.rule_id}]** {r.description}")
                if r.detail:
                    lines.append(f"  > {r.detail}")
                if r.suggestion:
                    lines.append(f"  > 💡 {r.suggestion}")
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Integration bridge: convert TextQualityResult → CheckResult
# ---------------------------------------------------------------------------

def to_check_results(tq_results: list[TextQualityResult]) -> list:
    """Convert TextQualityResults to the standard CheckResult format for ReviewReportGenerator."""
    results = []
    for tqr in tq_results:
        # Local import to avoid circular dependency
        class FakeCheckResult:
            def __init__(self, tqr):
                self.rule_id = tqr.rule_id
                self.check_type = "text_quality"
                self.domain = tqr.dimension_name
                self.description = tqr.description
                self.expected = None
                self.actual = None
                self.diff = None
                self.tolerance = 0.0
                self.severity = tqr.severity
                self.passed = tqr.passed
                self.requires_human_review = tqr.requires_human_review
                self.page_ref = tqr.page_ref
                self.excerpt = tqr.excerpt or tqr.detail
                self.sheet_context = tqr.section
                self.row_context = 0
                self.detail = tqr.suggestion or tqr.detail
                self.false_positive = tqr.false_positive
                self.false_positive_reason = tqr.false_positive_reason

        results.append(FakeCheckResult(tqr))
    return results


# ---------------------------------------------------------------------------
# Quick API
# ---------------------------------------------------------------------------

def quick_check(report_text: str, report_type: str = "general",
                 report_category: str = "government_audit") -> dict:
    """
    One-shot text quality evaluation. Returns score + classified results.

    Args:
        report_text: Full audit report text
        report_type: 'general' | 'econ_accountability' | 'natural_resources'
        report_category: 'government_audit' | 'cpa_attestation' | 'internal_audit'

    Returns:
        {score_data, classified, markdown_report}
    """
    tqf = TextQualityFilter(report_category=report_category)
    results = tqf.evaluate(report_text, report_type=report_type)
    score_data = tqf.score(results)
    classified = tqf.classify(results)
    md_report = tqf.generate_review_report(results, report_type)

    return {
        "score": score_data,
        "classified": classified,
        "markdown_report": md_report,
        "results": results,
    }
