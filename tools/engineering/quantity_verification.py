"""
工程量清单核对
==============
比对招标清单与结算清单，检出新增项、删减项、数量变更项。

用法:
    python -m tools.engineering.quantity_verification --input data.json --output result.json
"""

import json
import re
import argparse
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# 可配置阈值
# ============================================================
QUANTITY_CHANGE_THRESHOLD = 0.05      # 数量变更幅度阈值（默认5%，超过即视为变更）
CODE_MATCH_THRESHOLD = 0.8            # 编码模糊匹配相似度阈值
# ============================================================


@dataclass
class BOQItem:
    """工程量清单项"""
    code: str                       # 项目编码（如 010101001001）
    name: str                       # 项目名称
    unit: str                       # 单位（m³/m²/t等）
    quantity: float                 # 工程量
    unit_price: float = 0.0         # 综合单价（可选）
    total_price: float = 0.0        # 合价（可选）


@dataclass
class QuantityResult:
    """清单核对结果"""
    project_name: str
    new_items: list[dict] = field(default_factory=list)        # 新增项
    removed_items: list[dict] = field(default_factory=list)    # 删减项
    changed_items: list[dict] = field(default_factory=list)    # 数量变更项
    unchanged_items: list[dict] = field(default_factory=list)  # 无变化项
    summary: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "project_name": self.project_name,
            "summary": self.summary,
            "new_items": self.new_items,
            "removed_items": self.removed_items,
            "changed_items": self.changed_items,
            "unchanged_count": len(self.unchanged_items)
        }, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            f"# 工程量清单核对报告 — {self.project_name}",
            "",
            "## 汇总",
            f"| 类别 | 数量 |",
            f"|------|------|",
            f"| 新增项 | {len(self.new_items)} |",
            f"| 删减项 | {len(self.removed_items)} |",
            f"| 变更项 | {len(self.changed_items)} |",
            f"| 无变化项 | {len(self.unchanged_items)} |",
            f"| **合计** | {len(self.new_items) + len(self.removed_items) + len(self.changed_items) + len(self.unchanged_items)} |",
            "",
        ]

        if self.new_items:
            lines += ["## 新增项", "| 编码 | 名称 | 单位 | 结算数量 | 结算单价 |",
                       "|------|------|------|----------|----------|"]
            for it in self.new_items:
                lines.append(f"| {it['code']} | {it['name']} | {it['unit']} "
                             f"| {it['quantity']:,.2f} | {it.get('unit_price', 0):,.2f} |")

        if self.removed_items:
            lines += ["", "## 删减项", "| 编码 | 名称 | 单位 | 原数量 |",
                       "|------|------|------|--------|"]
            for it in self.removed_items:
                lines.append(f"| {it['code']} | {it['name']} | {it['unit']} "
                             f"| {it['quantity']:,.2f} |")

        if self.changed_items:
            lines += ["", "## 数量变更项",
                       "| 编码 | 名称 | 原数量 | 结算数量 | 量差 | 偏差率 |",
                       "|------|------|--------|----------|------|--------|"]
            for it in self.changed_items:
                lines.append(
                    f"| {it['code']} | {it['name']} "
                    f"| {it['original_qty']:,.2f} | {it['settlement_qty']:,.2f} "
                    f"| {it['qty_diff']:,.2f} | {it['change_rate']:.2%} |"
                )

        lines.append("")
        lines.append("---")
        lines.append("*本报告由融策工程咨询Agent自动生成，仅供专业人员参考。*")
        return "\n".join(lines)


def _normalize_code(code: str) -> str:
    """规范化项目编码：去空格、去特殊字符、转大写"""
    return re.sub(r'[^a-zA-Z0-9]', '', code).upper()


def _code_similarity(code_a: str, code_b: str) -> float:
    """计算两个编码的相似度（基于公共前缀长度）"""
    a = _normalize_code(code_a)
    b = _normalize_code(code_b)
    if not a or not b:
        return 0.0
    # 前缀匹配 + Jaccard-like字符集相似
    prefix_len = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            prefix_len += 1
        else:
            break
    # 取较短的编码长度作为分母
    min_len = min(len(a), len(b))
    return prefix_len / min_len if min_len > 0 else 0.0


def verify_quantities(
    tender_items: list[BOQItem],
    settlement_items: list[BOQItem],
    project_name: str = ""
) -> QuantityResult:
    """
    执行工程量清单核对

    Args:
        tender_items: 招标清单
        settlement_items: 结算清单
        project_name: 项目名称

    Returns:
        QuantityResult: 差异清单
    """
    # 构建编码→索引的映射
    tender_map = {_normalize_code(it.code): it for it in tender_items}
    settlement_map = {_normalize_code(it.code): it for it in settlement_items}

    tender_codes = set(tender_map.keys())
    settlement_codes = set(settlement_map.keys())

    result = QuantityResult(project_name=project_name)

    # 1. 新增项：结算有、招标无
    for code in settlement_codes - tender_codes:
        it = settlement_map[code]
        result.new_items.append({
            "code": it.code, "name": it.name, "unit": it.unit,
            "quantity": it.quantity, "unit_price": it.unit_price,
            "total_price": it.total_price
        })

    # 2. 删减项：招标有、结算无
    for code in tender_codes - settlement_codes:
        it = tender_map[code]
        result.removed_items.append({
            "code": it.code, "name": it.name, "unit": it.unit,
            "quantity": it.quantity
        })

    # 3. 共同项：检查数量变更
    for code in tender_codes & settlement_codes:
        t_item = tender_map[code]
        s_item = settlement_map[code]

        if t_item.quantity == 0:
            change_rate = float('inf') if s_item.quantity != 0 else 0.0
        else:
            change_rate = (s_item.quantity - t_item.quantity) / t_item.quantity

        if abs(change_rate) > QUANTITY_CHANGE_THRESHOLD:
            result.changed_items.append({
                "code": t_item.code,
                "name": t_item.name,
                "unit": t_item.unit,
                "original_qty": t_item.quantity,
                "settlement_qty": s_item.quantity,
                "qty_diff": round(s_item.quantity - t_item.quantity, 4),
                "change_rate": round(change_rate, 4),
                "direction": "增加" if change_rate > 0 else "减少"
            })
        else:
            result.unchanged_items.append({
                "code": t_item.code, "name": t_item.name,
                "quantity": t_item.quantity
            })

    # 汇总
    result.summary = {
        "招标清单项数": len(tender_items),
        "结算清单项数": len(settlement_items),
        "新增项数": len(result.new_items),
        "删减项数": len(result.removed_items),
        "数量变更项数": len(result.changed_items),
        "无变化项数": len(result.unchanged_items),
        "净增项数": len(result.new_items) - len(result.removed_items),
    }

    return result


# ============================================================
# CLI入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="工程量清单核对")
    parser.add_argument("--input", required=True, help="输入JSON文件路径")
    parser.add_argument("--output", required=True, help="输出JSON文件路径")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    project_name = data.get("project_name", "")

    tender_items = [BOQItem(
        code=it["code"], name=it["name"], unit=it.get("unit", ""),
        quantity=float(it["quantity"]),
        unit_price=float(it.get("unit_price", 0)),
        total_price=float(it.get("total_price", 0))
    ) for it in data.get("tender_items", [])]

    settlement_items = [BOQItem(
        code=it["code"], name=it["name"], unit=it.get("unit", ""),
        quantity=float(it["quantity"]),
        unit_price=float(it.get("unit_price", 0)),
        total_price=float(it.get("total_price", 0))
    ) for it in data.get("settlement_items", [])]

    result = verify_quantities(tender_items, settlement_items, project_name)

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
    print(f"项目: {project_name}")
    for k, v in result.summary.items():
        print(f"  {k}: {v}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
