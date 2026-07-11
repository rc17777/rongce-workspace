"""
workpaper_scorer.scorer — 核心评分引擎

实现四维核心评分 + 三大扣分项的完整评分逻辑。
纯规则引擎，不依赖 ML 模型，评分结果可解释、可复现。
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import List, Optional

from .models import (
    Workpaper,
    PreviousYearWorkpaper,
    ScoreReport,
    ScoreDimension,
    PenaltyItem,
    PenaltyCode,
    RiskFlag,
    Grade,
    ImprovementItem,
    YoYReport,
    AUDIT_ASSERTIONS,
    SAMPLING_METHODS,
    TEST_PROCEDURE_VERBS,
    DOCUMENT_TYPES,
    EVIDENCE_KEYWORDS,
    ASSERTION_KEYWORDS,
    EXCEPTION_KEYWORDS,
)


# ── 配置 ──────────────────────────────────────────────────────

class ScorerConfig:
    """评分阈值和权重配置"""

    # 维度满分
    MAX_DIMENSION_SCORE: float = 25.0
    TOTAL_MAX_SCORE: float = 100.0

    # 扣分上限
    MAX_PENALTY_NO_ANALYSIS: float = 10.0   # E 有数无说
    MAX_PENALTY_NO_EVIDENCE: float = 15.0    # F 有论无据
    MAX_PENALTY_COPYCAT: float = 5.0         # G 照抄嫌疑

    # L1 通过阈值
    L1_PASS_THRESHOLD: float = 70.0

    # L3 否决风险阈值（归一化）
    L3_VETO_RISK_THRESHOLD: float = 72.0  # 对应 v2 的 0.85 归一化

    # 有数无说检测
    NUMBERS_ONLY_RATIO_THRESHOLD: float = 0.7  # 数字内容占比超过此值触发
    MIN_ANALYSIS_CHARS: int = 200  # 最少分析文字数

    # 有论无据检测
    CONCLUSION_EVIDENCE_WINDOW: int = 500  # 结论后搜索证据的字符窗口

    # 照抄检测
    COPYCAT_SIMILARITY_HIGH: float = 0.90
    COPYCAT_SIMILARITY_MEDIUM: float = 0.70

    @classmethod
    def ls_ratio_to_l3_score(cls, l3_normalized: float) -> float:
        """L3 归一化分(0-1) → L1 百分制近似"""
        return l3_normalized * cls.TOTAL_MAX_SCORE


# ── 文本分析工具 ──────────────────────────────────────────────

class TextAnalyzer:
    """底稿文本分析辅助函数集"""

    @staticmethod
    def count_keyword_matches(text: str, keywords: List[str]) -> int:
        """统计关键词在文本中出现的种类数（去重）"""
        text_lower = text.lower()
        count = 0
        for kw in keywords:
            if kw.lower() in text_lower:
                count += 1
        return count

    @staticmethod
    def count_any_keyword_matches(text: str, keywords: List[str]) -> int:
        """统计关键词在文本中出现的总次数（不去重）"""
        text_lower = text.lower()
        total = 0
        for kw in keywords:
            total += text_lower.count(kw.lower())
        return total

    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """提取文本中的数字（含中文数字单位）"""
        return re.findall(
            r'\d+(?:\.\d+)?(?:%|万|亿|元|万元|亿元)?',
            text,
        )

    @staticmethod
    def estimate_number_content_ratio(text: str) -> float:
        """
        估算数字内容占比。
        计算数字字符占非空格字符的比例。
        """
        if not text:
            return 0.0
        cleaned = re.sub(r'\s+', '', text)  # 去空白
        if not cleaned:
            return 0.0
        number_chars = len(re.findall(r'[\d.%万亿元]', cleaned))
        return min(1.0, number_chars / len(cleaned))

    @staticmethod
    def count_analysis_chars(text: str) -> int:
        """
        估算分析性文字的字数。
        排除纯数字行、表格行、标题行。
        """
        lines = text.split('\n')
        analysis_lines = []
        for line in lines:
            stripped = line.strip()
            # 跳过纯数字/符号行
            if re.match(r'^[\d.,%+\-*/=│|┃\s]+$', stripped):
                continue
            # 跳过纯表格框线
            if re.match(r'^[─━│┃┏┓┗┛┣┫┳┻╋═\s]+$', stripped):
                continue
            analysis_lines.append(stripped)
        return sum(len(line) for line in analysis_lines)

    @staticmethod
    def split_conclusions(text: str) -> List[str]:
        """
        从文本中提取结论句列表。
        匹配 "结论：" / "结论:" / "综上" / "测试结果：" 等模式。
        """
        patterns = [
            r'结论[：:]\s*(.+?)(?=\n\n|\n(?:[^续]|$)|$)',
            r'测试结果[：:]\s*(.+?)(?=\n\n|\n(?:[^续]|$)|$)',
            r'综上[，,]\s*(.+?)(?=\n\n|\Z)',
            r'(?:^|\n)([^。\n]*无异常[^。\n]*)[。\n]',
            r'(?:^|\n)([^。\n]*结论[：:]?[^。\n]*)[。\n]',
        ]
        conclusions = []
        remaining = text
        for pattern in patterns:
            matches = re.findall(pattern, remaining, re.MULTILINE | re.DOTALL)
            for m in matches:
                m = m.strip()
                if m and len(m) > 2:
                    conclusions.append(m)
        return conclusions

    @staticmethod
    def has_evidence_nearby(text: str, conclusion_text: str, position: int, window: int = 500) -> bool:
        """
        检查结论文本内部及随后 window 个字符内是否包含证据关键词。
        证据可能在结论句中（如"结论：…依据：…"），也可能在结论之后的段落。
        """
        # 先检查结论文本自身
        if TextAnalyzer.count_keyword_matches(conclusion_text, EVIDENCE_KEYWORDS) > 0:
            return True
        # 再检查结论后的上下文
        snippet = text[position + len(conclusion_text): position + len(conclusion_text) + window]
        return TextAnalyzer.count_keyword_matches(snippet, EVIDENCE_KEYWORDS) > 0

    @staticmethod
    def text_similarity(text_a: str, text_b: str) -> float:
        """
        计算两个文本的相似度（Jaccard 基于字符 bigram）。
        这是一个轻量级、无外部依赖的实现，用于照抄检测。
        生产环境可替换为 embedding cosine similarity。
        """
        def bigrams(s: str) -> set:
            s = re.sub(r'\s+', '', s)
            return {s[i:i+2] for i in range(len(s) - 1)}

        ba = bigrams(text_a)
        bb = bigrams(text_b)
        if not ba or not bb:
            return 0.0
        intersection = len(ba & bb)
        union = len(ba | bb)
        return intersection / union if union > 0 else 0.0


# ── 核心评分引擎 ──────────────────────────────────────────────

class WorkpaperScorer:
    """
    底稿质量自动评分引擎。

    使用方法：
        scorer = WorkpaperScorer()
        report = scorer.score(workpaper, previous_year=optional_prev_wp)
        print(report.summary())
    """

    def __init__(self, config: Optional[ScorerConfig] = None):
        self.config = config or ScorerConfig()
        self.analyzer = TextAnalyzer()

    # ── 主入口 ─────────────────────────────────────────────────

    def score(
        self,
        workpaper: Workpaper,
        previous_year: Optional[PreviousYearWorkpaper] = None,
    ) -> ScoreReport:
        """
        对单张底稿进行完整评分。

        Args:
            workpaper: 待评分的底稿
            previous_year: 上年度同项目底稿（可选，用于照抄检测）

        Returns:
            ScoreReport: 完整评分报告
        """
        full_text = workpaper.get_full_text()

        # 四维核心评分
        score_a = self._score_target_clarity(full_text, workpaper)
        score_b = self._score_process_clarity(full_text, workpaper)
        score_c = self._score_evidence_sufficiency(full_text, workpaper)
        score_d = self._score_index_completeness(full_text, workpaper)

        # 三大扣分项
        penalty_e = self._penalty_numbers_without_analysis(full_text)
        penalty_f = self._penalty_conclusion_without_evidence(full_text, workpaper)
        penalty_g = self._penalty_copycat(workpaper, previous_year)

        # 汇总
        raw_score = score_a + score_b + score_c + score_d
        penalty_total = penalty_e.points_deducted + penalty_f.points_deducted + penalty_g.points_deducted
        final_score = max(0.0, raw_score + penalty_total)

        # 等级
        grade = self._map_to_grade(final_score)

        # 风险标记
        risk_flags = self._generate_risk_flags(score_a, score_b, score_c, score_d)

        # 改进清单
        improvement_checklist = self._generate_checklist(
            score_a, score_b, score_c, score_d,
            penalty_e, penalty_f, penalty_g,
        )

        # 年对年对比
        yoy_report = None
        if previous_year is not None:
            yoy_report = self._build_yoy_report(workpaper, previous_year)

        return ScoreReport(
            workpaper_id=workpaper.id,
            workpaper_title=workpaper.title,
            final_score=round(final_score, 1),
            grade=grade,
            passed_l1=final_score >= self.config.L1_PASS_THRESHOLD,
            dimension_scores={
                ScoreDimension.TARGET_CLARITY.value: score_a,
                ScoreDimension.PROCESS_CLARITY.value: score_b,
                ScoreDimension.EVIDENCE_SUFFICIENCY.value: score_c,
                ScoreDimension.INDEX_COMPLETENESS.value: score_d,
            },
            penalties=[penalty_e, penalty_f, penalty_g],
            risk_flags=risk_flags,
            improvement_checklist=improvement_checklist,
            yoy_report=yoy_report,
            scored_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── 维度 A：目标明确性 (0-25) ───────────────────────────────

    def _score_target_clarity(self, full_text: str, wp: Workpaper) -> float:
        """
        评分逻辑：
        - 25分: 明确写出标准认定术语，且认定与程序性质匹配
        - 20分: 写明了主要认定但遗漏次要认定
        - 15分: 有目标描述但未使用标准术语
        - 10分: 目标描述模糊
        - 5分:  仅程序名称无目标
        - 0分:  无任何目标描述
        """
        text = (wp.fields.target if wp.fields and wp.fields.target else
                wp.target if wp.target else
                full_text)

        has_assertion_terms = self.analyzer.count_keyword_matches(text, AUDIT_ASSERTIONS)
        has_assertion_keywords = self.analyzer.count_keyword_matches(text, ASSERTION_KEYWORDS)

        if has_assertion_terms >= 3 and has_assertion_keywords >= 1:
            return 25.0
        elif has_assertion_terms >= 2:
            return 20.0
        elif has_assertion_terms >= 1:
            return 15.0
        elif has_assertion_keywords >= 1:
            return 10.0
        elif len(text.strip()) > 20:
            # 有文字但无相关关键词 → 目标描述模糊
            return 5.0
        else:
            return 0.0

    # ── 维度 B：过程清晰性 (0-25) ──────────────────────────────

    def _score_process_clarity(self, full_text: str, wp: Workpaper) -> float:
        """
        评分逻辑（累计制）：
        - 基础分：有过程文字 → 5分
        - 含抽样方法关键词 → +10分（上限）
        - 含测试步骤关键词 → +5分
        - 含文件类型关键词 → +5分
        - 含覆盖比例/金额占比 → +5分
        """
        text = (
            f"{wp.fields.sampling_method} {wp.fields.selection_logic} "
            f"{' '.join(wp.fields.test_procedures) if wp.fields else ''} "
            f"{' '.join(wp.fields.documents_reviewed) if wp.fields else ''}"
            if wp.fields and any([
                wp.fields.sampling_method,
                wp.fields.selection_logic,
                wp.fields.test_procedures,
                wp.fields.documents_reviewed,
            ])
            else (wp.process if wp.process else full_text)
        )

        score = 0.0

        # 基础分：有过程文字
        if len(text.strip()) > 30:
            score += 5.0
        else:
            return 0.0  # 过程几乎为空

        # 抽样方法
        sampling_hits = self.analyzer.count_keyword_matches(text, SAMPLING_METHODS)
        if sampling_hits >= 3:
            score += 10.0
        elif sampling_hits >= 1:
            score += 6.0

        # 测试步骤动词
        procedure_hits = self.analyzer.count_keyword_matches(text, TEST_PROCEDURE_VERBS)
        if procedure_hits >= 3:
            score += 5.0
        elif procedure_hits >= 1:
            score += 3.0

        # 文件类型
        doc_hits = self.analyzer.count_keyword_matches(text, DOCUMENT_TYPES)
        if doc_hits >= 3:
            score += 3.0
        elif doc_hits >= 1:
            score += 2.0

        # 覆盖比例
        if (
            (wp.fields and wp.fields.coverage_ratio) or
            re.search(r'(?:占比|覆盖|比例|合计[约]?占).*?\d+%', text)
        ):
            score += 2.0

        return min(25.0, score)

    # ── 维度 C：证据充分性 (0-25) ──────────────────────────────

    def _score_evidence_sufficiency(self, full_text: str, wp: Workpaper) -> float:
        """
        评分逻辑：
        - 25分: 每条结论都有证据支撑，例外事项有记录
        - 20分: 主要结论有证据，个别次要结论缺证据
        - 15分: 有证据但逻辑关系需推断
        - 10分: 证据不完整
        - 5分:  结论基本无证据
        - 0分:  只有结论完全无证据
        """
        text = (wp.fields.conclusion_statement if wp.fields and wp.fields.conclusion_statement else
                wp.conclusion if wp.conclusion else
                full_text)

        evidence_hits = self.analyzer.count_any_keyword_matches(text, EVIDENCE_KEYWORDS)
        conclusions = self.analyzer.split_conclusions(full_text)

        # 基础分：证据关键词密度
        if evidence_hits >= 5:
            base_score = 20.0
        elif evidence_hits >= 3:
            base_score = 15.0
        elif evidence_hits >= 1:
            base_score = 10.0
        else:
            base_score = 0.0

        # 加分：每条结论都有证据（内部或后续）
        if conclusions and evidence_hits > 0:
            covered = 0
            for conclusion in conclusions:
                pos = full_text.find(conclusion)
                if pos >= 0 and self.analyzer.has_evidence_nearby(
                    full_text, conclusion, pos,
                    self.config.CONCLUSION_EVIDENCE_WINDOW,
                ):
                    covered += 1
            conclusion_coverage = covered / len(conclusions) if conclusions else 0
            bonus = conclusion_coverage * 5.0  # 最多 +5 分
        else:
            bonus = 0.0

        score = base_score + bonus

        # 扣分：有例外事项但未处理
        exception_count = self.analyzer.count_any_keyword_matches(full_text, EXCEPTION_KEYWORDS)
        if exception_count > 0:
            has_resolution = any(
                kw in full_text
                for kw in ["处理", "调整", "已修正", "已补", "经核实", "经确认",
                           "可接受", "不构成", "不影响", "未发现重大"]
            )
            if not has_resolution:
                score -= 5.0

        # 扣分：结构化字段中例外未记录处理方式
        if wp.fields and wp.fields.exceptions:
            unresolved = [e for e in wp.fields.exceptions if not e.get("resolution")]
            if unresolved:
                score -= 3.0

        return max(0.0, min(25.0, score))

    # ── 维度 D：索引完整性 (0-25) ──────────────────────────────

    def _score_index_completeness(self, full_text: str, wp: Workpaper) -> float:
        """
        评分逻辑：
        - 25分: 索引覆盖率高，格式统一
        - 20分: 主要引用有索引
        - 15分: 有索引但格式不统一
        - 10分: 仅有零星索引
        - 5分:  几乎无索引
        - 0分:  完全无索引
        """
        # 统计索引数量
        refs = wp.get_evidence_refs()

        # 从文本中检测索引模式
        index_patterns = re.findall(
            r'(?:索引|详见|参见|参照|见|附|附件)?[A-Za-z]+[-_][\d]+',
            full_text,
        )
        all_indices = list(set(refs + index_patterns))

        index_count = len(all_indices)

        if index_count >= 8:
            return 25.0
        elif index_count >= 5:
            return 20.0
        elif index_count >= 3:
            return 15.0
        elif index_count >= 1:
            return 10.0
        else:
            # 再检查是否有至少引用标记
            if re.search(r'(?:详见|参见|参照|索引)', full_text):
                return 5.0
            return 0.0

    # ── 扣分项 E：有数无说 (0 ~ -10) ────────────────────────────

    def _penalty_numbers_without_analysis(self, full_text: str) -> PenaltyItem:
        """
        数字内容占比过高且缺乏分析文字。
        """
        number_ratio = self.analyzer.estimate_number_content_ratio(full_text)
        analysis_chars = self.analyzer.count_analysis_chars(full_text)

        reason_parts = []
        points = 0.0

        if number_ratio > self.config.NUMBERS_ONLY_RATIO_THRESHOLD:
            excess = number_ratio - 0.5
            points = -min(self.config.MAX_PENALTY_NO_ANALYSIS, excess * 20)
            reason_parts.append(
                f"数字内容占比 {number_ratio:.0%}，超过阈值 {self.config.NUMBERS_ONLY_RATIO_THRESHOLD:.0%}"
            )

        if analysis_chars < self.config.MIN_ANALYSIS_CHARS:
            if points == 0:
                points = -5.0
            reason_parts.append(
                f"分析性文字仅 {analysis_chars} 字，不足 {self.config.MIN_ANALYSIS_CHARS} 字"
            )

        if points == 0:
            return PenaltyItem(
                code=PenaltyCode.NUMBERS_WITHOUT_ANALYSIS,
                points_deducted=0.0,
                reason="数字与分析比例合理",
            )

        return PenaltyItem(
            code=PenaltyCode.NUMBERS_WITHOUT_ANALYSIS,
            points_deducted=round(points, 1),
            reason="；".join(reason_parts),
            details={
                "number_content_ratio": round(number_ratio, 3),
                "analysis_chars": analysis_chars,
            },
        )

    # ── 扣分项 F：有论无据 (0 ~ -15) ───────────────────────────

    def _penalty_conclusion_without_evidence(
        self, full_text: str, wp: Workpaper
    ) -> PenaltyItem:
        """
        检测结论后是否紧跟证据。每条无据结论扣 5 分，上限 -15。
        """
        conclusions = self.analyzer.split_conclusions(full_text)

        if not conclusions:
            return PenaltyItem(
                code=PenaltyCode.CONCLUSION_WITHOUT_EVIDENCE,
                points_deducted=0.0,
                reason="未检测到显式结论声明",
            )

        unbacked = []
        for conclusion in conclusions:
            pos = full_text.find(conclusion)
            if pos < 0:
                continue
            has_evidence = self.analyzer.has_evidence_nearby(
                full_text, conclusion, pos,
                self.config.CONCLUSION_EVIDENCE_WINDOW,
            )
            if not has_evidence:
                unbacked.append(conclusion[:80] + ("..." if len(conclusion) > 80 else ""))

        if not unbacked:
            return PenaltyItem(
                code=PenaltyCode.CONCLUSION_WITHOUT_EVIDENCE,
                points_deducted=0.0,
                reason=f"全部 {len(conclusions)} 条结论均有证据支撑",
            )

        deduction = -min(self.config.MAX_PENALTY_NO_EVIDENCE, len(unbacked) * 5.0)

        return PenaltyItem(
            code=PenaltyCode.CONCLUSION_WITHOUT_EVIDENCE,
            points_deducted=round(deduction, 1),
            reason=f"发现 {len(unbacked)}/{len(conclusions)} 条结论缺少证据支撑",
            details={
                "total_conclusions": len(conclusions),
                "unbacked_count": len(unbacked),
                "unbacked_samples": unbacked[:3],  # 最多展示3条
            },
        )

    # ── 扣分项 G：照抄嫌疑 (0 ~ -5) ────────────────────────────

    def _penalty_copycat(
        self,
        wp: Workpaper,
        previous_year: Optional[PreviousYearWorkpaper],
    ) -> PenaltyItem:
        """
        与上年底稿做文本相似度对比。
        """
        if previous_year is None:
            return PenaltyItem(
                code=PenaltyCode.COPYCAT_SUSPICION,
                points_deducted=0.0,
                reason="无上年度底稿可供对比",
            )

        current_text = wp.get_full_text()
        prev_text = previous_year.raw_content

        if not current_text or not prev_text:
            return PenaltyItem(
                code=PenaltyCode.COPYCAT_SUSPICION,
                points_deducted=0.0,
                reason="当前或上年底稿内容为空",
            )

        similarity = self.analyzer.text_similarity(current_text, prev_text)

        has_diff_markers = bool(
            re.search(
                r'(?:本年|本期|当年|本年度|差异化|变化|变动|更新)',
                current_text,
            )
        )

        if similarity > self.config.COPYCAT_SIMILARITY_HIGH and not has_diff_markers:
            deduction = -self.config.MAX_PENALTY_COPYCAT
            reason = (
                f"与上年底稿高度相似（{similarity:.0%}），"
                f"且无本年度差异化标注，存在照抄嫌疑"
            )
        elif similarity > self.config.COPYCAT_SIMILARITY_MEDIUM and not has_diff_markers:
            deduction = -2.0
            reason = (
                f"与上年底稿较相似（{similarity:.0%}），"
                f"建议补充本年度差异化分析"
            )
        else:
            deduction = 0.0
            reason = (
                f"与上年底稿相似度 {similarity:.0%}"
                + ("，有本年度差异化标注" if has_diff_markers else "，在正常范围内")
            )

        return PenaltyItem(
            code=PenaltyCode.COPYCAT_SUSPICION,
            points_deducted=round(deduction, 1),
            reason=reason,
            details={
                "similarity": round(similarity, 3),
                "has_diff_markers": has_diff_markers,
                "previous_year": previous_year.year,
            },
        )

    # ── 等级映射 ────────────────────────────────────────────────

    @staticmethod
    def _map_to_grade(score: float) -> Grade:
        if score >= 90:
            return Grade.A
        elif score >= 80:
            return Grade.B
        elif score >= 70:
            return Grade.C
        elif score >= 60:
            return Grade.D
        else:
            return Grade.F

    # ── 风险标记生成 ────────────────────────────────────────────

    def _generate_risk_flags(
        self,
        score_a: float,
        score_b: float,
        score_c: float,
        score_d: float,
    ) -> List[RiskFlag]:
        flags: List[RiskFlag] = []

        if score_a < 10:
            flags.append(RiskFlag(
                code="RISK_NO_TARGET",
                level="high",
                message="底稿未明确审计目标和对应认定，存在方向性风险",
                suggestion="在底稿开头补充本程序对应的财务报表认定（存在/完整性/准确性/截止等）",
            ))
        elif score_a < 15:
            flags.append(RiskFlag(
                code="RISK_VAGUE_TARGET",
                level="medium",
                message="审计目标描述模糊，未使用标准认定术语",
                suggestion="使用标准认定术语重写目标段（如'本程序针对应收账款的存在性认定'）",
            ))

        if score_b < 10:
            flags.append(RiskFlag(
                code="RISK_BLACK_BOX",
                level="high",
                message="底稿过程描述不清晰，形成'黑箱'——无法判断审计程序是否恰当执行",
                suggestion="补充抽样方法、选取逻辑、测试步骤和核查文件类型",
            ))
        elif score_b < 15:
            flags.append(RiskFlag(
                code="RISK_VAGUE_PROCESS",
                level="medium",
                message="过程描述不够完整",
                suggestion="补充覆盖比例或抽查文件类型列表",
            ))

        if score_c < 10:
            flags.append(RiskFlag(
                code="RISK_NO_EVIDENCE",
                level="high",
                message="结论缺乏证据支撑，审计意见可能站不住脚",
                suggestion="为每条结论补充对应的证据引用（合同编号、凭证号、文件索引）",
            ))
        elif score_c < 15:
            flags.append(RiskFlag(
                code="RISK_WEAK_EVIDENCE",
                level="medium",
                message="部分结论的证据支撑不够充分",
                suggestion="逐条检查结论-证据对应关系，补充缺失的证据引用",
            ))

        if score_d < 10:
            flags.append(RiskFlag(
                code="RISK_NO_INDEX",
                level="high",
                message="缺少索引系统，复核人无法追溯证据来源",
                suggestion="建立统一的索引编号体系，在引用处标注索引号",
            ))
        elif score_d < 15:
            flags.append(RiskFlag(
                code="RISK_WEAK_INDEX",
                level="medium",
                message="索引覆盖不完整",
                suggestion="补充缺失的索引引用，统一索引格式",
            ))

        return flags

    # ── 改进清单生成 ────────────────────────────────────────────

    def _generate_checklist(
        self,
        score_a: float,
        score_b: float,
        score_c: float,
        score_d: float,
        penalty_e: PenaltyItem,
        penalty_f: PenaltyItem,
        penalty_g: PenaltyItem,
    ) -> List[ImprovementItem]:
        items: List[ImprovementItem] = []

        # 目标
        if score_a < 20:
            items.append(ImprovementItem(
                priority="high" if score_a < 10 else "medium",
                dimension=ScoreDimension.TARGET_CLARITY,
                item="补充程序目标段",
                action="在底稿开头写明本程序对应的财务报表认定（存在性/完整性/准确性/截止等），使用标准认定术语",
            ))

        # 过程
        if score_b < 20:
            items.append(ImprovementItem(
                priority="high" if score_b < 10 else "medium",
                dimension=ScoreDimension.PROCESS_CLARITY,
                item="补充过程描述",
                action=(
                    "写明：抽样方法类型 → 选取逻辑 → 样本量 → 覆盖比例 → "
                    "具体测试步骤 → 核查的文件类型清单"
                ),
            ))

        # 证据
        if score_c < 20:
            items.append(ImprovementItem(
                priority="high" if score_c < 10 else "medium",
                dimension=ScoreDimension.EVIDENCE_SUFFICIENCY,
                item="补充证据引用",
                action="为每条结论后面紧跟证据描述（合同号、凭证号、文件索引），确保结论-证据一一对应",
            ))

        # 索引
        if score_d < 20:
            items.append(ImprovementItem(
                priority="high" if score_d < 10 else "medium",
                dimension=ScoreDimension.INDEX_COMPLETENESS,
                item="建立索引系统",
                action="在明细表引用凭证号、测算表引用合同号、分析表引用明细表行号，所有支持性文件标注索引编号",
            ))

        # 有数无说
        if penalty_e.points_deducted < 0:
            items.append(ImprovementItem(
                priority="medium",
                dimension=ScoreDimension.PROCESS_CLARITY,
                item="补充分析性文字说明",
                action="将关键数字'翻译'成审计判断——100万余额是大是小？30%增长是正常还是异常？毛利率下降的原因是什么？",
            ))

        # 有论无据
        if penalty_f.points_deducted < 0:
            items.append(ImprovementItem(
                priority="high",
                dimension=ScoreDimension.EVIDENCE_SUFFICIENCY,
                item="补充结论对应的证据",
                action=(
                    f"有 {penalty_f.details.get('unbacked_count', 0) if penalty_f.details else 0} "
                    f"条结论缺少证据——为每条结论补充支撑依据"
                ),
            ))

        # 照抄嫌疑
        if penalty_g.points_deducted < 0:
            items.append(ImprovementItem(
                priority="medium",
                dimension=ScoreDimension.TARGET_CLARITY,
                item="补充本年度差异化分析",
                action=(
                    "说明本年度与上年度的差异点：业务结构变化、会计准则更新、"
                    "行业情况变化、风险评估结果变化，以及对应的程序调整"
                ),
            ))

        return items

    # ── 年度对比报告 ────────────────────────────────────────────

    def _build_yoy_report(
        self,
        wp: Workpaper,
        prev: PreviousYearWorkpaper,
    ) -> YoYReport:
        similarity = self.analyzer.text_similarity(
            wp.get_full_text(),
            prev.raw_content,
        )

        current_text = wp.get_full_text()
        has_changes = bool(
            re.search(
                r'(?:变化|变动|调整|新增|删|修改|更新|本年|本期|当年)',
                current_text,
            )
        )

        # 检测风险-程序不匹配：
        # 如果本年文本提到风险变化，但程序描述与上年高度相似
        risk_change_mentioned = bool(
            re.search(r'(?:风险.*[变增升]|新增.*风险|风险.*调整)', current_text)
        )
        risk_mismatch = risk_change_mentioned and similarity > 0.80

        details_parts = []
        if has_changes:
            details_parts.append("检测到本年度程序调整描述")
        if risk_mismatch:
            details_parts.append("⚠ 风险评估有变化但程序描述高度相似，可能存在程序未相应调整的风险")

        return YoYReport(
            similarity_score=round(similarity, 3),
            has_program_changes=has_changes,
            risk_mismatch_detected=risk_mismatch,
            details="；".join(details_parts) if details_parts else "未检测到显著变化",
        )
