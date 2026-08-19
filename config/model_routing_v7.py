# 融策大模型路由配置 v7.0
# ================================
# 重大变更（v6→v7）：
# 1. 🔴 新增「敏感项目国产优先」独立路由链（涉密数据不出境）
# 2. 🔴 全局fallback重构：消除代理单点故障下的僵尸降级
# 3. 🟡 opus-5增加触发阈值（不再无脑升级）
# 4. 🟡 合同猎犬去opus-5，fable-5升primary
# 5. 🟡 T3创意层后移至国产模型之后

# ═══════════════════════════════════════════
# 模型清单（按能力分层）
# ═══════════════════════════════════════════

MODEL_POOL = {
    # === 第零层：终审/零容错 ===
    "custom-cbwyy-opus5/claude-opus-5": {
        "tier": "T0", "cost": "极高", "window": "200K", "region": "海外",
        "use_case": "复核签字、终审定案、≤2次/项目",
        "trigger": "P0发现≥2条 OR 涉及金额≥项目预算30% OR 总问题≥10条",
        "input": ["text", "image"]
    },
    "custom-cbwyy-opus/claude-opus-4-8": {
        "tier": "T0", "cost": "极高", "window": "200K", "region": "海外",
        "use_case": "opus-5备用，项目经费有限时",
        "input": ["text", "image"]
    },

    # === 第一层：核心业务主力 ===
    "custom-cbwyy-claude/claude-sonnet-5": {
        "tier": "T1", "cost": "高", "window": "200K", "region": "海外",
        "use_case": "合规审查、法规解读、合同分析、常规复核",
        "input": ["text", "image"]
    },
    "custom-cbwyy-top-v1/deepseek-v4-pro": {
        "tier": "T1", "cost": "免费", "window": "128K", "region": "国产",
        "use_case": "数据侦察、数值分析、统计检测、Benford",
        "input": ["text"]
    },
    "custom-cbwyy-qwen/qwen3.7-plus": {
        "tier": "T1", "cost": "低", "window": "128K", "region": "国产",
        "use_case": "中文公文、底稿撰写、报告撰写、方案撰写、敏感项目出口",
        "input": ["text", "image"]
    },

    # === 第二层：专项能力 ===
    "custom-cbwyy-gpt55/gpt-5.5": {
        "tier": "T2", "cost": "中", "window": "128K", "region": "海外",
        "use_case": "英文/国际业务、表达审查",
        "input": ["text", "image"]
    },
    "custom-cbwyy-gemini/gemini-3.1-pro-preview": {
        "tier": "T2", "cost": "中", "window": "1M", "region": "海外",
        "use_case": "超长文档(>128K)分析、长报告总结",
        "input": ["text", "image"]
    },
    "custom-cbwyy-fable/claude-fable-5": {
        "tier": "T2", "cost": "中", "window": "200K", "region": "海外",
        "use_case": "决策咨询·做决策前先问、方案多角度审视、思路批判",
        "input": ["text", "image"]
    },
    "custom-cbwyy-kimi/kimi-k3": {
        "tier": "T2", "cost": "低", "window": "128K", "region": "国产",
        "use_case": "国产推理、中文长链推理、敏感项目第二防线",
        "input": ["text", "image"]
    },
    "custom-cbwyy-glm/glm-5.2": {
        "tier": "T2", "cost": "低", "window": "128K", "region": "国产",
        "use_case": "国产推理、敏感项目首选(128K窗口)、长会议纪要",
        "input": ["text"]
    },

    # === 第三层：创意/发散 ===
    "custom-cbwyy-luna/gpt-5.6-luna": {
        "tier": "T3", "cost": "中", "window": "128K", "region": "海外",
        "use_case": "创意构思、头脑风暴、方案发散",
        "input": ["text", "image"]
    },
    "custom-cbwyy-sol/gpt-5.6-sol": {
        "tier": "T3", "cost": "中", "window": "128K", "region": "海外",
        "use_case": "luna备用、策略分析",
        "input": ["text", "image"]
    },
    "custom-cbwyy-terra/gpt-5.6-terra": {
        "tier": "T3", "cost": "中", "window": "128K", "region": "海外",
        "use_case": "luna第二备用、深度研究",
        "input": ["text", "image"]
    },

    # === 第四层：轻量/低成本 ===
    "custom-cbwyy-top-v1/deepseek-v4-flash": {
        "tier": "T4", "cost": "免费", "window": "64K", "region": "国产",
        "use_case": "日常对话、OCR后处理、分类归档、心跳定时",
        "input": ["text", "image"]
    },
    "custom-cbwyy-doubao/doubao-seed-2.0-lite": {
        "tier": "T4", "cost": "免费", "window": "128K", "region": "国产",
        "use_case": "轻量兜底、flash不可用时的替代",
        "input": ["text"]
    },

    # === 直连逃生 ===
    "deepseek-direct/deepseek-chat": {
        "tier": "ESCAPE", "cost": "免费", "window": "64K", "region": "国产",
        "use_case": "代理全挂时的最后逃生通道（不经过cbwyy.top）",
        "input": ["text"]
    },
}


# ═══════════════════════════════════════════
# opus-5 触发阈值（全局规则）
# ═══════════════════════════════════════════

OPUS5_TRIGGER = {
    "conditions": [
        "P0级发现≥2条",
        "涉及金额≥项目预算的30%",
        "总问题数≥10条",
        "涉及刑事责任/国有资产流失/重大安全事故",
        "最终签字盖章前的最后一次复核",
    ],
    "logic": "OR",  # 任一满足即触发
    "max_calls_per_project": 2,  # ≤2次/项目
    "note": "复核哨兵/法规检察官自动读此阈值，其余Agent不检查"
}


# ═══════════════════════════════════════════
# 第一层：Agent级路由（18个Agent）
# ═══════════════════════════════════════════

AGENT_MODEL_ROUTES = {
    # ─── 核心审计 Agent ───
    "data_scout": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
        "reason": "数值分析精确优先，pro免费"
    },
    "contract_hound": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "合同条文逻辑严谨；去opus-5，合同条款不需要T0"
    },
    "bid_hunter": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
        "reason": "模式检测+统计分析，pro精确；kimi国产兜底"
    },
    "law_inspector": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "法规条文需严谨；涉刑/国资流失按阈值自动升级opus-5"
    },
    "workpaper_crafter": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro", "custom-cbwyy-gpt55/gpt-5.5"],
        "reason": "底稿中文公文，qwen原生最优"
    },
    "report_writer": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gpt55/gpt-5.5"],
        "reason": "审计报告中文公文，格式要求严格"
    },
    "review_sentinel": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-opus/claude-opus-4-8", "custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "复核：sonnet常规→Opus5.0触发阈值→opus-4-8备用→qwen兜底"
    },

    # ─── 工程咨询 Agent ───
    "budget_estimator": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
        "reason": "工程量计算需数值精确，pro免费"
    },
    "settlement_auditor": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-kimi/kimi-k3"],
        "reason": "结算审计=计算+合规，pro主力"
    },
    "fiscal_reviewer": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "财政评审重政策合规，sonnet严谨"
    },

    # ─── 绩效评价 Agent ───
    "performance_evaluator": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-fable/claude-fable-5", "custom-cbwyy-claude/claude-sonnet-5"],
        "reason": "绩效评价=数据分析+指标打分；指标设计先问fable多角度审视"
    },

    # ─── 专项检测 Agent ───
    "expert_bias_detector": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-kimi/kimi-k3", "custom-cbwyy-glm/glm-5.2"],
        "reason": "统计检测，pro精确；国产推理兜底"
    },
    "meeting_minutes_analyzer": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-glm/glm-5.2", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "中文会议纪要，qwen原生最优；长纪要(>128K)降级GLM国产"
    },

    # ─── 数据运维 Agent ───
    "ocr_processor": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "OCR后文本清洗，轻量任务"
    },
    "data_classifier": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "分类归档，轻量任务"
    },
    "data_desensitizer": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "脱敏任务，轻量精确"
    },
    "adjustment_scribe": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
        "reason": "调整分录=财务精确，不能出错"
    },

    # ─── 方案撰写 Agent ───
    "plan_writer": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-fable/claude-fable-5", "custom-cbwyy-claude/claude-sonnet-5"],
        "reason": "实施方案中文公文；重难点分析先问fable多视角审视"
    }
}


# ═══════════════════════════════════════════
# 第二层：场景路由（15个场景）
# ═══════════════════════════════════════════

SCENARIO_MODEL_ROUTES = {
    # 免费日常
    "daily_chat": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "日常对话/信息查询"
    },
    "heartbeat_task": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["deepseek-direct/deepseek-chat"],
        "desc": "心跳/定时任务，必须低成本。代理挂→直连逃生"
    },

    # 数据分析
    "data_check": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
        "desc": "数值核查/统计检测"
    },
    "financial_analysis": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-kimi/kimi-k3"],
        "desc": "财务分析/异常检测/金额复核"
    },

    # 合规审查
    "compliance_check": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-qwen/qwen3.7-plus"],
        "desc": "法规合规性审查；重大合规升级opus-5"
    },
    "law_interpretation": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-qwen/qwen3.7-plus"],
        "desc": "法律条文解读与适用，零容错"
    },

    # 中文公文
    "gov_document": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gemini/gemini-3.1-pro-preview"],
        "desc": "政府公文/审计报告/方案"
    },
    "report_writing": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gpt55/gpt-5.5"],
        "desc": "审计报告/绩效报告撰写"
    },

    # 创意/方案（T3层）
    "creative": {
        "primary": "custom-cbwyy-luna/gpt-5.6-luna",
        "fallbacks": ["custom-cbwyy-fable/claude-fable-5", "custom-cbwyy-sol/gpt-5.6-sol"],
        "desc": "创意构思/方案设计/头脑风暴；先发散再给fable审视"
    },

    # 长文档
    "long_document": {
        "primary": "custom-cbwyy-gemini/gemini-3.1-pro-preview",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-glm/glm-5.2"],
        "desc": "超长文档(>128K)/合同包批量分析；glm国产长文档兜底"
    },

    # 英文/国际
    "english": {
        "primary": "custom-cbwyy-gpt55/gpt-5.5",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
        "desc": "英文润色/翻译/国际业务"
    },

    # 终审/签字（opus-5按阈值触发）
    "final_review": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-opus/claude-opus-4-8"],
        "desc": "终审签字：sonnet常规→Opus5.0触发阈值→opus-4-8备用·≤2次/项目"
    },

    # 国产推理
    "china_reasoning": {
        "primary": "custom-cbwyy-glm/glm-5.2",
        "fallbacks": ["custom-cbwyy-kimi/kimi-k3", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "国产推理模型，GLM 128K窗口适合长文档"
    },

    # 咨询顾问 ⭐ fable-5升primary
    "consulting": {
        "primary": "custom-cbwyy-fable/claude-fable-5",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-luna/gpt-5.6-luna"],
        "desc": "重大决策前先问fable：做决策前先问，多角度审视、批判性分析"
    },

    # 轻量任务
    "lightweight": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "OCR后处理/分类/归档"
    },

    # ⭐ 新增：敏感项目国产优先路由
    "sensitive_project": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": [
            "custom-cbwyy-top-v1/deepseek-v4-pro",
            "custom-cbwyy-glm/glm-5.2",
            "custom-cbwyy-kimi/kimi-k3",
            "custom-cbwyy-top-v1/deepseek-v4-flash",
            "custom-cbwyy-doubao/doubao-seed-2.0-lite",
            "deepseek-direct/deepseek-chat",
        ],
        "desc": "涉密项目纯国产链：经责审计/专项资金/国企审计/招投标/政府补贴。数据不出境！"
    },
}


# ═══════════════════════════════════════════
# 第三层：全局Fallback链
# ═══════════════════════════════════════════

# 普通项目（14级，国产模型插队到海外模型之间）
GLOBAL_DEFAULT = {
    "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
    "fallbacks": [
        # 第1-2级：仍然是cbwyy.top，但快速过渡
        "custom-cbwyy-top-v1/deepseek-v4-pro",       #  2. 免费主力（国产·同代理）
        "custom-cbwyy-qwen/qwen3.7-plus",             #  3. ⭐ 国产第一出口（同代理但国产）
        "custom-cbwyy-kimi/kimi-k3",                  #  4. ⭐ 国产第二防线
        "custom-cbwyy-glm/glm-5.2",                   #  5. ⭐ 国产第三防线(128K)
        # 第6-10级：海外模型（国产全部不可用时）
        "custom-cbwyy-opus5/claude-opus-5",           #  6. 终审最强
        "custom-cbwyy-gemini/gemini-3.1-pro-preview", #  7. 长文档
        "custom-cbwyy-fable/claude-fable-5",          #  8. 咨询顾问
        "custom-cbwyy-claude/claude-sonnet-5",        #  9. 合规严谨
        "custom-cbwyy-gpt55/gpt-5.5",                 # 10. 英文/表达
        # 第11-13级：创意层
        "custom-cbwyy-luna/gpt-5.6-luna",             # 11. 创意
        "custom-cbwyy-sol/gpt-5.6-sol",               # 12. 策略
        "custom-cbwyy-terra/gpt-5.6-terra",           # 13. 深度研究
        # 第14-15级：最终兜底
        "custom-cbwyy-doubao/doubao-seed-2.0-lite",   # 14. 免费轻量（国产）
        "deepseek-direct/deepseek-chat",              # 15. ⭐ 直连逃生（不经过代理）
    ]
}


# 敏感项目专用（纯国产·数据不出境·7级降级）
SENSITIVE_FALLBACK = {
    "primary": "custom-cbwyy-qwen/qwen3.7-plus",
    "fallbacks": [
        "custom-cbwyy-top-v1/deepseek-v4-pro",        #  2. 免费主力（国产）
        "custom-cbwyy-glm/glm-5.2",                   #  3. 智谱128K（国产）
        "custom-cbwyy-kimi/kimi-k3",                  #  4. 月之暗面（国产）
        "custom-cbwyy-top-v1/deepseek-v4-flash",      #  5. flash轻量（国产）
        "custom-cbwyy-doubao/doubao-seed-2.0-lite",   #  6. 豆包免费（国产）
        "deepseek-direct/deepseek-chat",              #  7. ⭐ 直连逃生
    ],
    "desc": "纯国产链，零海外模型。适用：经责审计/专项资金/国企审计/招投标/政府补贴"
}


# ═══════════════════════════════════════════
# 敏感项目开关
# ═══════════════════════════════════════════

# 敏感项目强制国产 primary（默认开启）
# True  → Agent级路由在敏感项目下，primary 也强制换为国产品牌（涉密数据不出境）
# False → 仅过滤 fallback 为国产，primary 保持 Agent 专属模型（v6 旧行为）
SENSITIVE_FORCE_DOMESTIC_PRIMARY = True


# ═══════════════════════════════════════════
# 敏感项目自动识别
# ═══════════════════════════════════════════

SENSITIVE_KEYWORDS = [
    # 业务线
    "经责", "经济责任", "离任审计", "任中审计", "自然资源",
    "专项资金", "专项转移支付", "社保基金", "营养餐",
    "国企", "国有资产", "国企审计",
    "招投标", "围标", "串标",
    "政府补贴", "补贴审计", "财政补贴",
    # 内容
    "涉密", "敏感", "机密", "国家秘密",
    # 部门
    "纪检", "巡察", "纪委", "监察委",
    "财政局", "审计局", "发改委",
]

def is_sensitive_project(project_name: str, project_type: str = "") -> bool:
    """判断是否为敏感项目（需走国产路由）"""
    text = f"{project_name} {project_type}".lower()
    return any(kw in text for kw in SENSITIVE_KEYWORDS)


# ═══════════════════════════════════════════
# 路由查询函数
# ═══════════════════════════════════════════

def get_agent_route(agent_name: str, project_info: dict = None):
    """根据Agent名获取模型路由（可选项目信息判断敏感路由）"""
    route = AGENT_MODEL_ROUTES.get(agent_name)
    if not route:
        return GLOBAL_DEFAULT

    # 敏感项目：强制国产链（primary + fallbacks）
    if project_info and is_sensitive_project(
        project_info.get("name", ""),
        project_info.get("type", "")
    ):
        route = _sensitive_route(route)

    return route


def get_scenario_route(scenario: str, sensitive: bool = False):
    """根据场景名获取模型路由"""
    if sensitive and scenario != "sensitive_project":
        # 敏感项目直接走sensitive_project链
        return SCENARIO_MODEL_ROUTES.get("sensitive_project", SENSITIVE_FALLBACK)
    return SCENARIO_MODEL_ROUTES.get(scenario, GLOBAL_DEFAULT)


def get_best_route(agent_name=None, scenario=None, project_info=None):
    """
    三层路由：Agent > 场景 > 全局
    敏感项目自动切换国产链
    """
    is_sensitive = False
    if project_info:
        is_sensitive = is_sensitive_project(
            project_info.get("name", ""),
            project_info.get("type", "")
        )

    if agent_name and agent_name in AGENT_MODEL_ROUTES:
        route = AGENT_MODEL_ROUTES[agent_name]
        if is_sensitive:
            route = _sensitive_route(route)
        return ("agent", agent_name, route)

    if scenario and scenario in SCENARIO_MODEL_ROUTES:
        if is_sensitive:
            return ("scenario", "sensitive_project",
                    SCENARIO_MODEL_ROUTES["sensitive_project"])
        return ("scenario", scenario, SCENARIO_MODEL_ROUTES[scenario])

    return ("global",
            "sensitive" if is_sensitive else "default",
            SENSITIVE_FALLBACK if is_sensitive else GLOBAL_DEFAULT)


def get_fallback_chain(sensitive: bool = False):
    """获取完整fallback链"""
    return SENSITIVE_FALLBACK if sensitive else GLOBAL_DEFAULT


def get_model_tier(model_id: str):
    """查模型层级"""
    return MODEL_POOL.get(model_id, {}).get("tier", "UNKNOWN")


def get_model_region(model_id: str):
    """查模型区域（国产/海外）"""
    return MODEL_POOL.get(model_id, {}).get("region", "未知")


def get_cost_estimate(model_id: str):
    """查模型成本"""
    return MODEL_POOL.get(model_id, {}).get("cost", "未知")


def _sensitive_route(route: dict) -> dict:
    """敏感项目路由：强制全国产（primary + fallbacks）

    - fallbacks 一律过滤为国产
    - SENSITIVE_FORCE_DOMESTIC_PRIMARY=True 时，海外 primary 也替换为国产：
      优先提升 fallback 中排位最前的国产模型；若无可提升项则用敏感链默认
    """
    route = route.copy()
    route["fallbacks"] = _filter_domestic(route["fallbacks"])

    if SENSITIVE_FORCE_DOMESTIC_PRIMARY and \
            MODEL_POOL.get(route["primary"], {}).get("region") != "国产":
        if route["fallbacks"]:
            # 提升排位最前的国产 fallback 为 primary；
            # 原海外 primary 不入链（敏感项目链条必须全国产）
            route["primary"] = route["fallbacks"][0]
            route["fallbacks"] = route["fallbacks"][1:]
            if not route["fallbacks"]:
                # 无剩余国产降级 → 补敏感链默认降级
                route["fallbacks"] = list(SENSITIVE_FALLBACK["fallbacks"])
        else:
            # 该 Agent 无国产 fallback → 整体走敏感链
            route["primary"] = SENSITIVE_FALLBACK["primary"]
            route["fallbacks"] = list(SENSITIVE_FALLBACK["fallbacks"])

    return route


def _filter_domestic(fallbacks: list) -> list:
    """过滤出国产模型（敏感项目用）"""
    domestic = [f for f in fallbacks
                if MODEL_POOL.get(f, {}).get("region") == "国产"]
    if not domestic:
        domestic = [
            "custom-cbwyy-qwen/qwen3.7-plus",
            "custom-cbwyy-top-v1/deepseek-v4-pro",
            "custom-cbwyy-glm/glm-5.2",
            "custom-cbwyy-kimi/kimi-k3",
            "deepseek-direct/deepseek-chat",
        ]
    return domestic
