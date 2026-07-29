"""
工具6：benford_analysis — Benford定律首位数字异常检测

场景：采购审计、财务审计中，全量发票/合同金额的首位数字分布检验，
     识别人为操控金额（分拆发票、虚报金额等）

技术：卡方拟合优度检验 + 分组子分布对比
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter


# ── Benford理论分布 ──────────────────────────────────────────

BENFORD_THEORETICAL = {
    1: 0.3010, 2: 0.1761, 3: 0.1249, 4: 0.0969,
    5: 0.0792, 6: 0.0669, 7: 0.0580, 8: 0.0512, 9: 0.0458,
}


def _first_digit(n: float) -> int:
    """提取数字的首位非零数字"""
    if n == 0:
        return 0
    abs_n = abs(n)
    while abs_n >= 10:
        abs_n /= 10
    while abs_n < 1:
        abs_n *= 10
    return int(abs_n)


def _chi_square_p_value(chi2: float, df: int) -> float:
    """
    卡方检验近似p值（使用Wilson-Hilferty变换）
    输入：卡方统计量、自由度
    输出：近似p值
    """
    if chi2 <= 0:
        return 1.0
    if df <= 0:
        return 0.0

    # Wilson-Hilferty: (chi2/df)^(1/3) ~ N(1 - 2/(9*df), sqrt(2/(9*df)))
    z = (pow(chi2 / df, 1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
    # 标准正态CDF近似
    p = 0.5 * (1.0 + math.erf(-z / math.sqrt(2.0)))
    return p


# ── 数据结构 ──────────────────────────────────────────────────

@dataclass
class DigitDistribution:
    """单组首位数字分布"""
    digit: int
    actual_count: int
    actual_pct: float
    theoretical_pct: float
    deviation: float  # 实际 - 理论（百分点）
    deviation_ratio: float  # (实际-理论)/理论


@dataclass
class BenfordResult:
    """Benford分析完整结果"""
    total_records: int
    distribution: List[DigitDistribution]
    chi_square: float
    p_value: float
    is_significant: bool  # p < 0.05
    top_deviations: List[DigitDistribution]  # 偏差最大的3个数字
    interpretation: str


@dataclass
class GroupBenfordResult:
    """分组Benford对比结果"""
    group_name: str
    result: BenfordResult
    rank: int  # 偏差排名（1=偏差最大）


class BenfordAnalyzer:
    """Benford定律分析器"""

    def analyze(
        self,
        amounts: List[float],
        label: str = "全量",
    ) -> BenfordResult:
        """
        对金额列表执行Benford分析

        Args:
            amounts: 金额列表（正值）
            label: 数据标签
        """
        # 过滤非正值
        positive = [a for a in amounts if a > 0]
        total = len(positive)

        if total < 30:
            return BenfordResult(
                total_records=total,
                distribution=[],
                chi_square=0.0,
                p_value=1.0,
                is_significant=False,
                top_deviations=[],
                interpretation=f"数据量不足（{total}条），Benford分析需要至少30条数据才有统计意义",
            )

        # 首位数字统计
        digit_counter = Counter()
        for a in positive:
            fd = _first_digit(a)
            if 1 <= fd <= 9:
                digit_counter[fd] += 1

        # 构建分布
        distribution = []
        chi_square = 0.0
        for d in range(1, 10):
            actual = digit_counter.get(d, 0)
            actual_pct = actual / total
            theo_pct = BENFORD_THEORETICAL[d]
            deviation = actual_pct - theo_pct
            deviation_ratio = deviation / theo_pct if theo_pct > 0 else 0

            # 卡方贡献
            expected = total * theo_pct
            if expected > 0:
                chi_square += (actual - expected) ** 2 / expected

            distribution.append(DigitDistribution(
                digit=d,
                actual_count=actual,
                actual_pct=round(actual_pct, 4),
                theoretical_pct=round(theo_pct, 4),
                deviation=round(deviation, 4),
                deviation_ratio=round(deviation_ratio, 3),
            ))

        # 卡方检验
        p_value = _chi_square_p_value(chi_square, df=8)
        is_significant = p_value < 0.05

        # Top偏差
        sorted_dev = sorted(
            distribution,
            key=lambda x: abs(x.deviation),
            reverse=True,
        )
        top_dev = sorted_dev[:3]

        # 解读
        interpretation = self._interpret(is_significant, top_dev, label)

        return BenfordResult(
            total_records=total,
            distribution=distribution,
            chi_square=round(chi_square, 4),
            p_value=round(p_value, 4),
            is_significant=is_significant,
            top_deviations=top_dev,
            interpretation=interpretation,
        )

    def analyze_grouped(
        self,
        groups: Dict[str, List[float]],
    ) -> List[GroupBenfordResult]:
        """
        分组Benford分析（如按品类/单位分别分析）

        Args:
            groups: {分组名: 金额列表}
        """
        results = []
        for name, amounts in groups.items():
            result = self.analyze(amounts, label=name)
            results.append(GroupBenfordResult(
                group_name=name,
                result=result,
                rank=0,  # 稍后排序
            ))

        # 按卡方值降序排列（偏差最大的在前）
        results.sort(key=lambda r: r.result.chi_square, reverse=True)
        for i, r in enumerate(results):
            r.rank = i + 1

        return results

    def _interpret(
        self,
        is_significant: bool,
        top_dev: List[DigitDistribution],
        label: str,
    ) -> str:
        """生成分析解读"""
        parts = []

        if not is_significant:
            parts.append(
                f"✅ {label}的金额首位数字分布与Benford理论分布无显著差异"
                f"（p={self._last_p_value:.3f}），数据呈现自然分布特征，"
                f"未发现人为操控迹象。"
            )
            return " ".join(parts)

        parts.append(
            f"⚠️ {label}的金额首位数字分布与Benford理论分布存在显著差异，"
            f"提示可能存在人为操控。"
        )

        for dd in top_dev:
            direction = "偏高" if dd.deviation > 0 else "偏低"
            parts.append(
                f"首位数字{dd.digit}出现比例{direction}"
                f"（实际{dd.actual_pct*100:.1f}% vs 理论{dd.theoretical_pct*100:.1f}%，"
                f"偏差{abs(dd.deviation_ratio)*100:.0f}%）."
            )

        # 常见解释
        high_8_9 = any(
            dd.digit in (8, 9) and dd.deviation > 0
            for dd in top_dev
        )
        if high_8_9:
            parts.append(
                "首位8和9偏高是'分拆发票'的典型信号——将大额发票拆成多张小额发票，"
                "每张卡在审批额度上限以下。"
            )

        high_1 = any(dd.digit == 1 and dd.deviation > 0 for dd in top_dev)
        if high_1:
            parts.append(
                "首位1偏高可能表明存在大量小金额的重复性支出，"
                "建议核查是否存在拆分报销。"
            )

        return " ".join(parts)

    _last_p_value = 0.0

    def analyze(self, amounts, label="全量"):
        """包装以保存p值供_interpret使用"""
        result = self._analyze_impl(amounts, label)
        self._last_p_value = result.p_value
        return result

    def _analyze_impl(self, amounts, label):
        """内部实现（原analyze逻辑）"""
        positive = [a for a in amounts if a > 0]
        total = len(positive)

        if total < 30:
            return BenfordResult(
                total_records=total,
                distribution=[],
                chi_square=0.0,
                p_value=1.0,
                is_significant=False,
                top_deviations=[],
                interpretation=f"数据量不足（{total}条），Benford分析需要至少30条数据才有统计意义",
            )

        digit_counter = Counter()
        for a in positive:
            fd = _first_digit(a)
            if 1 <= fd <= 9:
                digit_counter[fd] += 1

        distribution = []
        chi_square = 0.0
        for d in range(1, 10):
            actual = digit_counter.get(d, 0)
            actual_pct = actual / total
            theo_pct = BENFORD_THEORETICAL[d]
            deviation = actual_pct - theo_pct
            deviation_ratio = deviation / theo_pct if theo_pct > 0 else 0
            expected = total * theo_pct
            if expected > 0:
                chi_square += (actual - expected) ** 2 / expected

            distribution.append(DigitDistribution(
                digit=d,
                actual_count=actual,
                actual_pct=round(actual_pct, 4),
                theoretical_pct=round(theo_pct, 4),
                deviation=round(deviation, 4),
                deviation_ratio=round(deviation_ratio, 3),
            ))

        p_value = _chi_square_p_value(chi_square, df=8)
        is_significant = p_value < 0.05
        sorted_dev = sorted(distribution, key=lambda x: abs(x.deviation), reverse=True)
        top_dev = sorted_dev[:3]
        self._last_p_value = p_value
        interpretation = self._interpret(is_significant, top_dev, label)

        return BenfordResult(
            total_records=total,
            distribution=distribution,
            chi_square=round(chi_square, 4),
            p_value=round(p_value, 4),
            is_significant=is_significant,
            top_deviations=top_dev,
            interpretation=interpretation,
        )


# ── MCP工具接口 ──────────────────────────────────────────────

def benford_analysis(
    amounts: List[float],
    csv_file: Optional[str] = None,
    amount_column: Optional[str] = None,
    group_column: Optional[str] = None,
) -> dict:
    """
    Benford定律首位数字异常检测

    Args:
        amounts: 金额数组（浮点数）
        csv_file: CSV文件路径（与amounts二选一）
        amount_column: CSV中金额列名（csv_file时必填）
        group_column: CSV中分组列名（如"品类""单位"，可选）

    Returns:
        分析结果dict，含分布表/卡方检验/分组对比/解读
    """
    import csv

    analyzer = BenfordAnalyzer()

    # CSV加载
    if csv_file and not amounts:
        loaded = []
        groups_data: Dict[str, List[float]] = {}
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    val = float(row.get(amount_column or "", "0").replace(",", ""))
                    loaded.append(val)
                    if group_column:
                        g = row.get(group_column, "未分类")
                        if g not in groups_data:
                            groups_data[g] = []
                        groups_data[g].append(val)
                except (ValueError, KeyError):
                    continue
        amounts = loaded

    # 全量分析
    overall = analyzer.analyze(amounts or [], label="全量数据")

    result = {
        "total_records": overall.total_records,
        "distribution": [
            {
                "digit": d.digit,
                "actual_count": d.actual_count,
                "actual_pct": f"{d.actual_pct*100:.1f}%",
                "theoretical_pct": f"{d.theoretical_pct*100:.1f}%",
                "deviation": f"{d.deviation*100:+.1f}%",
                "deviation_ratio": f"{d.deviation_ratio*100:+.0f}%",
            }
            for d in overall.distribution
        ],
        "chi_square": overall.chi_square,
        "p_value": overall.p_value,
        "is_significant": overall.is_significant,
        "significance_label": (
            "⚠️ 存在显著差异（p<0.05），提示人为操控" if overall.is_significant
            else "✅ 无显著差异，数据呈现自然分布特征"
        ),
        "top_deviations": [
            {
                "digit": d.digit,
                "direction": "偏高" if d.deviation > 0 else "偏低",
                "detail": (
                    f"首位{d.digit}实际{d.actual_pct*100:.1f}%"
                    f"（理论{d.theoretical_pct*100:.1f}%）"
                ),
                "signal": (
                    "分拆发票典型信号" if d.digit in (8, 9) and d.deviation > 0
                    else "重复小额支出" if d.digit == 1 and d.deviation > 0
                    else "需人工复核"
                ),
            }
            for d in overall.top_deviations
        ],
        "interpretation": overall.interpretation,
        "recommendation": (
            "建议对首位数字8和9偏高的品类进行逐票核查，重点确认是否存在分拆发票行为。"
            if overall.is_significant and any(
                d.digit in (8, 9) and d.deviation > 0 for d in overall.top_deviations
            )
            else "建议关注偏差最大的数字类别，结合业务背景判断是否需要进一步核查。"
            if overall.is_significant
            else "Benford分析未发现异常，可结合其他分析工具（供应商指纹/时间序列）综合判断。"
        ),
    }

    # 分组分析（如有）
    if group_column and "groups_data" in dir():
        grouped = analyzer.analyze_grouped(groups_data)
        result["grouped_analysis"] = [
            {
                "group": g.group_name,
                "rank": g.rank,
                "records": g.result.total_records,
                "chi_square": g.result.chi_square,
                "p_value": g.result.p_value,
                "is_significant": g.result.is_significant,
                "top_deviations": [
                    {"digit": d.digit, "deviation": f"{d.deviation*100:+.1f}%"}
                    for d in g.result.top_deviations
                ],
            }
            for g in grouped
        ]

    return result
