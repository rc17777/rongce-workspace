"""
Layer 1: Generic Table Model (通用表格抽象)

Any Word/PDF table → structured digital twin.
Does NOT presume "four statements + notes" — domain semantics are
injected by DomainAdapter (Layer 2).

Design principle: AI understands semantics, code does the math.
This layer does ONLY structural extraction — no accounting knowledge.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class Cell:
    """A single cell in a table row."""
    raw: str = ""
    value: Optional[float] = None
    is_number: bool = False
    is_header: bool = False
    is_total: bool = False  # "合计"/"总计"/"小计"
    is_subtotal: bool = False  # "其中："子项
    col_index: int = 0


@dataclass
class Row:
    """A single row in a table."""
    cells: list[Cell] = field(default_factory=list)
    row_index: int = 0
    is_header: bool = False
    is_total: bool = False
    is_empty: bool = False
    indent_level: int = 0  # 缩进层级（"其中："子项）


@dataclass
class Column:
    """Column metadata inferred from the table."""
    index: int = 0
    header: str = ""  # 列名（e.g., "期末余额", "年初余额"）
    role: str = ""  # "item_name" | "end_balance" | "begin_balance" | "ratio" | "note" | "unit"
    is_numeric: bool = False
    number_format: str = ""  # "thousands" | "paren_neg" | "wan_unit" | "normal"


@dataclass
class TableSheet:
    """A single table/sheet extracted from a document."""
    name: str = ""  # e.g., "资产负债表", "应收账款附注"
    page_ref: str = ""  # page number or section reference
    caption: str = ""  # table caption/title
    columns: list[Column] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)
    raw_text: str = ""  # original text context for AI review
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_cell(self, row_idx: int, col_idx: int) -> Optional[Cell]:
        if 0 <= row_idx < len(self.rows):
            row = self.rows[row_idx]
            if 0 <= col_idx < len(row.cells):
                return row.cells[col_idx]
        return None

    def get_value(self, row_idx: int, col_idx: int) -> Optional[float]:
        cell = self.get_cell(row_idx, col_idx)
        return cell.value if cell else None

    def find_rows_by_label(self, label: str, col_idx: int = 0) -> list[Row]:
        """Find rows where the first column (or specified col) matches a label."""
        results = []
        for row in self.rows:
            if row.is_empty:
                continue
            if col_idx < len(row.cells):
                if label in row.cells[col_idx].raw:
                    results.append(row)
        return results

    def find_row_by_exact_label(self, label: str, col_idx: int = 0) -> Optional[Row]:
        """Find first row with exact label match."""
        for row in self.rows:
            if col_idx < len(row.cells):
                if row.cells[col_idx].raw.strip() == label.strip():
                    return row
        return None


@dataclass
class TableDocument:
    """Complete document with all extracted tables."""
    source_path: str = ""
    source_type: str = ""  # "pdf" | "docx" | "xlsx"
    sheets: list[TableSheet] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    # Convenience: domain-specific lookup maps (populated by DomainAdapter)
    manifest: dict[str, Any] = field(default_factory=dict)
    note_map: dict[str, Any] = field(default_factory=dict)

    def get_sheet(self, name_pattern: str) -> Optional[TableSheet]:
        """Find a sheet by name (partial match)."""
        for sheet in self.sheets:
            if name_pattern in sheet.name:
                return sheet
        return None

    def get_sheets_by_name(self, name_pattern: str) -> list[TableSheet]:
        """Find all sheets matching a name pattern."""
        return [s for s in self.sheets if name_pattern in s.name]

    def all_sheet_names(self) -> list[str]:
        return [s.name for s in self.sheets]


# ---------------------------------------------------------------------------
# Number Parsing Utilities
# ---------------------------------------------------------------------------

# Number formats supported:
#   "normal"     —  1234567.89
#   "thousands"  —  1,234,567.89
#   "paren_neg"  —  (123.45) means -123.45
#   "wan_unit"   —  values in 万元 (multiply by 10000)
#   "yi_unit"    —  values in 亿元 (multiply by 100000000)

_THOUSANDS_RE = re.compile(r"^[\s]*\(?[\d,]+(?:\.\d+)?\)?[\s]*$")
_PAREN_NEG_RE = re.compile(r"^[\s]*\([\d,]+(?:\.\d+)?\)[\s]*$")
_WAN_MARKERS = ("万元", "万元/", "单位：万元", "金额单位：万元")
_YI_MARKERS = ("亿元", "亿元/", "单位：亿元", "金额单位：亿元")


def detect_number_format(text: str) -> str:
    """Detect the number format from a table's header or footer annotation."""
    text_lower = text.replace(" ", "")
    if any(m in text_lower for m in _YI_MARKERS):
        return "yi_unit"
    if any(m in text_lower for m in _WAN_MARKERS):
        return "wan_unit"
    return "normal"


def parse_number(raw: str, fmt: str = "normal") -> Optional[float]:
    """
    Parse a string into a float, handling audit-report conventions.

    Supported:
      - Thousands separators: "1,234,567.89" → 1234567.89
      - Parentheses negatives: "(123.45)" → -123.45
      - 万元 units: "123.45" with wan_unit → 1,234,500
      - 亿元 units: "1.23" with yi_unit → 123,000,000
      - Chinese dash: "—" or "-" → None
      - Percentages: "12.5%" → 0.125
    """
    if not raw or not isinstance(raw, str):
        return None

    text = raw.strip()

    # Empty / placeholder
    if not text or text in ("—", "-", "—", "—", "…", "...", "/", "N/A", "无", "不适用"):
        return None

    # Percentage
    is_pct = text.endswith("%")
    if is_pct:
        text = text[:-1]

    # Parentheses negative
    is_paren_neg = _PAREN_NEG_RE.match(text) is not None
    if is_paren_neg:
        text = text[1:-1]  # strip parentheses

    # Thousands separators
    text_clean = text.replace(",", "").replace("，", "").replace(" ", "")

    try:
        val = float(text_clean)
    except ValueError:
        return None

    if is_paren_neg:
        val = -val
    if is_pct:
        val = val / 100.0

    # Unit conversion
    if fmt == "wan_unit":
        val *= 10_000
    elif fmt == "yi_unit":
        val *= 100_000_000

    return val


def format_number(value: float, fmt: str = "normal") -> str:
    """Reverse of parse_number: format a float for display."""
    if fmt == "wan_unit":
        return f"{value / 10_000:,.2f}"
    if fmt == "yi_unit":
        return f"{value / 100_000_000:,.2f}"
    return f"{value:,.2f}"


# ---------------------------------------------------------------------------
# Table Extraction — Minimal Parsing Logic
# ---------------------------------------------------------------------------


def extract_table_from_rows(
    name: str,
    raw_rows: list[list[str]],
    page_ref: str = "",
    caption: str = "",
    number_format: str = "normal",
) -> TableSheet:
    """
    Convert raw rows (list of string lists) into a structured TableSheet.

    This is the minimal common interface. Actual extraction from PDF/Word
    is handled by report_parser.py (which may use officecli-docx, pdf tool, etc.).
    """
    if not raw_rows:
        return TableSheet(name=name, page_ref=page_ref, caption=caption)

    # Detect header row
    header_row_idx = 0
    columns: list[Column] = []
    rows: list[Row] = []

    for i, raw_row in enumerate(raw_rows):
        row = Row(row_index=i)

        # Detect empty row
        if all(not c or not c.strip() for c in raw_row):
            row.is_empty = True
            rows.append(row)
            continue

        # Detect header-like row (first non-empty row with text cells)
        is_potential_header = (
            i == 0
            or all(
                c and not _is_numeric_looking(c) for c in raw_row if c.strip()
            )
        )

        cells = []
        for j, raw_cell in enumerate(raw_row):
            cell_text = raw_cell.strip() if raw_cell else ""
            cell = Cell(raw=cell_text, col_index=j)

            # Detect indent (sub-items)
            indent = len(cell_text) - len(cell_text.lstrip(" 　"))
            if indent >= 2:
                row.indent_level = indent // 2

            # Detect totals
            if any(kw in cell_text for kw in ("合计", "总计", "小计", "合计", "合计")):
                cell.is_total = True
                row.is_total = True

            # Detect "其中：" sub-items
            if "其中" in cell_text or "其中：" in cell_text:
                cell.is_subtotal = True

            # Parse number
            cell.is_number = _is_numeric_looking(cell_text)
            if cell.is_number:
                cell.value = parse_number(cell_text, number_format)

            cells.append(cell)

        row.cells = cells

        # Build column headers from first header-like row
        if is_potential_header and not columns:
            columns = _infer_columns(cells)
            row.is_header = True
            header_row_idx = i

        rows.append(row)

    # If no header row detected, create default columns
    if not columns:
        columns = [
            Column(index=j, header=f"col_{j}", role="unknown")
            for j in range(len(rows[0].cells) if rows else 0)
        ]

    return TableSheet(
        name=name,
        page_ref=page_ref,
        caption=caption,
        columns=columns,
        rows=rows,
        metadata={"number_format": number_format, "header_row": header_row_idx},
    )


def _is_numeric_looking(text: str) -> bool:
    """Check if a string looks like it could be a number."""
    if not text or not text.strip():
        return False
    t = text.strip()
    # Has digits and only numeric/formatting chars
    return bool(re.match(r"^[\s]*\(?[\d,，.]+(?:\.\d+)?\)?[\s]*$", t))


def _infer_columns(cells: list[Cell]) -> list[Column]:
    """Infer column roles from header text."""
    columns = []
    for cell in cells:
        col = Column(index=cell.col_index, header=cell.raw)

        text = cell.raw.lower().replace(" ", "")

        # Role inference by keyword
        if any(kw in text for kw in ("项目", "科目", "名称", "指标", "item", "account")):
            col.role = "item_name"
        elif any(kw in text for kw in ("期末", "年末", "余额", "金额", "数额", "end", "期末数", "年末数")):
            col.role = "end_balance"
            col.role = "end_balance"
            col.is_numeric = True
        elif any(kw in text for kw in ("年初", "期初", "begin", "年初数", "期初数")):
            col.role = "begin_balance"
            col.is_numeric = True
        elif any(kw in text for kw in ("比例", "占比", "百分比", "%", "ratio")):
            col.role = "ratio"
            col.is_numeric = True
        elif any(kw in text for kw in ("备注", "说明", "note", "注释")):
            col.role = "note"
        elif cell.is_number:
            col.role = "numeric"
            col.is_numeric = True
        else:
            col.role = "unknown"

        columns.append(col)

    return columns


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def table_to_dict(sheet: TableSheet) -> dict[str, Any]:
    """Serialize a TableSheet to JSON-compatible dict."""
    return {
        "name": sheet.name,
        "page_ref": sheet.page_ref,
        "caption": sheet.caption,
        "metadata": sheet.metadata,
        "columns": [
            {
                "index": c.index,
                "header": c.header,
                "role": c.role,
                "is_numeric": c.is_numeric,
            }
            for c in sheet.columns
        ],
        "rows": [
            {
                "index": r.row_index,
                "is_header": r.is_header,
                "is_total": r.is_total,
                "is_empty": r.is_empty,
                "indent_level": r.indent_level,
                "cells": [
                    {
                        "raw": c.raw,
                        "value": c.value,
                        "is_number": c.is_number,
                        "is_total": c.is_total,
                        "col_index": c.col_index,
                    }
                    for c in r.cells
                ],
            }
            for r in sheet.rows
        ],
    }


def document_to_dict(doc: TableDocument) -> dict[str, Any]:
    return {
        "source_path": doc.source_path,
        "source_type": doc.source_type,
        "metadata": doc.metadata,
        "manifest": doc.manifest,
        "note_map": doc.note_map,
        "sheets": [table_to_dict(s) for s in doc.sheets],
    }


def save_document(doc: TableDocument, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(document_to_dict(doc), f, ensure_ascii=False, indent=2)


def load_document(path: str) -> TableDocument:
    """Load a TableDocument from JSON (reverse of save_document)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc = TableDocument(
        source_path=data.get("source_path", ""),
        source_type=data.get("source_type", ""),
        metadata=data.get("metadata", {}),
        manifest=data.get("manifest", {}),
        note_map=data.get("note_map", {}),
    )

    for sdata in data.get("sheets", []):
        sheet = TableSheet(
            name=sdata["name"],
            page_ref=sdata.get("page_ref", ""),
            caption=sdata.get("caption", ""),
            metadata=sdata.get("metadata", {}),
        )
        for cdata in sdata.get("columns", []):
            sheet.columns.append(Column(**{
                k: v for k, v in cdata.items()
                if k in ("index", "header", "role", "is_numeric", "number_format")
            }))
        for rdata in sdata.get("rows", []):
            row = Row(
                row_index=rdata["index"],
                is_header=rdata.get("is_header", False),
                is_total=rdata.get("is_total", False),
                is_empty=rdata.get("is_empty", False),
                indent_level=rdata.get("indent_level", 0),
            )
            for cdata in rdata.get("cells", []):
                cell = Cell(
                    raw=cdata.get("raw", ""),
                    value=cdata.get("value"),
                    is_number=cdata.get("is_number", False),
                    is_total=cdata.get("is_total", False),
                    col_index=cdata.get("col_index", 0),
                )
                row.cells.append(cell)
            sheet.rows.append(row)
        doc.sheets.append(sheet)

    return doc
