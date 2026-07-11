"""
材料调差计算
============
支持单价法和系数法两种模式，计算施工期材料价差，
支持风险幅度判断，生成逐月明细与汇总表。

用法:
    python -m tools.engineering.material_price_adjustment --input data.json --output result.json
"""

import json
import argparse
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# 可配置阈值
# ============================================================
RISK_RANGE_THRESHOLD = 0.05          # 风险幅度阈值（默认±5%，在此范围内不调差）
ADJUSTMENT_COEFFICIENT = 1.0         # 调差系数（默认1.0，即全额调整超出风险范围的部分）
# ============================================================


@dataclass
class MaterialPriceInfo:
    """材料价格信息（逐月）"""
    material_code: str              # 材料编码
    material_name: str              # 材料名称
    unit: str                       # 单位
    base_price: float               # 合同基准价（元/单位）
    monthly_info: dict[str, float]  # 施工期逐月信息价 {YYYY-MM: 价格}


@dataclass
class MaterialConsumption:
    """材料用量（逐月）"""
    material_code: str
    material_name: str
    unit: str
    monthly_qty: dict[str, float]   # 逐月用量 {YYYY-MM: 数量}


@dataclass
class MonthlyAdjustment:
    """单月调差明细"""
    month: str                      # YYYY-MM
    material_code: str
    material_name: str
    unit: str
    base_price: float               # 基准价
    info_price: float               # 当月信息价
    price_diff: float               # 价差（信息价 - 基准价）
    price_diff_rate: float          # 价差率
    consumption: float              # 当月用量
    raw_adjustment: float           # 原始调差金额（价差×用量）
    in_risk_range: bool             # 是否在风险范围内（不调）
    final_adjustment: float         # 最终调差金额


@dataclass
class MaterialResult:
    """材料调差完整结果"""
    project_name: str
    method: str                     # unit_price / coefficient
    monthly_details: list[MonthlyAdjustment] = field(default_factory=list)
    material_summary: list[dict] = field(default_factory=list)
    total_adjustment: float = 0.0

    def to_json(self) -> str:
        return json.dumps({
            "project_name": self.project_name,
            "method": self.method,
            "total_adjustment": round(self.total_adjustment, 2),
            "material_summary": self.material_summary,
            "monthly_details": [
                {
                    "month": d.month,
                    "material_code": d.material_code,
                    "material_name": d.material_name,
                    "base_price": d.base_price,
                    "info_price": d.info_price,
                    "price_diff": round(d.price_diff, 2),
                    "price_diff_rate": round(d.price_diff_rate, 4),
                    "consumption": d.consumption,
                    "raw_adjustment": round(d.raw_adjustment, 2),
                    "in_risk_range": d.in_risk_range,
                    "final_adjustment": round(d.final_adjustment, 2),
                }
                for d in self.monthly_details
            ]
        }, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        sign_word = "调增" if self.total_adjustment >= 0 else "调减"
        lines = [
            f"# 材料调差报告 — {self.project_name}",
            "",
            f"**调差模式**: {self.method}",
            f"**风险幅度**: ±{RISK_RANGE_THRESHOLD:.0%}（范围内不调）",
            f"**总调差金额**: {abs(self.total_adjustment):,.2f} 元（{sign_word}）",
            "",
            "## 材料汇总",
            "| 材料 | 基准价 | 总用量 | 总调差（元） |",
            "|------|--------|--------|-------------|",
        ]
        for mat in self.material_summary:
            lines.append(
                f"| {mat['name']} | {mat['base_price']:,.2f} | {mat['total_qty']:,.2f} "
                f"| {mat['adjustment']:+,.2f} |"
            )

        lines += ["", "## 逐月明细",
                   "| 月份 | 材料 | 基准价 | 信息价 | 价差率 | 用量 | 调差金额 |",
                   "|------|------|--------|--------|--------|------|----------|"]
        for d in self.monthly_details[:50]:  # 限制输出行数
            in_range = " (不调)" if d.in_risk_range else ""
            lines.append(
                f"| {d.month} | {d.material_name} | {d.base_price:,.2f} | {d.info_price:,.2f} "
                f"| {d.price_diff_rate:+.2%} | {d.consumption:,.2f} "
                f"| {d.final_adjustment:+,.2f}{in_range} |"
            )

        if len(self.monthly_details) > 50:
            lines.append(f"| ... | （共 {len(self.monthly_details)} 条，仅显示前50条） |")

        lines.append("")
        lines.append("---")
        lines.append("*本报告由融策工程咨询Agent自动生成，仅供专业人员参考。*")
        return "\n".join(lines)


def adjust_material_prices_unit_price(
    price_infos: list[MaterialPriceInfo],
    consumptions: list[MaterialConsumption],
    project_name: str = ""
) -> MaterialResult:
    """
    单价法调差：逐月逐材料计算价差

    公式: 调差金额 = Σ (当月信息价 - 基准价) × 当月用量
          价差在 ±RISK_RANGE_THRESHOLD% 以内时不调整

    Args:
        price_infos: 材料价格信息（含基准价和逐月信息价）
        consumptions: 材料逐月用量
        project_name: 项目名称

    Returns:
        MaterialResult: 调差结果
    """
    # 构建用量索引 {material_code: {month: qty}}
    cons_map: dict[str, dict[str, float]] = {}
    for c in consumptions:
        cons_map[c.material_code] = c.monthly_qty

    monthly_details: list[MonthlyAdjustment] = []
    material_totals: dict[str, dict] = {}

    for pi in price_infos:
        code = pi.material_code
        mat_adj_total = 0.0
        mat_qty_total = 0.0

        for month, info_price in sorted(pi.monthly_info.items()):
            # 获取该月用量
            qty = cons_map.get(code, {}).get(month, 0.0)
            if qty == 0:
                continue

            price_diff = info_price - pi.base_price
            price_diff_rate = price_diff / pi.base_price if pi.base_price != 0 else 0.0
            raw_adj = price_diff * qty
            mat_qty_total += qty

            # 风险范围判断
            in_risk = abs(price_diff_rate) <= RISK_RANGE_THRESHOLD
            final_adj = 0.0 if in_risk else raw_adj * ADJUSTMENT_COEFFICIENT
            mat_adj_total += final_adj

            monthly_details.append(MonthlyAdjustment(
                month=month,
                material_code=code,
                material_name=pi.material_name,
                unit=pi.unit,
                base_price=pi.base_price,
                info_price=info_price,
                price_diff=round(price_diff, 2),
                price_diff_rate=round(price_diff_rate, 4),
                consumption=qty,
                raw_adjustment=round(raw_adj, 2),
                in_risk_range=in_risk,
                final_adjustment=round(final_adj, 2)
            ))

        material_totals[code] = {
            "code": code,
            "name": pi.material_name,
            "base_price": pi.base_price,
            "total_qty": round(mat_qty_total, 4),
            "adjustment": round(mat_adj_total, 2)
        }

    total_adj = sum(m["adjustment"] for m in material_totals.values())

    return MaterialResult(
        project_name=project_name,
        method="单价法",
        monthly_details=monthly_details,
        material_summary=list(material_totals.values()),
        total_adjustment=round(total_adj, 2)
    )


def adjust_material_prices_coefficient(
    base_total: float,
    adjustment_coeff: float,
    project_name: str = ""
) -> MaterialResult:
    """
    系数法调差：按造价信息调整系数计算

    公式: 调差金额 = 基准总价 × (调整系数 - 1.0)

    Args:
        base_total: 基准期材料总价
        adjustment_coeff: 造价信息调整系数
        project_name: 项目名称

    Returns:
        MaterialResult: 调差结果
    """
    adjustment = base_total * (adjustment_coeff - 1.0)
    return MaterialResult(
        project_name=project_name,
        method="系数法",
        material_summary=[{
            "code": "TOTAL",
            "name": "全部材料",
            "base_price": base_total,
            "total_qty": 1.0,
            "adjustment": round(adjustment, 2)
        }],
        total_adjustment=round(adjustment, 2)
    )


def adjust_material_prices(
    price_infos: Optional[list[MaterialPriceInfo]] = None,
    consumptions: Optional[list[MaterialConsumption]] = None,
    base_total: Optional[float] = None,
    adjustment_coeff: Optional[float] = None,
    project_name: str = ""
) -> MaterialResult:
    """
    材料调差主函数，根据输入自动选择单价法或系数法

    Args:
        price_infos: 材料价格信息（单价法）
        consumptions: 材料逐月用量（单价法）
        base_total: 基准总价（系数法）
        adjustment_coeff: 调整系数（系数法）
        project_name: 项目名称
    """
    if price_infos and consumptions:
        return adjust_material_prices_unit_price(price_infos, consumptions, project_name)
    elif base_total is not None and adjustment_coeff is not None:
        return adjust_material_prices_coefficient(base_total, adjustment_coeff, project_name)
    else:
        raise ValueError("请提供单价法参数(price_infos+consumptions)或系数法参数(base_total+adjustment_coeff)")


# ============================================================
# CLI入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="材料调差计算")
    parser.add_argument("--input", required=True, help="输入JSON文件路径")
    parser.add_argument("--output", required=True, help="输出JSON文件路径")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    project_name = data.get("project_name", "")
    method = data.get("method", "unit_price")

    if method == "coefficient":
        base_total = float(data.get("base_total", 0))
        coeff = float(data.get("adjustment_coefficient", 1.0))
        result = adjust_material_prices(
            base_total=base_total, adjustment_coeff=coeff,
            project_name=project_name
        )
    else:
        # 默认单价法
        price_infos = [MaterialPriceInfo(
            material_code=pi["material_code"],
            material_name=pi["material_name"],
            unit=pi.get("unit", ""),
            base_price=float(pi["base_price"]),
            monthly_info=pi.get("monthly_info", {})
        ) for pi in data.get("price_infos", [])]

        consumptions = [MaterialConsumption(
            material_code=c["material_code"],
            material_name=c.get("material_name", ""),
            unit=c.get("unit", ""),
            monthly_qty=c.get("monthly_qty", {})
        ) for c in data.get("consumptions", [])]

        result = adjust_material_prices(price_infos, consumptions, project_name=project_name)

    if args.format in ("json", "both"):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.to_json())
        print(f"[✓] JSON结果已保存: {args.output}")

    if args.format in ("md", "both"):
        out_md = args.output.replace(".json", ".md")
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(result.to_markdown())
        print(f"[✓] Markdown报告已保存: {out_md}")

    sign = "调增" if result.total_adjustment >= 0 else "调减"
    print(f"\n{'='*50}")
    print(f"项目: {project_name} | 模式: {result.method}")
    print(f"总调差金额: {abs(result.total_adjustment):,.2f} 元（{sign}）")
    print(f"涉及材料: {len(result.material_summary)} 种")
    print(f"逐月明细: {len(result.monthly_details)} 条")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
