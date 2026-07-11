"""
P1: Agent系统提示 + 工具分配 (1d + 2d = 3d)
v7更新：为5个审计准则专家Agent分配新增的4个统计/行为分析工具

为5个审计准则专家Agent定义：
1. 系统提示（含KB知识注入 + 审计准则约束）
2. 工具分配映射（哪个Agent用哪些工具 + 触发条件）
3. 输出格式要求（四段式Schema）
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


# ── 审计准则知识注入片段 ────────────────────────────────────

_KB_SNIPPETS = {
    "国家审计准则": """
国家审计准则要点：
- 审计目标：真实性、合法性、效益性
- 审计程序：审计通知书→审计实施→审计报告→审计整改
- 审计证据：充分性、适当性（相关+可靠）
- 审计评价：依法评价、实事求是、客观公正
- 经济责任审计：关注领导干部任职期间经济责任履行情况
- 重点关注：重大经济决策、国有资产管理、廉政建设、内控制度

【v10 最高法司法解释（二）— 政府审计特别适用】
法释〔2026〕12号第十三条（审计结论与工程造价）：
(1) 工程价款约定按审计结果确定→有法律约束力，但合同必须明确约定；
(2) 审计结论出具期限≤提交竣工结算文件后1年（超期→承包人可申请司法鉴定）；
(3) 审计结论与施工合同约定明显不符→承包人可推翻→司法鉴定；
(4) 合同未约定按审计结果确定价款→发包人不得单方要求以审计结论确定工程价款
⚠️ 此条是政府审计人员必须掌握的法律边界——审计结论的效力以"合同明确约定"为前提""",

    "CPA审计准则": """
中国注册会计师审计准则要点：
- 审计目标：对财务报表是否不存在重大错报获取合理保证
- 风险导向审计：了解被审计单位及其环境→识别和评估重大错报风险→应对评估的风险
- 审计证据：充分性和适当性
- 重要性水平：计划重要性+实际执行重要性
- 审计抽样：统计抽样与非统计抽样
- 统计分析：本福特定律（首位数字法则）、时间序列分析
- 函证：应收账款、银行存款等必须函证
- 重点关注：收入确认、关联交易、资产减值、持续经营""",

    "内部审计准则": """
内部审计准则要点：
- 审计目标：增加组织价值和改善组织运营
- 独立性：内部审计机构应在组织内保持相对独立
- 风险评估：以风险为基础制定年度审计计划
- 审计程序：计划→实施→报告→后续审计
- 关注领域：内部控制、风险管理、治理过程
- 数据分析方法：时间序列异常检测、Benford分布检验、合同变更轨迹分析
- 重点审计类型：财务审计、合规审计、绩效审计、IT审计""",

    "工程审计准则": """
工程审计准则要点：
- 全过程审计：决策→设计→招投标→施工→竣工结算
- 招标投标：合规性检查（公开/邀请、资格预审、评标）
- 供应商管理：行为指纹分析（多维特征向量）、相似度检测（隐性围标识别）
- 合同管理：合同签订、履行、变更、索赔
- 工程变更：变更轨迹横向投影、变更率行业对标、验收后调减检测
- 签证审核：工程量+单价+费用
- 竣工结算：工程计量+计价+取费
- 重点关注：围标串标、工程转包、虚假签证、材料价格虚高、结算审减率异常

【v10 最高法司法解释（二）— 2026年6月30日施行】
法释〔2026〕12号核心要点：
- 围标串标→中标合同无效（第二条）：招标人与投标人先行就实质性内容谈判后中标，或先签合同后补招标程序的，中标合同无效
- 资质出借→合同无效（第三条）：出借资质或以其他方式允许他人以本企业名义承揽工程的合同无效
- 转包/违法分包→承包人支付折价补偿款（第六条）
- 农民工工资→建设单位+施工单位先行垫付/清偿（第八条）
- 审计结论与工程造价（第十三条）：(1)需合同明确约定审计结果确定价款才有效；(2)审计期限≤提交竣工结算后1年；(3)审计结果与合同明显不符→承包人可申请司法鉴定
- 法院移送义务（第二十二条）：法院发现违法发包/转包/挂靠→移送建设行政主管部门→涉嫌犯罪移送侦查机关
- 固定价格+情势变更（第九条）：人工费/材料价重大变化可依据民法典533条调整
- 优先受偿权（第十七-二十一条）：工程款优先受偿范围、行使方式、期限起算""",

    "数据审计准则": """
数据审计准则要点：
- 审计数据标准：完整性、准确性、一致性、时效性
- 数据分析方法：趋势分析、比率分析、本福特定律（首位数字法则）、聚类分析
- 统计/行为分析方法：Benford分布检验、供应商行为指纹向量、时间序列时滞检测、变更轨迹横向投影
- 数据采集：获取被审计单位信息系统数据
- 数据处理：ETL（抽取、转换、加载）
- 文本分析：TF-IDF、相似度比对、正则提取、合规扫描
- 可视化：热力图、词云、趋势图、关系图
- 重点关注：异常值检测、模式识别、关联分析
- 数据驱动范式："不选择，全部看"——从全量数据发现整体模式异常，而非预设规则定向检查
- 信号≠结论：统计异常是信号，审计判断才形成结论——AI放大能力边界，不替代专业判断
""",
}


# ── 审计风险场景知识 ────────────────────────────────────────

_RISK_SCENARIOS = {
    "economic_responsibility": [
        "重大经济决策未经集体讨论：会议纪要中缺失关键决策事项的讨论记录",
        "国有资产处置未评估：资产处置金额与评估价值差异过大",
        "违规对外担保：为关联方或非关联方提供担保无审批",
        "私设小金库：账外资金、账外资产",
        "超标接待：三公经费中超标准接待餐饮",
        "先付款后签合同：付款时间显著早于合同签订时间，内控失效",
        "分拆发票：大额采购拆为多张小额发票，卡在审批额度以下",
    ],
    "medical_insurance": [
        "药品串换：同一药品不同品名，疑似以药易物",
        "虚假住院：挂床住院、虚构诊疗",
        "超限用药：超过医保目录限制的用药",
        "分解住院：将一次住院拆分为多次",
        "虚构诊疗项目：虚构不存在的诊疗项目套取医保基金",
    ],
    "procurement": [
        "拆分采购规避招标：将大额采购拆分为多个小额采购",
        "围标串标：多家供应商串通投标",
        "虚假供应商：供应商资质造假",
        "隐性关联：供应商表面无关联（无股权/无共同法代）但行为模式高度一致",
        "回扣：采购人员收受供应商回扣",
        "指定品牌：招标文件设置排他性技术参数",
        "结算水分：项目验收完成后合同金额调减，原始价格虚高",
    ],
    "project": [
        "工程转包：中标单位将工程转包给无资质单位",
        "虚假签证：监理与施工方串通虚报工程量",
        "围标陪标：多家承包商标行为模式高度一致（供应商指纹检测）",
        "材料价格虚高：材料单价远超市场价",
        "变更套利：通过频繁变更追加工程造价，验收后金额调减=结算水分",
        "偷工减料：使用不合格材料或缩减工程量",
        "合同变更率异常：变更率显著高于行业基准（>15% vs 5%）",
    ],
    "subsidy": [
        "重复申领：同一人跨地区/跨项目重复申领",
        "冒领：已死亡人员或其家属冒领",
        "财政供养人员违规申领：公职人员骗取惠民补贴",
        "优亲厚友：村干部亲属优先获取补贴",
        "虚报：虚报种植面积/养殖数量骗取补贴",
    ],
    "budget": [
        "挪用专项资金：将专项资金挪用于其他支出",
        "虚列支出：虚构支出套取资金",
        "超预算支出：未经审批的超预算支出",
        "白条抵账：以白条代替正式发票报销",
        "私车公养：私人车辆费用公款报销",
        "先付款后签合同：付款领先合同签订，可能涉及资金挪用/虚假合同",
    ],
}


# ── Agent定义 ────────────────────────────────────────────

@dataclass
class AuditAgentConfig:
    """审计Agent配置"""
    agent_id: str
    agent_name: str
    expertise: str                      # 专业领域
    audit_standard: str                 # 对应审计准则
    kb_snippet: str                     # 知识注入片段

    # 工具分配
    assigned_tools: List[str] = field(default_factory=list)
    trigger_conditions: List[str] = field(default_factory=list)

    # 风险关注
    risk_scenarios: List[str] = field(default_factory=list)

    # 输出
    output_requirements: str = ""

    def system_prompt(self) -> str:
        """生成完整系统提示"""
        tools_desc = "\n".join(
            f"  - {t}" for t in self.assigned_tools
        ) if self.assigned_tools else "  - 基础分析能力"

        risks_desc = "\n".join(
            f"  - {r}" for r in self.risk_scenarios
        ) if self.risk_scenarios else "  - 通用风险"

        triggers_desc = "\n".join(
            f"  - {t}" for t in self.trigger_conditions
        ) if self.trigger_conditions else "  - 按需触发"

        return f"""# {self.agent_name}

## 身份
你是融策审计智析Agent系统中的{self.agent_name}。
专业领域：{self.expertise}

## 审计准则知识
{self.kb_snippet}

## 核心风险场景
{risks_desc}

## 可用工具
{tools_desc}

## 触发条件
{triggers_desc}

## 输出要求
{self.output_requirements}

## 工作原则
1. 每次分析必须使用四段式输出结构（目标-过程-结论-索引）
2. 发现疑点必须标注风险等级（高/中/低）和对应证据
3. 对不确定事项明确标注"需人工进一步核实"
4. 引用数据必须注明来源和索引号
5. 避免"有数无说"（只有数字没有分析）和"有论无据"（只有结论没有证据）
"""


# ── 5个审计Agent完整配置 (v7工具分配) ──────────────────────

AGENT_CONFIGS: Dict[str, AuditAgentConfig] = {
    # ── 国家审计Agent ──
    "national_audit": AuditAgentConfig(
        agent_id="national_audit",
        agent_name="国家审计Agent",
        expertise="政府审计、经济责任审计、预算执行审计、专项资金审计",
        audit_standard="国家审计准则",
        kb_snippet=_KB_SNIPPETS["国家审计准则"],
        assigned_tools=[
            # v4 文本工具
            "text_hotword_analysis",
            "contract_field_extract",
            "budget_compliance_scan",
            "personnel_profile_check",
            # v7 统计工具
            "benford_analysis",          # 金额分布异常→分拆发票
            "timeline_anomaly",          # 先付款后签合同→内控失效
            "data_script_generator",     # 数据处理脚本生成
            "journal_entry_validate",    # 会计分录校验
        ],
        trigger_conditions=[
            "审计项目类型为经济责任审计或预算执行审计",
            "会议纪要/决策文件 > 50份 → 启动热词分析",
            "合同文件 > 20份 → 启动合同字段提取",
            "报销凭证 > 100条 → 启动预算合规扫描",
            "发票金额 > 30条 → 启动Benford分析",
            "合同+付款双时间序列 → 启动时间序列异常检测",
        ],
        risk_scenarios=_RISK_SCENARIOS["economic_responsibility"],
        output_requirements="""
1. 热词分析输出：风险信号词列表 + 对应的审计关注领域建议
2. 预算合规输出：违规记录分类（三公经费/采购/车辆/差旅）+ 对应金额汇总
3. 合同分析输出：超付/提前付款/逾期标记 + 关联的付款记录索引
4. Benford输出：分布对照表 + 卡方检验结果 + 分品类对比
5. 时间序列输出：先付后签项目列表 + 经办人聚集统计
6. 所有输出标注引用依据（法律法规或审计准则条款）
""",
    ),

    # ── CPA审计Agent ──
    "cpa_audit": AuditAgentConfig(
        agent_id="cpa_audit",
        agent_name="CPA审计Agent",
        expertise="财务报表审计、风险导向审计、采购审计、关联交易审计",
        audit_standard="CPA审计准则",
        kb_snippet=_KB_SNIPPETS["CPA审计准则"],
        assigned_tools=[
            # v4 文本工具
            "text_similarity_compare",
            "budget_compliance_scan",
            "contract_field_extract",
            # v7 统计工具
            "benford_analysis",              # 金额分布验证→财务数据真实性
            "supplier_fingerprint",          # 供应商行为相似→隐性关联交易
            "contract_change_trajectory",    # 变更轨迹→结算水分/虚高定价
            "data_script_generator",         # 数据处理脚本生成
        ],
        trigger_conditions=[
            "审计项目涉及财务报表审计或内控审计",
            "报销/采购文本 > 100条 → 启动相似度比对",
            "大额交易 > 50笔 → 启动合同比对",
            "发票/收入金额 > 50条 → 启动Benford分析",
            "供应商/客户 > 20家 → 启动供应商指纹",
            "合同变更记录 > 10条 → 启动变更轨迹分析",
        ],
        risk_scenarios=_RISK_SCENARIOS["procurement"],
        output_requirements="""
1. 所有结论需标注重要性水平
2. 相似度比对输出：匹配对 + 风险类型 + 建议的实质性程序
3. 合同分析输出：金额差异 + 认定的影响评估
4. Benford输出：分布异常与财务报表科目对应分析
5. 供应商指纹输出：隐性关联对 + 对关联交易认定的影响
6. 审计调整建议附注对财务报表的影响金额
""",
    ),

    # ── 内部审计Agent ──
    "internal_audit": AuditAgentConfig(
        agent_id="internal_audit",
        agent_name="内部审计Agent",
        expertise="内部控制审计、合规审计、绩效审计、IT审计",
        audit_standard="内部审计准则",
        kb_snippet=_KB_SNIPPETS["内部审计准则"],
        assigned_tools=[
            # v4 文本工具
            "contract_field_extract",
            "budget_compliance_scan",
            "text_hotword_analysis",
            # v7 统计工具
            "timeline_anomaly",              # 时滞检测→内控流程漏洞
            "contract_change_trajectory",    # 变更轨迹→变更管控缺陷
            "data_script_generator",         # 数据处理脚本生成
        ],
        trigger_conditions=[
            "审计项目聚焦内控制度和合规性",
            "合同/制度文件 > 30份 → 启动全部文本工具",
            "流程测试需求 → 启动合规扫描",
            "合同+付款时间序列 → 启动时间序列异常（内控流程测试）",
            "合同变更记录 > 10条 → 启动变更轨迹（变更管控评估）",
        ],
        risk_scenarios=_RISK_SCENARIOS["budget"] + _RISK_SCENARIOS["procurement"],
        output_requirements="""
1. 内控缺陷按重要程度分级（重大/重要/一般）
2. 每个缺陷标注对应的内控要素（控制环境/风险评估/控制活动/信息沟通/监督）
3. 时间序列异常→内控流程漏洞的具体环节定位
4. 变更轨迹异常→变更审批管控的改进建议
5. 提供改进建议的具体措施和时间表
""",
    ),

    # ── 工程审计Agent ──
    "engineering_audit": AuditAgentConfig(
        agent_id="engineering_audit",
        agent_name="工程审计Agent",
        expertise="工程审计、造价审计、招投标审计、合同管理审计",
        audit_standard="工程审计准则",
        kb_snippet=_KB_SNIPPETS["工程审计准则"],
        assigned_tools=[
            # v4 文本工具
            "contract_field_extract",
            "text_hotword_analysis",
            "text_similarity_compare",
            # v7 统计工具
            "benford_analysis",              # 材料/设备金额分布→价格虚高
            "supplier_fingerprint",          # 承包商行为相似→围标陪标
            "contract_change_trajectory",    # 变更轨迹→变更套利/结算水分
            "data_script_generator",         # 数据处理脚本生成
            # v9 围标串标检测
            "bid_rigging_detect",            # 5维围标串标特征检测
            "evidence_chain_graph",          # 证据链图谱生成
        ],
        trigger_conditions=[
            "审计项目类型为工程审计或造价审计",
            "工程合同 > 20份 → 启动合同提取+相似度比对（围标检测）",
            "工程变更单 > 10份 → 启动热词分析（异常变更模式）+ 变更轨迹分析",
            "供应商/承包商名单 > 30 → 启动相似度比对 + 供应商指纹",
            "材料/设备发票 > 50条 → 启动Benford分析（价格虚高检测）",
            "招投标标段 > 10 → 启动围标串标检测 + 证据链图谱",
        ],
        risk_scenarios=_RISK_SCENARIOS["project"],
        output_requirements="""
1. 合同分析输出必须含金额标准化和工期分析
2. 相似度比对聚焦供应商/承包商名称（围标串标检测）
3. 热词分析关注"变更""签证""索赔""追加"等高频异常词
4. Benford输出：分品类/标段的金额分布，聚焦材料价格异常
5. 供应商指纹输出：高相似承包商组 + 建议的工商穿透核查方向
6. 变更轨迹输出：变更率行业对标 + 验收后调减项目清单 + 审减率联动
7. 围标检测输出：5维特征风险评分(0-5) + 证据链图谱（HTML/Markdown卡片）
""",
    ),

    # ── 数据审计Agent ──
    "data_audit": AuditAgentConfig(
        agent_id="data_audit",
        agent_name="数据审计Agent",
        expertise="大数据审计、文本分析、统计异常检测、行为模式识别、数据可视化",
        audit_standard="数据审计准则",
        kb_snippet=_KB_SNIPPETS["数据审计准则"],
        assigned_tools=[
            # v4 文本工具（全部5个）
            "text_hotword_analysis",
            "text_similarity_compare",
            "contract_field_extract",
            "personnel_profile_check",
            "budget_compliance_scan",
            # v7 统计/行为工具（全部4个）
            "benford_analysis",
            "supplier_fingerprint",
            "timeline_anomaly",
            "contract_change_trajectory",
            "data_script_generator",
            # v9 围标串标检测
            "bid_rigging_detect",            # 5维围标串标特征检测
            "evidence_chain_graph",          # 证据链图谱生成
        ],
        trigger_conditions=[
            "非结构化数据 > 1000条 → 启动全部v4+v7共9个工具",
            "大数据审计项目 → 并行执行所有文本分析和统计分析",
            "需要数据可视化 → 输出词云、分布图等",
            "全量数据分析需求 → 遵循'不选择，全部看'范式",
            "多工具交叉验证 → Benford+指纹+时间序列+变更轨迹联动分析",
        ],
        risk_scenarios=[
            "数据完整性不足：关键字段缺失或格式不一致",
            "数据时效性问题：使用过期数据进行分析",
            "异常值未处理：极端值影响分析结论",
            "相关性≠因果性：过度解读统计相关性",
            "统计异常≠审计结论：信号筛查需要人工审计判断确认",
            "工具链覆盖盲区：文本分析（v4）+统计/行为分析（v7）双翼需联动",
        ],
        output_requirements="""
1. 所有分析附带数据处理说明（数据量/清洗规则/异常处理）
2. 可视化输出附带数据源和生成参数
3. 异常检测结果标注置信度和可能误报率
4. 多工具交叉验证：同一异常被多个工具独立检出→提升可信度
5. 提供各工具的输入输出日志便于审计追踪
6. 异常信号≠审计结论——输出需区分"工具检出信号"和"建议人工核查方向"
""",
    ),
}


# ── Agent工具分配矩阵 ─────────────────────────────────────

def get_agent_tool_matrix() -> Dict[str, List[str]]:
    """获取Agent-工具分配矩阵"""
    return {
        config.agent_name: config.assigned_tools
        for config in AGENT_CONFIGS.values()
    }


def get_tool_agent_map() -> Dict[str, List[str]]:
    """获取工具-Agent反向映射"""
    tool_map: Dict[str, List[str]] = {}
    for config in AGENT_CONFIGS.values():
        for tool in config.assigned_tools:
            if tool not in tool_map:
                tool_map[tool] = []
            tool_map[tool].append(config.agent_name)
    return tool_map


def get_agent_for_project(project_type: str) -> List[AuditAgentConfig]:
    """根据项目类型获取应激活的Agent列表"""
    type_agent_map = {
        "economic_responsibility": ["national_audit", "data_audit"],
        "budget": ["national_audit", "internal_audit"],
        "medical_insurance": ["cpa_audit", "data_audit"],
        "procurement": ["cpa_audit", "internal_audit", "engineering_audit"],
        "project": ["engineering_audit", "data_audit"],
        "subsidy": ["national_audit", "data_audit"],
    }
    agent_ids = type_agent_map.get(project_type, ["data_audit"])
    return [AGENT_CONFIGS[aid] for aid in agent_ids]


def get_system_prompt(agent_id: str) -> str:
    """获取指定Agent的系统提示"""
    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        return "# 通用审计Agent\n\n请执行审计分析任务。"
    return config.system_prompt()


def get_all_system_prompts() -> Dict[str, str]:
    """获取所有Agent的系统提示"""
    return {
        aid: config.system_prompt()
        for aid, config in AGENT_CONFIGS.items()
    }


def inject_kb_to_prompt(base_prompt: str, agent_id: str) -> str:
    """将KB知识注入到基础提示中"""
    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        return base_prompt

    kb_block = f"""
## 审计准则知识库（自动注入）
{config.kb_snippet}

## 高风险场景提醒
"""
    for i, scenario in enumerate(config.risk_scenarios[:3], 1):
        kb_block += f"{i}. {scenario}\n"

    return base_prompt + "\n" + kb_block


# ── v8: 翻凭证Prompt模板库 ───────────────────────────────────

_VOUCHER_CHECK_TEMPLATES = {
    "AP": {
        "name": "应付账款科目校验",
        "template": (
            "请从序时账中筛选出摘要包含'{keyword}'但借方科目非'{expected_debit}'的凭证。"
            "列出凭证号、日期、摘要、借方科目、金额。按金额降序排列。"
        ),
        "default_params": {"keyword": "货款", "expected_debit": "库存商品/原材料"},
        "audit_focus": "跨期费用、虚假采购、科目错用",
        "risk_signals": [
            "货款对应非存货科目→可能虚假采购或费用跨期",
            "大量应付账款借方对应'其他应收款'→可能资金挪用",
            "年底集中大量货款凭证→关注截止性测试",
        ],
        "assigned_agents": ["national_audit", "cpa_audit"],
    },
    "AR": {
        "name": "应收账款异常贷方",
        "template": (
            "找出{account}贷方发生额前{top_n}名的非银行存款对应科目，"
            "并列出其摘要、日期、对方科目和金额。按金额降序排列。"
        ),
        "default_params": {"account": "应收账款", "top_n": 10},
        "audit_focus": "异常回款、关联方往来、债务重组",
        "risk_signals": [
            "应收账款贷方对应'其他应收款'→可能关联方利益输送",
            "应收账款贷方对应'营业外支出'→可能坏账核销不当",
            "大额贷方发生在审计截止日后→关注期后事项",
        ],
        "assigned_agents": ["cpa_audit", "internal_audit"],
    },
    "EXP": {
        "name": "费用重复报销检测",
        "template": (
            "筛选出同一报销人、同一金额（±{tolerance_pct}%浮动）在{window_days}天内重复出现的记录，"
            "输出报销人、凭证号、日期、摘要、金额。按重复次数降序排列。"
        ),
        "default_params": {"tolerance_pct": 5, "window_days": 3},
        "audit_focus": "重复报销、拆分报销、虚假报销",
        "risk_signals": [
            "同人同金额3天内重复→典型重复报销模式",
            "同人金额略低于审批阈值→拆分报销规避审批",
            "不同人同金额同摘要→团伙虚假报销",
        ],
        "assigned_agents": ["internal_audit", "national_audit"],
    },
    "FA": {
        "name": "固定资产资本化校验",
        "template": (
            "找出摘要包含'{keywords}'且金额超过{threshold}元，"
            "但未计入'{expected_account}'科目的记录。"
            "列出凭证号、日期、摘要、实际科目、金额。"
        ),
        "default_params": {
            "keywords": "采购/购买/设备",
            "threshold": 5000,
            "expected_account": "固定资产/在建工程",
        },
        "audit_focus": "资本化与费用化误判、资产完整性",
        "risk_signals": [
            "5000+设备采购记入'管理费用'→费用化处理影响当期利润",
            "设备采购记入'长期待摊费用'→变相费用化",
            "大量低值易耗品一次性费用化→关注资产实物管理",
        ],
        "assigned_agents": ["cpa_audit", "engineering_audit"],
    },
    "GENERAL": {
        "name": "通用翻查模板",
        "template": (
            "请从数据中：\n"
            "1. [筛选条件]：描述要筛选什么\n"
            "2. [排除条件]：描述要排除什么\n"
            "3. [输出要求]：描述怎么呈现结果（字段、排序、数量限制）"
        ),
        "default_params": {},
        "audit_focus": "通用",
        "risk_signals": [],
        "assigned_agents": ["data_audit"],
    },
}


def get_voucher_check_templates() -> Dict[str, Dict]:
    """获取所有翻凭证Prompt模板"""
    return _VOUCHER_CHECK_TEMPLATES


def get_templates_for_agent(agent_id: str) -> Dict[str, Dict]:
    """获取指定Agent适用的翻凭证模板"""
    return {
        k: v for k, v in _VOUCHER_CHECK_TEMPLATES.items()
        if agent_id in v.get("assigned_agents", [])
    }


def format_voucher_check_prompt(
    template_key: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    格式化翻凭证指令

    Args:
        template_key: AP | AR | EXP | FA | GENERAL
        params: 自定义参数字典（覆盖默认值）

    Returns:
        格式化后的Prompt指令
    """
    tpl = _VOUCHER_CHECK_TEMPLATES.get(template_key)
    if not tpl:
        return f"未知模板: {template_key}"

    merged_params = {**tpl["default_params"], **(params or {})}
    prompt = tpl["template"]

    # 替换占位符
    for k, v in merged_params.items():
        prompt = prompt.replace(f"{{{k}}}", str(v))

    # 附加审计关注和风险信号
    prompt += f"\n\n审计关注点：{tpl['audit_focus']}"
    if tpl["risk_signals"]:
        prompt += "\n风险信号参考："
        for sig in tpl["risk_signals"]:
            prompt += f"\n  - {sig}"

    return prompt


def inject_voucher_templates_to_prompt(
    base_prompt: str,
    agent_id: str,
) -> str:
    """将翻凭证模板注入到Agent系统提示"""
    templates = get_templates_for_agent(agent_id)
    if not templates:
        return base_prompt

    tpl_block = "\n## 翻凭证Prompt模板（v8自动注入）\n\n"
    tpl_block += "以下是可直接使用的审计翻凭证指令模板：\n\n"

    for key, tpl in templates.items():
        tpl_block += f"### {key}: {tpl['name']}\n"
        tpl_block += f"```\n{format_voucher_check_prompt(key)}\n```\n"
        tpl_block += f"适用Agent: {', '.join(tpl['assigned_agents'])}\n\n"

    return base_prompt + "\n" + tpl_block


# ── v11: 关联交易定性模板库 ───────────────────────────────────

_CHARACTERIZATION_TEMPLATES = {
    "SHELL_COMPANY": {
        "name": "影子公司+代持关联交易定性",
        "applicable_when": "检测到隐性关联方+非公允交易+未履行审批/回避程序",
        "template": (
            "{responsible_person}利用职务便利，通过{nominee_relation}代持设立{shell_company}（影子公司），"
            "与本公司发生关联交易。该交易未按规定履行关联交易审批及回避程序，"
            "交易对手实际控制人为本公司利害关系人，属于隐性关联交易；"
            "通过{transfer_method}等方式，变相转移国有资产、输送利益，"
            "违反《企业国有资产法》第四十三条、第四十四条规定，"
            "造成国有资产流失风险，属于违规关联交易、涉嫌利益输送。"
        ),
        "default_params": {
            "responsible_person": "某某（国企人员）",
            "nominee_relation": "亲友",
            "shell_company": "某某公司",
            "transfer_method": "高买低卖/虚增服务费用"
        },
        "legal_basis": [
            "《中华人民共和国企业国有资产法》第四十三条",
            "《中华人民共和国企业国有资产法》第四十四条",
        ],
        "evidence_requirements": [
            "代持协议或股权穿透证据",
            "交易价格偏离公允价的数据对比",
            "审批流程缺失/回避未执行的记录",
            "实际控制人与国企人员的关联关系证明",
        ],
        "risk_level": "high",
        "assigned_agents": ["national_audit", "internal_audit", "cpa_audit"],
    },
    "UNFAIR_PRICE": {
        "name": "非公允价格关联交易定性",
        "applicable_when": "交易价格偏离公允价≥10%+交易条款倾斜+无合理商业理由",
        "template": (
            "本公司与{related_party}（关联方）开展的{transaction_type}交易，"
            "交易价格偏离同期同类型非关联交易公允价格{deviation_pct}%，无合理商业理由；"
            "交易条款（{unfair_terms}）明显倾斜于关联方，实质为变相让利、利益输送；"
            "该交易未履行公允价格评估及审批程序，"
            "违反《企业国有资产法》第四十四条规定，损害国有资产权益，"
            "属于非公允关联交易、涉嫌利益输送。"
        ),
        "default_params": {
            "related_party": "某某公司",
            "transaction_type": "采购/销售",
            "deviation_pct": "XX",
            "unfair_terms": "账期、保证金、违约责任"
        },
        "legal_basis": [
            "《中华人民共和国企业国有资产法》第四十四条",
        ],
        "evidence_requirements": [
            "同期同地区同规格非关联交易价格对比表",
            "关联交易价格与公允价偏离度计算",
            "合同条款分析（账期/保证金/违约金对比）",
            "成本倒算或行业利润率对比",
        ],
        "risk_level": "high",
        "assigned_agents": ["cpa_audit", "internal_audit", "engineering_audit"],
    },
    "FREE_TRANSFER": {
        "name": "无偿输送/象征性收费定性",
        "applicable_when": "无对价或对价远低于成本+未签合同+未审批",
        "template": (
            "本公司{transfer_action}向{related_party}（关联方）提供{asset_type}，"
            "未收取合理对价、未签订规范合同、未履行审批程序；"
            "该行为直接违反《企业国有资产法》第四十四条""不得无偿向关联方提供资产""的禁止性规定，"
            "造成国有资产收益流失、{risk_type}，"
            "属于违规无偿输送、涉嫌利益输送。"
        ),
        "default_params": {
            "transfer_action": "无偿/以1元/年象征性价格",
            "related_party": "某某公司",
            "asset_type": "资金拆借/房产租赁/技术授权",
            "risk_type": "资金安全风险"
        },
        "legal_basis": [
            "《中华人民共和国企业国有资产法》第四十四条",
        ],
        "evidence_requirements": [
            "资产使用/资金占用的时长和规模",
            "同期市场租金/利率/许可费对比",
            "无合同或无对价条款的合同",
            "未履行审批程序的证据",
        ],
        "risk_level": "high",
        "assigned_agents": ["national_audit", "internal_audit"],
    },
    "FICTITIOUS_TRADE": {
        "name": "虚假贸易+空转走单定性",
        "applicable_when": "货物流/资金流/票据流不一致+无商业实质",
        "template": (
            "本公司与{related_party}（关联方）签订的{contract_type}合同，"
            "无真实货物交割/服务提供，货物流、资金流、票据流不一致，"
            "属于虚假贸易、空转走单；"
            "通过{method}等方式，套取国有资金、截留利润、输送利益；"
            "该交易无商业实质、未履行审批程序，"
            "违反《企业国有资产法》第四十三条、《公司法》第二十一条规定，"
            "造成国有资产流失，属于违规关联交易、涉嫌利益输送。"
        ),
        "default_params": {
            "related_party": "某某公司",
            "contract_type": "采购/销售",
            "method": "资金闭环、虚开发票"
        },
        "legal_basis": [
            "《中华人民共和国企业国有资产法》第四十三条",
            "《中华人民共和国公司法》第二十一条",
        ],
        "evidence_requirements": [
            "货物流：无物流单据/无实际交付/仓库记录空白",
            "资金流：全链路追踪→资金闭环/回流个人账户",
            "票据流：合同-发票-出入库单日期/金额/数量不一致",
            "商业实质：无上下游产业链支撑/交易对手为贸易空壳",
        ],
        "risk_level": "high",
        "assigned_agents": ["cpa_audit", "internal_audit", "data_audit"],
    },
    "COMPLIANCE_FLAW": {
        "name": "关联交易管理不规范（非利益输送）",
        "applicable_when": "偶尔/金额小/无利益流向/程序轻微瑕疵",
        "template": (
            "经核查，{transaction_desc}存在关联交易管理不规范问题："
            "{specific_issue}。"
            "该问题未发现利益单向流出或国有资产流失迹象，"
            "属于关联交易管理不规范、合规瑕疵。"
            "建议：{recommendation}。"
        ),
        "default_params": {
            "transaction_desc": "本公司与某某公司之间的交易",
            "specific_issue": "未及时履行关联交易审批/备案程序",
            "recommendation": "完善关联交易管理制度，加强审批流程管控"
        },
        "legal_basis": [],
        "evidence_requirements": [
            "确认金额较小、偶发性、无利益流向",
            "审批瑕疵的具体情况说明",
        ],
        "risk_level": "low",
        "assigned_agents": ["internal_audit"],
    },
}


def get_characterization_templates() -> Dict[str, Dict]:
    """获取所有关联交易定性模板"""
    return _CHARACTERIZATION_TEMPLATES


def get_characterization_templates_for_agent(agent_id: str) -> Dict[str, Dict]:
    """获取指定Agent适用的定性模板"""
    return {
        k: v for k, v in _CHARACTERIZATION_TEMPLATES.items()
        if agent_id in v.get("assigned_agents", [])
    }


def format_characterization(
    template_key: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    格式化关联交易定性表述

    Args:
        template_key: SHELL_COMPANY | UNFAIR_PRICE | FREE_TRANSFER | FICTITIOUS_TRADE | COMPLIANCE_FLAW
        params: 自定义参数（覆盖默认值）

    Returns:
        格式化后的定性表述
    """
    tpl = _CHARACTERIZATION_TEMPLATES.get(template_key)
    if not tpl:
        return f"未知定性模板: {template_key}"

    merged_params = {**tpl["default_params"], **(params or {})}
    text = tpl["template"]

    for k, v in merged_params.items():
        text = text.replace(f"{{{k}}}", str(v))

    # 附加法律依据和证据要求
    if tpl["legal_basis"]:
        text += "\n\n法律依据：\n"
        for law in tpl["legal_basis"]:
            text += f"  - {law}\n"

    if tpl["evidence_requirements"]:
        text += "\n证据要求：\n"
        for ev in tpl["evidence_requirements"]:
            text += f"  - {ev}\n"

    return text


def inject_characterization_templates_to_prompt(
    base_prompt: str,
    agent_id: str,
) -> str:
    """将关联交易定性模板注入到Agent系统提示"""
    templates = get_characterization_templates_for_agent(agent_id)
    if not templates:
        return base_prompt

    tpl_block = "\n## 关联交易定性模板（v11自动注入）\n\n"
    tpl_block += "查出关联交易问题后，使用以下标准定性表述（可直接套用）：\n\n"

    for key, tpl in templates.items():
        tpl_block += f"### {key}: {tpl['name']}\n"
        tpl_block += f"**适用条件**：{tpl['applicable_when']}\n\n"
        tpl_block += f"**标准表述**：\n> {format_characterization(key)}\n\n"
        tpl_block += f"**风险等级**：{tpl['risk_level']}\n\n"
        tpl_block += "---\n\n"

    # 避坑红线
    tpl_block += (
        '\n### ⚠️ 定性避坑红线\n\n'
        '1. **无确凿证据不定性「舞弊/贪腐」**：'
        '未拿到代持协议+资金闭环+利益分成+谈话承认→只用「涉嫌利益输送」，不用「舞弊/贪腐/侵占/挪用」\n'
        '2. **穿透核查留痕**：每个结论必须有证据支撑、可追溯\n'
        '3. **区分合规瑕疵与利益输送**：偶尔/小金额/轻微→「管理不规范」; 长期/大额/单向流出/人为操纵→「涉嫌利益输送」\n'
        '4. **终身追责意识**：今天的报告定性可能十年后被追溯→不妥协、不通融、不隐瞒\n'
    )

    return base_prompt + "\n" + tpl_block
