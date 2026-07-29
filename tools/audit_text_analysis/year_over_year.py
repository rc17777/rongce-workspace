"""
P1: 年度对比检测 — 防照抄 (2d)

对连续年度的审计底稿进行纵向对比，检测：
1. 文字雷同（无差异化分析）
2. 数字一致性（关键数据未更新）
3. 结构照搬（段落结构完全一致）

输出年度对比报告，标记疑似照抄的底稿。
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class YearMatch:
    """年度对比匹配结果"""
    section: str               # 匹配的段落/区域
    similarity: float          # 相似度
    current_text: str          # 本年度文本片段
    previous_text: str         # 上年度文本片段
    issue_type: str            # identical | near_identical | structural_copy | stale_number
    risk_level: str            # high | medium | low


@dataclass
class YearOverYearReport:
    """年度对比检测报告"""
    workpaper_id: str
    current_year: str
    previous_year: str

    overall_similarity: float
    section_matches: List[YearMatch]
    staleness_score: float         # 陈旧度：越接近1表示越陈旧

    has_diff_analysis: bool        # 是否有本年度差异化分析
    has_updated_numbers: bool      # 是否有数据更新
    stale_numbers: List[str]       # 疑似未更新的数据

    risk_level: str                # high | medium | low

    conclusion: str
    recommendation: str


class YearOverYearDetector:
    """年度对比检测器"""

    def __init__(self):
        # 本年度差异化标注关键词
        self.diff_markers = [
            "本年度", "本期", "本报告期", "较上年", "同比",
            "上年同期", "上期", "与上年相比", "差异分析",
            "变化", "变动", "新增", "减少", "增加", "调整",
            "更新", "修改", "修订", "重分类", "重组",
        ]

        # 年度数字模式（支持跨年度检测）
        self.year_patterns = [
            (r"\b(\d{4})\s*年", "年份"),
            (r"(\d{4})[/-](\d{2})[/-](\d{2})", "日期"),
            (r"[¥￥]\s*([\d,，.]+)\s*(?:元|万元?)", "金额"),
            (r"(\d+(?:\.\d+)?)\s*%", "百分比"),
        ]

    def compare(
        self,
        current_content: str,
        previous_content: str,
        workpaper_id: str = "",
        current_year: str = "",
        previous_year: str = "",
    ) -> YearOverYearReport:
        """
        年度对比检测

        Args:
            current_content: 本年度底稿内容
            previous_content: 上年度底稿内容
            workpaper_id: 底稿编号
            current_year: 本年度（如 "2024"）
            previous_year: 上年度（如 "2023"）

        Returns:
            YearOverYearReport
        """
        if not current_year:
            current_year = str(datetime.now().year)
        if not previous_year:
            previous_year = str(int(current_year) - 1)

        # 1. 整体相似度
        overall_sim = self._trigram_similarity(current_content, previous_content)

        # 2. 逐段对比
        section_matches = self._compare_sections(
            current_content, previous_content, current_year, previous_year
        )

        # 3. 检测差异化分析标记
        has_diff = self._has_diff_analysis(current_content)

        # 4. 检测数据是否更新
        has_updated_numbers, stale_numbers = self._check_number_updates(
            current_content, previous_content, current_year, previous_year
        )

        # 5. 陈旧度得分
        staleness = self._calc_staleness(
            overall_sim, has_diff, has_updated_numbers, section_matches
        )

        # 6. 风险等级
        risk_level = self._assess_risk(
            overall_sim, has_diff, has_updated_numbers
        )

        return YearOverYearReport(
            workpaper_id=workpaper_id,
            current_year=current_year,
            previous_year=previous_year,
            overall_similarity=round(overall_sim, 4),
            section_matches=section_matches,
            staleness_score=round(staleness, 2),
            has_diff_analysis=has_diff,
            has_updated_numbers=has_updated_numbers,
            stale_numbers=stale_numbers,
            risk_level=risk_level,
            conclusion=self._build_conclusion(
                overall_sim, has_diff, has_updated_numbers, risk_level
            ),
            recommendation=self._build_recommendation(
                risk_level, has_diff, has_updated_numbers
            ),
        )

    def _trigram_similarity(self, text1: str, text2: str) -> float:
        """三字符组相似度"""
        if not text1 or not text2:
            return 0.0

        t1 = {text1[i:i+3] for i in range(len(text1) - 2)}
        t2 = {text2[i:i+3] for i in range(len(text2) - 2)}

        if not t1 or not t2:
            return 0.0

        return len(t1 & t2) / len(t1 | t2)

    def _split_sections(self, content: str) -> List[Tuple[str, str]]:
        """将底稿拆分为逻辑段"""
        sections = []
        # 按常见标题分割
        patterns = [
            r"(?:一|二|三|四|五|六|七|八|九|十)[、.．]\s*(.+?)(?=(?:一|二|三|四|五|六|七|八|九|十)[、.．]|\Z)",
            r"(?:\d+)[.、]\s*(.+?)(?=\d+[.、]|\Z)",
            r"【(.+?)】(.*?)(?=【|\Z)",
        ]

        for pat in patterns:
            matches = list(re.finditer(pat, content, re.DOTALL))
            if matches:
                for i, m in enumerate(matches):
                    sections.append((m.group(0)[:50], m.group(0)))
                break

        if not sections:
            sections = [("全文", content)]

        return sections

    def _compare_sections(
        self,
        current: str,
        previous: str,
        current_year: str,
        previous_year: str,
    ) -> List[YearMatch]:
        """逐段对比"""
        cur_sections = self._split_sections(current)
        prev_sections = self._split_sections(previous)
        matches = []

        for cur_title, cur_text in cur_sections:
            for prev_title, prev_text in prev_sections:
                # 标题相似度
                title_sim = self._trigram_similarity(cur_title, prev_title)
                if title_sim < 0.3:
                    continue

                text_sim = self._trigram_similarity(cur_text, prev_text)

                if text_sim >= 0.9:
                    # 检查是否为仅年份替换
                    year_replaced_cur = re.sub(
                        r"\b" + current_year + r"\b", "XXXX", cur_text
                    )
                    year_replaced_prev = re.sub(
                        r"\b" + previous_year + r"\b", "XXXX", previous_text
                    )
                    pure_sim = self._trigram_similarity(
                        year_replaced_cur, year_replaced_prev
                    )

                    if pure_sim >= 0.95:
                        issue = "identical"
                        risk = "high"
                    elif pure_sim >= 0.85:
                        issue = "near_identical"
                        risk = "high"
                    else:
                        issue = "structural_copy"
                        risk = "medium"
                elif text_sim >= 0.7:
                    issue = "structural_copy"
                    risk = "medium"
                else:
                    continue

                matches.append(YearMatch(
                    section=cur_title[:40],
                    similarity=round(text_sim, 4),
                    current_text=cur_text[:100],
                    previous_text=prev_text[:100],
                    issue_type=issue,
                    risk_level=risk,
                ))

        return sorted(matches, key=lambda m: m.similarity, reverse=True)

    def _has_diff_analysis(self, content: str) -> bool:
        """检测本年度差异化分析标记"""
        return any(marker in content for marker in self.diff_markers)

    def _check_number_updates(
        self,
        current: str,
        previous: str,
        current_year: str,
        previous_year: str,
    ) -> Tuple[bool, List[str]]:
        """检测关键数据是否更新"""
        stale = []

        # 提取所有金额
        cur_amounts = set(re.findall(r"[¥￥]\s*([\d,，.]+)", current))
        prev_amounts = set(re.findall(r"[¥￥]\s*([\d,，.]+)", previous))

        # 检查是否有金额完全一致（可能未更新）
        same_amounts = cur_amounts & prev_amounts
        if same_amounts:
            # 排除零值和极小值
            significant = [
                a for a in same_amounts
                if float(a.replace(",", "").replace("，", "")) > 1000
            ]
            if significant:
                stale.append(f"金额未变化: {', '.join(significant[:3])}")
                if len(significant) > 3:
                    stale[-1] += f" 等{len(significant)}项"

        # 检查年份引用
        if previous_year in current and current_year not in current:
            stale.append(f"底稿中仅出现上年年份「{previous_year}」，疑似未更新")

        has_updated = len(stale) == 0

        return has_updated, stale

    def _calc_staleness(
        self,
        overall_sim: float,
        has_diff: bool,
        has_updated: bool,
        section_matches: List[YearMatch],
    ) -> float:
        """计算陈旧度得分"""
        score = overall_sim * 0.4  # 整体相似度权重40%

        if not has_diff:
            score += 0.3  # 无差异化分析 +30%
        if not has_updated:
            score += 0.2  # 数据未更新 +20%

        # 高危段落 +10%
        high_risk_matches = [m for m in section_matches if m.risk_level == "high"]
        if high_risk_matches:
            score += min(0.1, 0.02 * len(high_risk_matches))

        return min(1.0, score)

    def _assess_risk(
        self,
        overall_sim: float,
        has_diff: bool,
        has_updated: bool,
    ) -> str:
        """评估风险等级"""
        if overall_sim > 0.9 and not has_diff:
            return "high"
        elif overall_sim > 0.7 and (not has_diff or not has_updated):
            return "medium"
        elif overall_sim > 0.5:
            return "low"
        return "low"

    def _build_conclusion(
        self,
        overall_sim: float,
        has_diff: bool,
        has_updated: bool,
        risk_level: str,
    ) -> str:
        """构建结论"""
        parts = [f"与上年度底稿整体相似度{overall_sim:.1%}"]

        if not has_diff:
            parts.append("未发现本年度差异化分析标注")
        if not has_updated:
            parts.append("疑似关键数据未更新")

        if risk_level == "high":
            parts.insert(0, "⚠️ 高度疑似照抄上年")
        elif risk_level == "medium":
            parts.insert(0, "⚠️ 存在照抄嫌疑")
        else:
            parts.insert(0, "✅ 明显更新")

        return "；".join(parts)

    def _build_recommendation(
        self,
        risk_level: str,
        has_diff: bool,
        has_updated: bool,
    ) -> str:
        """构建改进建议"""
        recs = []
        if not has_diff:
            recs.append("添加本年度与上年度的差异化分析说明")
        if not has_updated:
            recs.append("更新底稿中的关键数据（金额、日期、年份）")
        if risk_level == "high":
            recs.append("建议重新编制本年度底稿，而非在上年基础上修改")

        return "；".join(recs) if recs else "底稿已有效更新，无需额外措施"


# ── 便捷函数 ─────────────────────────────────────────────

def detect_copy_paste(
    current_content: str,
    previous_content: str,
    workpaper_id: str = "",
    current_year: str = "",
    previous_year: str = "",
) -> YearOverYearReport:
    """快速检测照抄嫌疑"""
    detector = YearOverYearDetector()
    return detector.compare(
        current_content=current_content,
        previous_content=previous_content,
        workpaper_id=workpaper_id,
        current_year=current_year,
        previous_year=previous_year,
    )


def batch_year_comparison(
    workpapers: List[Tuple[str, str, str, str]],
    # [(id, current_content, previous_content, title), ...]
) -> List[YearOverYearReport]:
    """批量年度对比"""
    detector = YearOverYearDetector()
    reports = []
    for wp_id, cur, prev, title in workpapers:
        report = detector.compare(
            current_content=cur,
            previous_content=prev,
            workpaper_id=wp_id,
        )
        reports.append(report)
    return reports
