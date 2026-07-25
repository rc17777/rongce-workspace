# 融策大模型路由配置 v6.0
# ================================
# 模型池：17个（15业务 + 1直连逃生 + 1生图）
# 新增：claude-opus-5（cbwyy.top，anthropic-messages）
# 路由优先级：Agent路由 > 场景路由 > 全局默认

# ═══════════════════════════════════════════
# 模型清单（按能力分层）
# ═══════════════════════════════════════════

MODEL_POOL = {
    # === 第零层：终审/零容错 ===
    "custom-cbwyy-opus5/claude-opus-5": {
        "tier": "T0", "cost": "极高", "window": "200K",
        "use_case": "复核签字、终审定案、≤2次/项目",
        "input": ["text", "image"]
    },
    "custom-cbwyy-opus/claude-opus-4-8": {
        "tier": "T0", "cost": "极高", "window": "200K",
        "use_case": "opus-5的备用，项目经费有限时退而求其次",
        "input": ["text", "image"]
    },

    # === 第一层：核心业务主力 ===
    "custom-cbwyy-claude/claude-sonnet-5": {
        "tier": "T1", "cost": "高", "window": "200K",
        "use_case": "合规审查、法规解读、合同分析、常规复核",
        "input": ["text", "image"]
    },
    "custom-cbwyy-top-v1/deepseek-v4-pro": {
        "tier": "T1", "cost": "免费", "window": "128K",
        "use_case": "数据侦察、数值分析、统计检测、Benford",
        "input": ["text"]
    },
    "custom-cbwyy-qwen/qwen3.7-plus": {
        "tier": "T1", "cost": "低", "window": "128K",
        "use_case": "中文公文、底稿撰写、报告撰写、方案撰写",
        "input": ["text", "image"]
    },

    # === 第二层：专项能力 ===
    "custom-cbwyy-gpt55/gpt-5.5": {
        "tier": "T2", "cost": "中", "window": "128K",
        "use_case": "英文/国际业务、表达审查",
        "input": ["text", "image"]
    },
    "custom-cbwyy-gemini/gemini-3.1-pro-preview": {
        "tier": "T2", "cost": "中", "window": "1M",
        "use_case": "超长文档(>128K)分析、长报告总结",
        "input": ["text", "image"]
    },
    "custom-cbwyy-fable/claude-fable-5": {
        "tier": "T2", "cost": "中", "window": "200K",
        "use_case": "决策咨询、方案审视、多角度批判性分析",
        "input": ["text", "image"]
    },
    "custom-cbwyy-kimi/kimi-k3": {
        "tier": "T2", "cost": "低", "window": "128K",
        "use_case": "国产推理、中文长链推理",
        "input": ["text", "image"]
    },
    "custom-cbwyy-glm/glm-5.2": {
        "tier": "T2", "cost": "低", "window": "128K",
        "use_case": "国产推理、敏感项目首选、长会议纪要",
        "input": ["text"]
    },

    # === 第三层：创意/发散 ===
    "custom-cbwyy-luna/gpt-5.6-luna": {
        "tier": "T3", "cost": "中", "window": "128K",
        "use_case": "创意构思、头脑风暴、方案发散",
        "input": ["text", "image"]
    },
    "custom-cbwyy-sol/gpt-5.6-sol": {
        "tier": "T3", "cost": "中", "window": "128K",
        "use_case": "luna备用、策略分析",
        "input": ["text", "image"]
    },
    "custom-cbwyy-terra/gpt-5.6-terra": {
        "tier": "T3", "cost": "中", "window": "128K",
        "use_case": "luna第二备用、深度研究",
        "input": ["text", "image"]
    },

    # === 第四层：轻量/低成本 ===
    "custom-cbwyy-top-v1/deepseek-v4-flash": {
        "tier": "T4", "cost": "免费", "window": "64K",
        "use_case": "日常对话、OCR后处理、分类归档、心跳定时",
        "input": ["text", "image"]
    },
    "custom-cbwyy-doubao/doubao-seed-2.0-lite": {
        "tier": "T4", "cost": "免费", "window": "128K",
        "use_case": "轻量兜底、flash不可用时的替代",
        "input": ["text"]
    },

    # === 直连逃生 ===
    "deepseek-direct/deepseek-chat": {
        "tier": "ESCAPE", "cost": "免费", "window": "64K",
        "use_case": "代理全挂时的最后逃生通道",
        "input": ["text"]
    },
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
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "合同条文逻辑严谨，sonnet主力；重大合同升级opus-5"
    },
    "bid_hunter": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
        "reason": "模式检测+统计分析，pro精确；kimi国产兜底"
    },
    "law_inspector": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "法规条文需严谨逻辑；P0问题升级opus-5"
    },
    "workpaper_crafter": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro", "custom-cbwyy-gpt55/gpt-5.5"],
        "reason": "底稿是中文公文，qwen原生中文最优"
    },
    "report_writer": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gpt55/gpt-5.5"],
        "reason": "审计报告中文公文，格式要求严格"
    },
    "review_sentinel": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-opus/claude-opus-4-8", "custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "复核零容错：sonnet→opus-5(终审)→opus-4-8(备用终审)→qwen"
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
# 第二层：场景路由（14个场景）
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
        "desc": "心跳/定时任务，必须低成本"
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
        "desc": "法规合规性审查，严谨优先；重大合规升级opus-5"
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

    # 创意/方案
    "creative": {
        "primary": "custom-cbwyy-luna/gpt-5.6-luna",
        "fallbacks": ["custom-cbwyy-sol/gpt-5.6-sol", "custom-cbwyy-terra/gpt-5.6-terra"],
        "desc": "创意构思/方案设计/头脑风暴"
    },

    # 长文档
    "long_document": {
        "primary": "custom-cbwyy-gemini/gemini-3.1-pro-preview",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "超长文档(>128K)/合同包批量分析"
    },

    # 英文/国际
    "english": {
        "primary": "custom-cbwyy-gpt55/gpt-5.5",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
        "desc": "英文润色/翻译/国际业务"
    },

    # 终审/签字 ⭐ opus-5加持
    "final_review": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-opus/claude-opus-4-8"],
        "desc": "终审签字，sonnet→opus-5(最强)→opus-4-8"
    },

    # 国产推理
    "china_reasoning": {
        "primary": "custom-cbwyy-glm/glm-5.2",
        "fallbacks": ["custom-cbwyy-kimi/kimi-k3", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "国产推理模型，敏感项目数据不出境"
    },

    # 咨询顾问
    "consulting": {
        "primary": "custom-cbwyy-fable/claude-fable-5",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-luna/gpt-5.6-luna"],
        "desc": "做决策前先问，多角度审视"
    },

    # 轻量任务
    "lightweight": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "OCR后处理/分类/归档"
    },
}


# ═══════════════════════════════════════════
# 第三层：全局Fallback链（15级）
# ═══════════════════════════════════════════

GLOBAL_DEFAULT = {
    "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
    "fallbacks": [
        "custom-cbwyy-top-v1/deepseek-v4-pro",       #  2. 免费主力
        "custom-cbwyy-opus5/claude-opus-5",           #  3. 最强终审
        "custom-cbwyy-gemini/gemini-3.1-pro-preview", #  4. 长文档
        "custom-cbwyy-qwen/qwen3.7-plus",             #  5. 中文公文
        "custom-cbwyy-fable/claude-fable-5",          #  6. 咨询顾问
        "custom-cbwyy-claude/claude-sonnet-5",        #  7. 合规严谨
        "custom-cbwyy-gpt55/gpt-5.5",                 #  8. 英文/表达
        "custom-cbwyy-luna/gpt-5.6-luna",             #  9. 创意发散
        "custom-cbwyy-sol/gpt-5.6-sol",               # 10. 策略分析
        "custom-cbwyy-terra/gpt-5.6-terra",           # 11. 深度研究
        "custom-cbwyy-kimi/kimi-k3",                  # 12. 国产推理
        "custom-cbwyy-glm/glm-5.2",                   # 13. 国产长文档
        "custom-cbwyy-doubao/doubao-seed-2.0-lite",   # 14. 免费轻量
        "deepseek-direct/deepseek-chat",              # 15. 直连逃生
    ]
}


# ═══════════════════════════════════════════
# 路由查询函数
# ═══════════════════════════════════════════

def get_agent_route(agent_name):
    return AGENT_MODEL_ROUTES.get(agent_name, GLOBAL_DEFAULT)

def get_scenario_route(scenario):
    return SCENARIO_MODEL_ROUTES.get(scenario, GLOBAL_DEFAULT)

def get_best_route(agent_name=None, scenario=None):
    """优先级: agent > scenario > global"""
    if agent_name and agent_name in AGENT_MODEL_ROUTES:
        return ("agent", agent_name, AGENT_MODEL_ROUTES[agent_name])
    if scenario and scenario in SCENARIO_MODEL_ROUTES:
        return ("scenario", scenario, SCENARIO_MODEL_ROUTES[scenario])
    return ("global", "default", GLOBAL_DEFAULT)

def get_model_tier(model_id):
    """查模型层级"""
    return MODEL_POOL.get(model_id, {}).get("tier", "UNKNOWN")

def get_cost_estimate(model_id):
    """查模型成本"""
    return MODEL_POOL.get(model_id, {}).get("cost", "未知")
