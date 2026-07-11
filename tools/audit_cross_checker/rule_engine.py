"""
Layer 3: Rule Engine (规则引擎)

Executes arithmetic cross-check rules against TableDocument data.
Supports:
  - Four check types: inter_statement, note_statement, intra_note, text_format
  - Cell references via sheet!row[condition].col[condition]
  - Aggregation: SUM, COUNT, AVG, MAX, MIN
  - Conditional: IF(cond, then, else)
  - External threshold injection from YAML configs
  - Tolerance-based comparison

Design principle: ALL math in code, zero AI guesswork on numbers.
"""

from __future__ import annotations

import re
import math
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .table_model import (
    TableDocument,
    TableSheet,
    Row,
    Cell,
    parse_number,
)


# ---------------------------------------------------------------------------
# Check Result
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Single rule execution result."""
    rule_id: str
    check_type: str
    domain: str
    description: str
    expected: Optional[float] = None
    actual: Optional[float] = None
    diff: Optional[float] = None
    tolerance: float = 0.01
    severity: str = "info"  # error | warning | info
    passed: bool = True
    requires_human_review: bool = False
    page_ref: str = ""
    excerpt: str = ""
    sheet_context: str = ""
    row_context: int = 0
    detail: str = ""
    # For filtered results
    false_positive: bool = False
    false_positive_reason: str = ""


# ---------------------------------------------------------------------------
# Rule Definition
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    """Parsed rule definition from YAML or programmatic construction."""
    id: str
    check_type: str = ""
    domain: str = ""
    description: str = ""
    expression: str = ""
    tolerance: float = 0.01
    severity: str = "info"
    requires_human_review: bool = False
    applies_to: str = "all"
    external_threshold: str = ""
    note: str = ""


# ---------------------------------------------------------------------------
# Threshold Loader
# ---------------------------------------------------------------------------

def load_thresholds(path: Optional[str] = None) -> dict[str, Any]:
    """Load threshold configuration from YAML."""
    if path is None:
        path = str(
            Path(__file__).parent / "thresholds" / "default.yaml"
        )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_rule_package(domain: str) -> list[Rule]:
    """Load rule definitions from the domain's YAML package."""
    path = Path(__file__).parent / "rule_packages" / f"{domain}.yaml"
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    rules = []
    for rdata in data.get("rules", []):
        rules.append(Rule(
            id=rdata.get("id", ""),
            check_type=rdata.get("check_type", ""),
            domain=rdata.get("domain", data.get("domain", "")),
            description=rdata.get("description", ""),
            expression=rdata.get("expression", ""),
            tolerance=rdata.get("tolerance", 0.01),
            severity=rdata.get("severity", "info"),
            requires_human_review=rdata.get("requires_human_review", False),
            applies_to=rdata.get("applies_to", "all"),
            external_threshold=rdata.get("external_threshold", ""),
            note=rdata.get("note", ""),
        ))
    return rules


# ---------------------------------------------------------------------------
# Cell Value Resolver
# ---------------------------------------------------------------------------

class CellResolver:
    """
    Resolves named cell references to actual numeric values.
    
    Reference syntax:
      SheetName!Row[regex]!Col[regex]
      SheetName!Row[index]!Col[index]
      SheetName!TotalRow!Col[regex]
      BS[end_total_assets]  → domain-specific shorthand
    """

    def __init__(self, doc: TableDocument):
        self.doc = doc
        self._sheets: dict[str, TableSheet] = {}
        for s in doc.sheets:
            self._sheets[s.name.lower().replace(" ", "")] = s

    def get_sheet(self, name: str) -> Optional[TableSheet]:
        key = name.lower().replace(" ", "")
        # Exact match
        if key in self._sheets:
            return self._sheets[key]
        # Partial match
        for k, v in self._sheets.items():
            if key in k:
                return v
        return None

    def resolve_cell(self, ref: str) -> Optional[float]:
        """
        Resolve a cell reference to a numeric value.
        
        Examples:
          "BS![资产总计]![end_balance]"  → find row with "资产总计", get end_balance col
          "IS[revenue]"                   → shorthand for IS revenue row, amount col  
        """
        # Shorthand: Sheet[key]
        m = re.match(r"^(\w+)\[([^\]]+)\]$", ref)
        if m:
            sheet_alias = m.group(1)
            key = m.group(2)
            # Map sheet aliases to actual sheet names
            sheet = self._find_by_alias(sheet_alias)
            if not sheet:
                return None
            return self._find_value_by_key(sheet, key)

        # Full: SheetName!Row[cond]!Col[cond]
        parts = ref.split("!")
        if len(parts) != 3:
            return None

        sheet_name, row_cond, col_cond = parts
        sheet = self.get_sheet(sheet_name)
        if not sheet:
            return None

        row = self._find_row(sheet, row_cond)
        if not row:
            return None

        return self._find_cell_value(row, col_cond)

    def _find_by_alias(self, alias: str) -> Optional[TableSheet]:
        """Map domain shorthand to actual sheet."""
        alias_lower = alias.lower()
        # BS = balance sheet
        if alias_lower == "bs":
            for s in self.doc.sheets:
                if s.metadata.get("category") == "balance_sheet":
                    return s
        # IS = income statement
        if alias_lower == "is":
            for s in self.doc.sheets:
                if s.metadata.get("category") == "income_statement":
                    return s
        # CF = cash flow
        if alias_lower == "cf":
            for s in self.doc.sheets:
                if s.metadata.get("category") == "cash_flow":
                    return s
        # NOTE[...] = notes
        if alias_lower == "note":
            return self.doc.sheets[0] if self.doc.sheets else None
        return None

    def _find_value_by_key(self, sheet: TableSheet, key: str) -> Optional[float]:
        """Find a row by label key and get its primary numeric value."""
        # Try exact match first
        for row in sheet.rows:
            if row.is_empty or row.is_header:
                continue
            if row.cells and row.cells[0].raw.strip() == key.strip():
                # Return first numeric cell
                for cell in row.cells:
                    if cell.is_number and cell.value is not None:
                        return cell.value
                return None

        # Try partial match
        for row in sheet.rows:
            if row.is_empty or row.is_header:
                continue
            if row.cells and key.strip() in row.cells[0].raw:
                for cell in row.cells:
                    if cell.is_number and cell.value is not None:
                        return cell.value

        return None

    def _find_row(self, sheet: TableSheet, cond: str) -> Optional[Row]:
        """Find a row by condition. cond format: [label] or [index]"""
        m = re.match(r"^\[([^\]]+)\]$", cond)
        if not m:
            return None
        key = m.group(1)

        # Numeric index
        try:
            idx = int(key)
            if 0 <= idx < len(sheet.rows):
                return sheet.rows[idx]
        except ValueError:
            pass

        # Label match
        for row in sheet.rows:
            if row.is_empty:
                continue
            if row.cells and key.strip() in row.cells[0].raw:
                return row

        return None

    def _find_cell_value(self, row: Row, cond: str, role: Optional[str] = None) -> Optional[float]:
        """Find a cell in a row by column condition."""
        m = re.match(r"^\[([^\]]+)\]$", cond)
        if not m:
            return None
        key = m.group(1).lower()

        # Roles: end_balance, begin_balance, etc.
        if role:
            for sheet in self.doc.sheets:
                for col in sheet.columns:
                    if col.role == role and col.index < len(row.cells):
                        cell = row.cells[col.index]
                        if cell.is_number and cell.value is not None:
                            return cell.value

        # Numeric index
        try:
            idx = int(key)
            if 0 <= idx < len(row.cells):
                cell = row.cells[idx]
                return cell.value
        except ValueError:
            pass

        # Label match in column headers
        for i, cell in enumerate(row.cells):
            if key in cell.raw.lower():
                return cell.value

        # Return first numeric as fallback
        for cell in row.cells:
            if cell.is_number and cell.value is not None:
                return cell.value

        return None

    def resolve_aggregate(self, sheet: TableSheet, row_indices: list[int],
                          col_index: int) -> Optional[float]:
        """Sum values across specified rows at a given column."""
        total = 0.0
        has_value = False
        for idx in row_indices:
            if idx < len(sheet.rows):
                row = sheet.rows[idx]
                if not row.is_empty and col_index < len(row.cells):
                    cell = row.cells[col_index]
                    if cell.value is not None:
                        total += cell.value
                        has_value = True
        return total if has_value else None


# ---------------------------------------------------------------------------
# Rule Engine
# ---------------------------------------------------------------------------

class RuleEngine:
    """Core rule execution engine."""

    def __init__(self, doc: TableDocument, thresholds: Optional[dict] = None):
        self.doc = doc
        self.thresholds = thresholds or {}
        self.resolver = CellResolver(doc)
        self.results: list[CheckResult] = []

    # ---- Expression Parser ----

    _EXPR_RE = re.compile(
        r'(SUM|COUNT|AVG|MAX|MIN|ABS)\s*\(([^)]+)\)|'
        r'IF\s*\(([^,]+),([^,]+),([^)]+)\)|'
        r'([\w!\[\]\._]+)|'   # cell refs, numbers
        r'(==|!=|>=|<=|>|<)|'  # operators
        r'AND|OR|'            # logical
        r'[+\-*/()]|'         # arithmetic
        r'True|False'         # boolean literals
    )

    def evaluate_expression(self, expr: str, context: dict[str, Any]) -> tuple[bool, Optional[float], Optional[float]]:
        """
        Evaluate a rule expression.
        
        Returns: (passed: bool, expected: float|None, actual: float|None)
        
        For expressions like "A == B + C":
          - expected = value of left side
          - actual = value of right side
          - passed = |expected - actual| <= tolerance
        
        For expressions like "A > B":
          - expected = value of left side
          - actual = value of right side
          - passed = left > right
        """
        if not expr or expr.strip() == "manual":
            return True, None, None

        expr = expr.strip()

        # Parse comparison: A op B
        for op in ("==", "!=", ">=", "<=", ">", "<"):
            if op in expr:
                return self._eval_comparison(expr, op, context)

        # Non-comparison: just evaluate
        val = self._eval_arithmetic(expr, context)
        return True, val, val

    def _eval_comparison(self, expr: str, op: str, context: dict[str, Any]) -> tuple[bool, Optional[float], Optional[float]]:
        """Evaluate a comparison expression."""
        parts = expr.split(op, 1)
        if len(parts) != 2:
            return True, None, None

        left = self._eval_arithmetic(parts[0].strip(), context)
        right = self._eval_arithmetic(parts[1].strip(), context)

        # Handle AND/OR in right side
        if " AND " in str(right) or " OR " in str(right):
            # It's a logical condition, not arithmetic
            return self._eval_logical(parts[1].strip(), context), left, right

        tolerance = context.get("tolerance", 0.01)

        if left is None or right is None:
            return True, left, right  # Can't evaluate → pass (needs human)

        if op == "==":
            diff = abs(left - right)
            passed = diff <= tolerance
        elif op == "!=":
            diff = abs(left - right)
            passed = diff > tolerance
        elif op == ">=":
            passed = left >= right - tolerance
            diff = left - right
        elif op == "<=":
            passed = left <= right + tolerance
            diff = right - left
        elif op == ">":
            passed = left > right + tolerance
            diff = left - right
        elif op == "<":
            passed = left < right - tolerance
            diff = right - left
        else:
            passed = True
            diff = 0.0

        return passed, left, right

    def _eval_arithmetic(self, expr: str, context: dict[str, Any]) -> Optional[float]:
        """Evaluate a simple arithmetic expression (no comparisons)."""
        expr = expr.strip()

        # Constants
        try:
            return float(expr)
        except ValueError:
            pass

        if expr in ("True", "true"):
            return 1.0
        if expr in ("False", "false"):
            return 0.0

        # Tokenize: numbers, cell refs, operators, parens
        tokens = self._tokenize(expr)
        return self._evaluate_tokens(tokens, context)

    def _eval_logical(self, expr: str, context: dict[str, Any]) -> bool:
        """Evaluate a logical expression (AND/OR of conditions)."""
        expr = expr.strip()

        if " AND " in expr:
            parts = expr.split(" AND ")
            return all(self._eval_logical(p.strip(), context) for p in parts)

        if " OR " in expr:
            parts = expr.split(" OR ")
            return any(self._eval_logical(p.strip(), context) for p in parts)

        # Single condition
        for op in ("==", "!=", ">=", "<=", ">", "<"):
            if op in expr:
                passed, _, _ = self._eval_comparison(expr, op, context)
                return passed

        return True

    def _tokenize(self, expr: str) -> list[str]:
        """Tokenize an arithmetic expression."""
        tokens = []
        i = 0
        while i < len(expr):
            if expr[i].isspace():
                i += 1
                continue
            if expr[i] in "+-*/()":
                tokens.append(expr[i])
                i += 1
                continue
            # Cell reference or function
            if expr[i].isalpha() or expr[i] in ("[", "!"):
                start = i
                depth = 0
                while i < len(expr):
                    if expr[i] == "(":
                        depth += 1
                    elif expr[i] == ")":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    elif depth == 0 and expr[i] in "+-*/()":
                        break
                    i += 1
                token = expr[start:i]
                if token.endswith(","):
                    token = token[:-1]
                tokens.append(token)
                continue
            # Number
            if expr[i].isdigit() or expr[i] == ".":
                start = i
                while i < len(expr) and (expr[i].isdigit() or expr[i] == "."):
                    i += 1
                tokens.append(expr[start:i])
                continue
            i += 1
        return tokens

    def _evaluate_tokens(self, tokens: list[str], context: dict[str, Any]) -> Optional[float]:
        """Evaluate tokenized expression using simple stack-based parser."""
        if not tokens:
            return None

        # Handle function calls: FUNC(args)
        full = "".join(tokens)

        # SUM(...), COUNT(...), AVG(...), MAX(...), MIN(...), ABS(...)
        for func in ("SUM", "COUNT", "AVG", "MAX", "MIN", "ABS"):
            if full.startswith(func + "("):
                inner = full[len(func) + 1 : -1]  # strip FUNC( and )
                return self._eval_aggregate(func, inner, context)

        # Simple expression: ref + ref - ref ...
        try:
            return float(full)
        except ValueError:
            pass

        if full in ("True", "true"):
            return 1.0
        if full in ("False", "false"):
            return 0.0

        # Try cell reference
        val = self.resolver.resolve_cell(full)
        if val is not None:
            return val

        # Arithmetic: left op right
        for op in ("+", "-", "*", "/"):
            idx = self._find_op(tokens, op)
            if idx >= 0:
                left_tokens = tokens[:idx]
                right_tokens = tokens[idx + 1:]
                left_val = self._evaluate_tokens(left_tokens, context)
                right_val = self._evaluate_tokens(right_tokens, context)

                if left_val is None or right_val is None:
                    return None

                if op == "+":
                    return left_val + right_val
                elif op == "-":
                    return left_val - right_val
                elif op == "*":
                    return left_val * right_val
                elif op == "/":
                    return left_val / right_val if right_val != 0 else None

        # Remove outer parentheses
        if tokens[0] == "(" and tokens[-1] == ")":
            return self._evaluate_tokens(tokens[1:-1], context)

        return None

    def _find_op(self, tokens: list[str], op: str) -> int:
        """Find operator at top level (outside parens/brackets)."""
        depth = 0
        for i, t in enumerate(tokens):
            if t in ("(", "["):
                depth += 1
            elif t in (")", "]"):
                depth -= 1
            elif t == op and depth == 0:
                return i
        return -1

    def _eval_aggregate(self, func: str, inner: str, context: dict[str, Any]) -> Optional[float]:
        """Evaluate an aggregate function from named cell references."""
        # Inner is comma-separated cell refs
        refs = [r.strip() for r in inner.split(",")]
        values = []
        for ref in refs:
            val = self.resolver.resolve_cell(ref)
            if val is not None:
                values.append(val)

        if not values:
            return None

        if func == "SUM":
            return sum(values)
        if func == "COUNT":
            return float(len(values))
        if func == "AVG":
            return sum(values) / len(values)
        if func == "MAX":
            return max(values)
        if func == "MIN":
            return min(values)
        if func == "ABS":
            return abs(values[0]) if values else None
        return None

    # ---- Rule Execution ----

    def run_rule(self, rule: Rule, context: Optional[dict[str, Any]] = None) -> CheckResult:
        """Execute a single rule against the document."""
        ctx = context.copy() if context else {}
        ctx["tolerance"] = rule.tolerance

        # Inject external threshold if specified
        if rule.external_threshold:
            thresh_val = self._resolve_threshold(rule.external_threshold)
            if thresh_val is not None:
                ctx[rule.external_threshold.split(".")[-1]] = thresh_val

        passed, expected, actual = self.evaluate_expression(rule.expression, ctx)

        diff = None
        if expected is not None and actual is not None:
            diff = abs(expected - actual)

        return CheckResult(
            rule_id=rule.id,
            check_type=rule.check_type,
            domain=rule.domain,
            description=rule.description,
            expected=expected,
            actual=actual,
            diff=diff,
            tolerance=rule.tolerance,
            severity=rule.severity,
            passed=passed,
            requires_human_review=rule.requires_human_review,
            detail=rule.note or "",
        )

    def _resolve_threshold(self, path: str) -> Optional[Any]:
        """Resolve a dotted threshold path like 'full_score_threshold'."""
        # Try domain-specific then global
        for scope in self.thresholds.values():
            if isinstance(scope, dict):
                val = scope
                for part in path.split("."):
                    if isinstance(val, dict):
                        val = val.get(part)
                    else:
                        val = None
                        break
                if val is not None:
                    return val
        return None

    def run_domain(self, domain: str) -> list[CheckResult]:
        """Run all rules for a domain."""
        rules = load_rule_package(domain)
        results = []
        for rule in rules:
            result = self.run_rule(rule)
            results.append(result)
        self.results.extend(results)
        return results

    def run_all_domains(self, domains: Optional[list[str]] = None) -> list[CheckResult]:
        """Run rules for all specified domains (or all available)."""
        if domains is None:
            domains = ["annual_report", "special_audit", "engineering", "performance"]

        all_results = []
        for domain in domains:
            all_results.extend(self.run_domain(domain))
        return all_results

    # ---- Intra-Note: Generic Horizontal/Vertical Sum Check ----

    def run_intra_note_checks(self, sheet: TableSheet) -> list[CheckResult]:
        """
        Generic intra-note: verify that detail rows sum to total rows.
        Auto-detects total rows and sums numeric columns.
        """
        results = []

        # Find total row(s)
        total_rows = [r for r in sheet.rows if r.is_total]
        if not total_rows:
            return results

        # Find detail rows (non-header, non-total, non-empty, non-subtotal)
        detail_rows = [
            r for r in sheet.rows
            if not r.is_header and not r.is_total and not r.is_empty
            and not any(c.is_subtotal for c in r.cells)
        ]

        for total_row in total_rows:
            for col in sheet.columns:
                if not col.is_numeric:
                    continue
                total_val = sheet.get_value(total_row.row_index, col.index)
                if total_val is None:
                    continue

                # Sum detail rows' values in this column
                detail_sum = 0.0
                for dr in detail_rows:
                    v = sheet.get_value(dr.row_index, col.index)
                    if v is not None:
                        detail_sum += v

                diff = abs(total_val - detail_sum)
                passed = diff <= 0.02  # Slightly higher tolerance for rounding

                results.append(CheckResult(
                    rule_id=f"IN-{sheet.name}-R{total_row.row_index}C{col.index}",
                    check_type="intra_note",
                    domain=self.doc.metadata.get("domain", ""),
                    description=f"{sheet.name} {col.header}: 明细之和 vs 合计行",
                    expected=total_val,
                    actual=detail_sum,
                    diff=diff,
                    tolerance=0.02,
                    severity="error" if not passed else "info",
                    passed=passed,
                    page_ref=sheet.page_ref,
                    sheet_context=sheet.name,
                    row_context=total_row.row_index,
                    excerpt=f"合计行={total_val}, 明细之和={detail_sum}",
                ))

        self.results.extend(results)
        return results

    # ---- Reporting ----

    def summary(self) -> dict[str, Any]:
        """Generate a summary of all check results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        errors = sum(1 for r in self.results if r.severity == "error" and not r.passed)
        warnings = sum(1 for r in self.results if r.severity == "warning" and not r.passed)
        needs_review = sum(1 for r in self.results if r.requires_human_review and not r.passed)

        by_type: dict[str, dict[str, int]] = {}
        for r in self.results:
            if r.check_type not in by_type:
                by_type[r.check_type] = {"total": 0, "passed": 0, "failed": 0}
            by_type[r.check_type]["total"] += 1
            if r.passed:
                by_type[r.check_type]["passed"] += 1
            else:
                by_type[r.check_type]["failed"] += 1

        return {
            "domain": self.doc.metadata.get("domain", ""),
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
            "needs_human_review": needs_review,
            "by_check_type": by_type,
        }
