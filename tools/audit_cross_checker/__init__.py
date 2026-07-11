"""
Audit Cross Checker — 审计报告算术勾稽引擎 v1.0

Four-layer architecture for audit report arithmetic verification:

  Layer 1: TableModel         — generic table abstraction (any Word/PDF table)
  Layer 2: DomainAdapter      — domain-specific semantics (年报/专项/工程/绩效)
  Layer 3: RuleEngine         — rule DSL + arithmetic execution
  Layer 4: ReviewFilter       — AI-driven false-positive filtering

Usage:
  from tools.audit_cross_checker import AuditCrossChecker
  
  checker = AuditCrossChecker("report.docx", domain="performance")
  results = checker.run()
  checker.generate_reports("output/")
"""

from .table_model import (
    TableDocument,
    TableSheet,
    Cell,
    Row,
    Column,
    extract_table_from_rows,
    parse_number,
    format_number,
    save_document,
    load_document,
)
from .domain_adapter import (
    DomainAdapter,
    AnnualReportAdapter,
    SpecialAuditAdapter,
    EngineeringAdapter,
    PerformanceAdapter,
    get_adapter,
    apply_all_adapters,
    auto_detect_domain,
    list_adapters,
)
from .rule_engine import (
    RuleEngine,
    Rule,
    CheckResult,
    load_rule_package,
    load_thresholds,
)
from .review_filter import ReviewFilter, FP_REASONS
from .review_report_generator import (
    ReviewReportGenerator,
    generate_markdown_report,
    generate_excel_report,
)
from .report_parser import ReportParser

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class AuditCrossChecker:
    """
    Main orchestrator: parse → classify → check → filter → report.
    
    Usage:
        checker = AuditCrossChecker("audit_report.docx")
        checker.run()
        checker.print_summary()
        checker.generate_reports("output/")
    """

    def __init__(
        self,
        source_path: str,
        domain: str = "auto",
        thresholds_path: str = "",
    ):
        self.source_path = source_path
        self.doc: TableDocument = None  # type: ignore[assignment]
        self.domain = domain
        self.thresholds = load_thresholds(thresholds_path if thresholds_path else None)
        self.engine: RuleEngine = None  # type: ignore[assignment]
        self.filter: ReviewFilter = None  # type: ignore[assignment]
        self.results: list[CheckResult] = []
        self.classified: dict = {}
        self._parsed = False
        self._ran = False

    def parse(self) -> TableDocument:
        """Parse the source document into structured table model."""
        parser = ReportParser(self.source_path)
        self.doc = parser.parse()
        self._parsed = True
        return self.doc

    def apply_domain(self) -> TableDocument:
        """Apply domain adapter(s) to classify and enrich tables."""
        if not self._parsed:
            self.parse()

        if self.domain == "auto":
            detections = auto_detect_domain(self.doc)
            if detections:
                self.domain = detections[0][0]
            else:
                self.domain = "annual_report"

        adapter = get_adapter(self.domain)
        if adapter:
            self.doc = adapter.apply(self.doc)

        return self.doc

    def run(self) -> list[CheckResult]:
        """
        Run the full pipeline: parse → adapt → check → filter.
        
        Returns filtered check results.
        """
        if not self._parsed:
            self.parse()

        self.apply_domain()

        # Run rule engine
        self.engine = RuleEngine(self.doc, self.thresholds)
        results = self.engine.run_all_domains([self.domain])

        # Also run generic intra-note checks
        for sheet in self.doc.sheets:
            if sheet.metadata.get("category") not in ("unknown",):
                self.engine.run_intra_note_checks(sheet)

        # Apply review filter
        self.filter = ReviewFilter(self.doc, self.thresholds)
        self.results = self.filter.filter(self.engine.results)
        self.classified = self.filter.classify(self.results)

        self._ran = True
        return self.results

    def generate_reports(self, output_dir: str) -> dict[str, str]:
        """Generate Excel + Markdown review reports."""
        if not self._ran:
            self.run()

        generator = ReviewReportGenerator(
            classified=self.classified,
            domain=self.domain,
            source_path=self.source_path,
        )
        base_name = f"复核报告_{self.domain}"
        return generator.generate_all(output_dir, base_name)

    def print_summary(self) -> None:
        """Print a human-readable summary."""
        if not self._ran:
            self.run()

        s = self.engine.summary() if self.engine else {}
        fs = self.filter.summary(self.classified) if self.filter else {}

        print("=" * 60)
        print(f"  审计复核报告摘要 — {self.domain}")
        print("=" * 60)
        print(f"  源文件：{self.source_path}")
        print(f"  检查领域：{self.domain}")
        print(f"  表格数：{len(self.doc.sheets) if self.doc else 0}")
        print("-" * 60)
        print(f"  总检查数：{s.get('total_checks', 0)}")
        print(f"  通过：    {s.get('passed', 0)}")
        print(f"  未通过：  {s.get('failed', 0)}")
        print("-" * 60)
        print(f"  确认错误：  {fs.get('confirmed_errors', 0)}")
        print(f"  需人工复核：{fs.get('needs_human_review', 0)}")
        print(f"  误报（筛除）：{fs.get('false_positives', 0)}")
        print(f"  误报率：    {fs.get('fp_rate', 0):.1%}")
        print("-" * 60)

        if fs.get("fp_reasons"):
            print("  误报原因分布：")
            for reason, count in fs["fp_reasons"].items():
                print(f"    - {reason}: {count}")

        # Show confirmed errors
        confirmed = self.classified.get("confirmed", [])
        if confirmed:
            print("-" * 60)
            print(f"  确认错误明细（{len(confirmed)}项）：")
            for r in confirmed[:10]:
                print(f"    [{r.severity}] {r.description}")
                if r.expected is not None and r.actual is not None:
                    print(f"        预期 {r.expected:,.2f} / 实际 {r.actual:,.2f} / 差异 {r.diff:,.2f}")
            if len(confirmed) > 10:
                print(f"    ... 还有 {len(confirmed) - 10} 项")

        print("=" * 60)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def quick_check(source_path: str, domain: str = "auto") -> list[CheckResult]:
    """Quick one-liner: parse, check, filter, return results."""
    checker = AuditCrossChecker(source_path, domain)
    return checker.run()


__all__ = [
    # Core
    "AuditCrossChecker",
    "quick_check",
    # Layer 1
    "TableDocument", "TableSheet", "Cell", "Row", "Column",
    "extract_table_from_rows", "parse_number", "format_number",
    "save_document", "load_document",
    # Layer 2
    "DomainAdapter", "AnnualReportAdapter", "SpecialAuditAdapter",
    "EngineeringAdapter", "PerformanceAdapter",
    "get_adapter", "apply_all_adapters", "auto_detect_domain", "list_adapters",
    # Layer 3
    "RuleEngine", "Rule", "CheckResult", "load_rule_package", "load_thresholds",
    # Layer 4
    "ReviewFilter", "FP_REASONS",
    # Reports
    "ReviewReportGenerator", "generate_markdown_report", "generate_excel_report",
    # Parser
    "ReportParser",
]
