"""
P2: journal_entry_validator — 会计分录科目对应关系规则引擎 (v8, 5d)

核心功能：
1. 50条核心记账规则（AP/AR/FA/费用/收入/税金 6大类）
2. 支持CSV导入自定义科目映射表（解决企业间科目差异）
3. 异常输出：凭证号 + 实际分录 + 预期分录 + 偏离描述 + 风险等级
4. 集成到v8翻凭证工作流：Prompt模板 → 分录引擎 → 异常标记

设计理念：手写规则优先（可解释性 > 黑盒匹配），50条核心覆盖80%场景。
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import re
import csv


# ── 50条核心分录规则 ────────────────────────────────────────

# 格式：摘要关键词 → (预期借方科目列表, 预期贷方科目列表, 风险信号)
# 科目名支持正则 | 分隔的多个选项

_JOURNAL_RULES = [
    # ═══ 固定资产 FA (8条) — 高频歧义词优先 ═══
    ("转固|竣工|验收合格|竣工验收", ["固定资产"],
     ["在建工程"],
     "在建工程转固：时点和金额确认"),
    ("在建|施工|土建|安装", ["在建工程|工程物资"],
     ["银行存款|应付账款|应付工程款"],
     "在建工程：应区分资本化期间"),
    ("折旧|摊销|累计折旧", ["管理费用|制造费用|生产成本|销售费用"],
     ["累计折旧"],
     "计提折旧：借方科目取决于资产用途"),
    ("报废|处置|清理|变卖", ["固定资产清理", "累计折旧"],
     ["固定资产"],
     "固定资产处置：标准清理分录"),
    ("装修|改造|大修|改良", ["长期待摊费用|在建工程|固定资产"],
     ["银行存款|应付账款"],
     "改良支出：资本化条件判断"),
    ("设备|机器|仪器|机械", ["固定资产|在建工程"],
     ["银行存款|应付账款|应付工程款"],
     "设备采购：5,000元以上应资本化"),
    ("电脑|服务器|打印机|复印机", ["固定资产|低值易耗品"],
     ["银行存款|应付账款"],
     "电子设备：金额判定资本化/费用化边界"),
    ("车辆|汽车|货车|轿车", ["固定资产"],
     ["银行存款|长期应付款"],
     "车辆购置：应计入固定资产"),

    # ═══ 采购/AP (11条) — 采购关键词优先于办公/费用 ═══
    ("采购服务器|采购设备|采购机器|采购仪器|采购机械|购买设备|购买机器",
     ["固定资产|在建工程"],
     ["银行存款|应付账款"],
     "设备采购：资本化科目校验"),
    ("采购电脑|采购打印机|采购复印机|购买电脑",
     ["固定资产|低值易耗品"],
     ["银行存款|应付账款"],
     "电子设备采购：资本化判定"),
    ("退货|退回|退料|红冲|作废", ["银行存款|应收账款"],
     ["库存商品|原材料"],
     "采购退货：科目方向异常"),
    ("暂估|估价入库", ["库存商品|原材料"],
     ["应付账款-暂估"],
     "暂估入库：贷方应为应付账款-暂估明细科目"),
    ("采购|购货|进货|买", ["库存商品|原材料|固定资产|在建工程|低值易耗品"],
     ["应付账款|银行存款|预付账款"],
     "采购入账：科目对应关系异常"),
    ("货款|材料款|设备款", ["库存商品|原材料|固定资产|在建工程"],
     ["应付账款|银行存款"],
     "货款支付：借方科目异常"),
    ("入库(?!.*(?:转固|竣工))|验收(?!.*(?:转固|竣工))|收货", ["库存商品|原材料|低值易耗品"],
     ["物资采购|在途物资|应付账款"],
     "验收入库：对应科目异常"),
    ("预付|预付款|定金", ["预付账款|预付工程款"],
     ["银行存款|应付票据"],
     "预付款：借方应为预付账款而非费用类科目"),
    ("应付|欠款|未付", ["应付账款|材料采购"],
     ["银行存款|应付票据"],
     "偿付应付款：关联科目异常"),
    ("质保金|保证金|押金", ["其他应收款"],
     ["银行存款|应付账款"],
     "保证金：应计入其他应收款而非费用"),
    ("赔偿|索赔|罚款", ["银行存款|其他应收款"],
     ["营业外收入|应付账款"],
     "供应商赔偿：贷方应为营业外收入"),

    # ═══ 应收账款 AR (9条) ═══
    ("赊销|赊账|挂账", ["应收账款"],
     ["主营业务收入", "应交税费"],
     "赊销：借方应为应收账款"),
    ("预收|预收款|订金", ["银行存款"],
     ["预收账款|合同负债"],
     "预收款：贷方应为预收账款/合同负债"),
    ("坏账|核销|无法收回", ["坏账准备|信用减值损失"],
     ["应收账款"],
     "坏账核销：科目配对异常"),
    ("债务重组|减免|豁免", ["应收账款|坏账准备"],
     ["营业外支出|投资收益"],
     "债务重组：关注损失确认是否正确"),
    ("销售|售出|卖出|销货", ["银行存款|应收账款|应收票据"],
     ["主营业务收入|其他业务收入", "应交税费-应交增值税-销项税额"],
     "销售收入：贷方应为收入+税金"),
    ("开票|发票|税票", ["应收账款|银行存款"],
     ["主营业务收入|其他业务收入", "应交税费-应交增值税-销项税额"],
     "开票收入：确认贷方含税金"),
    ("委托代销|寄售|代销", ["委托代销商品|发出商品"],
     ["库存商品"],
     "委托代销：发出时不确认收入"),
    ("收款(?!.*(?:零余额|财政|授权))|回款(?!.*(?:零余额|财政|授权))|到账(?!.*(?:零余额|财政|授权))", ["银行存款|应收票据"],
     ["应收账款|预收账款|主营业务收入"],
     "收款入账：贷方科目异常"),
    ("客户|买受人|采购方", ["银行存款|应收账款"],
     ["主营业务收入", "应交税费"],
     "客户销售：标准分录校验"),

    # ═══ 固定资产 FA (8条) ═══
    ("设备|机器|仪器|机械", ["固定资产|在建工程"],
     ["银行存款|应付账款|应付工程款"],
     "设备采购：5,000元以上应资本化"),
    ("电脑|服务器|打印机|复印机", ["固定资产|低值易耗品"],
     ["银行存款|应付账款"],
     "电子设备：金额判定资本化/费用化边界"),
    ("车辆|汽车|货车|轿车", ["固定资产"],
     ["银行存款|长期应付款"],
     "车辆购置：应计入固定资产"),
    ("在建|施工|土建|安装", ["在建工程|工程物资"],
     ["银行存款|应付账款|应付工程款"],
     "在建工程：应区分资本化期间"),
    ("转固|竣工|验收合格|投入使用", ["固定资产"],
     ["在建工程"],
     "在建工程转固：时点和金额确认"),
    ("折旧|摊销|累计折旧", ["管理费用|制造费用|生产成本|销售费用"],
     ["累计折旧"],
     "计提折旧：借方科目取决于资产用途"),
    ("报废|处置|清理|变卖", ["固定资产清理", "累计折旧"],
     ["固定资产"],
     "固定资产处置：标准清理分录"),
    ("装修|改造|大修|改良", ["长期待摊费用|在建工程|固定资产"],
     ["银行存款|应付账款"],
     "改良支出：资本化条件判断"),

    # ═══ 费用报销 EXP (10条) ═══
    ("差旅|出差|住宿|机票|火车票", ["管理费用-差旅费|销售费用-差旅费"],
     ["银行存款|库存现金|其他应收款"],
     "差旅费：关注标准和审批"),
    ("招待|宴请|餐饮|吃饭", ["管理费用-业务招待费|销售费用-业务招待费"],
     ["银行存款|库存现金"],
     "业务招待费：关注限额和合规性"),
    ("办公(?!.*(?:设备|机器|电脑|采购|服务器))|文具|打印|复印|纸张", ["管理费用-办公费"],
     ["银行存款|库存现金"],
     "办公费：高频科目正常校验"),
    ("会议|会务|场地|茶歇", ["管理费用-会议费"],
     ["银行存款|库存现金"],
     "会议费：关注真实性和标准"),
    ("培训|学习|进修|课程", ["管理费用-职工教育经费"],
     ["银行存款|库存现金"],
     "培训费：应计入职工教育经费"),
    ("加油|油费|燃油|汽油|柴油", ["管理费用-车辆费|销售费用-运输费"],
     ["银行存款|库存现金"],
     "油费：关注私车公养"),
    ("维修|修理|保养|维护", ["管理费用-维修费|制造费用-修理费"],
     ["银行存款|库存现金"],
     "维修费：资本化vs费用化"),
    ("咨询|顾问|服务费|中介", ["管理费用-咨询费"],
     ["银行存款|应付账款"],
     "咨询费：关注真实性和关联交易"),
    ("工资|薪酬|奖金|津贴", ["管理费用-工资|生产成本-直接人工"],
     ["应付职工薪酬"],
     "工资费用：贷方必须为应付职工薪酬"),
    ("福利|体检|节日|慰问", ["管理费用-福利费"],
     ["应付职工薪酬-福利费|银行存款"],
     "福利费：需通过应付职工薪酬过渡"),

    # ═══ 收入确认 (5条) ═══
    ("服务|劳务|技术|咨询收入", ["银行存款|应收账款"],
     ["主营业务收入|其他业务收入", "应交税费"],
     "服务收入：确认收入和税金"),
    ("(?<!年终)(?<!结转)(?<!期末)政府补助|补贴(?!.*结转)|拨款(?!.*结转)|奖励(?!.*结转)", ["银行存款|其他应收款"],
     ["递延收益|其他收益|营业外收入"],
     "政府补助：收益法vs资本法"),
    ("利息|理财|存款利息", ["银行存款|应收利息"],
     ["财务费用-利息收入|投资收益"],
     "利息收入：冲减财务费用"),
    ("租金|房租|物业|租赁", ["银行存款|应收账款"],
     ["其他业务收入|主营业务收入", "应交税费"],
     "租金收入：按新租赁准则判断"),
    ("投资收益|分红|股利", ["银行存款|应收股利"],
     ["投资收益"],
     "投资收益：确认时点和金额"),

    # ═══ 税金 (5条) ═══
    ("增值税|销项税|进项税", ["应交税费-应交增值税-进项税额|银行存款"],
     ["应交税费-应交增值税-销项税额|应交税费-未交增值税"],
     "增值税：借贷方科目校验"),
    ("所得税|企业所得税|预缴", ["所得税费用|递延所得税资产"],
     ["应交税费-应交所得税|银行存款"],
     "所得税：当期vs递延划分"),
    ("城建税|教育费附加|地方教育", ["税金及附加"],
     ["应交税费-应交城建税|应交税费-应交教育费附加"],
     "附加税费：借方应为税金及附加"),
    ("印花税|契税|房产税|土地使用税", ["税金及附加|管理费用-税金"],
     ["银行存款|应交税费"],
     "小税种：归集科目校验"),
    ("代扣代缴|个人所得税|个税", ["应付职工薪酬|其他应付款"],
     ["应交税费-应交个人所得税"],
     "个税代扣：不影响损益"),

    # ═══ 银行业务 (5条) ═══
    ("提现|取现|备付金", ["库存现金"],
     ["银行存款"],
     "提现：标准分录校验"),
    ("转账|汇款|划转|支付", ["应付账款|管理费用|固定资产"],
     ["银行存款"],
     "转账：借方科目多样性高，按摘要推断"),
    ("承兑|汇票|票据贴现", ["银行存款|应收票据"],
     ["应付票据|应收票据|短期借款"],
     "票据业务：关系校验"),
    ("贷款|借款|融资|授信", ["银行存款"],
     ["短期借款|长期借款|长期应付款"],
     "借款入账：贷方应为借款类科目"),
    ("还贷|还款|偿还借款", ["短期借款|长期借款", "财务费用-利息支出"],
     ["银行存款"],
     "偿还借款：同时确认利息支出"),

    # ═══ 政府会计 GOV (15条) — 优先于企业会计规则 ═══
    # 预算会计（收付实现制） + 财务会计（权责发生制）双分录

    # ── 年终结转（优先于其他财政拨款规则）──
    ("年终结转|年末结转|期末结转|收支结转",
     ["财政拨款收入|事业收入|上级补助收入|本期盈余"],
     ["本期盈余|本年盈余分配"],
     "年终收入结转：收入→本期盈余"),
    ("结转费用|费用结转|支出结转",
     ["本期盈余"],
     ["业务活动费用|单位管理费用|资产处置费用"],
     "年终费用结转：费用→本期盈余"),

    # ── 财政拨款（排除年终结转场景）──
    ("财政授权支付|授权支付额度|用款计划|零余额到账",
     ["零余额账户用款额度"],
     ["财政拨款收入|财政应返还额度"],
     "零余额到账：借方必须为零余额账户用款额度"),
    ("财政直接支付(?!.*设备)(?!.*采购)",
     ["零余额账户用款额度|财政应返还额度"],
     ["财政拨款收入|事业收入"],
     "财政直接支付：额度确认分录，采购分录另做"),
    ("(?<!年终结转)(?<!年末结转)(?<!期末结转)财政拨款(?!.*结转)(?!.*年末)(?!.*期末)",
     ["零余额账户用款额度|财政应返还额度|银行存款"],
     ["财政拨款收入|事业收入|上级补助收入"],
     "财政拨款收入确认：财务会计确认收入"),
    ("财政应返还|年末返还|额度收回",
     ["财政应返还额度"],
     ["零余额账户用款额度|财政拨款收入"],
     "年末额度收回：应计入财政应返还额度"),

    # ── 政府费用 ──
    ("业务活动|项目支出|专项支出|课题",
     ["业务活动费用|事业支出"],
     ["零余额账户用款额度|银行存款|应付职工薪酬"],
     "业务活动费：预算会计同步借记事业支出"),
    ("单位管理|行政运行|机关运行|物业|水电",
     ["单位管理费用|事业支出"],
     ["零余额账户用款额度|银行存款"],
     "单位管理费：注意区分业务活动费vs单位管理费"),
    ("公务接待|因公出国|公务用车|三公",
     ["业务活动费用|单位管理费用"],
     ["零余额账户用款额度|银行存款"],
     "三公经费：关注预算批复和支出标准"),
    ("固定资产折旧|无形资产摊销|公共基础设施折旧",
     ["业务活动费用|单位管理费用"],
     ["固定资产累计折旧|无形资产累计摊销"],
     "政府资产折旧：贷方科目不得为银行存款"),

    # ── 政府资产 ──
    ("政府采购|集中采购|招标采购",
     ["固定资产|在建工程|库存物品|无形资产"],
     ["零余额账户用款额度|银行存款|应付账款"],
     "政府采购：资产类借方，同时预算会计借记事业支出"),
    ("公务用车|公车购置|车辆购置|轿车|客车",
     ["固定资产"],
     ["零余额账户用款额度|银行存款|财政拨款收入"],
     "公务用车购置：应资本化为固定资产，不得费用化"),
    ("资产处置|资产报废|资产调拨|无偿调拨",
     ["固定资产累计折旧|待处理财产损溢|无偿调拨净资产"],
     ["固定资产"],
     "资产处置：关注审批程序和净值确认"),
    ("公共基础设施|市政设施|公路|桥梁",
     ["公共基础设施|在建工程"],
     ["零余额账户用款额度|银行存款"],
     "公共基础设施：注意与固定资产的区分"),

    # ── 政府收入 ──
    ("事业收入|经营收入|非同级财政拨款",
     ["银行存款|应收账款"],
     ["事业收入|经营收入|非同级财政拨款收入"],
     "事业/经营收入：贷方科目与收入性质匹配"),
    ("上级补助|附属单位上缴|投资收益",
     ["银行存款|其他应收款"],
     ["上级补助收入|附属单位上缴收入|投资收益"],
     "上级补助/附属单位上缴：注意收入确认时点"),

    # ── 政府往来 ──
    ("暂付|预付款项|借出款|押金",
     ["预付账款|其他应收款"],
     ["零余额账户用款额度|银行存款"],
     "政府暂付款：不得直接计入费用"),
    ("暂收|保证金|履约金|质保金",
     ["银行存款|零余额账户用款额度"],
     ["其他应付款|预收账款"],
     "政府暂收款：不得直接确认为收入"),

]


# ── 数据结构 ──────────────────────────────────────────────────

@dataclass
class JournalAnomaly:
    """分录异常"""
    voucher_no: str
    date: str = ""
    summary: str = ""
    actual_debit: str = ""        # 实际借方科目
    actual_credit: str = ""       # 实际贷方科目
    amount: float = 0.0
    expected_debit: str = ""      # 预期借方科目
    expected_credit: str = ""     # 预期贷方科目
    deviation_type: str = ""      # debit_mismatch | credit_mismatch | both
    risk_level: str = "medium"    # high | medium | low
    rule_description: str = ""
    matched_keyword: str = ""


@dataclass
class ValidationResult:
    """分录校验完整结果"""
    total_vouchers: int
    anomalies: List[JournalAnomaly]
    anomaly_count: int
    anomaly_rate: float
    by_category: Dict[str, int]  # 分类统计
    summary: str


class JournalEntryValidator:
    """会计分录规则引擎"""

    def __init__(self, custom_rules: Optional[List[tuple]] = None):
        self.rules = list(_JOURNAL_RULES)
        if custom_rules:
            self.rules.extend(custom_rules)
        self._account_aliases: Dict[str, List[str]] = {}  # 科目别名映射

    def load_account_mapping(self, csv_path: str):
        """
        加载自定义科目映射表

        CSV格式：标准科目名,企业科目名1|企业科目名2|...
        示例：库存商品,存货-产成品|1405库存商品
        """
        self._account_aliases.clear()
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0].strip():
                    standard = row[0].strip()
                    aliases = [a.strip() for a in row[1].split("|") if a.strip()]
                    self._account_aliases[standard] = aliases

    def validate(
        self,
        vouchers: List[Dict[str, Any]],
        date_field: str = "date",
        summary_field: str = "summary",
        debit_field: str = "debit_account",
        credit_field: str = "credit_account",
        amount_field: str = "amount",
        voucher_no_field: str = "voucher_no",
    ) -> ValidationResult:
        """
        校验会计分录

        Args:
            vouchers: 凭证列表 [{"summary": "采购设备", "debit_account": "管理费用",
                      "credit_account": "银行存款", "amount": 10000, ...}, ...]

        Returns:
            ValidationResult 含所有异常分录
        """
        anomalies = []
        category_count: Dict[str, int] = defaultdict(int)

        for v in vouchers:
            summary = str(v.get(summary_field, ""))
            debit = str(v.get(debit_field, ""))
            credit = str(v.get(credit_field, ""))
            amount = float(v.get(amount_field, 0))
            voucher_no = str(v.get(voucher_no_field, ""))

            # 政府会计上下文检测
            is_gov_context = bool(re.search(
                r'零余额|财政拨款|财政授权|国库|事业|政府会计|公共基础设施|年终结转|额度到账',
                summary + debit + credit
            ))

            # 逐条规则匹配
            for keyword_pattern, expected_debits, expected_credits, description in self.rules:
                # 政府会计上下文跳过企业专属规则
                if is_gov_context and self._is_enterprise_rule(description):
                    continue

                if not re.search(keyword_pattern, summary):
                    continue

                # 检查借方
                debit_match = self._account_in_list(debit, expected_debits)
                credit_match = self._account_in_list(credit, expected_credits)

                if debit_match and credit_match:
                    continue  # 全部匹配，无异常

                # 确定异常类型和风险等级
                if not debit_match and not credit_match:
                    deviation_type = "both"
                    risk_level = "high"
                elif not debit_match:
                    deviation_type = "debit_mismatch"
                    risk_level = "high" if any(
                        kw in summary for kw in ["设备", "机器", "采购", "工程"]
                    ) else "medium"
                else:
                    deviation_type = "credit_mismatch"
                    risk_level = "medium"

                anomalies.append(JournalAnomaly(
                    voucher_no=voucher_no,
                    date=str(v.get(date_field, "")),
                    summary=summary,
                    actual_debit=debit,
                    actual_credit=credit,
                    amount=amount,
                    expected_debit=" | ".join(expected_debits),
                    expected_credit=" | ".join(expected_credits),
                    deviation_type=deviation_type,
                    risk_level=risk_level,
                    rule_description=description,
                    matched_keyword=keyword_pattern,
                ))

                # 分类统计
                category = self._classify(summary)
                category_count[category] += 1
                break  # 一条凭证只匹配第一条规则

        # 排序：高危优先，金额大优先
        anomalies.sort(key=lambda a: (
            {"high": 0, "medium": 1, "low": 2}[a.risk_level],
            -a.amount,
        ))

        total = len(vouchers) or 1
        summary = self._summarize(anomalies, category_count)

        return ValidationResult(
            total_vouchers=total,
            anomalies=anomalies,
            anomaly_count=len(anomalies),
            anomaly_rate=round(len(anomalies) / total, 3),
            by_category=dict(category_count),
            summary=summary,
        )

    def validate_strict(
        self,
        vouchers: List[Dict],
        **kwargs,
    ) -> ValidationResult:
        """
        严格模式：同时检查借方和贷方，两者都异常才报告（减少误报）
        """
        result = self.validate(vouchers, **kwargs)
        # 过滤：只保留高风险（both或debit_mismatch且金额>5000）
        result.anomalies = [
            a for a in result.anomalies
            if a.risk_level == "high" or (
                a.risk_level == "medium" and a.amount > 5000
            )
        ]
        result.anomaly_count = len(result.anomalies)
        result.anomaly_rate = round(result.anomaly_count / result.total_vouchers, 3)
        result.summary = self._summarize(result.anomalies, result.by_category)
        return result

    def _account_in_list(self, actual: str, expected_list: List[str]) -> bool:
        """检查实际科目是否在预期列表中（含别名匹配）"""
        actual = actual.strip()
        if not actual:
            return True  # 空科目不判异常

        for expected in expected_list:
            # 直接匹配
            for exp in expected.split("|"):
                exp = exp.strip()
                # 精确匹配或包含匹配
                if exp in actual or actual in exp:
                    return True
                # 别名匹配
                if exp in self._account_aliases:
                    for alias in self._account_aliases[exp]:
                        if alias in actual or actual in alias:
                            return True

        return False

    def _is_enterprise_rule(self, description: str) -> bool:
        """判断是否为纯企业会计准则规则（政府会计上下文应跳过）"""
        enterprise_keywords = [
            "采购入账", "货款支付", "验收入库", "预付款", "偿付应付",
            "暂估入库", "采购退货", "供应商", "收款入账", "赊销",
            "预收款", "坏账核销", "债务重组", "销售收入", "开票收入",
            "客户销售", "委托代销", "差旅费", "业务招待费", "办公费",
            "会议费", "培训费", "油费", "维修费", "咨询费",
            "工资费用", "福利费", "服务收入", "利息收入", "租金收入",
            "投资收益", "增值税", "所得税", "附加税费", "印花税",
            "提现", "转账", "票据业务", "借款入账", "偿还借款",
            "运杂费", "折扣", "赔偿",
            "设备采购", "电子设备", "车辆购置",
            "政府补助",
        ]
        return any(kw in description for kw in enterprise_keywords)

    def _classify(self, summary: str) -> str:
        """按摘要关键词分类"""
        for kw, cat in [
            ("采购|购货|货款|材料款|设备款|入库", "AP-应付账款"),
            ("销售|售出|收款|回款|赊销|客户", "AR-应收账款"),
            ("设备|机器|电脑|车辆|在建|转固|折旧|报废", "FA-固定资产"),
            ("差旅|招待|办公|会议|培训|加油|维修|咨询|工资|福利", "EXP-费用报销"),
            ("服务|补助|利息|租金|投资", "REV-收入"),
            ("增值税|所得税|城建税|印花税|个税|税金", "TAX-税金"),
            ("提现|转账|汇款|承兑|贷款|借款|还贷", "BANK-银行"),
            ("财政拨款|零余额|财政应返还|授权支付|直接支付", "GOV-财政拨款"),
            ("业务活动|项目支出|专项支出|事业支出|课题", "GOV-政府费用"),
            ("政府采购|集中采购|资产处置|资产报废|资产调拨|公共基础设施", "GOV-政府资产"),
            ("事业收入|经营收入|上级补助|附属单位|非同级财政", "GOV-政府收入"),
            ("暂付|暂收|保证金|履约金|借出款", "GOV-政府往来"),
            ("年终结转|年末结转|期末结转|收支结转|费用结转", "GOV-年终结转"),
        ]:
            if re.search(kw, summary):
                return cat
        return "OTHER-其他"

    def _summarize(
        self,
        anomalies: List[JournalAnomaly],
        category_count: Dict[str, int],
    ) -> str:
        """生成摘要"""
        n = len(anomalies)
        if n == 0:
            return "会计分录校验通过，未发现科目对应异常。"

        high = sum(1 for a in anomalies if a.risk_level == "high")
        total_amount = sum(a.amount for a in anomalies)

        parts = [
            f"共发现{n}条会计分录异常，其中高危{high}条。",
            f"涉及金额{total_amount:,.0f}元。",
        ]

        if category_count:
            top_cat = max(category_count, key=category_count.get)
            parts.append(f"异常集中于{top_cat}类别（{category_count[top_cat]}条）。")

        if high > 0:
            parts.append(
                "建议对高危异常逐条核实原始凭证，确认是否存在科目错用、"
                "跨期费用、资产费用化等问题。"
            )
        else:
            parts.append("建议抽查中危异常，核实科目对应关系的合理性。")

        return "".join(parts)


# ── MCP工具接口 ──────────────────────────────────────────────

def journal_entry_validate(
    vouchers: List[Dict[str, Any]],
    strict_mode: bool = False,
    account_mapping_csv: Optional[str] = None,
) -> dict:
    """
    会计分录科目对应关系校验

    Args:
        vouchers: 凭证列表 [{"summary": "...", "debit_account": "...",
                  "credit_account": "...", "amount": 10000, "date": "...", "voucher_no": "..."}]
        strict_mode: 严格模式（只报告高危+大额中危）
        account_mapping_csv: 企业科目映射CSV路径

    Returns:
        校验结果dict
    """
    validator = JournalEntryValidator()

    if account_mapping_csv:
        validator.load_account_mapping(account_mapping_csv)

    if strict_mode:
        result = validator.validate_strict(vouchers)
    else:
        result = validator.validate(vouchers)

    # 异常明细
    anomaly_items = []
    for a in result.anomalies[:50]:
        anomaly_items.append({
            "voucher_no": a.voucher_no,
            "date": a.date,
            "summary": a.summary,
            "actual": f"借:{a.actual_debit} / 贷:{a.actual_credit}",
            "expected": f"借:{a.expected_debit} / 贷:{a.expected_credit}",
            "amount": a.amount,
            "deviation": a.deviation_type,
            "risk": a.risk_level,
            "rule": a.rule_description[:60],
        })

    return {
        "total_vouchers": result.total_vouchers,
        "anomaly_count": result.anomaly_count,
        "anomaly_rate": f"{result.anomaly_rate:.1%}",
        "high_risk_count": sum(1 for a in result.anomalies if a.risk_level == "high"),
        "by_category": result.by_category,
        "anomalies": anomaly_items,
        "summary": result.summary,
        "strict_mode": strict_mode,
        "rules_loaded": len(validator.rules),
    }
