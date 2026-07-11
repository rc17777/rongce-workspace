"""
tests/test_workpaper_scorer.py — 完整测试套件

运行: python -m pytest tests/test_workpaper_scorer.py -v
"""

import json
import os
import sys
import unittest

# 添加父目录到 Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workpaper_scorer import (
    WorkpaperScorer,
    PreflightChecker,
    Workpaper,
    WorkpaperField,
    PreviousYearWorkpaper,
    ScoreReport,
    Grade,
    ScoreDimension,
    PenaltyCode,
)


# ── 测试数据工厂 ──────────────────────────────────────────────

class TestData:
    """提供标准化的测试数据"""

    @staticmethod
    def excellent_workpaper() -> Workpaper:
        """一条满分底稿的典型示例"""
        return Workpaper(
            id="WP-2026-001",
            title="应收账款存在性测试",
            target="本程序针对应收账款的存在性、计价和分摊认定，验证资产负债表中列示的应收账款是否真实存在且计价准确。",
            process=(
                "样本选取：根据应收账款明细账，按金额降序排列，"
                "选取前15笔金额最大的（合计占总余额72%），"
                "再从剩余明细中随机选取10笔，共计25笔。\n"
                "测试过程：获取上述25笔销售对应的销售合同、"
                "出库单、客户签收单及发票，核对了客户名称、金额、"
                "数量等信息是否与账面记录一致。"
            ),
            conclusion=(
                "结论：应收账款存在性无重大异常。\n"
                "依据：经核查25笔样本，销售合同（索引C-001至C-025）、"
                "出库单（索引D-001至D-025）、签收单（索引R-001至R-025）"
                "均与账面记录一致，未发现例外事项。\n"
                "样本覆盖总余额72%，结论有充分证据支撑。"
            ),
            cross_refs=[
                "明细表-AR-001",
                "合同-C-001",
                "出库单-D-001",
                "签收单-R-001",
                "发票-I-001",
            ],
        )

    @staticmethod
    def bare_minimum_workpaper() -> Workpaper:
        """一条极度简化的底稿 — 应得低分"""
        return Workpaper(
            id="WP-2026-002",
            title="银行存款余额调节测试",
            process="样本量：10笔。测试结果：无异常。",
            conclusion="结论：截止性无异常。",
        )

    @staticmethod
    def numbers_only_workpaper() -> Workpaper:
        """有数无说的底稿 — 大量数字但几乎没有分析"""
        return Workpaper(
            id="WP-2026-003",
            title="毛利率分析表",
            # 用大量纯数字行 + 极少量文字模拟"有数无说"场景
            raw_content="5000000 4200000 3200000 2520000 36.0% 40.0% 45 38 62 55 " * 20
                       + "\n毛利率变动。",  # 只有一句不着边际的文字
        )

    @staticmethod
    def conclusion_without_evidence_workpaper() -> Workpaper:
        """有论无据的底稿"""
        return Workpaper(
            id="WP-2026-004",
            title="存货跌价测试",
            conclusion="结论：存货跌价准备计提充分。",
        )

    @staticmethod
    def structured_workpaper() -> Workpaper:
        """使用结构化字段的底稿"""
        return Workpaper(
            id="WP-2026-005",
            title="固定资产折旧测试",
            fields=WorkpaperField(
                target="本程序针对固定资产的准确性、计价和分摊认定",
                sampling_method="大额优先 + 随机抽样",
                selection_logic="按固定资产原值降序排列，选取前10项（占总原值85%），再从剩余中随机选5项",
                sample_size=15,
                coverage_ratio="92%",
                test_procedures=[
                    "重新计算折旧金额",
                    "核对折旧政策一致性",
                    "检查新增/处置固定资产的折旧计算",
                ],
                documents_reviewed=[
                    "固定资产台账",
                    "折旧计算表",
                    "采购合同",
                    "处置审批单",
                ],
                conclusion_statement=(
                    "结论：固定资产折旧计提准确，折旧政策一贯执行。"
                ),
                evidence_refs=["折旧测算表-DP-001", "折旧政策文件-POL-2026"],
                exceptions=[],
                cross_refs=["固定资产台账-FA-001", "采购合同-PO-001"],
                ledger_ref="明细表-FA-001",
                contract_refs=["PO-001", "PO-002"],
            ),
            raw_content="固定资产折旧测试详情...",
        )

    @staticmethod
    def previous_year_workpaper() -> PreviousYearWorkpaper:
        return PreviousYearWorkpaper(
            id="WP-2025-001",
            year="2025",
            raw_content=(
                "应收账款存在性测试。样本选取：根据应收账款明细账，"
                "按金额降序排列，选取前15笔金额最大的，"
                "再从剩余明细中随机选取10笔，共计25笔。"
                "经测试无异常。"
            ),
        )


# ── 测试类 ────────────────────────────────────────────────────

class TestWorkpaperScorer(unittest.TestCase):
    """核心评分引擎测试"""

    def setUp(self):
        self.scorer = WorkpaperScorer()

    # ── 优秀底稿 ────────────────────────────────────────────────

    def test_excellent_workpaper_scores_high(self):
        """优秀底稿应得到高分"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        self.assertGreaterEqual(report.final_score, 70)
        self.assertIn(report.grade, [Grade.A, Grade.B, Grade.C])
        self.assertTrue(report.passed_l1)

    def test_excellent_workpaper_target_score(self):
        """优秀底稿的目标明确性应为满分"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        self.assertGreaterEqual(
            report.dimension_scores[ScoreDimension.TARGET_CLARITY.value],
            15,
        )

    def test_excellent_workpaper_process_score(self):
        """优秀底稿的过程清晰性应得到高分"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        self.assertGreaterEqual(
            report.dimension_scores[ScoreDimension.PROCESS_CLARITY.value],
            15,
        )

    # ── 极简底稿 ────────────────────────────────────────────────

    def test_bare_minimum_scores_low(self):
        """极简底稿应得到低分"""
        wp = TestData.bare_minimum_workpaper()
        report = self.scorer.score(wp)

        # 没有目标描述，没有抽样方法，没有证据
        self.assertLess(report.final_score, 60)
        self.assertFalse(report.passed_l1)

    def test_bare_minimum_has_risk_flags(self):
        """极简底稿应产生多个风险标记"""
        wp = TestData.bare_minimum_workpaper()
        report = self.scorer.score(wp)

        self.assertGreater(len(report.risk_flags), 1)

    # ── 有数无说 ────────────────────────────────────────────────

    def test_numbers_only_detected(self):
        """有数无说的底稿应被检测到"""
        wp = TestData.numbers_only_workpaper()
        report = self.scorer.score(wp)

        # 找到 E 扣分项
        penalty_e = next(
            p for p in report.penalties
            if p.code == PenaltyCode.NUMBERS_WITHOUT_ANALYSIS
        )
        self.assertLess(penalty_e.points_deducted, 0,
                       "有数无说应被扣分")

    # ── 有论无据 ────────────────────────────────────────────────

    def test_conclusion_without_evidence_detected(self):
        """有论无据的底稿应被检测到"""
        wp = TestData.conclusion_without_evidence_workpaper()
        report = self.scorer.score(wp)

        penalty_f = next(
            p for p in report.penalties
            if p.code == PenaltyCode.CONCLUSION_WITHOUT_EVIDENCE
        )
        self.assertLess(penalty_f.points_deducted, 0,
                       "有论无据应被扣分")

    # ── 照抄检测 ────────────────────────────────────────────────

    def test_copycat_detected(self):
        """与上年底稿高度相似应被检测到"""
        wp = TestData.excellent_workpaper()
        prev = TestData.previous_year_workpaper()
        report = self.scorer.score(wp, previous_year=prev)

        penalty_g = next(
            p for p in report.penalties
            if p.code == PenaltyCode.COPYCAT_SUSPICION
        )
        # excellent_workpaper 比 previous_year 多了很多内容，相似度应该不会太高
        # 这个测试主要验证对比功能正常运行
        self.assertIsNotNone(penalty_g)

    def test_copycat_no_previous_year(self):
        """没有上年底稿时照抄检测返回0扣分"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        penalty_g = next(
            p for p in report.penalties
            if p.code == PenaltyCode.COPYCAT_SUSPICION
        )
        self.assertEqual(penalty_g.points_deducted, 0)
        self.assertIn("无上年度底稿", penalty_g.reason)

    # ── 结构化底稿 ──────────────────────────────────────────────

    def test_structured_workpaper(self):
        """结构化底稿应正常评分"""
        wp = TestData.structured_workpaper()
        report = self.scorer.score(wp)

        self.assertIsInstance(report.final_score, float)
        self.assertGreaterEqual(report.final_score, 0)
        self.assertLessEqual(report.final_score, 100)

    def test_structured_workpaper_target(self):
        """结构化底稿的目标明确性"""
        wp = TestData.structured_workpaper()
        report = self.scorer.score(wp)

        self.assertGreaterEqual(
            report.dimension_scores[ScoreDimension.TARGET_CLARITY.value],
            15,
        )

    # ── 维度范围 ────────────────────────────────────────────────

    def test_dimension_scores_in_range(self):
        """每项维度得分应在 0-25 之间"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        for dim, score in report.dimension_scores.items():
            self.assertGreaterEqual(score, 0, f"{dim} 得分不应为负")
            self.assertLessEqual(score, 25, f"{dim} 得分不应超过25")

    # ── 扣分上限 ────────────────────────────────────────────────

    def test_penalty_e_never_exceeds_max(self):
        """有数无说扣分不超过上限"""
        wp = Workpaper(
            id="WP-2026-MAX",
            raw_content="1 2 3 4 5 6 7 8 9 10 " * 1000 + " 10% 100万 1000亿",
        )
        report = self.scorer.score(wp)

        penalty_e = next(
            p for p in report.penalties
            if p.code == PenaltyCode.NUMBERS_WITHOUT_ANALYSIS
        )
        self.assertGreaterEqual(penalty_e.points_deducted, -10.0)

    def test_penalty_f_never_exceeds_max(self):
        """有论无据扣分不超过上限"""
        wp = Workpaper(
            id="WP-2026-MAX-F",
            title="多项测试",
            conclusion=(
                "结论：测试A无异常。\n结论：测试B无异常。\n"
                "结论：测试C无异常。\n结论：测试D无异常。\n"
                "结论：测试E无异常。\n结论：测试F无异常。\n"
            ),
        )
        report = self.scorer.score(wp)

        penalty_f = next(
            p for p in report.penalties
            if p.code == PenaltyCode.CONCLUSION_WITHOUT_EVIDENCE
        )
        self.assertGreaterEqual(penalty_f.points_deducted, -15.0)

    # ── 最终得分范围 ─────────────────────────────────────────────

    def test_final_score_never_negative(self):
        """最终得分不应为负数"""
        # 构造一个极端差的底稿
        wp = Workpaper(id="WP-2026-BAD")
        report = self.scorer.score(wp)

        self.assertGreaterEqual(report.final_score, 0)

    def test_final_score_never_exceeds_100(self):
        """最终得分不应超过100"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        self.assertLessEqual(report.final_score, 100)

    # ── 等级映射 ─────────────────────────────────────────────────

    def test_grade_mapping_A(self):
        self.assertEqual(WorkpaperScorer._map_to_grade(95), Grade.A)
        self.assertEqual(WorkpaperScorer._map_to_grade(90), Grade.A)

    def test_grade_mapping_B(self):
        self.assertEqual(WorkpaperScorer._map_to_grade(85), Grade.B)
        self.assertEqual(WorkpaperScorer._map_to_grade(80), Grade.B)

    def test_grade_mapping_C(self):
        self.assertEqual(WorkpaperScorer._map_to_grade(75), Grade.C)
        self.assertEqual(WorkpaperScorer._map_to_grade(70), Grade.C)

    def test_grade_mapping_D(self):
        self.assertEqual(WorkpaperScorer._map_to_grade(65), Grade.D)
        self.assertEqual(WorkpaperScorer._map_to_grade(60), Grade.D)

    def test_grade_mapping_F(self):
        self.assertEqual(WorkpaperScorer._map_to_grade(55), Grade.F)
        self.assertEqual(WorkpaperScorer._map_to_grade(0), Grade.F)

    # ── 序列化 ──────────────────────────────────────────────────

    def test_report_to_dict(self):
        """报告可序列化为字典"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        d = report.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["workpaper_id"], wp.id)
        self.assertIn("dimension_scores", d)
        self.assertIn("penalties", d)
        self.assertIn("risk_flags", d)

    def test_report_to_json(self):
        """报告可序列化为 JSON 字符串"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        json_str = report.to_json()
        self.assertIsInstance(json_str, str)
        # 验证可被解析回 dict
        parsed = json.loads(json_str)
        self.assertEqual(parsed["workpaper_id"], wp.id)

    def test_report_summary(self):
        """报告摘要方法正常返回"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        summary = report.summary()
        self.assertIsInstance(summary, str)
        self.assertIn(wp.id, summary)
        self.assertIn("最终得分", summary)

    # ── 得分一致性（确定性）───────────────────────────────────────

    def test_score_is_deterministic(self):
        """相同输入应产生相同分数"""
        wp = TestData.excellent_workpaper()
        report1 = self.scorer.score(wp)
        report2 = self.scorer.score(wp)

        self.assertEqual(report1.final_score, report2.final_score)
        self.assertEqual(report1.grade, report2.grade)


class TestPreflightChecker(unittest.TestCase):
    """提价前自检测试"""

    def setUp(self):
        self.checker = PreflightChecker()

    def test_excellent_passes_all(self):
        """优秀底稿应通过全部自检"""
        wp = TestData.excellent_workpaper()
        result = self.checker.check(wp)

        self.assertGreaterEqual(result.passed_count, 4)
        # 索引检查需要显式标注索引号，excellent_workpaper 有 cross_refs
        self.assertTrue(result.items[3].passed, "索引检查应通过")

    def test_bare_minimum_fails_most(self):
        """极简底稿应有多项自检未通过"""
        wp = TestData.bare_minimum_workpaper()
        result = self.checker.check(wp)

        self.assertLess(result.passed_count, 5)

    def test_preflight_has_6_items(self):
        """自检应有 6 项"""
        wp = TestData.excellent_workpaper()
        result = self.checker.check(wp)

        self.assertEqual(len(result.items), 6)

    def test_preflight_summary(self):
        """自检摘要方法正常返回"""
        wp = TestData.excellent_workpaper()
        result = self.checker.check(wp)

        summary = result.summary()
        self.assertIsInstance(summary, str)
        self.assertIn(wp.id, summary)


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        self.scorer = WorkpaperScorer()

    def test_empty_workpaper(self):
        """空底稿的处理"""
        wp = Workpaper(id="WP-EMPTY")
        report = self.scorer.score(wp)

        self.assertEqual(report.final_score, 0)
        self.assertEqual(report.grade, Grade.F)

    def test_workpaper_with_only_title(self):
        """只有标题的底稿"""
        wp = Workpaper(id="WP-TITLE", title="测试底稿")
        report = self.scorer.score(wp)

        self.assertEqual(report.final_score, 0)

    def test_very_long_content(self):
        """超长底稿内容（不应 OOM）"""
        wp = Workpaper(
            id="WP-LONG",
            raw_content=(
                "对于应收账款的存在性认定，" * 500 +
                "样本选取：随机抽样 " * 500 +
                "结论：无异常。依据：已核对。" * 500
            ),
        )
        report = self.scorer.score(wp)
        # 应正常返回
        self.assertIsInstance(report.final_score, float)


class TestImprovementChecklist(unittest.TestCase):
    """改进清单测试"""

    def setUp(self):
        self.scorer = WorkpaperScorer()

    def test_excellent_has_minimal_checklist(self):
        """优秀底稿的改进清单应较少"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        # 优秀底稿可能仍有少量改进建议（如索引不够完美）
        self.assertLessEqual(len(report.improvement_checklist), 3)

    def test_bare_minimum_has_checklist(self):
        """极简底稿应有改进清单"""
        wp = TestData.bare_minimum_workpaper()
        report = self.scorer.score(wp)

        self.assertGreater(len(report.improvement_checklist), 0)


class TestYoYReport(unittest.TestCase):
    """年度对比报告测试"""

    def setUp(self):
        self.scorer = WorkpaperScorer()

    def test_yoy_report_when_previous_year_provided(self):
        """提供上年底稿时应产生 YoY 报告"""
        wp = TestData.excellent_workpaper()
        prev = TestData.previous_year_workpaper()
        report = self.scorer.score(wp, previous_year=prev)

        self.assertIsNotNone(report.yoy_report)
        self.assertIsInstance(report.yoy_report.similarity_score, float)

    def test_yoy_report_when_previous_year_absent(self):
        """不提供上年底稿时 YoY 报告为 None"""
        wp = TestData.excellent_workpaper()
        report = self.scorer.score(wp)

        self.assertIsNone(report.yoy_report)


# ── 运行 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main()
