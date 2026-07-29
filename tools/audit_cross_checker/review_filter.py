"""
Layer 4: Review Filter (终审误报过滤层)

AI-driven false-positive filtering. After the rule engine produces results,
this layer classifies each issue into:
  - confirmed_error:  real error, keep it
  - false_positive:   structural quirk, discard
  - needs_human_review: ambiguous, flag for auditor

This is the critical third layer from the original article:
  "AI 还会回到原文，判断'这个差异是真的数字错了，
   还是表格结构特殊导致的'"

Implementation: programmatic false-positive detection patterns
supplemented by structured context for AI-driven review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .rule_engine import CheckResult
from .table_model import TableDocument

# ---------------------------------------------------------------------------
# False-Positive Detection Patterns
# ---------------------------------------------------------------------------


@dataclass
class FPPattern:
    """A known pattern that causes false positives in arithmetic checks."""
    name: str
    description: str
    # Function that examines a CheckResult + document context → is FP?
    detector: Any = None  # callable


# ---------------------------------------------------------------------------
# Structured FP Reasons
# ---------------------------------------------------------------------------

FP_REASONS = {
    "subtotal_excluded": 'subtotal row excluded from sum',
    "subtraction_item": 'subtraction row excluded',
    "percentage_column": 'percentage column, should not be summed',
    "dual_period": 'dual period columns, wrong column selected',
    "unit_mismatch": 'unit mismatch (wan yuan vs yuan)',
    "rounding_aggregate": 'cumulative rounding errors exceed tolerance',
    "header_as_data": 'header row misidentified as data row',
    "note_structure": 'non-standard note table layout',
    "nested_total": 'nested total rows, double-counted',
    "sign_convention": 'sign convention differences',
    "interim_column": 'intermediate calculation column',
}


# ---------------------------------------------------------------------------
# Review Filter
# ---------------------------------------------------------------------------

class ReviewFilter:
    """
    Filters check results to remove false positives.

    Works in two modes:
      1. Programmatic: applies known FP patterns (rule-based)
      2. Context-aware: prepares structured context for AI-driven review
    """

    def __init__(self, doc: TableDocument, thresholds: Optional[dict] = None):
        self.doc = doc
        self.thresholds = thresholds or {}
        self._pattern_registry: dict[str, FPPattern] = {}
        self._register_default_patterns()

    def _register_default_patterns(self) -> None:
        """Register built-in false-positive detection patterns."""
        self._pattern_registry.update({
            "tiny_diff": FPPattern(
                name="tiny_diff",
                description="差异极小（<0.05），可能是舍入累积",
            ),
            "subtraction_item": FPPattern(
                name="subtraction_item",
                description="该项以'减：'开头，不应参与求和",
            ),
            "subtotal_intermediate": FPPattern(
                name="subtotal_intermediate",
                description="该行是'其中：'中间项，已在父项中",
            ),
            "unit_mismatch": FPPattern(
                name="unit_mismatch",
                description="万元/元单位不一致",
            ),
            "percentage_column": FPPattern(
                name="percentage_column",
                description="该列是百分比列，不应算术求和",
            ),
        })

    # ---- Programmatic Filtering ----

    def filter(self, results: list[CheckResult]) -> list[CheckResult]:
        """
        Apply programmatic false-positive detection.

        Returns filtered results with false_positive flag set on FPs.
        """
        filtered = []
        for r in results:
            if r.passed:
                r.false_positive = False
                filtered.append(r)
                continue

            # Check each pattern
            is_fp, reason = self._check_fp(r)
            r.false_positive = is_fp
            r.false_positive_reason = reason

            # confirmed errors and needs-human-review both pass through
            filtered.append(r)

        return filtered

    def _check_fp(self, result: CheckResult) -> tuple[bool, str]:
        """Check a single result against all FP patterns. Returns (is_fp, reason)."""

        # Pattern 1: Tiny diff (rounding artifact)
        if result.diff is not None and result.diff < 0.05:
            return True, FP_REASONS["rounding_aggregate"]

        # Pattern 2: Subtraction item in summation
        if result.sheet_context and self._is_subtraction_row(result.sheet_context, result.row_context):
            return True, FP_REASONS["subtraction_item"]

        # Pattern 3: Subtotal/intermediate row
        excerpt = result.excerpt.lower()
        if "其中" in excerpt or "其中：" in excerpt:
            return True, FP_REASONS["subtotal_excluded"]

        # Pattern 4: Percentage column
        if result.check_type == "intra_note" and self._is_percentage_context(result):
            return True, FP_REASONS["percentage_column"]

        # Pattern 5: Dual-period confusion
        if self._is_dual_period_context(result):
            return True, FP_REASONS["dual_period"]

        # Pattern 6: Unit mismatch
        if self._detect_unit_mismatch(result):
            return True, FP_REASONS["unit_mismatch"]

        return False, ""

    def _is_subtraction_row(self, sheet_name: str, row_index: int) -> bool:
        """Check if the row is a subtraction row (减：xxx)."""
        sheet = self.doc.get_sheet(sheet_name)
        if not sheet:
            return False
        if row_index < len(sheet.rows):
            row = sheet.rows[row_index]
            if row.cells and row.cells[0].raw.startswith("减："):
                return True
            if row.cells and row.cells[0].raw.startswith("减:"):
                return True
        return False

    def _is_percentage_context(self, result: CheckResult) -> bool:
        """Check if the check result involves a percentage column."""
        for sheet in self.doc.sheets:
            for col in sheet.columns:
                if col.role == "ratio" or col.role == "weight":
                    return True
        return False

    def _is_dual_period_context(self, result: CheckResult) -> bool:
        """Check if the sheet has dual-period columns (本期/上期)."""
        for sheet in self.doc.sheets:
            period_count = sum(
                1 for c in sheet.columns
                if c.role in ("end_balance", "begin_balance")
            )
            if period_count >= 2:
                return True
        return False

    def _detect_unit_mismatch(self, result: CheckResult) -> bool:
        """Check for unit mismatch (万元 vs 元)."""
        if result.diff is not None:
            # If diff is close to 10000x or 1/10000 of expected, likely unit mismatch
            if result.expected and result.expected != 0:
                ratio = abs(result.diff / result.expected)
                if 0.99 <= ratio / 10000 <= 1.01 or 0.99 <= ratio * 10000 <= 1.01:
                    return True
        return False

    # ---- Classification ----

    def classify(self, results: list[CheckResult]) -> dict[str, list[CheckResult]]:
        """
        Classify results into three buckets:
          - confirmed: real errors (keep, fix)
          - false_positive: FP (discard)
          - needs_review: ambiguous (human must decide)
        """
        confirmed = []
        false_positives = []
        needs_review = []

        for r in results:
            if r.passed:
                continue  # Don't include passed checks in issue report

            if r.false_positive:
                false_positives.append(r)
            elif r.requires_human_review:
                needs_review.append(r)
            else:
                confirmed.append(r)

        return {
            "confirmed": confirmed,
            "false_positive": false_positives,
            "needs_review": needs_review,
        }

    # ---- Prepare Context for AI-Driven Review ----

    def prepare_ai_context(self, result: CheckResult) -> dict[str, Any]:
        """
        Prepare structured context for AI to do final review.

        The AI reads this context + original document and decides
        whether the result is a real error or a false positive.
        """
        context: dict[str, Any] = {
            "rule_id": result.rule_id,
            "description": result.description,
            "expected": result.expected,
            "actual": result.actual,
            "diff": result.diff,
            "tolerance": result.tolerance,
            "severity": result.severity,
            "page_ref": result.page_ref,
            "sheet_context": result.sheet_context,
            "row_context": result.row_context,
            "excerpt": result.excerpt,
            "domain": result.domain,
            "check_type": result.check_type,
        }

        # Add surrounding rows for context
        if result.sheet_context:
            sheet = self.doc.get_sheet(result.sheet_context)
            if sheet and result.row_context > 0:
                context["surrounding_rows"] = []
                start = max(0, result.row_context - 3)
                end = min(len(sheet.rows), result.row_context + 4)
                for i in range(start, end):
                    row = sheet.rows[i]
                    context["surrounding_rows"].append({
                        "index": i,
                        "is_header": row.is_header,
                        "is_total": row.is_total,
                        "cells": [c.raw for c in row.cells[:10]],
                    })

        # Column info
        if result.sheet_context:
            sheet = self.doc.get_sheet(result.sheet_context)
            if sheet:
                context["columns"] = [
                    {"header": c.header, "role": c.role}
                    for c in sheet.columns
                ]

        return context

    def generate_ai_review_prompt(self, result: CheckResult) -> str:
        """Generate a prompt for AI-driven final review of a single result."""
        ctx = self.prepare_ai_context(result)
        return f"""请审核以下算术勾稽检查结果，判断是真错误还是误报：

检查项：{ctx['description']}
预期值：{ctx['expected']}
实际值：{ctx['actual']}
差异：{ctx['diff']}（容差：{ctx['tolerance']}）
页码：{ctx['page_ref']}
表格：{ctx['sheet_context']}
上下文行：
{ctx.get('surrounding_rows', [])}

请判断：
- confirmed_error：这是真实的数字错误
- false_positive_structural：表格格式特殊导致的误报（如含"其中："子项、百分比列等）
- false_positive_rounding：舍入差异
- needs_human_review：两种情况都可能，需人工判断

选择一项，并简述理由。"""

    # ---- Statistics ----

    def fp_rate(self) -> float:
        """Calculate false-positive rate across all filtered results."""
        fp_count = sum(1 for r in self.doc.metadata.get("_all_results", []) if r.false_positive)
        total_failed = sum(1 for r in self.doc.metadata.get("_all_results", []) if not r.passed)
        if total_failed == 0:
            return 0.0
        return fp_count / total_failed

    def summary(self, classified: dict[str, list[CheckResult]]) -> dict[str, Any]:
        return {
            "confirmed_errors": len(classified["confirmed"]),
            "false_positives": len(classified["false_positive"]),
            "needs_human_review": len(classified["needs_review"]),
            "fp_rate": (
                len(classified["false_positive"])
                / max(1, len(classified["confirmed"]) + len(classified["false_positive"]) + len(classified["needs_review"]))
            ),
            "fp_reasons": self._count_fp_reasons(classified["false_positive"]),
        }

    def _count_fp_reasons(self, fps: list[CheckResult]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for fp in fps:
            reason = fp.false_positive_reason or "unknown"
            counts[reason] = counts.get(reason, 0) + 1
        return counts
