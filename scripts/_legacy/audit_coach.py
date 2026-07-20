#!/usr/bin/env python3
"""
审计教练 (Audit Coach) — 对话式审计方案生成引擎

灵感来源: 360安全龙虾「龙虾教练」— 对话式训Agent
审计落地: 像跟资深审计合伙人聊天一样 → 自动生成方案/清单/风险/报告框架

用法:
  python scripts/audit_coach.py              # 交互式对话
  python scripts/audit_coach.py --quick       # 快速模式（最少5轮）
  python scripts/audit_coach.py --demo        # 演示模式（自动填入示例对话）
"""
from __future__ import annotations

import sys
import json
import textwrap
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output" / "coach"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
#  审计知识库
# ============================================================

KNOWLEDGE_BASE = {
    "绩效评价": {
        "依据": [
            "《预算法》及其实施条例",
            "《项目支出绩效评价管理办法》（财预〔2020〕10号）",
            "《第三方机构预算绩效评价业务监督管理暂行办法》",
            "相关专项资金管理办法",
        ],
        "风险领域": [
            ("决策合理性", "立项依据是否充分、绩效目标是否明确、预算编制是否科学"),
            ("资金管理", "资金拨付及时性、专款专用、是否存在截留挪用"),
            ("过程管理", "制度健全性、执行有效性、过程监控到位情况"),
            ("产出完成", "数量指标/质量指标/时效指标/成本指标的完成率"),
            ("效益实现", "经济效益/社会效益/生态效益/可持续影响/满意度"),
        ],
        "常见问题": [
            "绩效目标设置笼统、缺乏可量化指标",
            "专项资金被挤占挪用",
            "项目进度滞后、资金执行率偏低",
            "绩效自评流于形式、与实际偏差大",
            "满意度调查样本不足、代表性不强",
        ],
        "资料清单": [
            "项目立项批复文件及可行性研究报告",
            "专项资金管理办法及资金下达文件",
            "项目实施方案及绩效目标申报表",
            "财务账册、会计凭证、银行对账单",
            "项目合同、验收报告、决算资料",
            "绩效自评报告及佐证材料",
            "满意度调查原始问卷及统计结果",
        ],
    },
    "资产清查": {
        "依据": [
            "《行政事业性国有资产管理条例》",
            "《行政事业单位资产清查核实管理办法》",
            "《政府会计制度——行政事业单位会计科目和报表》",
            "本级财政部门资产清查工作通知",
        ],
        "风险领域": [
            ("账实相符", "账面资产与实际资产是否一致、盘盈盘亏及原因"),
            ("资产使用", "资产使用效益评估、闲置资产识别、低效运转"),
            ("资产处置", "报废报损程序是否合规、残值评估是否合理"),
            ("出租出借", "是否经过审批、是否签订协议、收益是否上缴"),
            ("制度建设", "资产管理制度是否健全、岗位设置是否合规"),
        ],
        "常见问题": [
            "已报废资产长期未核销，账实严重不符",
            "房屋建筑物闲置未提出盘活方案",
            "资产处置未按规定程序报批",
            "出借资产未签订使用协议、未收取使用费",
            "资产卡片信息不完整、更新不及时",
        ],
        "资料清单": [
            "资产台账、资产卡片（电子版）",
            "固定资产明细账、累计折旧明细账",
            "房屋建筑物产权证、土地使用权证",
            "资产报废报批文件及审批记录",
            "资产出租出借合同及收益上缴凭证",
            "近三年资产盘点记录及差异处理材料",
            "资产管理制度文件及岗位职责说明",
        ],
    },
    "专项债审计": {
        "依据": [
            "《地方政府专项债券发行管理暂行办法》",
            "《地方政府专项债券项目资金绩效管理办法》",
            "《关于加快地方政府专项债券发行使用有关工作的通知》",
            "项目实施方案及财务评价报告",
        ],
        "风险领域": [
            ("项目合规", "项目是否符合专项债支持领域、立项审批是否完备"),
            ("资金使用", "是否专款专用、是否按工程进度拨付、有无挪用"),
            ("收益测算", "项目收益与融资自求平衡是否真实可行"),
            ("信息披露", "项目信息是否及时准确公开"),
            ("偿债管理", "还本付息计划是否落实、偿债资金来源是否有保障"),
        ],
        "常见问题": [
            "项目前期论证不充分，立项条件不成熟",
            "专项债资金沉淀闲置，使用效率低下",
            "项目收益预测过于乐观，与实际情况偏差大",
            "资金用于非专项债支持领域",
            "项目建设进度严重落后于计划",
        ],
        "资料清单": [
            "项目可行性研究报告及批复",
            "专项债券实施方案（一案两书）",
            "财务评价报告和法律意见书",
            "项目收益与融资自求平衡测算表",
            "资金拨付凭证及银行流水",
            "项目合同及工程进度报告",
            "信息披露相关文件",
        ],
    },
    "经济责任审计": {
        "依据": [
            "《党政主要领导干部和国有企事业单位主要领导人员经济责任审计规定》（中办发〔2019〕45号）",
            "《审计法》",
            "被审计单位三定方案及职责分工文件",
        ],
        "风险领域": [
            ("贯彻执行", "党和国家经济方针政策、决策部署的贯彻落实情况"),
            ("重大决策", "重大经济事项决策、执行和效果"),
            ("财政财务", "财政财务收支的真实合法效益性"),
            ("内部控制", "内部管理制度的制定和执行"),
            ("廉政建设", "在经济活动中落实党风廉政建设责任情况"),
        ],
        "常见问题": [
            "重大经济事项未经集体决策",
            "预算执行率偏低、资金使用效益不高",
            "内控制度形同虚设、执行不到位",
            "政府采购未按规定程序执行",
            "以往审计发现问题未整改到位",
        ],
        "资料清单": [
            "被审计领导干部任职文件、述职报告",
            "任期内的重大决策会议纪要",
            "预算编报、批复、执行相关文件",
            "财务账册、会计凭证、决算报表",
            "内控制度汇编及执行记录",
            "政府采购项目台账及档案",
            "以往审计报告及整改资料",
        ],
    },
    "预算执行审计": {
        "依据": [
            "《预算法》及其实施条例",
            "《审计法》",
            "财政部门预算批复文件",
        ],
        "风险领域": [
            ("预算编制", "预算编制的科学性、完整性、细化程度"),
            ("预算执行", "预算执行率、预算调整合规性"),
            ("资金使用", "资金使用的合规性、安全性、效益性"),
            ("决算编报", "决算编报的真实性、准确性、完整性"),
            ("三公经费", "三公经费预算执行及公开情况"),
        ],
        "常见问题": [
            "预算编制不细化、随意性大",
            "无预算支出、超预算支出",
            "项目支出与基本支出混用",
            "年底突击花钱",
            "三公经费超预算、超标准",
        ],
        "资料清单": [
            "年度部门预算编制说明及批复文件",
            "预算调整的申请及批复文件",
            "财务账册、会计凭证、国库集中支付记录",
            "部门决算报表及编制说明",
            "三公经费支出明细及公开记录",
            "政府采购预算执行情况表",
        ],
    },
    "工程结算审核": {
        "依据": [
            "《建设工程价款结算暂行办法》",
            "《建设工程工程量清单计价规范》（GB50500）",
            "施工合同、招标文件、投标文件",
        ],
        "风险领域": [
            ("工程量", "工程量计算的准确性、现场与图纸一致性"),
            ("综合单价", "单价套用的合理性、合同内外单价区分"),
            ("变更签证", "工程变更的合理性、签证的真实性"),
            ("材料价差", "材料价格的取定依据、调价公式的正确性"),
            ("规费税金", "规费税金计取的合规性"),
        ],
        "常见问题": [
            "工程量多计、重计",
            "高套定额、单价异常",
            "变更签证手续不完善或事后补签",
            "材料价格取定缺乏依据",
            "结算金额超概算、超合同价",
        ],
        "资料清单": [
            "招标文件、投标文件、中标通知书",
            "施工合同及补充协议",
            "竣工图纸、施工图纸",
            "工程量计算书、结算书",
            "工程变更签证单、技术核定单",
            "材料价格确认单、认价单",
            "隐蔽工程验收记录、竣工验收报告",
        ],
    },
}


# ============================================================
#  对话状态机
# ============================================================

class ConversationEngine:
    """对话式访谈引擎"""

    def __init__(self, demo_mode: bool = False, quick_mode: bool = False):
        self.state = "greeting"
        self.answers = {
            "项目类型": "",
            "被审计单位": "",
            "审计期间": "",
            "资金规模": "",
            "委托方": "",
            "重点关注": "",
            "审计团队": "",
            "时间安排": "",
            "特殊要求": "",
        }
        self.questions_asked = 0
        self.demo_mode = demo_mode
        self.quick_mode = quick_mode
        self.history: list[tuple[str, str]] = []  # (coach说, 用户答)

        # Demo 答案（自动填入）
        self._demo_answers = {
            "项目类型": "绩效评价",
            "被审计单位": "XX市教育局",
            "审计期间": "2025年1月至12月",
            "资金规模": "5,800万元（市级财政专项资金）",
            "委托方": "XX市财政局",
            "重点关注": "资金使用合规性和产出质量，特别是偏远学校的资金到位情况",
            "审计团队": "项目负责人1人+注册会计师2人+助理2人",
            "时间安排": "进场2周，总计30天完成",
            "特殊要求": "需要出具分学校的绩效评分排名",
        }

    def ask(self, user_input: str = "") -> str:
        """接收用户输入，返回教练的下一句话"""
        if user_input:
            self._record_answer(user_input)
            self.history.append(("coach_ack", self._acknowledge()))
        return self._next_question()

    def _record_answer(self, user_input: str):
        """将用户输入保存到对应字段"""
        # 状态→答案字段映射：当前状态对应刚问过的问题（即刚被回答了的问题）
        # 注意：greeting 后状态是"项目类型"，所以项目类型答案应在"项目类型"状态时记录
        mapping = {
            "greeting": "项目类型",  # 只在第一次调用时生效
            "项目类型": "项目类型",
            "被审计单位": "被审计单位",
            "审计期间": "审计期间",
            "资金规模": "资金规模",
            "委托方": "委托方",
            "重点关注": "重点关注",
            "审计团队": "审计团队",
            "时间安排": "时间安排",
            "特殊要求": "特殊要求",
        }
        prev_state = self.state if self.state != "generating" else "特殊要求"
        
        # 特殊处理：首次调用时 state 可能还是 greeting
        if self.state == "greeting":
            prev_state = "greeting"
            
        field = mapping.get(prev_state)
        if field:
            # 演示模式下使用预设答案
            if self.demo_mode and field in self._demo_answers:
                self.answers[field] = self._demo_answers[field]
            else:
                self.answers[field] = user_input
        self.questions_asked += 1

    def _acknowledge(self) -> str:
        """对用户输入的自然回应"""
        acks = {
            "greeting": None,
            "项目类型": "好的，{ans}——这个类型我熟，重点和坑都清楚。",
            "被审计单位": "明白了，{ans}。",
            "审计期间": "{ans}，记下了。",
            "资金规模": "资金量{ans}，规模不小，得盯紧点。",
            "委托方": "{ans}委托的，了解。",
            "重点关注": "重点关注{ans}，我会在方案里标注。",
            "审计团队": "团队配置{ans}，合理。",
            "时间安排": "时间{ans}，节奏比较紧凑。",
            "特殊要求": "特殊要求收到了。所有信息齐了，我来汇总。",
        }
        ack = acks.get(self.state, "")
        if ack:
            ans_field = self.state if self.state != "greeting" else "项目类型"
            return ack.format(ans=self.answers.get(ans_field, "这项"))
        return ""

    def _next_question(self) -> str:
        """根据当前状态返回下一个问题"""
        demo_a = self._demo_answers if self.demo_mode else {}

        if self.state == "greeting":
            self.state = "项目类型"
            return textwrap.dedent(f"""\
                [*] 你好，我是融策审计教练。
                帮你把模糊的审计需求梳理成一套完整的方案、清单和报告框架。

                咱们一步步来——先从项目类型开始：
                【1】绩效评价  【2】资产清查  【3】专项债审计
                【4】经济责任审计  【5】预算执行审计  【6】工程结算审核
                {f'(演示模式，自动选: {demo_a["项目类型"]})' if self.demo_mode else ''}
            """).strip()

        questions = {
            "项目类型": f"第二条：被审计单位是谁？（全称）{f' [{demo_a.get("被审计单位", "")}]' if self.demo_mode else ''}",
            "被审计单位": f"审计期间是什么？{f' [{demo_a.get("审计期间", "")}]' if self.demo_mode else ''}",
            "审计期间": f"涉及的资金规模和来源？{f' [{demo_a.get("资金规模", "")}]' if self.demo_mode else ''}",
            "资金规模": f"谁委托的？（委托单位全称）{f' [{demo_a.get("委托方", "")}]' if self.demo_mode else ''}",
            "委托方": "__SHOW_RISKS__",  # 标记：需要展示风险领域
        }

        next_state_map = {
            "项目类型": "被审计单位", "被审计单位": "审计期间",
            "审计期间": "资金规模", "资金规模": "委托方",
            "委托方": "重点关注",
        }

        if self.state in questions:
            q = questions[self.state]
            self.state = next_state_map[self.state]
            if q == "__SHOW_RISKS__":
                # 展示风险领域并询问重点关注（此时state已变为"重点关注"）
                ptype = self.answers["项目类型"]
                kb = KNOWLEDGE_BASE.get(ptype, {})
                risks = kb.get("风险领域", [])
                risk_list = "\n".join(f"  - {r[0]}：{r[1]}" for r in risks)
                return textwrap.dedent(f"""\
                    根据{ptype}的特点，常见风险领域有：
                {risk_list}

                    你这次重点关注哪些方面？{f' [{demo_a.get("重点关注", "")}]' if self.demo_mode else ''}（直接说或选以上领域都可以）
                """).strip()
            return q

        if self.state == "重点关注":
            self.state = "审计团队"
            return f"审计团队怎么配置？{f' [{demo_a.get("审计团队", "")}]' if self.demo_mode else ''}（如：项目负责人1人+主审2人+助理3人）"

        if self.state == "审计团队":
            self.state = "时间安排"
            return f"时间安排？{f' [{demo_a.get("时间安排", "")}]' if self.demo_mode else ''}（如：预计进场X天，总计X天）"

        if self.state == "时间安排":
            self.state = "特殊要求"
            return f"最后一条：还有什么特殊要求吗？{f' [{demo_a.get("特殊要求", "")}]' if self.demo_mode else ''}（没有直接说「无」）"

        if self.state == "特殊要求":
            self.state = "generating"
            return "[OK] 信息收集完毕！正在为你生成..."

        return ""


# ============================================================
#  方案生成器
# ============================================================

class OutputGenerator:
    """根据访谈结果生成审计方案、清单、风险提示、报告框架"""

    def __init__(self, answers: dict):
        self.a = answers
        self.ptype = answers["项目类型"]
        self.kb = KNOWLEDGE_BASE.get(self.ptype, {})

    def generate_all(self) -> dict[str, str]:
        return {
            "审计实施方案": self._gen_plan(),
            "资料需求清单": self._gen_checklist(),
            "风险提示清单": self._gen_risk_alert(),
            "报告框架": self._gen_report_framework(),
        }

    def _gen_plan(self) -> str:
        """生成审计实施方案"""
        risks = "\n".join(f"（{i+1}）{r[0]}——{r[1]}" for i, r in enumerate(self.kb.get("风险领域", [])))
        basis = "\n".join(f"  - {b}" for b in self.kb.get("依据", []))

        return textwrap.dedent(f"""\
            # 审计实施方案

            ## 一、审计依据
            {basis}

            ## 二、被审计单位
            {self.a['被审计单位']}

            ## 三、审计期间
            {self.a['审计期间']}

            ## 四、审计目标
            通过对{self.a['被审计单位']}{self.a['审计期间']}{self.ptype}情况进行审计，重点关注{self.a['重点关注']}，揭示存在的问题和风险，提出改进建议，促进规范管理和提高资金使用效益。

            ## 五、审计范围
            资金范围：{self.a['资金规模']}
            业务范围：{self.ptype}涉及的全部业务事项

            ## 六、审计内容和重点
            {risks}
            **本次重点**：{self.a['重点关注']}

            ## 七、审计方法
            综合运用资料审查法、数据分析法、现场勘查法、访谈调研法、函证法、穿行测试法、对比分析法、复核计算法等。

            ## 八、人员配置
            {self.a['审计团队']}

            ## 九、时间安排
            {self.a['时间安排']}

            ## 十、工作要求
            1. 严格遵守审计准则和职业道德规范
            2. 做好审计底稿编制，做到一事一稿、证据充分
            3. 加强与被审计单位的沟通协调
            4. 及时向委托方报告重大问题和审计进展
            5. 做好保密工作，不得泄露审计过程中获取的信息
            {"6. " + self.a['特殊要求'] if self.a['特殊要求'] and self.a['特殊要求'] != '无' else ''}

            ---
            编制单位：四川融策会计师事务所
            编制日期：{datetime.now().strftime('%Y年%m月%d日')}
        """).strip()

    def _gen_checklist(self) -> str:
        """生成资料需求清单"""
        items = self.kb.get("资料清单", [])
        lines = [f"# 资料需求清单\n\n致：{self.a['被审计单位']}\n\n根据审计工作需要，请贵单位于收到本清单后5个工作日内提供以下资料：\n"]
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item}")
        lines.append(f"\n---\n四川融策会计师事务所\n{datetime.now().strftime('%Y年%m月%d日')}")
        return "\n".join(lines)

    def _gen_risk_alert(self) -> str:
        """生成风险提示清单"""
        lines = [f"# 风险提示清单\n\n项目：{self.a['被审计单位']} {self.a['审计期间']} {self.ptype}\n"]
        lines.append("## [HIGH] 高风险\n")
        problems = self.kb.get("常见问题", [])
        for i, p in enumerate(problems[:3], 1):
            lines.append(f"{i}. {p}  [!] 涉及金额较大 / 性质严重 / 整改难度高")
        lines.append("\n## [MID] 中风险\n")
        for i, p in enumerate(problems[3:5], 4):
            lines.append(f"{i-3}. {p}  [!] 需关注但影响相对可控")
        lines.append("\n## [LOW] 低风险\n")
        if len(problems) > 5:
            for i, p in enumerate(problems[5:], 6):
                lines.append(f"{i-5}. {p}  [!] 管理层面可优化的环节")
        else:
            lines.append("1. 制度完善性、档案管理规范性等常规管理事项")
        lines.append(f"\n## 本次重点关注\n{self.a['重点关注']}")
        return "\n".join(lines)

    def _gen_report_framework(self) -> str:
        """生成报告框架（Markdown，可直接喂给 audit_doc_formatter）"""
        risks = self.kb.get("风险领域", [])
        risk_sections = ""
        for r in risks[:4]:
            risk_sections += f"\n# {r[0]}\n[请根据审计发现描述{r[0]}方面的问题，包括具体事项、涉及金额、违反的规定等]\n"

        return textwrap.dedent(f"""\
            # 核心发现摘要
            >  [请填写最重要的审计发现1]
            >  [请填写最重要的审计发现2]
            >  [请填写最重要的审计发现3]

            # 一、项目概述
            根据{self.a['委托方']}的委托，四川融策会计师事务所对{self.a['被审计单位']}{self.a['审计期间']}{self.ptype}进行了审计。本次审计涉及资金{self.a['资金规模']}。审计组由{self.a['审计团队']}组成，历时{self.a['时间安排']}。

            # 1.1 项目背景
            [请填写项目立项背景、资金构成、实施内容等基本信息]

            # {self.a['审计期间']}{self.ptype}目标
            [请结合审计目标填写]

            # 审计方法
            [请填写具体采用的方法和覆盖范围]

            # 二、项目总体情况
            [请概括项目总体评价，包括资金使用情况、项目完成情况等]

            {risk_sections}
            # 四、问题发现汇总
            [请汇总所有发现问题，按风险等级分类]

            # 五、改进建议
            [请针对发现问题提出具体、可操作的建议]
        """).strip()


# ============================================================
#  交互式对话
# ============================================================

def run_interactive():
    """交互模式 —— 逐轮对话"""
    print("""
╔═══════════════════════════════════════════╗
║       [+] 融策审计教练 (Audit Coach)        ║
║  像跟资深审计合伙人聊天一样，梳理审计方案     ║
╚═══════════════════════════════════════════╝
""")
    engine = ConversationEngine()
    print(f"\n{engine.ask()}\n")

    while engine.state != "generating":
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("q", "退出", "quit"):
            print("随时回来继续 [*]")
            return
        response = engine.ask(user_input)
        print(f"\n{response}\n")

    # 生成
    gen = OutputGenerator(engine.answers)
    outputs = gen.generate_all()

    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    prefix = f"{engine.answers['被审计单位'][:8]}_{engine.ptype}"

    for name, content in outputs.items():
        fname = f"{prefix}_{name}_{timestamp}.md"
        fpath = OUTPUT_DIR / fname
        fpath.write_text(content, encoding="utf-8")
        print(f"  [FILE] {name}: {fpath.name}")

    # 整合输出
    combined = "\n\n---\n\n".join(f"# {k}\n\n{v}" for k, v in outputs.items())
    combined_path = OUTPUT_DIR / f"{prefix}_全部方案_{timestamp}.md"
    combined_path.write_text(combined, encoding="utf-8")
    print(f"\n  [PKG] 汇总: {combined_path.name}")

    # 询问是否导出 docx
    print(f"\n[LIST] 要一键导出为 Word 格式报告吗？(y/n)")
    choice = input("> ").strip().lower()
    if choice in ("y", "yes", "是"):
        try:
            sys.path.insert(0, str(ROOT / "scripts"))
            from audit_doc_formatter import TEMPLATES, ContentParser, SectionMatcher, FormatterEngine

            template = TEMPLATES.get(engine.answers["项目类型"], TEMPLATES["通用审计"])
            sections = ContentParser.parse(outputs["报告框架"])
            mapping = SectionMatcher.match(sections, template)
            engine2 = FormatterEngine(template)
            docx_path = OUTPUT_DIR / f"{prefix}_报告框架_{timestamp}.docx"
            engine2.format(mapping, output_path=docx_path)
            print(f"  [OK] Word 报告: {docx_path}")
        except Exception as e:
            print(f"  [!] 导出 Word 失败: {e}")

    print(f"\n[DIR] 所有文件在: {OUTPUT_DIR}")


def run_demo():
    """演示模式 — 自动填入示例答案，跑完整流程"""
    print("""
╔═══════════════════════════════════════════╗
║    [+] 审计教练 — 演示模式                 ║
╚═══════════════════════════════════════════╝
""")
    engine = ConversationEngine(demo_mode=True)
    print(f"\n{engine.ask()}\n")
    print("  [演示模式: 自动填入答案，跳过等待]")
    import time

    while engine.state != "generating":
        # 自动填入演示答案
        time.sleep(0.3)
        response = engine.ask("demo")
        if engine.state == "generating":
            print(f"\n{response}\n")
            break
        print(f"  >>> {response}\n")

    gen = OutputGenerator(engine.answers)
    outputs = gen.generate_all()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # 保存所有输出
    saved_files = []
    for name, content in outputs.items():
        fname = f"DEMO_{engine.answers['被审计单位']}_{name}_{timestamp}.md"
        fpath = OUTPUT_DIR / fname
        fpath.write_text(content, encoding="utf-8")
        saved_files.append((name, fpath))

    # 显示摘要
    print("=" * 65)
    print(f"  项目: {engine.answers['被审计单位']} {engine.answers['审计期间']} {engine.answers['项目类型']}")
    print("=" * 65)
    for name, path in saved_files:
        size = path.stat().st_size
        print(f"  [OK] {name}: {path.name} ({size:,} 字节)")

    # 预览报告框架
    print("\n[LIST] === 报告框架预览（前800字） ===")
    preview = outputs["报告框架"][:800]
    print(preview)
    if len(outputs["报告框架"]) > 800:
        print("  ...(完整内容见文件)")

    # 导出 docx
    print("\n[FILE] 正在导出 Word 格式...")
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from audit_doc_formatter import TEMPLATES, ContentParser, SectionMatcher, FormatterEngine

        template = TEMPLATES.get(engine.answers["项目类型"], TEMPLATES["通用审计"])
        sections = ContentParser.parse(outputs["报告框架"])
        mapping = SectionMatcher.match(sections, template)
        formatter = FormatterEngine(template)
        docx_path = OUTPUT_DIR / f"DEMO_{engine.answers['被审计单位']}_报告_{timestamp}.docx"
        formatter.format(mapping, output_path=docx_path)
        print(f"  [OK] Word 报告: {docx_path.name}")
    except Exception as e:
        print(f"  [!] Word 导出失败: {e}")

    print(f"\n[DIR] 所有文件在: {OUTPUT_DIR}")
    print(f"   可以直接给客户看方案框架和风险清单了。")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="融策审计教练 — 对话式审计方案生成")
    parser.add_argument("--demo", action="store_true", help="演示模式（自动填入示例）")
    parser.add_argument("--quick", action="store_true", help="快速模式")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
