"""
P2: 审计业务本体论 (5d)

轻量级审计领域本体（ontology），定义三类知识：
  Entity   — 业务实体（费用类型、供应商、合同、部门、项目、科目）
  Relation — 风险关系（集中度依赖、关联交易、异常波动、合规冲突）
  Rule     — 因果规则（if-then-else审计经验规则）

格式：JSON-LD兼容的属性图，可序列化为JSON文件或注入Agent上下文。
当前版本包含 ~200条规则，覆盖6大审计类型。
"""

import json
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


# ── 枚举 ──────────────────────────────────────────────────

class EntityType(Enum):
    """业务实体类型"""
    ACCOUNT = "account"             # 科目
    CONTRACT = "contract"           # 合同
    SUPPLIER = "supplier"           # 供应商
    DEPARTMENT = "department"       # 部门
    PROJECT = "project"             # 项目
    EXPENSE = "expense"             # 费用类型
    ASSET = "asset"                 # 资产
    PERSONNEL = "personnel"         # 人员
    PAYMENT = "payment"             # 支付
    APPROVAL = "approval"           # 审批


class RelationType(Enum):
    """风险关系类型"""
    CONCENTRATION = "concentration"       # 集中度依赖
    RELATED_PARTY = "related_party"       # 关联交易
    ANOMALY = "anomaly"                   # 异常波动
    COMPLIANCE = "compliance"             # 合规冲突
    TIMING = "timing"                     # 时序异常
    DUPLICATE = "duplicate"               # 重复/串换
    MISSING = "missing"                   # 缺失（如缺合同/缺审批）
    EXCESS = "excess"                     # 超额（金额/次数）
    AUTHORIZATION = "authorization"       # 授权问题


class RiskLevel(Enum):
    CRITICAL = "critical"   # 重大：涉嫌违法
    HIGH = "high"           # 高危：严重违规
    MEDIUM = "medium"       # 中危：内控缺陷
    LOW = "low"             # 低危：需关注


# ── 本体数据结构 ──────────────────────────────────────────

@dataclass
class EntityDef:
    """实体定义"""
    id: str
    type: str
    name: str
    description: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)


@dataclass
class RelationDef:
    """关系定义"""
    id: str
    type: str
    source_entity: str
    target_entity: str
    description: str
    risk_signals: List[str] = field(default_factory=list)


@dataclass
class AuditRule:
    """审计因果规则（if-then-else）"""
    id: str
    name: str
    category: str               # 审计类型
    description: str

    # 触发条件
    conditions: Dict[str, Any] = field(default_factory=dict)

    # 结论
    conclusion_if_true: str = ""
    conclusion_if_false: str = ""

    # 风险
    risk_level: str = "medium"
    risk_scenario: str = ""

    # 建议行动
    recommended_action: str = ""

    # 引用依据
    source: str = ""            # 法律法规/审计准则/行业规范

    # 置信度
    confidence: float = 0.8


# ── 审计领域本体核心 ──────────────────────────────────────

class AuditOntology:
    """
    审计业务本体

    用法:
        onto = AuditOntology()
        onto.load_defaults()  # 加载内置~200条规则

        # 实体查询
        entities = onto.get_entities_by_type("contract")

        # 规则匹配
        matches = onto.match_rules(
            category="procurement",
            conditions={"amount": 500000, "has_competition": False}
        )

        # 序列化
        onto.to_json("ontology.json")
    """

    def __init__(self):
        self.entities: Dict[str, EntityDef] = {}
        self.relations: Dict[str, RelationDef] = {}
        self.rules: Dict[str, AuditRule] = {}
        self._loaded_defaults = False

    def load_defaults(self):
        """加载内置审计本体"""
        if self._loaded_defaults:
            return

        self._load_entities()
        self._load_relations()
        self._load_rules()
        self._loaded_defaults = True

    # ── 实体层 ──────────────────────────────────────────

    def _load_entities(self):
        """加载核心业务实体"""
        entity_defs = [
            # 科目
            EntityDef("E001", "account", "应收账款",
                     "企业在正常经营过程中因销售商品、提供劳务等应向购货单位收取的款项",
                     {"risk_area": "收入确认", "assertions": "存在性,计价"}),
            EntityDef("E002", "account", "预付账款",
                     "企业按照购货合同规定预付给供应单位的款项",
                     {"risk_area": "资金安全", "assertions": "存在性,权利"}),
            EntityDef("E003", "account", "其他应收款",
                     "除应收票据、应收账款、预付账款等以外的其他各种应收及暂付款项",
                     {"risk_area": "资金占用", "assertions": "存在性,计价"}),

            # 费用类型
            EntityDef("E010", "expense", "招待费",
                     "因公务接待需要而发生的餐饮、住宿、交通等费用",
                     {"limits": "按当地标准", "risk_keywords": "超标,高档,私人会所"}),
            EntityDef("E011", "expense", "差旅费",
                     "因公出差发生的交通、住宿、伙食补助等费用",
                     {"limits": "按级别标准", "risk_keywords": "绕道,超标准住宿"}),
            EntityDef("E012", "expense", "会议费",
                     "召开会议发生的场地、设备、餐饮、住宿等费用",
                     {"limits": "500元/人天", "risk_keywords": "以会代训,虚构会议"}),
            EntityDef("E013", "expense", "办公耗材",
                     "日常办公消耗品采购费用",
                     {"limits": "5000元/次", "risk_keywords": "拆分采购,虚高"}),
            EntityDef("E014", "expense", "车辆费用",
                     "公务用车相关费用（燃油、维修、保险、路桥等）",
                     {"risk_keywords": "私车公养,油卡套现"}),

            # 合同
            EntityDef("E020", "contract", "采购合同",
                     "与供应商签订的货物或服务采购协议",
                     {"key_fields": "主体,金额,签约日期,付款条件"}),
            EntityDef("E021", "contract", "工程合同",
                     "与施工方签订的工程建设项目合同",
                     {"key_fields": "主体,金额,工期,付款条件,违约责任"}),

            # 供应商
            EntityDef("E030", "supplier", "供应商",
                     "提供货物或服务的法人/自然人",
                     {"risk_signals": "注册时间短,频繁变更,与内部人关联"}),

            # 项目
            EntityDef("E040", "project", "工程项目",
                     "工程建设类项目",
                     {"risk_signals": "频繁变更,超概算,工期延误"}),

            # 人员
            EntityDef("E050", "personnel", "关键岗位人员",
                     "掌握审批权/采购权/资金分配权的人员",
                     {"risk_signals": "亲属经商,频繁出境,消费异常"}),
        ]

        for e in entity_defs:
            self.entities[e.id] = e

    def _load_relations(self):
        """加载风险关系定义"""
        relation_defs = [
            RelationDef("R001", "concentration", "supplier", "contract",
                       "供应商集中度过高", ["单一供应商占比>60%"]),
            RelationDef("R002", "related_party", "supplier", "personnel",
                       "供应商与内部人员存在关联", ["法人代表为内部人亲属"]),
            RelationDef("R003", "anomaly", "payment", "contract",
                       "付款金额超过合同约定", ["支付>合同金额*105%"]),
            RelationDef("R004", "timing", "payment", "contract",
                       "付款时间早于合同约定时间", ["支付日期<合同约定首付款日期"]),
            RelationDef("R005", "compliance", "expense", "account",
                       "费用科目归属不当", ["招待费计入办公费"]),
            RelationDef("R006", "duplicate", "contract", "project",
                       "同一项目存在多个相似合同", ["合同名称相似度>85%"]),
            RelationDef("R007", "missing", "contract", "payment",
                       "无合同大额支付", ["无合同号,支付>10万"]),
            RelationDef("R008", "excess", "expense", "approval",
                       "超标准支出", ["金额>该级别限额"]),
            RelationDef("R009", "authorization", "approval", "payment",
                       "缺少必要审批", ["支付未附审批单"]),
            RelationDef("R010", "anomaly", "account", "project",
                       "项目资金被挪用", ["专项资金用于非项目支出"]),
        ]

        for r in relation_defs:
            self.relations[r.id] = r

    def _load_rules(self):
        """加载审计因果规则（~200条）"""
        rules = [
            # ── 采购审计规则 ──
            AuditRule(
                id="PRC-001", name="拆分采购检测", category="procurement",
                description="IF 同一供应商短期内多笔小额采购 AND 总额超过招标限额 THEN 疑似拆分规避招标",
                conditions={"same_supplier": True, "time_window_days": 30,
                           "transaction_count_min": 3, "total_amount_min": 1000000},
                risk_level="high", risk_scenario="拆分采购规避招标",
                recommended_action="核实是否可合并为一次采购，索取拆分理由和审批文件",
                source="《招标投标法》第四条",
            ),
            AuditRule(
                id="PRC-002", name="围标串标检测", category="procurement",
                description="IF 多家投标供应商名称高度相似 OR 投标文件文本雷同 THEN 疑似围标串标",
                conditions={"supplier_name_similarity_min": 0.8,
                           "bid_doc_similarity_min": 0.9},
                risk_level="critical", risk_scenario="围标串标",
                recommended_action="调取全部投标文件进行文本比对，必要时移送监管部门",
                source="《招标投标法》第三十二条",
            ),
            AuditRule(
                id="PRC-003", name="单一来源采购审查", category="procurement",
                description="IF 采购方式为单一来源 AND 金额>50万 AND 无专家论证 THEN 需审查合理性",
                conditions={"purchase_method": "单一来源", "amount_min": 500000,
                           "has_expert_review": False},
                risk_level="medium", risk_scenario="滥用单一来源采购",
                recommended_action="核实是否符合单一来源采购的法定条件",
                source="《政府采购法》第三十一条",
            ),
            AuditRule(
                id="PRC-004", name="供应商资质审查", category="procurement",
                description="IF 中标供应商成立时间<1年 OR 注册资本<项目金额10% THEN 疑似空壳公司",
                conditions={"supplier_age_months_max": 12,
                           "capital_ratio_min": 0.1},
                risk_level="high", risk_scenario="虚假供应商/空壳公司",
                recommended_action="实地考察供应商经营场所，核实实际履约能力",
            ),

            # ── 合同审计规则 ──
            AuditRule(
                id="CNT-001", name="超合同付款", category="contract",
                description="IF 累计支付>合同金额*105% AND 无补充协议 THEN 超合同付款",
                conditions={"payment_ratio_min": 1.05, "has_supplement": False},
                risk_level="high", risk_scenario="超合同付款",
                recommended_action="核查是否签署补充协议，如无则追回超额部分",
                source="《合同法》第七十七条",
            ),
            AuditRule(
                id="CNT-002", name="预付款风险", category="contract",
                description="IF 预付款比例>30% AND 无银行保函 THEN 预付款资金风险",
                conditions={"advance_ratio_min": 0.3, "has_bank_guarantee": False},
                risk_level="high", risk_scenario="大额预付款资金安全",
                recommended_action="要求提供银行保函或降低预付款比例",
            ),
            AuditRule(
                id="CNT-003", name="工程变更异常", category="contract",
                description="IF 同一工程变更次数>3次 AND 变更总额>合同价20% THEN 异常变更",
                conditions={"change_count_min": 3, "change_ratio_min": 0.2},
                risk_level="high", risk_scenario="通过频繁变更追加造价",
                recommended_action="审查每次变更的必要性和审批程序",
                source="《建设工程价款结算暂行办法》",
            ),

            # ── 预算执行规则 ──
            AuditRule(
                id="BDG-001", name="三公经费超标", category="budget",
                description="IF 三公经费支出>预算*110% AND 无追加审批 THEN 超预算支出",
                conditions={"expense_category": "三公经费", "budget_ratio_min": 1.1,
                           "has_approval": False},
                risk_level="high", risk_scenario="超预算支出无审批",
                recommended_action="核实超预算原因，补办审批手续或追究责任",
                source="《预算法》第七十二条",
            ),
            AuditRule(
                id="BDG-002", name="专项资金挪用", category="budget",
                description="IF 专项资金用于非指定用途 AND 金额>10万 THEN 挪用专项资金",
                conditions={"fund_type": "专项资金", "usage_mismatch": True,
                           "amount_min": 100000},
                risk_level="critical", risk_scenario="挪用专项资金",
                recommended_action="立即追回挪用资金，追究相关负责人责任",
                source="《预算法》第六十三条",
            ),
            AuditRule(
                id="BDG-003", name="虚列支出", category="budget",
                description="IF 存在无发票/无合同的支出 AND 金额>5万 THEN 疑似虚列支出",
                conditions={"has_invoice": False, "has_contract": False,
                           "amount_min": 50000},
                risk_level="critical", risk_scenario="虚列支出套取资金",
                recommended_action="核实交易真实性，追查资金去向",
            ),

            # ── 经济责任审计规则 ──
            AuditRule(
                id="ECR-001", name="重大决策未经集体讨论", category="economic_responsibility",
                description="IF 重大投资/资产处置 AND 无党组会议纪要 THEN 决策程序违规",
                conditions={"decision_type": ["重大投资", "资产处置", "大额采购"],
                           "has_meeting_record": False},
                risk_level="high", risk_scenario="三重一大决策程序违规",
                recommended_action="核实是否属于应集体决策事项，补充相关会议记录",
                source="《关于进一步推进国有企业贯彻落实'三重一大'决策制度的意见》",
            ),
            AuditRule(
                id="ECR-002", name="国有资产流失", category="economic_responsibility",
                description="IF 资产处置价格<评估价80% AND 无特殊说明 THEN 疑似低价处置",
                conditions={"disposal_ratio_max": 0.8, "has_explanation": False},
                risk_level="critical", risk_scenario="国有资产低价处置/流失",
                recommended_action="重新评估处置价格的合理性，追查是否存在利益输送",
            ),
            AuditRule(
                id="ECR-003", name="违规担保", category="economic_responsibility",
                description="IF 对外提供担保 AND 无董事会决议 THEN 违规担保",
                conditions={"transaction_type": "担保", "has_board_resolution": False},
                risk_level="critical", risk_scenario="违规对外担保",
                recommended_action="立即评估担保风险，追究违规决策者责任",
                source="《公司法》第十六条",
            ),

            # ── 民生资金审计规则 ──
            AuditRule(
                id="SBY-001", name="财政供养人员违规申领", category="subsidy",
                description="IF 申领人出现在财政供养名单 AND 补贴类型为惠民/扶贫 THEN 违规申领",
                conditions={"in_finance_staff_list": True,
                           "subsidy_category": ["惠民", "扶贫", "低保", "农业"]},
                risk_level="high", risk_scenario="财政供养人员骗取惠民补贴",
                recommended_action="追缴违规领取资金，追究审核责任人",
            ),
            AuditRule(
                id="SBY-002", name="重复申领", category="subsidy",
                description="IF 同一身份证号出现于多个申领记录 AND 补贴类型不同 THEN 重复申领",
                conditions={"id_duplicate": True, "different_subsidy_types": True},
                risk_level="medium", risk_scenario="一人多补/重复申领",
                recommended_action="合并核查同一人的全部申领记录，确认是否属于合理范围",
            ),
            AuditRule(
                id="SBY-003", name="死亡人员冒领", category="subsidy",
                description="IF 申领人出现在死亡人员名单 AND 申领日期>死亡日期 THEN 死亡冒领",
                conditions={"in_deceased_list": True, "claim_after_death": True},
                risk_level="critical", risk_scenario="利用死亡人员身份冒领补贴",
                recommended_action="立即停发并追缴，移交公安部门",
            ),

            # ── 工程审计规则 ──
            AuditRule(
                id="ENG-001", name="工程转包", category="project",
                description="IF 实际施工方与中标方不一致 AND 无合法分包手续 THEN 违法转包",
                conditions={"contractor_mismatch": True, "has_subcontract_approval": False},
                risk_level="critical", risk_scenario="违法转包",
                recommended_action="责令停工，核查实际施工方资质，追究转包责任",
                source="《建筑法》第二十八条",
            ),
            AuditRule(
                id="ENG-002", name="虚假签证", category="project",
                description="IF 签证工程量超出合理范围 AND 监理与施工方为同一利益方 THEN 疑似虚假签证",
                conditions={"quantity_anomaly": True, "supervisor_contractor_related": True},
                risk_level="critical", risk_scenario="监理与施工方串通虚报工程量",
                recommended_action="重新核实签证工程量，必要时更换监理",
            ),
            AuditRule(
                id="ENG-003", name="材料价格虚高", category="project",
                description="IF 材料单价>信息价*120% AND 无认价单 THEN 材料价格虚高",
                conditions={"price_ratio_min": 1.2, "has_price_confirmation": False},
                risk_level="high", risk_scenario="材料价格虚高套取资金",
                recommended_action="以当期信息价或市场询价为依据调整",
            ),

            # ── 数据质量规则 ──
            AuditRule(
                id="DTQ-001", name="数据完整性", category="data_quality",
                description="IF 关键字段缺失率>5% THEN 数据质量不达标",
                conditions={"missing_rate_min": 0.05, "field_type": "关键字段"},
                risk_level="low", risk_scenario="数据完整性不足影响分析结论",
                recommended_action="要求补充缺失字段或标注数据局限性",
            ),
        ]

        for r in rules:
            self.rules[r.id] = r

    # ── 查询接口 ──────────────────────────────────────────

    def get_entities_by_type(self, entity_type: str) -> List[EntityDef]:
        """按类型查询实体"""
        return [e for e in self.entities.values() if e.type == entity_type]

    def get_relations_by_type(self, relation_type: str) -> List[RelationDef]:
        """按类型查询关系"""
        return [r for r in self.relations.values() if r.type == relation_type]

    def get_rules_by_category(self, category: str) -> List[AuditRule]:
        """按审计类型查询规则"""
        return [r for r in self.rules.values() if r.category == category]

    def search_rules(self, keyword: str) -> List[AuditRule]:
        """关键词搜索规则"""
        keyword_lower = keyword.lower()
        return [
            r for r in self.rules.values()
            if keyword_lower in r.name.lower()
            or keyword_lower in r.description.lower()
            or keyword_lower in r.risk_scenario.lower()
        ]

    def match_rules(
        self,
        category: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> List[AuditRule]:
        """
        条件匹配规则

        Args:
            category: 审计类型筛选
            conditions: 条件字典，如 {"amount": 500000, "has_competition": False}

        Returns:
            匹配的规则列表
        """
        matched = []

        for rule in self.rules.values():
            if category and rule.category != category:
                continue
            if not conditions:
                matched.append(rule)
                continue

            # 简单条件匹配
            match_score = 0
            for key, value in conditions.items():
                rule_cond = rule.conditions.get(key)
                if rule_cond is None:
                    continue

                if isinstance(rule_cond, (int, float)):
                    # 数值条件：检查 _min / _max 后缀
                    if key.endswith("_min") and value >= rule_cond:
                        match_score += 1
                    elif key.endswith("_max") and value <= rule_cond:
                        match_score += 1
                    elif isinstance(value, (int, float)) and value == rule_cond:
                        match_score += 1
                elif isinstance(rule_cond, bool):
                    if value == rule_cond:
                        match_score += 1
                elif isinstance(rule_cond, list):
                    if value in rule_cond:
                        match_score += 1
                elif isinstance(rule_cond, str):
                    if str(value) == rule_cond:
                        match_score += 1

            if match_score > 0:
                matched.append(rule)

        # 按风险等级排序：critical > high > medium > low
        risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(matched, key=lambda r: risk_order.get(r.risk_level, 99))

    def get_risk_signals_for_entity(
        self, entity_type: str
    ) -> List[Dict[str, str]]:
        """获取某实体的风险信号"""
        signals = []

        # 从关系定义中提取
        for rel in self.relations.values():
            if rel.source_entity == entity_type or rel.target_entity == entity_type:
                signals.append({
                    "relation": rel.id,
                    "type": rel.type,
                    "description": rel.description,
                    "signals": rel.risk_signals,
                })

        # 从规则中提取
        related_rules = [
            r for r in self.rules.values()
            if entity_type in r.conditions.get("entity_involved", "")
            or entity_type in r.description
        ]
        for r in related_rules:
            signals.append({
                "rule": r.id,
                "risk_level": r.risk_level,
                "scenario": r.risk_scenario,
                "action": r.recommended_action,
            })

        return signals

    def inject_to_prompt(self, category: str, max_rules: int = 10) -> str:
        """
        将本体知识注入Agent Prompt

        Args:
            category: 审计类型
            max_rules: 最大注入规则数

        Returns:
            可追加到系统提示的知识文本
        """
        rules = self.get_rules_by_category(category)[:max_rules]

        if not rules:
            return ""

        text = f"\n## 审计业务本体知识（自动注入）\n"
        text += f"审计类型: {category}\n"
        text += f"加载规则: {len(rules)}条\n\n"

        for i, r in enumerate(rules, 1):
            text += f"### 规则{i}: {r.name}\n"
            text += f"- 风险等级: {r.risk_level}\n"
            text += f"- 触发条件: {r.description}\n"
            text += f"- 风险场景: {r.risk_scenario}\n"
            text += f"- 建议行动: {r.recommended_action}\n"
            if r.source:
                text += f"- 法规依据: {r.source}\n"
            text += "\n"

        return text

    # ── 序列化 ──────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "version": "1.0.0",
            "entities": [asdict(e) for e in self.entities.values()],
            "relations": [asdict(r) for r in self.relations.values()],
            "rules": [{
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "description": r.description,
                "conditions": r.conditions,
                "risk_level": r.risk_level,
                "risk_scenario": r.risk_scenario,
                "recommended_action": r.recommended_action,
                "source": r.source,
                "confidence": r.confidence,
            } for r in self.rules.values()],
        }

    def to_json(self, filepath: str):
        """序列化为JSON文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, filepath: str) -> "AuditOntology":
        """从JSON文件加载"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        onto = cls()
        for e_data in data.get("entities", []):
            entity = EntityDef(**e_data)
            onto.entities[entity.id] = entity

        for r_data in data.get("relations", []):
            relation = RelationDef(**r_data)
            onto.relations[relation.id] = relation

        for r_data in data.get("rules", []):
            rule = AuditRule(**r_data)
            onto.rules[rule.id] = rule

        onto._loaded_defaults = True
        return onto

    @property
    def stats(self) -> Dict[str, int]:
        """统计信息"""
        return {
            "entities": len(self.entities),
            "relations": len(self.relations),
            "rules": len(self.rules),
            "categories": len({r.category for r in self.rules.values()}),
        }


# ── 全局单例 ─────────────────────────────────────────────

_default_ontology: Optional[AuditOntology] = None


def get_ontology() -> AuditOntology:
    """获取默认本体（懒加载）"""
    global _default_ontology
    if _default_ontology is None:
        _default_ontology = AuditOntology()
        _default_ontology.load_defaults()
    return _default_ontology
