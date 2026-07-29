"""
P1: 四大避坑约束 (2d)

将「数审派」文章的4个实战误区转化为Agent系统的设计约束和条件边:
  误区1: 只看文本不结合业务 → 交叉验证检查
  误区2: 过度依赖机器 → 人机核验强制检查
  误区3: 数据归集不完整 → 覆盖率强制检查
  误区4: 通用模型直接套用 → 规则定制检查

对应 LangGraph 条件边，可嵌入 pipeline.py 或独立使用。
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class PitfallCheck:
    """单个避坑检查结果"""
    pitfall_id: str
    pitfall_name: str
    passed: bool
    score: float        # 0.0-1.0
    detail: str
    recommendation: str = ""


@dataclass
class PitfallReport:
    """避坑综合检查报告"""
    checks: List[PitfallCheck]
    all_passed: bool
    failed_count: int
    summary: str


class PitfallGuard:
    """
    避坑约束检查器

    在流水线的关键节点执行检查，不通过则触发退回（back edge）
    """

    # ── 误区1：只看文本不结合业务 ──────────────────────────

    def check_cross_validation(
        self,
        findings: List[Dict[str, Any]],
        required_data_sources: Optional[List[str]] = None,
    ) -> PitfallCheck:
        """
        检查分析结果是否进行了多维交叉验证

        要求：每个审计疑点必须引用至少一个非纯文本数据源
        （如资金流水、合同台账、审批记录等）
        """
        if not findings:
            return PitfallCheck(
                pitfall_id="P01_cross_validation",
                pitfall_name="误区1：只看文本不结合业务",
                passed=True,
                score=1.0,
                detail="无疑点，无需交叉验证",
            )

        required = required_data_sources or [
            "资金", "流水", "台账", "审批", "合同", "凭证",
            "付款", "收款", "账", "银行", "财政",
        ]

        cross_validated = 0
        uncrossed = []

        for f in findings:
            # 检查finding是否有cross_refs字段
            cross_refs = f.get("cross_refs", [])
            # 检查risk_flags是否有cross_refs
            risk_flags = f.get("risk_flags", [])
            for rf in risk_flags:
                if isinstance(rf, dict):
                    cross_refs.extend(rf.get("cross_refs", []))

            if cross_refs:
                cross_validated += 1
            else:
                # 检查是否在文本中提到了非文本数据源
                text = f.get("source_file", "") + str(f.get("risk_flags", ""))
                if any(src in text for src in required):
                    cross_validated += 1
                else:
                    uncrossed.append(f.get("index", "?"))

        ratio = cross_validated / len(findings) if findings else 1.0

        passed = ratio >= 0.7  # 至少70%的疑点有交叉验证

        return PitfallCheck(
            pitfall_id="P01_cross_validation",
            pitfall_name="误区1：只看文本不结合业务",
            passed=passed,
            score=ratio,
            detail=(
                f"交叉验证率: {ratio:.0%} ({cross_validated}/{len(findings)})"
            ),
            recommendation=(
                "" if passed else
                f"以下疑点缺少交叉验证: {uncrossed}。建议补充资金流水或审批记录的数据源引用。"
            ),
        )

    # ── 误区2：过度依赖机器 ────────────────────────────────

    def check_human_review(
        self,
        findings: List[Dict[str, Any]],
        human_review_status: Optional[List[Dict[str, Any]]] = None,
    ) -> PitfallCheck:
        """
        检查高风险疑点是否全部经过人工复核

        要求：所有 severity=high 的疑点必须完成 human_review
        """
        high_risk = [f for f in findings if f.get("severity") == "high"]

        if not high_risk:
            return PitfallCheck(
                pitfall_id="P02_human_review",
                pitfall_name="误区2：过度依赖机器",
                passed=True,
                score=1.0,
                detail="无高风险疑点，无需强制人工复核",
            )

        if not human_review_status:
            return PitfallCheck(
                pitfall_id="P02_human_review",
                pitfall_name="误区2：过度依赖机器",
                passed=False,
                score=0.0,
                detail=f"有{len(high_risk)}条高风险疑点但未提交人工复核",
                recommendation="所有高风险疑点必须经过人工复核",
            )

        # 建立索引
        reviewed_map = {
            item.get("index", ""): item.get("decision", "pending")
            for item in human_review_status
        }

        pending = 0
        for f in high_risk:
            idx = f.get("index", "")
            if reviewed_map.get(idx, "pending") == "pending":
                pending += 1

        ratio = 1.0 - (pending / len(high_risk)) if high_risk else 1.0

        passed = pending == 0  # 全部完成复核

        return PitfallCheck(
            pitfall_id="P02_human_review",
            pitfall_name="误区2：过度依赖机器",
            passed=passed,
            score=ratio,
            detail=(
                f"高风险疑点复核率: {ratio:.0%} "
                f"({len(high_risk) - pending}/{len(high_risk)})"
            ),
            recommendation=(
                "" if passed else
                f"还有{pending}条高风险疑点待人工复核，继续前请完成"
            ),
        )

    # ── 误区3：数据归集不完整 ──────────────────────────────

    def check_data_coverage(
        self,
        expected_count: int,
        actual_count: int,
        missing_items: Optional[List[str]] = None,
        min_coverage: float = 0.95,
    ) -> PitfallCheck:
        """检查数据归集覆盖率"""
        if expected_count == 0:
            return PitfallCheck(
                pitfall_id="P03_data_coverage",
                pitfall_name="误区3：数据归集不完整",
                passed=True,
                score=1.0,
                detail="无预期文件数，跳过覆盖检查",
            )

        coverage = actual_count / expected_count if expected_count > 0 else 0
        passed = coverage >= min_coverage

        return PitfallCheck(
            pitfall_id="P03_data_coverage",
            pitfall_name="误区3：数据归集不完整",
            passed=passed,
            score=min(coverage / min_coverage, 1.0),
            detail=(
                f"数据覆盖率: {coverage:.1%} "
                f"（实收{actual_count}/期望{expected_count}）"
            ),
            recommendation=(
                "" if passed else
                f"覆盖率不足{min_coverage:.0%}，缺失项: {missing_items or '未知'}。"
                f"继续分析可能产生筛查盲区。"
            ),
        )

    # ── 误区4：通用模型直接套用 ────────────────────────────

    def check_rule_customization(
        self,
        project_type: str,
        rule_set: Optional[Dict[str, Any]] = None,
        default_rules_used: bool = False,
    ) -> PitfallCheck:
        """
        检查规则集是否针对项目类型定制

        要求：规则集不能是纯默认规则，必须至少包含项目类型相关的定制
        """
        if not rule_set:
            return PitfallCheck(
                pitfall_id="P04_rule_customization",
                pitfall_name="误区4：通用模型直接套用",
                passed=False,
                score=0.0,
                detail="未配置规则集",
                recommendation=f"请为 {project_type} 类型项目配置专用规则",
            )

        # 检查是否有项目类型的定制痕迹
        customization_signs = [
            project_type in str(rule_set),
            "custom_" in str(rule_set),
            rule_set.get("audit_type") == project_type,
            rule_set.get("custom_rules"),
            not default_rules_used,
        ]

        customization_score = sum(customization_signs) / len(customization_signs)
        passed = customization_score >= 0.4

        return PitfallCheck(
            pitfall_id="P04_rule_customization",
            pitfall_name="误区4：通用模型直接套用",
            passed=passed,
            score=customization_score,
            detail=(
                f"规则定制度: {customization_score:.0%} "
                f"({'已定制' if passed else '使用默认规则'})"
            ),
            recommendation=(
                "" if passed else
                f"建议为 {project_type} 项目加载专用审计规则，而非使用通用默认规则。"
            ),
        )

    # ── 综合检查 ──────────────────────────────────────────

    def run_all(
        self,
        findings: List[Dict[str, Any]],
        expected_count: int,
        actual_count: int,
        project_type: str,
        human_review_status: Optional[List[Dict[str, Any]]] = None,
        rule_set: Optional[Dict[str, Any]] = None,
        default_rules_used: bool = False,
    ) -> PitfallReport:
        """执行全部4项避坑检查"""
        checks = [
            self.check_cross_validation(findings),
            self.check_human_review(findings, human_review_status),
            self.check_data_coverage(expected_count, actual_count),
            self.check_rule_customization(
                project_type, rule_set, default_rules_used
            ),
        ]

        all_passed = all(c.passed for c in checks)
        failed_count = sum(1 for c in checks if not c.passed)

        if all_passed:
            summary = "✅ 4项避坑检查全部通过，可以继续"
        else:
            failed_names = [c.pitfall_name for c in checks if not c.passed]
            summary = f"❌ {failed_count}项避坑检查未通过: {', '.join(failed_names)}"

        return PitfallReport(
            checks=checks,
            all_passed=all_passed,
            failed_count=failed_count,
            summary=summary,
        )
