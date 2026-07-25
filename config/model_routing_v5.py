# 融策大模型路由配置 v5.0
# ================================
# 双层路由：场景路由（api_gateway.py）+ Agent路由（agent_registry.json）
# 优先级：Agent路由 > 场景路由 > 全局默认

# ═══════════════════════════════════════════
# 第一层：Agent级路由（22个Agent各自偏好）
# ═══════════════════════════════════════════

AGENT_MODEL_ROUTES = {
    # ─── 核心审计 Agent ───
    "data_scout": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash"],
        "reason": "数值分析精确优先，pro免费"
    },
    "contract_hound": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro", "custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "合同条文逻辑严谨，sonnet最强"
    },
    "bid_hunter": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
        "reason": "模式检测+统计分析，pro精确"
    },
    "law_inspector": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "法规条文解读需要严谨逻辑"
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
        "reason": "复核零容错，最强逻辑模型，紧急时上opus-5"
    },

    # ─── 工程咨询 Agent ───
    "budget_estimator": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash"],
        "reason": "工程量计算需要数值精确"
    },
    "settlement_auditor": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
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
        "reason": "绩效评价=数据分析+指标打分；指标体系设计先问fable顾问"
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
        "reason": "中文会议纪要，qwen原生理解最优；长纪要(>128K)降级GLM国产推理"
    },

    # ─── 数据运维 Agent ───
    "ocr_processor": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus"],
        "reason": "OCR后文本清洗，轻量任务，flash足够"
    },
    "data_classifier": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "分类归档，轻量任务"
    },
    "data_desensitizer": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "reason": "脱敏任务，轻量但需精确匹配"
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
        "reason": "实施方案中文公文格式；重难点分析先问fable顾问多角度审视"
    }
}

# ═══════════════════════════════════════════
# 第二层：场景路由（按任务类型，无特定Agent时使用）
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
        "desc": "数值核查/Benford/统计分析"
    },
    "financial_analysis": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-kimi/kimi-k3"],
        "desc": "财务分析、异常检测、金额复核"
    },

    # 合规审查
    "compliance_check": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-opus/claude-opus-4-8"],
        "desc": "法规合规性审查，逻辑严谨优先"
    },
    "law_interpretation": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "法律条文解读与适用"
    },

    # 中文公文
    "gov_document": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gemini/gemini-3.1-pro-preview"],
        "desc": "政府公文/审计报告/方案撰写"
    },
    "report_writing": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gpt55/gpt-5.5"],
        "desc": "审计报告、绩效评价报告撰写"
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
        "desc": "超长文档(>128K)分析/总结"
    },

    # 英文
    "english": {
        "primary": "custom-cbwyy-gpt55/gpt-5.5",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
        "desc": "英文润色/翻译/国际业务"
    },

    # 压舱石
    "final_review": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus/claude-opus-4-8"],
        "desc": "终审/最终签字，零容错"
    },

    # 国产推理
    "china_reasoning": {
        "primary": "custom-cbwyy-glm/glm-5.2",
        "fallbacks": ["custom-cbwyy-kimi/kimi-k3", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "国产推理模型，敏感项目优先。GLM 128K窗口适合长文档"
    },

    # 咨询顾问
    "consulting": {
        "primary": "custom-cbwyy-fable/claude-fable-5",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-luna/gpt-5.6-luna"],
        "desc": "做决策前先问，战略咨询"
    },

    # 轻量任务
    "lightweight": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "OCR后处理/分类/归档/格式转换"
    },
}

# ═══════════════════════════════════════════
# 第三层：全局默认（fallback链，所有Agent的最终兜底）
# ═══════════════════════════════════════════

GLOBAL_DEFAULT = {
    "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
    "fallbacks": [
        "custom-cbwyy-top-v1/deepseek-v4-pro",
        "custom-cbwyy-gemini/gemini-3.1-pro-preview",
        "custom-cbwyy-qwen/qwen3.7-plus",
        "custom-cbwyy-fable/claude-fable-5",
        "custom-cbwyy-claude/claude-sonnet-5",
        "custom-cbwyy-gpt55/gpt-5.5",
        "custom-cbwyy-luna/gpt-5.6-luna",
        "custom-cbwyy-sol/gpt-5.6-sol",
        "custom-cbwyy-terra/gpt-5.6-terra",
        "custom-cbwyy-kimi/kimi-k3",
        "custom-cbwyy-glm/glm-5.2",
        "custom-cbwyy-doubao/doubao-seed-2.0-lite",
        "deepseek-direct/deepseek-chat",
    ]
}

# ═══════════════════════════════════════════
# 路由查询函数
# ═══════════════════════════════════════════

def get_agent_route(agent_name):
    """根据Agent名获取模型路由"""
    return AGENT_MODEL_ROUTES.get(agent_name, GLOBAL_DEFAULT)

def get_scenario_route(scenario):
    """根据场景名获取模型路由"""
    return SCENARIO_MODEL_ROUTES.get(scenario, GLOBAL_DEFAULT)

def get_best_route(agent_name=None, scenario=None):
    """
    双层路由：Agent优先，场景兜底，全局保底
    优先级: agent > scenario > global
    """
    if agent_name and agent_name in AGENT_MODEL_ROUTES:
        return ("agent", agent_name, AGENT_MODEL_ROUTES[agent_name])
    if scenario and scenario in SCENARIO_MODEL_ROUTES:
        return ("scenario", scenario, SCENARIO_MODEL_ROUTES[scenario])
    return ("global", "default", GLOBAL_DEFAULT)
