"""
变更签证审核
============
执行"三查原则"（真伪/合规/造价）审核变更签证，
检测累计变更是否触发合同上限条款，生成审核清单。

用法:
    python -m tools.engineering.change_order_audit --input data.json --output result.json
"""

import json
import argparse
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, date

# ============================================================
# 可配置阈值
# ============================================================
CONTRACT_PRICE_CHANGE_LIMIT = 0.15   # 合同变更累计上限（默认15%，超此值需重新招标）
APPROVAL_STEPS_REQUIRED = [          # 必须的审批环节
    "监理审核", "建设单位审批"
]
CONSTRUCTION_LOG_WINDOW_DAYS = 7     # 施工日志对应用的天数窗口（变更日期±N天内有日志记录）
# ============================================================


@dataclass
class ChangeOrder:
    """变更签证记录"""
    change_id: str                  # 变更编号
    change_date: str                # 变更日期 YYYY-MM-DD
    description: str                # 变更内容描述
    amount: float                   # 变更金额（元，正数=增加，负数=减少）
    approval_chain: list[str]       # 审批流程 ["监理审核", "建设单位审批", ...]
    approval_status: str            # 审批状态: approved/pending/rejected
    has_construction_log: bool = False      # 是否有对应施工日志
    construction_log_date: str = ""         # 施工日志日期
    verifier: str = ""                      # 审核人
    remark: str = ""                        # 备注


@dataclass
class ChangeAuditItem:
    """单个变更的审核结果"""
    change_id: str
    change_date: str
    description: str
    amount: float
    authenticity_check: str         # 真伪检查结果: pass/fail/warning
    authenticity_detail: str
    compliance_check: str           # 合规检查结果
    compliance_detail: str
    cost_check: str                 # 造价检查结果
    cost_detail: str
    overall_verdict: str            # 综合判定: pass/review/fail
    issues: list[str] = field(default_factory=list)


@dataclass
class ChangeOrderResult:
    """变更签证审核完整结果"""
    project_name: str
    contract_amount: float          # 合同总价
    audit_items: list[ChangeAuditItem] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    total_change_amount: float = 0.0
    change_rate: float = 0.0
    limit_triggered: bool = False   # 是否触发重新招标上限

    def to_json(self) -> str:
        return json.dumps({
            "project_name": self.project_name,
            "contract_amount": self.contract_amount,
            "total_change_amount": round(self.total_change_amount, 2),
            "change_rate": round(self.change_rate, 4),
            "limit_triggered": self.limit_triggered,
            "summary": self.summary,
            "audit_items": [
                {
                    "change_id": it.change_id,
                    "change_date": it.change_date,
                    "description": it.description,
                    "amount": it.amount,
                    "authenticity_check": it.authenticity_check,
                    "compliance_check": it.compliance_check,
                    "cost_check": it.cost_check,
                    "overall_verdict": it.overall_verdict,
                    "issues": it.issues
                }
                for it in self.audit_items
            ]
        }, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            f"# 变更签证审核报告 — {self.project_name}",
            "",
            "## 汇总",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 合同总价 | {self.contract_amount:,.2f} 元 |",
            f"| 变更总数 | {self.summary.get('total_changes', 0)} 项 |",
            f"| 累计变更金额 | {self.total_change_amount:+,.2f} 元 |",
            f"| 变更率 | {self.change_rate:.2%} |",
            f"| 通过 | {self.summary.get('passed', 0)} 项 |",
            f"| 存疑 | {self.summary.get('review', 0)} 项 |",
            f"| 未通过 | {self.summary.get('failed', 0)} 项 |",
        ]

        if self.limit_triggered:
            lines.append(f"| ⚠️ 触发重新招标上限 | 累计变更超合同价 {CONTRACT_PRICE_CHANGE_LIMIT:.0%} |")
        else:
            lines.append(f"| 重招上限 | 未触发（{CONTRACT_PRICE_CHANGE_LIMIT:.0%}） |")

        lines += ["", "## 审核明细"]

        for it in self.audit_items:
            emoji = {"pass": "✅", "review": "⚠️", "fail": "❌"}.get(it.overall_verdict, "❓")
            lines += [
                f"### {emoji} {it.change_id} — {it.change_date}",
                f"**内容**: {it.description}",
                f"**金额**: {it.amount:+,.2f} 元",
                f"**判定**: {it.overall_verdict}",
                "",
                "| 检查项 | 结果 | 说明 |",
                "|--------|------|------|",
                f"| 真伪 | {it.authenticity_check} | {it.authenticity_detail} |",
                f"| 合规 | {it.compliance_check} | {it.compliance_detail} |",
                f"| 造价 | {it.cost_check} | {it.cost_detail} |",
            ]
            if it.issues:
                lines.append("**问题**:")
                for issue in it.issues:
                    lines.append(f"- {issue}")
            lines.append("")

        # 累计变更趋势
        if len(self.audit_items) > 1:
            items_sorted = sorted(self.audit_items, key=lambda x: x.change_date)
            cumulative = 0.0
            lines += ["## 累计变更趋势", "| 日期 | 本次金额 | 累计金额 | 累计变更率 |",
                       "|------|----------|----------|------------|"]
            for it in items_sorted:
                cumulative += it.amount
                rate = cumulative / self.contract_amount if self.contract_amount else 0
                lines.append(
                    f"| {it.change_date} | {it.amount:+,.2f} | {cumulative:+,.2f} "
                    f"| {rate:.2%} |"
                )

        lines.append("")
        lines.append("---")
        lines.append("*本报告由融策工程咨询Agent自动生成，仅供专业人员参考。*")
        return "\n".join(lines)


def _check_authenticity(change: ChangeOrder) -> tuple[str, str, list[str]]:
    """
    真伪检查：是否有施工日志对应

    Returns:
        (check_result, detail, issues)
    """
    issues = []
    if not change.has_construction_log:
        issues.append(f"变更 {change.change_id} 无对应施工日志记录")
        return ("warning", "未找到对应施工日志，真实性待核实", issues)

    # 检查日志日期是否在变更日期附近
    try:
        change_dt = datetime.strptime(change.change_date, "%Y-%m-%d").date()
        log_dt = datetime.strptime(change.construction_log_date, "%Y-%m-%d").date()
        diff_days = abs((change_dt - log_dt).days)
        if diff_days > CONSTRUCTION_LOG_WINDOW_DAYS:
            issues.append(
                f"施工日志日期 {change.construction_log_date} 与变更日期 "
                f"{change.change_date} 相差 {diff_days} 天，超出 {CONSTRUCTION_LOG_WINDOW_DAYS} 天窗口"
            )
            return ("warning", f"施工日志日期偏差 {diff_days} 天", issues)
        return ("pass", f"施工日志日期匹配（偏差 {diff_days} 天）", issues)
    except ValueError:
        return ("warning", "日期格式异常，无法比对", issues)


def _check_compliance(change: ChangeOrder) -> tuple[str, str, list[str]]:
    """
    合规检查：审批流程是否完整

    Returns:
        (check_result, detail, issues)
    """
    issues = []

    if change.approval_status == "rejected":
        issues.append(f"变更 {change.change_id} 审批状态为'已拒绝'")
        return ("fail", "审批已拒绝", issues)

    if change.approval_status == "pending":
        issues.append(f"变更 {change.change_id} 审批状态为'待审批'")
        return ("warning", "审批未完成", issues)

    # 检查必要审批环节
    for step in APPROVAL_STEPS_REQUIRED:
        found = any(step in a for a in change.approval_chain)
        if not found:
            issues.append(f"缺少必要审批环节: {step}")
            return ("fail", f"审批流程不完整: 缺少'{step}'", issues)

    return ("pass", f"审批流程完整（{len(change.approval_chain)} 环节）", issues)


def _check_cost(change: ChangeOrder) -> tuple[str, str, list[str]]:
    """
    造价检查：金额合理性

    Returns:
        (check_result, detail, issues)
    """
    issues = []

    if change.amount == 0:
        issues.append("变更金额为零，请核实是否为占位记录")
        return ("warning", "变更金额为零", issues)

    # 检查是否有审核人
    if not change.verifier:
        issues.append("变更签证缺少造价审核人签字")
        return ("warning", "缺少审核人", issues)

    return ("pass", f"金额 {change.amount:+,.2f} 元，审核人: {change.verifier}", issues)


def audit_change_orders(
    changes: list[ChangeOrder],
    contract_amount: float,
    project_name: str = ""
) -> ChangeOrderResult:
    """
    执行变更签证审核（三查原则）

    Args:
        changes: 变更签证记录列表
        contract_amount: 合同总价
        project_name: 项目名称

    Returns:
        ChangeOrderResult: 审核结果
    """
    audit_items: list[ChangeAuditItem] = []

    for change in changes:
        all_issues = []

        # 三查
        auth_result, auth_detail, auth_issues = _check_authenticity(change)
        all_issues.extend(auth_issues)

        comp_result, comp_detail, comp_issues = _check_compliance(change)
        all_issues.extend(comp_issues)

        cost_result, cost_detail, cost_issues = _check_cost(change)
        all_issues.extend(cost_issues)

        # 综合判定
        results = [auth_result, comp_result, cost_result]
        if "fail" in results:
            verdict = "fail"
        elif "warning" in results:
            verdict = "review"
        else:
            verdict = "pass"

        audit_items.append(ChangeAuditItem(
            change_id=change.change_id,
            change_date=change.change_date,
            description=change.description,
            amount=change.amount,
            authenticity_check=auth_result,
            authenticity_detail=auth_detail,
            compliance_check=comp_result,
            compliance_detail=comp_detail,
            cost_check=cost_result,
            cost_detail=cost_detail,
            overall_verdict=verdict,
            issues=all_issues
        ))

    # 汇总
    total_change = sum(c.amount for c in changes)
    change_rate = abs(total_change) / contract_amount if contract_amount else 0
    limit_triggered = change_rate > CONTRACT_PRICE_CHANGE_LIMIT

    verdict_counts = {"pass": 0, "review": 0, "fail": 0}
    for it in audit_items:
        verdict_counts[it.overall_verdict] += 1

    return ChangeOrderResult(
        project_name=project_name,
        contract_amount=contract_amount,
        audit_items=audit_items,
        summary={
            "total_changes": len(changes),
            **verdict_counts
        },
        total_change_amount=round(total_change, 2),
        change_rate=round(change_rate, 4),
        limit_triggered=limit_triggered
    )


# ============================================================
# CLI入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="变更签证审核")
    parser.add_argument("--input", required=True, help="输入JSON文件路径")
    parser.add_argument("--output", required=True, help="输出JSON文件路径")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    project_name = data.get("project_name", "")
    contract_amount = float(data.get("contract_amount", 0))

    changes = [ChangeOrder(
        change_id=c["change_id"],
        change_date=c["change_date"],
        description=c.get("description", ""),
        amount=float(c.get("amount", 0)),
        approval_chain=c.get("approval_chain", []),
        approval_status=c.get("approval_status", "pending"),
        has_construction_log=c.get("has_construction_log", False),
        construction_log_date=c.get("construction_log_date", ""),
        verifier=c.get("verifier", ""),
        remark=c.get("remark", "")
    ) for c in data.get("changes", [])]

    result = audit_change_orders(changes, contract_amount, project_name)

    if args.format in ("json", "both"):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.to_json())
        print(f"[✓] JSON结果已保存: {args.output}")

    if args.format in ("md", "both"):
        out_md = args.output.replace(".json", ".md")
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(result.to_markdown())
        print(f"[✓] Markdown报告已保存: {out_md}")

    print(f"\n{'='*50}")
    print(f"项目: {project_name} | 合同价: {contract_amount:,.2f} 元")
    print(f"变更数: {result.summary['total_changes']} | "
          f"通过: {result.summary['pass']} | 存疑: {result.summary['review']} | 未通过: {result.summary['fail']}")
    print(f"累计变更: {result.total_change_amount:+,.2f} 元 ({result.change_rate:.2%})")
    if result.limit_triggered:
        print(f"⚠️ 累计变更超合同价 {CONTRACT_PRICE_CHANGE_LIMIT:.0%}，需重新招标！")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
