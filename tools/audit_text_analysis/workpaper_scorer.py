"""
L1 底稿质量自动评分引擎 — WorkpaperScorer

基于「程峰标准」四维评分 + 三大扣分项：
  A. 目标明确性（0-25分）
  B. 过程清晰性（0-25分）
  C. 证据充分性（0-25分）
  D. 索引完整性（0-25分）

扣分项：
  E. 有数无说（0 ~ -10）
  F. 有论无据（0 ~ -15）
  G. 照抄嫌疑（0 ~ -5）

通过阈值：≥ 70分（L1复核）
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


# ── 枚举 ──────────────────────────────────────────────────

class QualityGrade(Enum):
    A = "A级 — 优秀底稿，可直接通过L1复核"
    B = "B级 — 良好底稿，少量修改后通过"
    C = "C级 — 合格底稿，需补充完善"
    D = "D级 — 不足底稿，退回修改"
    F = "F级 — 不合格底稿，退回重做"


# ── 数据结构 ──────────────────────────────────────────────

@dataclass
class ScoreReport:
    """评分报告"""
    workpaper_id: str
    workpaper_title: str = ""

    # 四维得分
    score_a: int = 0   # 目标明确性
    score_b: int = 0   # 过程清晰性
    score_c: int = 0   # 证据充分性
    score_d: int = 0   # 索引完整性

    # 扣分
    penalty_e: int = 0  # 有数无说
    penalty_f: int = 0  # 有论无据
    penalty_g: int = 0  # 照抄嫌疑

    # 总分
    raw_score: int = 0
    penalty_total: int = 0
    final_score: int = 0
    grade: str = ""

    # 详情
    dimension_details: Dict[str, str] = field(default_factory=dict)
    risk_flags: List[str] = field(default_factory=list)
    improvement_checklist: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.final_score >= 70

    @property
    def grade_enum(self) -> QualityGrade:
        if self.final_score >= 90:
            return QualityGrade.A
        elif self.final_score >= 80:
            return QualityGrade.B
        elif self.final_score >= 70:
            return QualityGrade.C
        elif self.final_score >= 60:
            return QualityGrade.D
        return QualityGrade.F


# ── 关键词库 ──────────────────────────────────────────────

class AuditKeywordBank:
    """审计专用关键词库"""

    ASSERTION_TERMS = [
        "存在", "存在性", "完整性", "准确性", "计价", "分摊",
        "截止", "权利", "义务", "列报", "披露", "认定",
        "验证", "目标", "测试",
    ]

    SAMPLING_TERMS = [
        "随机抽样", "分层抽样", "大额优先", "PPS抽样", "系统抽样",
        "金额降序", "判断抽样", "全量检查", "选取", "抽取", "抽样",
        "按金额", "按比例",
    ]

    TEST_PROCEDURE_TERMS = [
        "获取", "核对", "检查", "验证", "比较", "重新计算",
        "函证", "盘点", "观察", "询问", "分析", "追踪",
        "交叉比对", "复核", "测试",
    ]

    DOCUMENT_TYPE_TERMS = [
        "合同", "发票", "出库单", "签收单", "银行对账单",
        "凭证", "明细账", "权证", "评估报告", "验收单",
        "审批单", "付款申请", "结算单", "变更单", "签证单",
        "会议纪要", "招标文件", "中标通知",
    ]

    EVIDENCE_TERMS = [
        "依据", "证据", "支撑", "经检查", "经核查", "经抽查",
        "来源", "详见索引", "参照", "根据", "参见", "附",
        "详见", "索引", "编号",
    ]

    CONCLUSION_PATTERNS = [
        r"(?:审计)?结论[：:]",
        r"(?:经|通过|经过)(?:检查|核查|测试|分析|复核)",
        r"(?:未发现|发现|存在|不存在).*?(?:异常|问题|差异|违规|错误)",
        r"(?:可以|能够|无法)(?:确认|验证|认定)",
    ]

    EXCEPTION_TERMS = [
        "差异", "异常", "不符", "例外", "问题",
        "违规", "超标", "超支", "错报",
    ]

    INDEX_PATTERNS = [
        r"[A-Z]-\d+",              # A-1, B-2 ...
        r"[A-Z]{2,3}-\d{2,4}",    # WP-01, AA-101 ...
        r"底稿[编号号]?[：:]?\s*[\w\-]+",
        r"索引[：:]?\s*[\w\-]+",
    ]


# ── 评分引擎 ──────────────────────────────────────────────

class WorkpaperScorer:
    """
    底稿质量自动评分引擎

    用法:
        scorer = WorkpaperScorer()
        report = scorer.score(workpaper_content, previous_year_content)
        if not report.passed:
            for item in report.improvement_checklist:
                print(item)
    """

    def __init__(self):
        self.kb = AuditKeywordBank()

    def score(
        self,
        content: str,
        workpaper_id: str = "",
        workpaper_title: str = "",
        previous_year_content: Optional[str] = None,
    ) -> ScoreReport:
        """
        对单张底稿进行质量评分

        Args:
            content: 底稿文本内容
            workpaper_id: 底稿编号
            workpaper_title: 底稿标题
            previous_year_content: 上年度同项目底稿内容（用于照抄检测）

        Returns:
            ScoreReport: 评分报告
        """
        report = ScoreReport(
            workpaper_id=workpaper_id,
            workpaper_title=workpaper_title,
        )

        # 四维核心评分
        report.score_a = self._score_target_clarity(content)
        report.score_b = self._score_process_clarity(content)
        report.score_c = self._score_evidence_sufficiency(content)
        report.score_d = self._score_index_completeness(content)

        # 三大扣分项
        report.penalty_e = self._penalty_numbers_without_analysis(content)
        report.penalty_f = self._penalty_conclusion_without_evidence(content)
        report.penalty_g = self._penalty_copy_last_year(content, previous_year_content)

        # 总分
        report.raw_score = report.score_a + report.score_b + report.score_c + report.score_d
        report.penalty_total = report.penalty_e + report.penalty_f + report.penalty_g
        report.final_score = max(0, report.raw_score + report.penalty_total)
        report.grade = report.grade_enum.value

        # 组装详情和改进清单
        report.dimension_details = self._build_details(report)
        report.risk_flags = self._build_risk_flags(report)
        report.improvement_checklist = self._build_checklist(report)

        return report

    # ── 维度A：目标明确性 ─────────────────────────────────

    def _score_target_clarity(self, content: str) -> int:
        """评分维度A：目标明确性（0-25分）"""
        assertion_hits = [term for term in self.kb.ASSERTION_TERMS if term in content]

        if not assertion_hits:
            self._a_detail = "未找到任何认定相关术语"
            return 0

        # 检查是否使用标准认定术语（存在性、完整性等）
        standard_terms = {"存在", "存在性", "完整性", "准确性", "计价", "分摊",
                         "截止", "权利", "义务", "列报", "披露"}
        standard_hits = [t for t in assertion_hits if t in standard_terms]

        if len(standard_hits) >= 2:
            self._a_detail = f"使用标准认定术语：{', '.join(standard_hits)}"
            return 25
        elif len(standard_hits) == 1:
            self._a_detail = f"使用了1个标准认定术语({standard_hits[0]})，建议补充其他相关认定"
            return 20
        elif len(assertion_hits) >= 2:
            self._a_detail = f"有关认定描述，但术语不规范：{', '.join(assertion_hits[:3])}"
            return 15
        elif len(assertion_hits) == 1:
            self._a_detail = f"目标描述模糊，仅有非标准术语：{assertion_hits[0]}"
            return 10
        return 5

    # ── 维度B：过程清晰性 ─────────────────────────────────

    def _score_process_clarity(self, content: str) -> int:
        """评分维度B：过程清晰性（0-25分）"""
        sampling_hits = [t for t in self.kb.SAMPLING_TERMS if t in content]
        procedure_hits = [t for t in self.kb.TEST_PROCEDURE_TERMS if t in content]
        doc_hits = [t for t in self.kb.DOCUMENT_TYPE_TERMS if t in content]

        # 检查覆盖比例
        coverage_pattern = r"(?:覆盖|占比|比例|金额占比|数量占比).*?(\d+(?:\.\d+)?)\s*%"
        has_coverage = bool(re.search(coverage_pattern, content))

        score = 0
        if sampling_hits:
            score += 10
        if procedure_hits:
            score += 5
        if doc_hits:
            score += 5
        if has_coverage:
            score += 5

        if not sampling_hits and not procedure_hits:
            self._b_detail = "无抽样方法也无测试步骤描述"
        elif sampling_hits and procedure_hits and doc_hits and has_coverage:
            self._b_detail = ("过程描述完整：已说明抽样方法、测试步骤、"
                            f"文件类型和覆盖比例")
        elif sampling_hits and procedure_hits:
            self._b_detail = "说明了方法和步骤，但缺少覆盖比例或文件类型"
        elif sampling_hits:
            self._b_detail = "有抽样方法但缺少测试步骤"
        elif procedure_hits:
            self._b_detail = "有测试步骤但未说明抽样方法"
        else:
            self._b_detail = "过程描述不完整"

        return score

    # ── 维度C：证据充分性 ─────────────────────────────────

    def _score_evidence_sufficiency(self, content: str) -> int:
        """评分维度C：证据充分性（0-25分）"""
        evidence_hits = [t for t in self.kb.EVIDENCE_TERMS if t in content]

        # 检测结论-证据对应关系
        conclusions = []
        for pat in self.kb.CONCLUSION_PATTERNS:
            conclusions.extend(re.finditer(pat, content))

        # 检查例外处理
        exception_hits = [t for t in self.kb.EXCEPTION_TERMS if t in content]

        score = 0

        if not evidence_hits:
            self._c_detail = "完全无证据支撑"
            return 0

        evidence_count = len(evidence_hits)

        if evidence_count >= 5 and len(conclusions) > 0:
            # 检查每条结论后500字符内是否有证据
            has_evidence_after_conclusion = True
            for m in conclusions:
                post_text = content[m.end():m.end() + 500]
                if not any(t in post_text for t in self.kb.EVIDENCE_TERMS):
                    has_evidence_after_conclusion = False
                    break

            if has_evidence_after_conclusion:
                score = 25
                self._c_detail = "每条结论均有对应证据支撑"
            else:
                score = 20
                self._c_detail = "主要结论有证据，但部分缺少对应证据"
        elif evidence_count >= 3:
            score = 15
            self._c_detail = "有证据但结论与证据之间的逻辑关系不够清晰"
        elif evidence_count >= 1:
            score = 10
            self._c_detail = "证据不完整"
        else:
            score = 0
            self._c_detail = "无证据"

        # 例外处理检测
        if exception_hits:
            has_resolution = any(
                kw in content for kw in
                ["处理", "解决", "整改", "调整", "纠正", "说明", "原因"]
            )
            if not has_resolution:
                score = max(0, score - 5)
                self._c_detail += "；有例外事项但缺少处理说明（-5分）"

        return score

    # ── 维度D：索引完整性 ─────────────────────────────────

    def _score_index_completeness(self, content: str) -> int:
        """评分维度D：索引完整性（0-25分）"""
        index_matches = []
        for pat in self.kb.INDEX_PATTERNS:
            index_matches.extend(re.findall(pat, content))

        unique_indexes = set(index_matches)
        index_count = len(unique_indexes)

        # 估算底稿中应有多少引用（粗略估计：每500字符应有1个引用）
        expected_refs = max(1, len(content) // 500)

        if index_count == 0:
            self._d_detail = "完全无索引系统"
            return 0

        coverage = min(1.0, index_count / expected_refs)

        if coverage >= 0.9:
            score = 25
            self._d_detail = f"索引覆盖率优秀（{coverage:.0%}），{index_count}个索引"
        elif coverage >= 0.7:
            score = 20
            self._d_detail = f"主要引用有索引，覆盖率{coverage:.0%}"
        elif coverage >= 0.5:
            score = 15
            self._d_detail = f"索引覆盖率{coverage:.0%}，部分引用缺索引"
        elif coverage >= 0.3:
            score = 10
            self._d_detail = f"索引覆盖率{coverage:.0%}，大量引用缺索引"
        else:
            score = 5
            self._d_detail = f"仅有零星索引（{index_count}个）"

        return score

    # ── 扣分E：有数无说 ────────────────────────────────────

    def _penalty_numbers_without_analysis(self, content: str) -> int:
        """扣分E：有数无说（0 ~ -10）"""
        if not content:
            return 0

        total_chars = len(content)
        numeric_chars = len(re.findall(r"\d", content))

        if total_chars == 0:
            return 0

        numeric_ratio = numeric_chars / total_chars

        # 文字分析长度（去除数字和标点后的纯文本长度）
        text_only = re.sub(r"[\d\s\W]+", "", content)
        text_len = len(text_only)

        if numeric_ratio > 0.7 and text_len < 200:
            penalty = min(10, int((numeric_ratio - 0.5) * 20))
            self._e_detail = (
                f"数字占比{numeric_ratio:.0%}，文字分析仅{text_len}字 → 扣{penalty}分"
            )
            return -penalty

        if numeric_ratio > 0.5 and text_len < 100:
            penalty = min(5, int((numeric_ratio - 0.4) * 10))
            self._e_detail = (
                f"数字占比较高({numeric_ratio:.0%})，分析偏少 → 扣{penalty}分"
            )
            return -penalty

        self._e_detail = "数字与文字分析比例合理"
        return 0

    # ── 扣分F：有论无据 ────────────────────────────────────

    def _penalty_conclusion_without_evidence(self, content: str) -> int:
        """扣分F：有论无据（0 ~ -15）"""
        ungrounded_count = 0

        for pat in self.kb.CONCLUSION_PATTERNS:
            for m in re.finditer(pat, content):
                post_text = content[m.end():m.end() + 500]
                has_evidence = any(
                    t in post_text for t in self.kb.EVIDENCE_TERMS
                )
                if not has_evidence:
                    ungrounded_count += 1

        if ungrounded_count == 0:
            self._f_detail = "结论均有相应证据支撑"
            return 0

        penalty = min(15, ungrounded_count * 5)
        self._f_detail = (
            f"发现{ungrounded_count}条结论缺少证据支撑 → 扣{penalty}分"
        )
        return -penalty

    # ── 扣分G：照抄嫌疑 ────────────────────────────────────

    def _penalty_copy_last_year(
        self, content: str, previous_year: Optional[str]
    ) -> int:
        """扣分G：照抄嫌疑（0 ~ -5）"""
        if not previous_year or not content:
            self._g_detail = "无上年度底稿对比"
            return 0

        # 简单相似度计算（Jaccard on character trigrams）
        def trigrams(text: str) -> set:
            return {text[i:i+3] for i in range(len(text) - 2)}

        cur_tri = trigrams(content)
        prev_tri = trigrams(previous_year)

        if not cur_tri or not prev_tri:
            return 0

        intersection = cur_tri & prev_tri
        union = cur_tri | prev_tri
        similarity = len(intersection) / len(union) if union else 0

        # 检查是否有本年度差异化标注
        has_diff_marker = any(
            kw in content for kw in
            ["本年度", "本期", "本报告期", "较上年", "同比", "差异分析",
             "变化", "新增", "调整", "更新"]
        )

        if similarity > 0.9 and not has_diff_marker:
            self._g_detail = f"与上年度高度雷同（{similarity:.1%}），无本年度差异化标注 → 扣5分"
            return -5
        elif similarity > 0.7 and not has_diff_marker:
            self._g_detail = f"与上年度较高相似（{similarity:.1%}），缺少差异化分析 → 扣2分"
            return -2
        else:
            self._g_detail = (
                f"与上年度相似度{similarity:.1%}，"
                f"{'有本年度差异化标注' if has_diff_marker else '无明显照抄嫌疑'}"
            )
            return 0

    # ── 辅助方法 ──────────────────────────────────────────

    def _build_details(self, report: ScoreReport) -> Dict[str, str]:
        return {
            "A_目标明确性": getattr(self, "_a_detail", "未评估"),
            "B_过程清晰性": getattr(self, "_b_detail", "未评估"),
            "C_证据充分性": getattr(self, "_c_detail", "未评估"),
            "D_索引完整性": getattr(self, "_d_detail", "未评估"),
            "E_有数无说": getattr(self, "_e_detail", "未评估"),
            "F_有论无据": getattr(self, "_f_detail", "未评估"),
            "G_照抄嫌疑": getattr(self, "_g_detail", "未评估"),
        }

    def _build_risk_flags(self, report: ScoreReport) -> List[str]:
        flags = []
        if report.score_a < 15:
            flags.append(f"目标模糊（{report.score_a}/25分）")
        if report.score_b < 15:
            flags.append(f"过程不清（{report.score_b}/25分）")
        if report.score_c < 15:
            flags.append(f"证据不足（{report.score_c}/25分）")
        if report.score_d < 15:
            flags.append(f"索引缺失（{report.score_d}/25分）")
        if report.penalty_e < 0:
            flags.append(f"有数无说（{report.penalty_e}分）")
        if report.penalty_f < 0:
            flags.append(f"有论无据（{report.penalty_f}分）")
        if report.penalty_g < 0:
            flags.append(f"照抄嫌疑（{report.penalty_g}分）")
        if report.final_score < 70:
            flags.append(f"不合格（{report.final_score}分 < 70分阈值）")
        return flags

    def _build_checklist(self, report: ScoreReport) -> List[str]:
        checklist = []
        if report.score_a < 20:
            checklist.append("【目标】补充对应的审计认定（存在性/完整性/准确性等）")
        if report.score_b < 20:
            checklist.append("【过程】补充抽样方法和测试步骤的详细描述")
        if report.score_c < 20:
            checklist.append("【证据】为每条结论补充对应的证据索引")
        if report.score_d < 20:
            checklist.append("【索引】完善交叉引用索引号，确保可追溯")
        if report.penalty_e < 0:
            checklist.append("【有数无说】增加对数据的文字分析和解读")
        if report.penalty_f < 0:
            checklist.append("【有论无据】为每个结论补充证据链支撑")
        if report.penalty_g < 0:
            checklist.append("【照抄嫌疑】标注本年度变化点和差异化分析")
        return checklist

    def batch_score(
        self,
        workpapers: List[Tuple[str, str, str]],  # (id, title, content)
        previous_year_map: Optional[Dict[str, str]] = None,
    ) -> List[ScoreReport]:
        """
        批量评分多张底稿

        Args:
            workpapers: [(id, title, content), ...]
            previous_year_map: {id: previous_year_content, ...}
        """
        reports = []
        for wp_id, wp_title, wp_content in workpapers:
            prev = previous_year_map.get(wp_id) if previous_year_map else None
            report = self.score(
                content=wp_content,
                workpaper_id=wp_id,
                workpaper_title=wp_title,
                previous_year_content=prev,
            )
            reports.append(report)

        return reports

    def summary(self, reports: List[ScoreReport]) -> Dict[str, Any]:
        """生成批量评分摘要"""
        if not reports:
            return {"total": 0, "passed": 0, "failed": 0}

        passed = [r for r in reports if r.passed]
        failed = [r for r in reports if not r.passed]

        avg_score = sum(r.final_score for r in reports) / len(reports)

        return {
            "total": len(reports),
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate": f"{len(passed)/len(reports)*100:.1f}%",
            "avg_score": round(avg_score, 1),
            "grade_distribution": {
                "A": sum(1 for r in reports if r.grade_enum == QualityGrade.A),
                "B": sum(1 for r in reports if r.grade_enum == QualityGrade.B),
                "C": sum(1 for r in reports if r.grade_enum == QualityGrade.C),
                "D": sum(1 for r in reports if r.grade_enum == QualityGrade.D),
                "F": sum(1 for r in reports if r.grade_enum == QualityGrade.F),
            },
            "top_issues": self._top_issues(reports),
            "failed_workpapers": [{
                "id": r.workpaper_id,
                "title": r.workpaper_title,
                "score": r.final_score,
                "grade": r.grade_enum.name,
            } for r in failed],
        }

    def _top_issues(
        self, reports: List[ScoreReport], top_n: int = 5
    ) -> List[str]:
        """提取批量评分中的TOP问题"""
        issue_count: Dict[str, int] = {}
        for r in reports:
            for issue in r.risk_flags:
                base = issue.split("（")[0] if "（" in issue else issue
                issue_count[base] = issue_count.get(base, 0) + 1

        sorted_issues = sorted(
            issue_count.items(), key=lambda x: x[1], reverse=True
        )
        return [
            f"{issue}（{count}份底稿）"
            for issue, count in sorted_issues[:top_n]
        ]
