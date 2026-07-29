"""
workpaper_scorer.preflight — 底稿提交前自检

在底稿提交复核前自动执行 6 项检查，即时反馈改进建议。
用于嵌入底稿编制 Agent 的"保存前自检"环节。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .models import (
    Workpaper,
    AUDIT_ASSERTIONS,
    ASSERTION_KEYWORDS,
    SAMPLING_METHODS,
    TEST_PROCEDURE_VERBS,
    EVIDENCE_KEYWORDS,
    EXCEPTION_KEYWORDS,
)


@dataclass
class PreflightItem:
    """单项自检结果"""
    check_id: int
    """检查项编号 1-6"""
    name: str
    """检查项名称"""
    passed: bool
    """是否通过"""
    rule: str
    """检查规则描述"""
    message: str = ""
    """详细说明"""
    suggestion: str = ""
    """改进建议（未通过时）"""


@dataclass
class PreflightResult:
    """自检结果汇总"""
    workpaper_id: str
    items: List[PreflightItem] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    all_passed: bool = False

    def summary(self) -> str:
        lines = [
            f"底稿自检: {self.workpaper_id}",
            f"通过: {self.passed_count}/6  {'✅ 全部通过' if self.all_passed else '❌ 需要修改'}",
            "",
        ]
        for item in self.items:
            status = "✅" if item.passed else "❌"
            lines.append(f"  {status} #{item.check_id} {item.name}")
            if not item.passed:
                lines.append(f"     规则: {item.rule}")
                lines.append(f"     建议: {item.suggestion}")
        return "\n".join(lines)


class PreflightChecker:
    """
    底稿提交前自检引擎。

    在 Agent 协助审计人员编制底稿时，保存前自动检查 6 项：
    1. 目标 — 是否包含认定术语？
    2. 过程 — 是否包含抽样方法和测试步骤？
    3. 结论 — 每条结论是否紧跟证据？
    4. 索引 — 引用是否有索引号？
    5. 依据 — 每个数字是否有来源标注？
    6. 差异 — 异常事项是否记录和处理？

    Usage:
        checker = PreflightChecker()
        result = checker.check(workpaper)
        if not result.all_passed:
            print(result.summary())
    """

    def check(self, wp: Workpaper) -> PreflightResult:
        full_text = wp.get_full_text()

        items = [
            self._check_1_target(full_text),
            self._check_2_process(full_text, wp),
            self._check_3_conclusion_evidence(full_text),
            self._check_4_index(full_text, wp),
            self._check_5_source(full_text),
            self._check_6_exceptions(full_text),
        ]

        passed = sum(1 for i in items if i.passed)
        failed = len(items) - passed

        return PreflightResult(
            workpaper_id=wp.id,
            items=items,
            passed_count=passed,
            failed_count=failed,
            all_passed=failed == 0,
        )

    # ── 检查 1：目标 ─────────────────────────────────────────────

    def _check_1_target(self, full_text: str) -> PreflightItem:
        has_assertion = any(
            kw.lower() in full_text.lower()
            for kw in AUDIT_ASSERTIONS + ASSERTION_KEYWORDS
        )
        return PreflightItem(
            check_id=1,
            name="目标",
            passed=has_assertion,
            rule="是否包含认定术语？",
            message="已包含认定/目标相关术语" if has_assertion else "未检测到认定术语",
            suggestion="在底稿开头补充程序目标段，使用标准认定术语（如'本程序针对…的存在性/完整性/准确性认定'）"
            if not has_assertion else "",
        )

    # ── 检查 2：过程 ─────────────────────────────────────────────

    def _check_2_process(self, full_text: str, wp: Workpaper) -> PreflightItem:
        if wp.fields:
            has_sampling = bool(wp.fields.sampling_method)
            has_procedure = bool(wp.fields.test_procedures)
        else:
            has_sampling = any(
                kw in full_text for kw in SAMPLING_METHODS
            )
            has_procedure = any(
                kw in full_text for kw in TEST_PROCEDURE_VERBS
            )

        passed = has_sampling or has_procedure
        return PreflightItem(
            check_id=2,
            name="过程",
            passed=passed,
            rule="是否包含抽样方法和测试步骤？",
            message=(
                f"抽样方法: {'✅' if has_sampling else '❌'} | "
                f"测试步骤: {'✅' if has_procedure else '❌'}"
            ),
            suggestion="补充：抽样方法类型、选取逻辑、样本量、覆盖比例、测试步骤、核查文件清单"
            if not passed else "",
        )

    # ── 检查 3：结论-证据对应 ────────────────────────────────────

    def _check_3_conclusion_evidence(self, full_text: str) -> PreflightItem:
        # 查找结论标记
        conclusion_positions = [
            m.start()
            for m in re.finditer(
                r'(?:结论[：:]|测试结果[：:]|综上[，,])',
                full_text,
            )
        ]

        if not conclusion_positions:
            return PreflightItem(
                check_id=3,
                name="结论-证据对应",
                passed=True,  # 没有显式结论段，不报错（由 scorer 处理）
                rule="每条结论是否紧跟证据？",
                message="未检测到显式结论标记，跳过检查",
            )

        # 检查每条结论自身及后续 500 字符内是否有证据关键词
        all_backed = True
        for pos in conclusion_positions:
            # 取结论自身 + 后续 500 字符
            snippet = full_text[pos: pos + 500]
            if not any(kw in snippet for kw in EVIDENCE_KEYWORDS):
                all_backed = False
                break

        return PreflightItem(
            check_id=3,
            name="结论-证据对应",
            passed=all_backed,
            rule="每条结论是否紧跟证据？",
            message="全部结论均有证据支撑" if all_backed else "部分结论缺少证据引用",
            suggestion="在每条结论后紧跟证据描述（合同号、凭证号、文件索引）"
            if not all_backed else "",
        )

    # ── 检查 4：索引 ─────────────────────────────────────────────

    def _check_4_index(self, full_text: str, wp: Workpaper) -> PreflightItem:
        refs = wp.get_evidence_refs()
        # 也从文本中提取
        text_refs = re.findall(
            r'(?:索引|详见|参见|参照|见|附|附件)?[A-Za-z]+[-_][\d]+',
            full_text,
        )
        all_refs = set(refs + text_refs)

        has_index = len(all_refs) > 0
        return PreflightItem(
            check_id=4,
            name="索引",
            passed=has_index,
            rule="引用是否有索引号？",
            message=f"检测到 {len(all_refs)} 个索引引用" if has_index else "未检测到索引引用",
            suggestion="为所有引用（凭证、合同、文件）标注统一格式的索引编号"
            if not has_index else "",
        )

    # ── 检查 5：数字来源 ─────────────────────────────────────────

    def _check_5_source(self, full_text: str) -> PreflightItem:
        # 检测数字
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%|万|亿|元|万元|亿元)?', full_text)

        # 检测来源标注
        source_markers = re.findall(
            r'(?:来源|数据来源|根据.*?[，,。]|参照.*?[，,。]|详见.*?索引)',
            full_text,
        )

        # 简化判断：如果有数字且有至少一个来源标注 → 通过
        if not numbers:
            return PreflightItem(
                check_id=5,
                name="数字来源",
                passed=True,
                rule="每个数字是否有来源标注？",
                message="无数字数据，无需检查来源",
            )

        # 有数字但来源标注比例低
        source_density = len(source_markers) / max(1, len(numbers) // 3)
        passed = source_density > 0.3  # 至少每 3 个数字有 1 个来源标注

        return PreflightItem(
            check_id=5,
            name="数字来源",
            passed=passed,
            rule="每个数字是否有来源标注？",
            message=(
                f"共 {len(numbers)} 个数字，{len(source_markers)} 个来源标注"
                if source_markers
                else f"共 {len(numbers)} 个数字，无来源标注"
            ),
            suggestion="为关键数据标注来源（如'数据来源于明细账表D-1'）"
            if not passed else "",
        )

    # ── 检查 6：例外事项处理 ─────────────────────────────────────

    def _check_6_exceptions(self, full_text: str) -> PreflightItem:
        exceptions = [
            kw for kw in EXCEPTION_KEYWORDS
            if kw in full_text
        ]

        if not exceptions:
            return PreflightItem(
                check_id=6,
                name="差异处理",
                passed=True,
                rule="异常事项是否已处理和记录？",
                message="未检测到异常/差异关键词",
            )

        # 有异常关键词 → 检查是否有处理记录
        has_resolution = any(
            kw in full_text
            for kw in ["处理", "调整", "已修正", "已补", "经核实",
                      "经确认", "可接受", "不构成", "不影响", "未发现重大"]
        )

        return PreflightItem(
            check_id=6,
            name="差异处理",
            passed=has_resolution,
            rule="异常事项是否已处理和记录？",
            message=(
                f"检测到异常关键词: {', '.join(exceptions[:3])}，"
                + ("已记录处理方式" if has_resolution else "缺少处理记录")
            ),
            suggestion=(
                "对每个异常/差异事项记录：差异描述、原因分析、处理方式、对审计结论的影响"
            )
            if not has_resolution else "",
        )
