"""
Layer 2: Domain Adapters (领域适配器)

Each adapter maps domain-specific semantics onto the generic TableModel.
Four scenarios: annual_report, special_audit, engineering, performance.

Key responsibility:
  1. Classify sheets into domain categories (BS, IS, CF, etc.)
  2. Build manifest (column layout declarations)
  3. Build note_map (account → note sheet mappings)
  4. Enrich Column roles with domain semantics
"""

from __future__ import annotations

from typing import Optional

from .table_model import (
    TableDocument,
    TableSheet,
    Column,
    detect_number_format,
)

# ---------------------------------------------------------------------------
# Base Adapter Interface
# ---------------------------------------------------------------------------


class DomainAdapter:
    """Base class for domain-specific table adapters."""

    domain: str = "unknown"
    label: str = "Unknown"

    # Keywords used to classify sheets
    sheet_classifiers: dict[str, list[str]] = {}

    def classify_sheet(self, sheet: TableSheet) -> str:
        """Classify a sheet into a domain category. Override per adapter."""
        name = sheet.name.lower().replace(" ", "")
        caption = sheet.caption.lower().replace(" ", "")
        combined = name + " " + caption

        for category, keywords in self.sheet_classifiers.items():
            for kw in keywords:
                if kw.lower().replace(" ", "") in combined:
                    return category
        return "unknown"

    def build_manifest(self, doc: TableDocument) -> dict[str, Any]:
        """Build manifest.json equivalent for this domain."""
        return {}

    def build_note_map(self, doc: TableDocument) -> dict[str, Any]:
        """Build note_map.json equivalent for this domain."""
        return {}

    def enrich_columns(self, sheet: TableSheet, category: str) -> None:
        """Enrich column roles with domain semantics."""
        pass

    def apply(self, doc: TableDocument) -> TableDocument:
        """
        Full application: classify → enrich → manifest → note_map.
        Returns the enriched document.
        """
        for sheet in doc.sheets:
            category = self.classify_sheet(sheet)
            sheet.metadata["domain"] = self.domain
            sheet.metadata["category"] = category
            self.enrich_columns(sheet, category)

        doc.manifest = self.build_manifest(doc)
        doc.note_map = self.build_note_map(doc)
        doc.metadata["domain"] = self.domain
        return doc


# ---------------------------------------------------------------------------
# Annual Report Adapter (年报审计)
# ---------------------------------------------------------------------------

class AnnualReportAdapter(DomainAdapter):
    """Maps 四表一注 (four statements + notes) onto the generic model."""

    domain = "annual_report"
    label = "年报审计"

    sheet_classifiers = {
        "balance_sheet": [
            "资产负债表", "balance sheet", "资产负债表（续）",
        ],
        "income_statement": [
            "利润表", "损益表", "income statement", "利润及利润分配表",
        ],
        "cash_flow": [
            "现金流量表", "cash flow", "现金流量表（续）",
        ],
        "equity_change": [
            "所有者权益变动表", "权益变动表", "equity change",
            "股东权益变动表",
        ],
        "notes_account": [
            "货币资金", "应收账款", "应收票据", "预付款项", "其他应收款",
            "存货", "固定资产", "在建工程", "无形资产", "长期股权投资",
            "短期借款", "应付账款", "预收款项", "应付职工薪酬", "应交税费",
            "长期借款", "应付债券", "实收资本", "资本公积", "盈余公积",
            "营业收入", "营业成本", "销售费用", "管理费用", "财务费用",
            "资产减值", "信用减值", "坏账准备", "累计折旧", "累计摊销",
            "递延所得税", "预计负债", "或有事项", "租赁", "关联交易",
            "期后事项", "其他综合收益", "每股收益",
        ],
        "notes_other": [
            "公司基本情况", "主要会计政策", "合并范围", "企业合并",
            "子公司", "联营企业", "合营企业", "金融工具", "公允价值",
            "股份支付", "职工薪酬", "政府补助", "所得税",
        ],
    }

    # Known cross-statement reconciliation patterns for BS
    BS_RECONCILE_ACCOUNTS = {
        "应收账款": ("应收账款", "坏账准备", "应收账款账面价值"),
        "其他应收款": ("其他应收款", "坏账准备", "其他应收款账面价值"),
        "存货": ("存货", "存货跌价准备", "存货账面价值"),
        "固定资产": ("固定资产原值", "累计折旧", "固定资产减值准备", "固定资产账面价值"),
        "在建工程": ("在建工程", "在建工程减值准备", "在建工程账面价值"),
        "无形资产": ("无形资产原值", "累计摊销", "无形资产减值准备", "无形资产账面价值"),
    }

    def build_manifest(self, doc: TableDocument) -> dict[str, Any]:
        manifest: dict[str, Any] = {
            "domain": self.domain,
            "statements": {},
        }

        for sheet in doc.sheets:
            cat = sheet.metadata.get("category", "")
            if cat in ("balance_sheet", "income_statement", "cash_flow", "equity_change"):
                manifest["statements"][cat] = {
                    "sheet_name": sheet.name,
                    "page_ref": sheet.page_ref,
                    "columns": [
                        {"index": c.index, "header": c.header, "role": c.role}
                        for c in sheet.columns
                    ],
                    "number_format": sheet.metadata.get("number_format", "normal"),
                }

        return manifest

    def build_note_map(self, doc: TableDocument) -> dict[str, Any]:
        note_map: dict[str, Any] = {}
        for sheet in doc.sheets:
            cat = sheet.metadata.get("category", "")
            if cat == "notes_account":
                note_map[sheet.name] = {
                    "sheet_name": sheet.name,
                    "page_ref": sheet.page_ref,
                }
        return note_map

    def enrich_columns(self, sheet: TableSheet, category: str) -> None:
        """Enrich: detect 合并 vs 母公司, period columns, unit."""
        # Detect reporting scope
        name_lower = sheet.name.lower().replace(" ", "")
        if "合并" in name_lower:
            sheet.metadata["scope"] = "consolidated"
        elif "母公司" in name_lower or "公司本部" in name_lower:
            sheet.metadata["scope"] = "parent"
        else:
            sheet.metadata["scope"] = "unspecified"

        # Detect number format from caption or first rows
        fmt = sheet.metadata.get("number_format", "")
        if not fmt:
            # Scan first few rows for unit markers
            for i in range(min(5, len(sheet.rows))):
                for cell in sheet.rows[i].cells:
                    df = detect_number_format(cell.raw)
                    if df != "normal":
                        fmt = df
                        break
                if fmt and fmt != "normal":
                    break
        sheet.metadata["number_format"] = fmt if fmt else "normal"

        # For BS/IS/CF sheets, label columns with period info
        if category in ("balance_sheet", "income_statement", "cash_flow", "equity_change"):
            for col in sheet.columns:
                hdr = col.header
                if "期末" in hdr or "202" in hdr:
                    col.role = "end_balance"
                    col.is_numeric = True
                elif "年初" in hdr or "期初" in hdr or "上年" in hdr:
                    col.role = "begin_balance"
                    col.is_numeric = True


# ---------------------------------------------------------------------------
# Special Audit Adapter (专项审计)
# ---------------------------------------------------------------------------

class SpecialAuditAdapter(DomainAdapter):
    """Maps 专项审计 tables (budget vs actual, term comparison, rectification)."""

    domain = "special_audit"
    label = "专项审计"

    sheet_classifiers = {
        "budget_vs_actual": [
            "预算执行", "预算与实际", "预算对比", "预算批复与执行",
            "收支预算", "资金预算", "财政拨款",
        ],
        "term_comparison": [
            "任期", "任期初", "任期初末", "经济责任", "任期经济",
            "离任", "任中", "任期对比",
        ],
        "fund_balance": [
            "专项资金", "收支平衡", "资金平衡", "专款",
            "资金来源与运用", "资金收支",
        ],
        "problem_summary": [
            "问题汇总", "审计发现问题", "违规", "整改",
            "审计发现", "问题清单",
        ],
        "rectification": [
            "整改情况", "整改追踪", "整改落实", "整改结果",
            "已整改", "正在整改", "未整改",
        ],
    }

    def build_manifest(self, doc: TableDocument) -> dict[str, Any]:
        manifest: dict[str, Any] = {
            "domain": self.domain,
            "tables": {},
        }
        for sheet in doc.sheets:
            cat = sheet.metadata.get("category", "")
            if cat != "unknown":
                manifest["tables"][cat] = {
                    "sheet_name": sheet.name,
                    "page_ref": sheet.page_ref,
                    "columns": [
                        {"index": c.index, "header": c.header, "role": c.role}
                        for c in sheet.columns
                    ],
                }
        return manifest

    def enrich_columns(self, sheet: TableSheet, category: str) -> None:
        """Enrich: detect budget/actual/term columns."""
        for col in sheet.columns:
            hdr = col.header
            if any(kw in hdr for kw in ("预算", "批复", "计划", "budget")):
                col.role = "budget_amount"
                col.is_numeric = True
            elif any(kw in hdr for kw in ("实际", "执行", "决算", "actual")):
                col.role = "actual_amount"
                col.is_numeric = True
            elif any(kw in hdr for kw in ("差异", "差额", "超支", "结余")):
                col.role = "difference"
                col.is_numeric = True
            elif any(kw in hdr for kw in ("任期初", "期初", "上任初")):
                col.role = "term_begin"
                col.is_numeric = True
            elif any(kw in hdr for kw in ("任期初末", "期末", "离任时")):
                col.role = "term_end"
                col.is_numeric = True
            elif any(kw in hdr for kw in ("整改状态", "是否整改", "状态")):
                col.role = "rectification_status"


# ---------------------------------------------------------------------------
# Engineering Adapter (工程咨询)
# ---------------------------------------------------------------------------

class EngineeringAdapter(DomainAdapter):
    """Maps engineering consulting tables (five-comparison, BOQ, variation)."""

    domain = "engineering"
    label = "工程咨询"

    sheet_classifiers = {
        "five_way_comparison": [
            "五算", "概算", "预算", "标底", "结算", "决算",
            "投资估算", "设计概算", "施工图预算", "招标控制价",
            "竣工结算", "竣工决算", "造价对比",
        ],
        "boq": [
            "工程量清单", "分部分项", "清单计价", "BOQ",
            "工程量", "综合单价",
        ],
        "variation": [
            "变更", "签证", "洽商", "工程变更", "设计变更",
            "变更增减", "变更汇总",
        ],
        "progress_payment": [
            "进度款", "工程款", "计量支付", "支付申请",
            "已完工程量", "工程进度",
        ],
        "material_adjustment": [
            "材料调差", "材料价格", "价差", "信息价",
            "材料价差调整",
        ],
    }

    def build_manifest(self, doc: TableDocument) -> dict[str, Any]:
        manifest: dict[str, Any] = {
            "domain": self.domain,
            "tables": {},
        }
        for sheet in doc.sheets:
            cat = sheet.metadata.get("category", "")
            if cat != "unknown":
                manifest["tables"][cat] = {
                    "sheet_name": sheet.name,
                    "page_ref": sheet.page_ref,
                    "columns": [
                        {"index": c.index, "header": c.header, "role": c.role}
                        for c in sheet.columns
                    ],
                }
        return manifest

    def enrich_columns(self, sheet: TableSheet, category: str) -> None:
        """Enrich: detect estimate/budget/contract/settlement/decision columns."""
        if category == "five_way_comparison":
            for col in sheet.columns:
                hdr = col.header
                if any(kw in hdr for kw in ("概算", "估算", "estimate")):
                    col.role = "estimate_amount"
                    col.is_numeric = True
                elif any(kw in hdr for kw in ("预算", "施工图预算", "budget")):
                    col.role = "budget_amount"
                    col.is_numeric = True
                elif any(kw in hdr for kw in ("标底", "控制价", "合同价", "中标")):
                    col.role = "contract_amount"
                    col.is_numeric = True
                elif any(kw in hdr for kw in ("结算", "settlement")):
                    col.role = "settlement_amount"
                    col.is_numeric = True
                elif any(kw in hdr for kw in ("决算", "final")):
                    col.role = "final_amount"
                    col.is_numeric = True

        elif category == "variation":
            for col in sheet.columns:
                hdr = col.header
                if any(kw in hdr for kw in ("变更前")):
                    col.role = "before_change"
                    col.is_numeric = True
                elif any(kw in hdr for kw in ("变更后")):
                    col.role = "after_change"
                    col.is_numeric = True
                elif any(kw in hdr for kw in ("增减", "变更金额")):
                    col.role = "change_amount"
                    col.is_numeric = True


# ---------------------------------------------------------------------------
# Performance Adapter (绩效评价)
# ---------------------------------------------------------------------------

class PerformanceAdapter(DomainAdapter):
    """Maps performance evaluation tables (indicator system, scoring)."""

    domain = "performance"
    label = "绩效评价"

    sheet_classifiers = {
        "indicator_system": [
            "绩效指标", "指标体系", "评价指标", "考核指标",
            "绩效目标", "指标框架", "评分标准",
        ],
        "scoring_detail": [
            "评分表", "打分", "自评", "复评", "得分明细",
            "评价得分", "绩效评分",
        ],
        "self_vs_review": [
            "自评与复评", "自评对比", "复核对比",
        ],
        "fund_efficiency": [
            "资金效率", "资金到位", "资金使用", "预算执行",
            "到位率", "使用率", "执行率",
        ],
        "target_completion": [
            "目标完成", "产出数量", "产出质量", "产出时效",
            "效益指标", "满意度",
        ],
        "multi_source_verification": [
            "台账", "现场核查", "抽查", "核实", "多源比对",
        ],
    }

    def build_manifest(self, doc: TableDocument) -> dict[str, Any]:
        manifest: dict[str, Any] = {
            "domain": self.domain,
            "tables": {},
        }
        for sheet in doc.sheets:
            cat = sheet.metadata.get("category", "")
            if cat != "unknown":
                manifest["tables"][cat] = {
                    "sheet_name": sheet.name,
                    "page_ref": sheet.page_ref,
                    "columns": [
                        {"index": c.index, "header": c.header, "role": c.role}
                        for c in sheet.columns
                    ],
                }
        return manifest

    def enrich_columns(self, sheet: TableSheet, category: str) -> None:
        """Enrich: detect indicator hierarchy, weight, self-score, review-score."""
        for col in sheet.columns:
            hdr = col.header.lower().replace(" ", "")
            if "指标" in hdr or "项目" in hdr or "indicator" in hdr:
                col.role = "indicator_name"
            elif "权重" in hdr or "weight" in hdr:
                col.role = "weight"
                col.is_numeric = True
            elif "目标" in hdr or "target" in hdr:
                col.role = "target_value"
                col.is_numeric = True
            elif "实际" in hdr and "自评" not in hdr and "复评" not in hdr:
                col.role = "actual_value"
                col.is_numeric = True
            elif "自评" in hdr:
                col.role = "self_score"
                col.is_numeric = True
            elif "复评" in hdr or "复核" in hdr:
                col.role = "review_score"
                col.is_numeric = True
            elif "得分" in hdr:
                col.role = "score"
                col.is_numeric = True
            elif "到位率" in hdr:
                col.role = "arrival_rate"
                col.is_numeric = True
            elif "使用率" in hdr:
                col.role = "usage_rate"
                col.is_numeric = True
            elif "执行率" in hdr:
                col.role = "execution_rate"
                col.is_numeric = True
            elif "台账" in hdr:
                col.role = "ledger_value"
                col.is_numeric = True
            elif "财务" in hdr or "账面" in hdr:
                col.role = "financial_value"
                col.is_numeric = True
            elif "现场" in hdr or "抽查" in hdr:
                col.role = "on_site_value"
                col.is_numeric = True


# ---------------------------------------------------------------------------
# Adapter Registry & Auto-Detection
# ---------------------------------------------------------------------------

_ADAPTERS: dict[str, DomainAdapter] = {
    "annual_report": AnnualReportAdapter(),
    "special_audit": SpecialAuditAdapter(),
    "engineering": EngineeringAdapter(),
    "performance": PerformanceAdapter(),
}


def get_adapter(domain: str) -> Optional[DomainAdapter]:
    """Get a domain adapter by name."""
    return _ADAPTERS.get(domain)


def list_adapters() -> list[dict[str, str]]:
    """List all available domain adapters."""
    return [
        {"domain": a.domain, "label": a.label}
        for a in _ADAPTERS.values()
    ]


def auto_detect_domain(doc: TableDocument) -> list[tuple[str, float]]:
    """
    Auto-detect which domain(s) a document belongs to.
    
    Returns a list of (domain, confidence) pairs sorted by confidence descending.
    """
    scores: dict[str, float] = {}
    total_sheets = len(doc.sheets)

    if total_sheets == 0:
        return []

    for domain, adapter in _ADAPTERS.items():
        classified = 0
        for sheet in doc.sheets:
            cat = adapter.classify_sheet(sheet)
            if cat != "unknown":
                classified += 1
        scores[domain] = classified / total_sheets if total_sheets > 0 else 0

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def apply_all_adapters(doc: TableDocument) -> TableDocument:
    """
    Apply all domain adapters. Each sheet is classified by the best-matching
    adapter, and adapters enrich only their own sheets.
    """
    # Auto-detect primary domain
    detections = auto_detect_domain(doc)
    primary = detections[0][0] if detections else "annual_report"

    adapter = get_adapter(primary)
    if adapter:
        doc = adapter.apply(doc)

    return doc
