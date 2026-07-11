"""
工具13：three_flow_checker — 三流合一交叉验证器

v11新增，基于「闲舟渡流年」《关联交易隐形利益输送，国企内审硬核实战》。

核心逻辑：
  "货物流、资金流、票据流、合同流"四流交叉比对 →
  一流不一致=+1分 → 四流全不一致=4分虚假贸易评分

检测维度：
  1. 合同流 vs 资金流：合同金额/日期/对手方 vs 付款记录
  2. 合同流 vs 货物流：合同数量/规格 vs 出入库/物流记录
  3. 合同流 vs 票据流：合同信息 vs 发票信息
  4. 资金流 vs 货物流：付款金额 vs 实际交货数量
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime
import csv


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class FlowMismatch:
    """单个流不一致记录"""
    transaction_id: str
    mismatch_type: str  # contract_vs_fund | contract_vs_goods | fund_vs_goods | contract_vs_invoice
    field: str           # amount / date / counterparty / quantity / specification
    expected: str
    actual: str
    deviation: str = ""  # 偏差描述
    severity: str = "medium"  # high / medium / low


@dataclass
class ThreeFlowResult:
    """三流合一验证完整结果"""
    total_transactions: int
    matched_transactions: int       # 四流一致
    mismatched_transactions: int    # 至少一流不一致
    mismatches: List[FlowMismatch]
    summary_by_type: Dict[str, int]  # mismatch_type → count
    fictitious_trade_scores: Dict[str, int]  # transaction_id → 0-4分
    high_risk_transactions: List[str]  # 虚假贸易评分≥3
    summary: str


# ═══════════════════════════════════════════════════════════════
# 三流合一验证器
# ═══════════════════════════════════════════════════════════════

class ThreeFlowChecker:
    """
    三流合一交叉验证器

    输入4类数据：
    - contracts: 合同数据 [{contract_id, counterparty, amount, quantity, sign_date, ...}]
    - funds: 资金流水 [{payment_id, contract_id, payer, payee, amount, pay_date, ...}]
    - goods: 货物流 [{delivery_id, contract_id, quantity, spec, receipt_date, ...}]
    - invoices: 票据流 [{invoice_id, contract_id, amount, invoice_date, counterparty, ...}]

    输出：
    - 四流不一致记录
    - 虚假贸易评分（0-4）
    - 高风险交易清单
    """

    def __init__(
        self,
        amount_tolerance: float = 0.05,   # 金额容差 5%
        date_tolerance_days: int = 7,      # 日期容差 7天
        quantity_tolerance: float = 0.03,  # 数量容差 3%
    ):
        self.amount_tolerance = amount_tolerance
        self.date_tolerance_days = date_tolerance_days
        self.quantity_tolerance = quantity_tolerance

    def check(
        self,
        contracts: List[Dict[str, Any]],
        funds: Optional[List[Dict[str, Any]]] = None,
        goods: Optional[List[Dict[str, Any]]] = None,
        invoices: Optional[List[Dict[str, Any]]] = None,
    ) -> ThreeFlowResult:
        """
        主检测入口

        Args:
            contracts: 合同列表
            funds: 资金流水（可选）
            goods: 货物流记录（可选）
            invoices: 票据流记录（可选）

        Returns:
            ThreeFlowResult
        """
        funds = funds or []
        goods = goods or []
        invoices = invoices or []

        mismatches: List[FlowMismatch] = []
        scores: Dict[str, int] = defaultdict(int)

        # 构建索引
        funds_by_contract = defaultdict(list)
        for f in funds:
            cid = f.get("contract_id", "")
            if cid:
                funds_by_contract[cid].append(f)

        goods_by_contract = defaultdict(list)
        for g in goods:
            cid = g.get("contract_id", "")
            if cid:
                goods_by_contract[cid].append(g)

        invoices_by_contract = defaultdict(list)
        for inv in invoices:
            cid = inv.get("contract_id", "")
            if cid:
                invoices_by_contract[cid].append(inv)

        # 逐合同比对
        matched = 0
        for contract in contracts:
            cid = contract.get("contract_id", "")
            contract_amount = float(contract.get("amount", 0))
            contract_quantity = float(contract.get("quantity", 0))
            contract_date = contract.get("sign_date", "")
            counterparty = contract.get("counterparty", "")

            flow_issues = 0

            # 1. 合同 vs 资金
            if funds_by_contract.get(cid):
                self._check_contract_vs_funds(
                    contract, funds_by_contract[cid], mismatches, flow_issues
                )
            elif funds:
                # 有资金数据但本合同无对应记录
                flow_issues += 1
                mismatches.append(FlowMismatch(
                    transaction_id=cid,
                    mismatch_type="contract_vs_fund",
                    field="payment",
                    expected="有付款记录",
                    actual="无对应付款",
                    severity="high",
                    deviation="合同存在但资金流缺失"
                ))
                scores[cid] = scores.get(cid, 0) + 1

            # 2. 合同 vs 货物
            if goods_by_contract.get(cid):
                self._check_contract_vs_goods(
                    contract, goods_by_contract[cid], mismatches, flow_issues
                )
            elif goods:
                flow_issues += 1
                mismatches.append(FlowMismatch(
                    transaction_id=cid,
                    mismatch_type="contract_vs_goods",
                    field="delivery",
                    expected="有交货记录",
                    actual="无对应交货",
                    severity="high",
                    deviation="合同存在但货物流缺失"
                ))
                scores[cid] = scores.get(cid, 0) + 1

            # 3. 合同 vs 发票
            if invoices_by_contract.get(cid):
                self._check_contract_vs_invoices(
                    contract, invoices_by_contract[cid], mismatches, flow_issues
                )
            elif invoices:
                flow_issues += 1
                mismatches.append(FlowMismatch(
                    transaction_id=cid,
                    mismatch_type="contract_vs_invoice",
                    field="invoice",
                    expected="有发票记录",
                    actual="无对应发票",
                    severity="high",
                    deviation="合同存在但票据流缺失"
                ))
                scores[cid] = scores.get(cid, 0) + 1

            # 4. 资金 vs 货物（交叉验证）
            if funds_by_contract.get(cid) and goods_by_contract.get(cid):
                self._check_funds_vs_goods(
                    funds_by_contract[cid], goods_by_contract[cid], cid, mismatches
                )

            if flow_issues == 0:
                matched += 1

            scores[cid] = scores.get(cid, 0) + flow_issues

        # 汇总
        summary_by_type = Counter(m.mismatch_type for m in mismatches)
        high_risk = [tid for tid, score in scores.items() if score >= 3]

        summary = (
            f"三流合一验证完成：共{len(contracts)}笔交易，"
            f"四流一致{matched}笔，不一致{len(contracts)-matched}笔。"
            f"虚假贸易高风险（评分≥3）：{len(high_risk)}笔。"
        )

        return ThreeFlowResult(
            total_transactions=len(contracts),
            matched_transactions=matched,
            mismatched_transactions=len(contracts) - matched,
            mismatches=mismatches,
            summary_by_type=dict(summary_by_type),
            fictitious_trade_scores=dict(scores),
            high_risk_transactions=high_risk,
            summary=summary,
        )

    def _check_contract_vs_funds(
        self, contract: Dict, fund_records: List[Dict],
        mismatches: List[FlowMismatch], flow_issues: List
    ):
        cid = contract.get("contract_id", "")
        c_amount = float(contract.get("amount", 0))
        c_date = contract.get("sign_date", "")
        c_counterparty = contract.get("counterparty", "")

        total_paid = sum(float(f.get("amount", 0)) for f in fund_records)

        # 金额比对
        if c_amount > 0 and abs(total_paid - c_amount) / c_amount > self.amount_tolerance:
            flow_issues.append(1)
            mismatches.append(FlowMismatch(
                transaction_id=cid,
                mismatch_type="contract_vs_fund",
                field="amount",
                expected=f"合同金额 {c_amount}",
                actual=f"付款总额 {total_paid}",
                deviation=f"偏差 {(total_paid - c_amount) / c_amount * 100:.1f}%",
                severity="high" if abs(total_paid - c_amount) / c_amount > 0.2 else "medium",
            ))

        # 对手方比对
        for f in fund_records:
            f_payee = f.get("payee", "")
            f_payer = f.get("payer", "")
            if c_counterparty and f_payee and c_counterparty not in f_payee and f_payer not in c_counterparty:
                mismatches.append(FlowMismatch(
                    transaction_id=cid,
                    mismatch_type="contract_vs_fund",
                    field="counterparty",
                    expected=f"合同对手方 {c_counterparty}",
                    actual=f"付款收付方 {f_payer}→{f_payee}",
                    severity="high",
                    deviation="合同对手方与付款对手方不一致"
                ))
                break

    def _check_contract_vs_goods(
        self, contract: Dict, goods_records: List[Dict],
        mismatches: List[FlowMismatch], flow_issues: List
    ):
        cid = contract.get("contract_id", "")
        c_quantity = float(contract.get("quantity", 0))

        total_delivered = sum(float(g.get("quantity", 0)) for g in goods_records)

        if c_quantity > 0 and abs(total_delivered - c_quantity) / c_quantity > self.quantity_tolerance:
            flow_issues.append(1)
            mismatches.append(FlowMismatch(
                transaction_id=cid,
                mismatch_type="contract_vs_goods",
                field="quantity",
                expected=f"合同数量 {c_quantity}",
                actual=f"实收数量 {total_delivered}",
                deviation=f"偏差 {(total_delivered - c_quantity) / c_quantity * 100:.1f}%",
                severity="high" if abs(total_delivered - c_quantity) / c_quantity > 0.2 else "medium",
            ))

    def _check_contract_vs_invoices(
        self, contract: Dict, invoice_records: List[Dict],
        mismatches: List[FlowMismatch], flow_issues: List
    ):
        cid = contract.get("contract_id", "")
        c_amount = float(contract.get("amount", 0))

        total_invoiced = sum(float(inv.get("amount", 0)) for inv in invoice_records)

        if c_amount > 0 and abs(total_invoiced - c_amount) / c_amount > self.amount_tolerance:
            flow_issues.append(1)
            mismatches.append(FlowMismatch(
                transaction_id=cid,
                mismatch_type="contract_vs_invoice",
                field="amount",
                expected=f"合同金额 {c_amount}",
                actual=f"发票总额 {total_invoiced}",
                deviation=f"偏差 {(total_invoiced - c_amount) / c_amount * 100:.1f}%",
                severity="high" if abs(total_invoiced - c_amount) / c_amount > 0.2 else "medium",
            ))

    def _check_funds_vs_goods(
        self, fund_records: List[Dict], goods_records: List[Dict],
        cid: str, mismatches: List[FlowMismatch]
    ):
        """资金 vs 货物：付款金额 vs 实收数量是否匹配"""
        total_paid = sum(float(f.get("amount", 0)) for f in fund_records)
        total_quantity = sum(float(g.get("quantity", 0)) for g in goods_records)

        if total_paid > 0 and total_quantity > 0:
            # 简化的单价比对：总付款/总数量
            unit_paid = total_paid / total_quantity
            # 如果合同有单价信息，可在此比对
            # 此处做基本判定：付款金额不为零但交货数量为零→重大异常
            pass

        if total_paid > 0 and total_quantity == 0:
            mismatches.append(FlowMismatch(
                transaction_id=cid,
                mismatch_type="fund_vs_goods",
                field="existence",
                expected=f"付款 {total_paid}元应有对应交货",
                actual="有付款无交货",
                severity="high",
                deviation="资金已流出但无实物流转→虚假贸易嫌疑"
            ))


# ═══════════════════════════════════════════════════════════════
# 便捷接口
# ═══════════════════════════════════════════════════════════════

def check_three_flows(
    contracts: List[Dict[str, Any]],
    funds: Optional[List[Dict[str, Any]]] = None,
    goods: Optional[List[Dict[str, Any]]] = None,
    invoices: Optional[List[Dict[str, Any]]] = None,
    amount_tolerance: float = 0.05,
) -> ThreeFlowResult:
    """
    便捷接口：三流合一验证

    Args:
        contracts: 合同数据
        funds: 资金流水（可选）
        goods: 货物流记录（可选）
        invoices: 票据流记录（可选）
        amount_tolerance: 金额容差（默认5%）

    Returns:
        ThreeFlowResult
    """
    checker = ThreeFlowChecker(amount_tolerance=amount_tolerance)
    return checker.check(contracts, funds, goods, invoices)


def export_mismatches_to_csv(result: ThreeFlowResult, output_path: str) -> None:
    """导出不一致记录到CSV"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "交易ID", "不一致类型", "字段", "期望值", "实际值",
            "偏差", "严重程度"
        ])
        for m in result.mismatches:
            writer.writerow([
                m.transaction_id, m.mismatch_type, m.field,
                m.expected, m.actual, m.deviation, m.severity,
            ])
    print(f"已导出{len(result.mismatches)}条不一致记录到 {output_path}")
