"""
workpaper_scorer — 审计底稿质量自动评分引擎

基于「程峰标准」四维核心指标 + 三大扣分项，对单张审计底稿进行
结构化质量评分，输出评分报告和改进清单。

适用场景：融策审计智析Agent — L1 项目组内复核（逐页检查）

Usage:
    from workpaper_scorer import WorkpaperScorer, Workpaper

    scorer = WorkpaperScorer()
    wp = Workpaper(
        id="WP-2026-001",
        title="应收账款存在性测试",
        target="本程序针对应收账款的存在性认定...",
        process="样本选取：根据应收账款明细账，按金额降序排列...",
        conclusion="经测试，应收账款存在性无重大异常。依据：...",
        cross_refs=["明细表-D1", "合同-C-003"],
        raw_content=full_markdown_text,
    )
    report = scorer.score(wp)
    print(report.final_score, report.grade, report.passed_l1)
"""

from .models import (
    Workpaper,
    WorkpaperField,
    ScoreReport,
    ScoreDimension,
    PenaltyItem,
    PenaltyCode,
    RiskFlag,
    Grade,
    ImprovementItem,
    YoYReport,
    PreviousYearWorkpaper,
    AUDIT_ASSERTIONS,
    SAMPLING_METHODS,
    TEST_PROCEDURE_VERBS,
    DOCUMENT_TYPES,
    EVIDENCE_KEYWORDS,
    ASSERTION_KEYWORDS,
)
from .scorer import WorkpaperScorer
from .preflight import PreflightChecker, PreflightResult, PreflightItem

__all__ = [
    # Core
    "WorkpaperScorer",
    "PreflightChecker",
    # Models
    "Workpaper",
    "WorkpaperField",
    "ScoreReport",
    "ScoreDimension",
    "PenaltyItem",
    "PenaltyCode",
    "RiskFlag",
    "Grade",
    "ImprovementItem",
    "YoYReport",
    "PreviousYearWorkpaper",
    "PreflightResult",
    "PreflightItem",
    # Constants
    "AUDIT_ASSERTIONS",
    "SAMPLING_METHODS",
    "TEST_PROCEDURE_VERBS",
    "DOCUMENT_TYPES",
    "EVIDENCE_KEYWORDS",
    "ASSERTION_KEYWORDS",
]
