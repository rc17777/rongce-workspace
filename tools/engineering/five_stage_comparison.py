"""
五算对比引擎
============
输入估算、概算、预算、结算、决算五个阶段的造价数据，
逐项对比各阶段偏差，检出超概/超预项，生成对比汇总表。

用法:
    python -m tools.engineering.five_stage_comparison --input data.json --output result.json
"""

import json
import argparse
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# 可配置阈值（修改此处调整对比灵敏度）
# ============================================================
ITEM_OVERRUN_THRESHOLD = 0.10      # 单分部分项偏差率阈值（默认10%）
TOTAL_OVERRUN_THRESHOLD = 0.05     # 总造价偏差率阈值（默认5%）
# ============================================================


@dataclass
class CostItem:
    """单个分部分项的造价数据"""
    code: str                       # 项目编码
    name: str                       # 项目名称
    unit: str = ""                  # 单位
    estimate: float = 0.0           # 估算
    budget_estimate: float = 0.0    # 概算
    budget: float = 0.0             # 预算
    settlement: float = 0.0         # 结算
    final_account: float = 0.0      # 决算


@dataclass
class StageComparison:
    """两个阶段之间的对比结果"""
    from_stage: str
    to_stage: str
    from_amount: float
    to_amount: float
    deviation: float                # 偏差金额
    deviation_rate: float           # 偏差率（小数）

    @property
    def is_overrun(self) -> bool:
        """是否超概/超预"""
        return self.deviation_rate > ITEM_OVERRUN_THRESHOLD

    @property
    def overrun_category(self) -> str:
        """偏差原因分类"""
        if self.deviation_rate <= 0:
            return "节约"
        elif self.deviation_rate <= 0.05:
            return "正常波动"
        elif self.deviation_rate <= 0.10:
            return "轻微超支"
        elif self.deviation_rate <= 0.20:
            return "明显超支"
        else:
            return "严重超支"


@dataclass
class FiveStageResult:
    """五算对比完整结果"""
    project_name: str
    items: list[dict] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    overrun_items: list[dict] = field(default_factory=list)
    total_deviation_rate: float = 0.0

    def to_json(self) -> str:
        return json.dumps({
            "project_name": self.project_name,
            "items": self.items,
            "summary": self.summary,
            "overrun_items": self.overrun_items,
            "total_deviation_rate": round(self.total_deviation_rate, 4)
        }, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """生成人类可读的Markdown对比表"""
        lines = [
            f"# 五算对比报告 — {self.project_name}",
            "",
            "## 汇总",
            f"| 指标 | 金额（万元） |",
            f"|------|------------|",
        ]
        for k, v in self.summary.items():
            lines.append(f"| {k} | {v:,.2f} |")

        lines += [
            "",
            f"**总偏差率**: {self.total_deviation_rate:.2%}",
            f"**超项数**: {len(self.overrun_items)}",
            "",
            "## 超概/超预明细",
            "| 编码 | 名称 | 阶段 | 偏差率 | 分类 |",
            "|------|------|------|--------|------|",
        ]
        for item in self.overrun_items:
            lines.append(
                f"| {item['code']} | {item['name']} | {item['stage']} "
                f"| {item['rate']:.2%} | {item['category']} |"
            )

        lines += [
            "",
            "## 分部分项明细",
            "| 编码 | 名称 | 估算 | 概算 | 预算 | 结算 | 决算 | 最大偏差率 |",
            "|------|------|------|------|------|------|------|------------|",
        ]
        for item in self.items:
            lines.append(
                f"| {item['code']} | {item['name']} "
                f"| {item['estimate']:,.2f} | {item['budget_estimate']:,.2f} "
                f"| {item['budget']:,.2f} | {item['settlement']:,.2f} "
                f"| {item['final_account']:,.2f} | {item['max_deviation_rate']:.2%} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("*本报告由融策工程咨询Agent自动生成，仅供专业人员参考。*")
        return "\n".join(lines)


def _safe_rate(numerator: float, denominator: float) -> float:
    """安全计算偏差率，分母为零时返回0"""
    if denominator == 0:
        return 0.0 if numerator == 0 else float('inf')
    return numerator / denominator


def _compare_stages(from_amount: float, to_amount: float,
                    from_name: str, to_name: str) -> StageComparison:
    """计算两个阶段之间的偏差"""
    deviation = to_amount - from_amount
    rate = _safe_rate(deviation, from_amount)
    return StageComparison(
        from_stage=from_name,
        to_stage=to_name,
        from_amount=from_amount,
        to_amount=to_amount,
        deviation=deviation,
        deviation_rate=rate
    )


def five_stage_compare(items: list[CostItem], project_name: str = "") -> FiveStageResult:
    """
    执行五算对比分析

    Args:
        items: 分部分项造价数据列表
        project_name: 项目名称

    Returns:
        FiveStageResult: 包含对比结果、超项清单、汇总表
    """
    # 汇总各阶段总造价
    total_estimate = sum(i.estimate for i in items)
    total_budget_estimate = sum(i.budget_estimate for i in items)
    total_budget = sum(i.budget for i in items)
    total_settlement = sum(i.settlement for i in items)
    total_final = sum(i.final_account for i in items)

    summary = {
        "估算总额": total_estimate,
        "概算总额": total_budget_estimate,
        "预算总额": total_budget,
        "结算总额": total_settlement,
        "决算总额": total_final,
    }

    # 逐项对比
    result_items = []
    overrun_items = []

    for item in items:
        # 四段对比
        comparisons = [
            _compare_stages(item.estimate, item.budget_estimate, "估算→概算", "估算→概算"),
            _compare_stages(item.budget_estimate, item.budget, "概算→预算", "概算→预算"),
            _compare_stages(item.budget, item.settlement, "预算→结算", "预算→结算"),
            _compare_stages(item.settlement, item.final_account, "结算→决算", "结算→决算"),
        ]

        # 找出最大偏差
        max_comp = max(comparisons, key=lambda c: abs(c.deviation_rate))

        item_result = {
            "code": item.code,
            "name": item.name,
            "estimate": item.estimate,
            "budget_estimate": item.budget_estimate,
            "budget": item.budget,
            "settlement": item.settlement,
            "final_account": item.final_account,
            "max_deviation_rate": round(max_comp.deviation_rate, 4),
            "max_deviation_stage": max_comp.to_stage,
            "stage_details": [
                {
                    "stage": c.to_stage,
                    "deviation": round(c.deviation, 2),
                    "rate": round(c.deviation_rate, 4),
                    "is_overrun": c.is_overrun,
                    "category": c.overrun_category
                }
                for c in comparisons
            ]
        }
        result_items.append(item_result)

        # 任一段超阈值即记录
        for c in comparisons:
            if c.is_overrun:
                overrun_items.append({
                    "code": item.code,
                    "name": item.name,
                    "stage": c.to_stage,
                    "deviation": round(c.deviation, 2),
                    "rate": round(c.deviation_rate, 4),
                    "category": c.overrun_category
                })

    # 总偏差率（决算vs概算）
    total_deviation = _safe_rate(
        total_final - total_budget_estimate,
        total_budget_estimate
    )

    return FiveStageResult(
        project_name=project_name,
        items=result_items,
        summary=summary,
        overrun_items=overrun_items,
        total_deviation_rate=total_deviation
    )


# ============================================================
# CLI入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="五算对比引擎")
    parser.add_argument("--input", required=True, help="输入JSON文件路径")
    parser.add_argument("--output", required=True, help="输出JSON文件路径")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both",
                        help="输出格式")
    args = parser.parse_args()

    # 读取输入
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    project_name = data.get("project_name", "")
    raw_items = data.get("items", [])

    # 解析为CostItem
    items = [CostItem(
        code=it.get("code", ""),
        name=it.get("name", ""),
        unit=it.get("unit", ""),
        estimate=float(it.get("estimate", 0)),
        budget_estimate=float(it.get("budget_estimate", 0)),
        budget=float(it.get("budget", 0)),
        settlement=float(it.get("settlement", 0)),
        final_account=float(it.get("final_account", 0)),
    ) for it in raw_items]

    # 执行对比
    result = five_stage_compare(items, project_name)

    # 输出
    if args.format in ("json", "both"):
        out_json = args.output
        with open(out_json, "w", encoding="utf-8") as f:
            f.write(result.to_json())
        print(f"[✓] JSON结果已保存: {out_json}")

    if args.format in ("md", "both"):
        out_md = args.output.replace(".json", ".md")
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(result.to_markdown())
        print(f"[✓] Markdown报告已保存: {out_md}")

    # 终端摘要
    print(f"\n{'='*50}")
    print(f"项目: {project_name}")
    print(f"概算总额: {result.summary['概算总额']:,.2f} 万元")
    print(f"决算总额: {result.summary['决算总额']:,.2f} 万元")
    print(f"总偏差率: {result.total_deviation_rate:.2%}")
    print(f"超项数: {len(result.overrun_items)}")
    if result.total_deviation_rate > TOTAL_OVERRUN_THRESHOLD:
        print(f"⚠️ 总造价超概 {result.total_deviation_rate:.2%}，超出警戒线 {TOTAL_OVERRUN_THRESHOLD:.0%}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
