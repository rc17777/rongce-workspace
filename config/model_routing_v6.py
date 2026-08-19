# 融策大模型路由配置 v6.0（四信号 × 四方法）
# =====================================================
# 设计依据：AURORA视界《一篇讲清模型路由》
#   - 优化目标：单次成功任务的总成本（模型+工具+重试+时延），不是 Token 单价
#   - 四类信号：任务(task) / 轨迹(trajectory) / 系统(system) / 风险(risk)
#   - 四种方法：规则(rule) / 分类(classification) / 级联(cascade) / 阶段(stage)
#   - 铁律：路由可以换模型，验收标准不能跟着变化；高风险操作不跳过权限与人工审批
#
# 决策优先级（从高到低）：
#   1. 风险策略   — 高风险操作强制强模型 + 人工审批
#   2. 轨迹信号   — 卡住/重复失败 → 级联升级（带升级冷却）
#   3. 阶段路由   — 任务进度阶段（探索/规划/执行/验收）→ 档位
#   4. 分类路由   — 任务特征标签 → 能力档位
#   5. 规则路由   — Agent > 场景 > 全局默认（继承 v5）
#   6. 系统状态   — 候选模型不可用/限流 → fallback 链
#
# 兼容性：get_agent_route / get_scenario_route / get_best_route 与 v5 同名同行为，
#         新能力全部通过 Router 类暴露。v5 文件保留不删。

import json
import os
import time
from datetime import datetime

# ═══════════════════════════════════════════
# 0. 模型池：能力档位
# ═══════════════════════════════════════════
# tier 是路由的中间语言：方法算出"该用哪一档"，档位再映射到具体模型。
# 新增模型只需登记到这里，各路由规则不用改。

MODEL_POOL = {
    # 高效档：便宜、快、稳定，适合边界清晰/可验证/机械执行
    "efficient": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "常规执行：搜索/提取/分类/格式化/机械编辑",
    },
    # 精确档：数值与财务计算，v4-pro 免费且精确
    "numerical": {
        "primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
        "desc": "数值核查/Benford/结算计算/调整分录",
    },
    # 强推理档：疑难会诊，跨文件诊断/方案取舍
    "strong": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "合规审查/法规解读/跨文件推理/方案取舍",
    },
    # 中文公文档：qwen 原生中文
    "chinese_doc": {
        "primary": "custom-cbwyy-qwen/qwen3.7-plus",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gpt55/gpt-5.5"],
        "desc": "审计报告/底稿/政府公文/方案撰写",
    },
    # 长上下文档：>128K
    "long_context": {
        "primary": "custom-cbwyy-gemini/gemini-3.1-pro-preview",
        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
        "desc": "超长文档分析/长会议纪要",
    },
    # 创意档
    "creative": {
        "primary": "custom-cbwyy-luna/gpt-5.6-luna",
        "fallbacks": ["custom-cbwyy-sol/gpt-5.6-sol", "custom-cbwyy-terra/gpt-5.6-terra"],
        "desc": "创意/头脑风暴/方案设计",
    },
    # 咨询档：决策前先问
    "consulting": {
        "primary": "custom-cbwyy-fable/claude-fable-5",
        "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-luna/gpt-5.6-luna"],
        "desc": "战略咨询/多角度审视",
    },
    # 安全网档：零容错终审，可触发 opus（≤2次/项目）
    "safety_net": {
        "primary": "custom-cbwyy-claude/claude-sonnet-5",
        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-opus/claude-opus-4-8"],
        "desc": "终审签字/高风险决策，最强逻辑",
    },
}

# 档位能力梯度（用于级联升级：卡住时升一档）
TIER_LADDER = ["efficient", "numerical", "chinese_doc", "long_context",
               "strong", "consulting", "creative", "safety_net"]

# 级联升级目标映射：从基础档位直接升到下一档推理能力（比线性阶梯更合理）
CASCADE_UPGRADE_MAP = {
    "efficient": "numerical",     # flash 卡住 → pro 精确档
    "numerical": "strong",        # 数据任务卡住 → 强推理诊断
    "chinese_doc": "strong",      # 公文卡住 → 强推理
    "long_context": "strong",
    "creative": "strong",
    "consulting": "strong",
    "strong": "safety_net",       # 强模型也卡住 → 安全网（≤2次/项目）
    "safety_net": "safety_net",   # 已到顶不再升
}

# ═══════════════════════════════════════════
# 1. 规则路由（继承 v5 的 Agent/场景规则，原样保留）
# ═══════════════════════════════════════════

AGENT_MODEL_ROUTES = {
    # ─── 核心审计 Agent ───
    "data_scout": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                   "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash"],
                   "reason": "数值分析精确优先，pro免费"},
    "contract_hound": {"primary": "custom-cbwyy-claude/claude-sonnet-5",
                       "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro", "custom-cbwyy-qwen/qwen3.7-plus"],
                       "reason": "合同条文逻辑严谨，sonnet最强"},
    "bid_hunter": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                   "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
                   "reason": "模式检测+统计分析，pro精确"},
    "law_inspector": {"primary": "custom-cbwyy-claude/claude-sonnet-5",
                      "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
                      "reason": "法规条文解读需要严谨逻辑"},
    "workpaper_crafter": {"primary": "custom-cbwyy-qwen/qwen3.7-plus",
                          "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro", "custom-cbwyy-gpt55/gpt-5.5"],
                          "reason": "底稿是中文公文，qwen原生中文最优"},
    "report_writer": {"primary": "custom-cbwyy-qwen/qwen3.7-plus",
                      "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gpt55/gpt-5.5"],
                      "reason": "审计报告中文公文，格式要求严格"},
    "review_sentinel": {"primary": "custom-cbwyy-claude/claude-sonnet-5",
                        "fallbacks": ["custom-cbwyy-opus5/claude-opus-5", "custom-cbwyy-opus/claude-opus-4-8",
                                      "custom-cbwyy-qwen/qwen3.7-plus"],
                        "reason": "复核零容错，最强逻辑模型，紧急时上opus-5"},
    # ─── 工程咨询 Agent ───
    "budget_estimator": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                         "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash"],
                         "reason": "工程量计算需要数值精确"},
    "settlement_auditor": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                           "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
                           "reason": "结算审计=计算+合规，pro主力"},
    "fiscal_reviewer": {"primary": "custom-cbwyy-claude/claude-sonnet-5",
                        "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
                        "reason": "财政评审重政策合规，sonnet严谨"},
    # ─── 绩效评价 Agent ───
    "performance_evaluator": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                              "fallbacks": ["custom-cbwyy-fable/claude-fable-5", "custom-cbwyy-claude/claude-sonnet-5"],
                              "reason": "绩效评价=数据分析+指标打分；指标体系设计先问fable顾问"},
    # ─── 专项检测 Agent ───
    "expert_bias_detector": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                             "fallbacks": ["custom-cbwyy-kimi/kimi-k3", "custom-cbwyy-glm/glm-5.2"],
                             "reason": "统计检测，pro精确；国产推理兜底"},
    "meeting_minutes_analyzer": {"primary": "custom-cbwyy-qwen/qwen3.7-plus",
                                 "fallbacks": ["custom-cbwyy-glm/glm-5.2", "custom-cbwyy-top-v1/deepseek-v4-pro"],
                                 "reason": "中文会议纪要，qwen原生理解最优；长纪要(>128K)降级GLM国产推理"},
    # ─── 数据运维 Agent ───
    "ocr_processor": {"primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
                      "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus"],
                      "reason": "OCR后文本清洗，轻量任务，flash足够"},
    "data_classifier": {"primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
                        "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
                        "reason": "分类归档，轻量任务"},
    "data_desensitizer": {"primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
                          "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
                          "reason": "脱敏任务，轻量但需精确匹配"},
    "adjustment_scribe": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                          "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
                          "reason": "调整分录=财务精确，不能出错"},
    # ─── 方案撰写 Agent ───
    "plan_writer": {"primary": "custom-cbwyy-qwen/qwen3.7-plus",
                    "fallbacks": ["custom-cbwyy-fable/claude-fable-5", "custom-cbwyy-claude/claude-sonnet-5"],
                    "reason": "实施方案中文公文格式；重难点分析先问fable顾问多角度审视"},
}

SCENARIO_MODEL_ROUTES = {
    "daily_chat": {"primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
                   "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
                   "desc": "日常对话/信息查询"},
    "heartbeat_task": {"primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
                       "fallbacks": ["deepseek-direct/deepseek-chat"],
                       "desc": "心跳/定时任务，必须低成本。代理挂→直连逃生"},
    "data_check": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                   "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-flash", "custom-cbwyy-kimi/kimi-k3"],
                   "desc": "数值核查/Benford/统计分析"},
    "financial_analysis": {"primary": "custom-cbwyy-top-v1/deepseek-v4-pro",
                           "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-kimi/kimi-k3"],
                           "desc": "财务分析、异常检测、金额复核"},
    "compliance_check": {"primary": "custom-cbwyy-claude/claude-sonnet-5",
                         "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-opus/claude-opus-4-8"],
                         "desc": "法规合规性审查，逻辑严谨优先"},
    "law_interpretation": {"primary": "custom-cbwyy-claude/claude-sonnet-5",
                           "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
                           "desc": "法律条文解读与适用"},
    "gov_document": {"primary": "custom-cbwyy-qwen/qwen3.7-plus",
                     "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gemini/gemini-3.1-pro-preview"],
                     "desc": "政府公文/审计报告/方案撰写"},
    "report_writing": {"primary": "custom-cbwyy-qwen/qwen3.7-plus",
                       "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-gpt55/gpt-5.5"],
                       "desc": "审计报告、绩效评价报告撰写"},
    "creative": {"primary": "custom-cbwyy-luna/gpt-5.6-luna",
                 "fallbacks": ["custom-cbwyy-sol/gpt-5.6-sol", "custom-cbwyy-terra/gpt-5.6-terra"],
                 "desc": "创意构思/方案设计/头脑风暴"},
    "long_document": {"primary": "custom-cbwyy-gemini/gemini-3.1-pro-preview",
                      "fallbacks": ["custom-cbwyy-qwen/qwen3.7-plus", "custom-cbwyy-top-v1/deepseek-v4-pro"],
                      "desc": "超长文档(>128K)分析/总结"},
    "english": {"primary": "custom-cbwyy-gpt55/gpt-5.5",
                "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5"],
                "desc": "英文润色/翻译/国际业务"},
    "final_review": {"primary": "custom-cbwyy-claude/claude-sonnet-5",
                     "fallbacks": ["custom-cbwyy-opus/claude-opus-4-8"],
                     "desc": "终审/最终签字，零容错"},
    "china_reasoning": {"primary": "custom-cbwyy-glm/glm-5.2",
                        "fallbacks": ["custom-cbwyy-kimi/kimi-k3", "custom-cbwyy-top-v1/deepseek-v4-pro"],
                        "desc": "国产推理模型，敏感项目优先。GLM 128K窗口适合长文档"},
    "consulting": {"primary": "custom-cbwyy-fable/claude-fable-5",
                   "fallbacks": ["custom-cbwyy-claude/claude-sonnet-5", "custom-cbwyy-luna/gpt-5.6-luna"],
                   "desc": "做决策前先问，战略咨询"},
    "lightweight": {"primary": "custom-cbwyy-top-v1/deepseek-v4-flash",
                    "fallbacks": ["custom-cbwyy-top-v1/deepseek-v4-pro"],
                    "desc": "OCR后处理/分类/归档/格式转换"},
}

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
    ],
}

# ═══════════════════════════════════════════
# 2. 分类路由：任务特征标签 → 能力档位
# ═══════════════════════════════════════════
# 标签按文章建议写成工程约束，不写"简单/中等/困难"这种主观词。
# 场景命中的标签决定了基础档位，之后可被轨迹/阶段/风险信号覆盖。

SCENARIO_TIERS = {
    "daily_chat": "efficient",
    "heartbeat_task": "efficient",
    "data_check": "numerical",
    "financial_analysis": "numerical",
    "compliance_check": "strong",
    "law_interpretation": "strong",
    "gov_document": "chinese_doc",
    "report_writing": "chinese_doc",
    "creative": "creative",
    "long_document": "long_context",
    "english": "strong",
    "final_review": "safety_net",
    "china_reasoning": "strong",
    "consulting": "consulting",
    "lightweight": "efficient",
}

# 任务特征 → 需要升档的信号（命中任一即最低提到 strong 档）
TASK_FEATURES_UPGRADE = {
    "cross_file_reasoning": "跨文件/跨模块推理，一次方向错后面全跑偏 → strong",
    "ambiguous_requirement": "模糊需求/方案取舍，需要推理 → strong",
    "migration_plan": "迁移/改造方案制定 → strong",
    "side_effects": "含副作用操作 → 走风险策略",
}

# ═══════════════════════════════════════════
# 3. 风险策略：风险等级 → 强制档位 + 人工审批
# ═══════════════════════════════════════════
# 铁律：模型能力替代不了权限控制。风险规则永远第一优先，且不允许被降级覆盖。

RISK_POLICY = {
    # 高风险：强制 safety_net + 必须人工审批
    "high": {
        "forced_tier": "safety_net",
        "require_approval": True,
        "desc": "必须人工审批，无论路由到多强的模型都不能跳过",
        "operations": [
            "payment", "delete_data", "permission_change", "external_publish",
            "audit_conclusion", "report_signing",  # 审计结论出具/报告签字
            "send_message_external", "money_transfer",
        ],
    },
    # 中风险：强制 strong 档起步
    "medium": {
        "forced_tier": "strong",
        "require_approval": False,
        "desc": "强模型降低误判概率",
        "operations": [
            "contract_review", "law_interpret", "report_review",
            "compliance_judge", "fiscal_policy_check",
        ],
    },
    # 低风险：正常路由，不干预
    "low": {
        "forced_tier": None,
        "require_approval": False,
        "desc": "正常走任务/轨迹/阶段路由",
    },
}

# ═══════════════════════════════════════════
# 4. 级联路由：轨迹信号 → 升级条件
# ═══════════════════════════════════════════
# 文章要点：升级条件必须写死，不能让小模型无限试错。
# 升级时带上交接单（handoff），不从头重来。

CASCADE_RULES = {
    # 同一错误签名连续出现 N 次 → 升级
    "same_error_twice": {"signal": "same_error_count", "threshold": 2,
                         "action": "upgrade", "reason": "同一错误连续2次，疑似卡住"},
    # 连续 N 轮无新增有效改动（工具调用重复/差异来回撤销）→ 升级
    "no_progress_rounds": {"signal": "no_progress_rounds", "threshold": 3,
                           "action": "upgrade", "reason": "3轮无有效进展，小模型在空转"},
    # 同一工具重复调用 N 次无新结果 → 升级
    "tool_call_repeat": {"signal": "tool_call_repeat_count", "threshold": 3,
                         "action": "upgrade", "reason": "重复调用同一工具无新结果"},
    # 测试失败范围扩大 → 升级
    "failure_spread": {"signal": "failure_count_growth", "threshold": 0,
                       "action": "upgrade", "reason": "失败范围扩大，需要强模型介入诊断"},
    # 升级冷却：同任务 10 分钟内最多升级 2 次，防止来回抖动
    "upgrade_cooldown_sec": 600,
    "max_upgrades_per_task": 2,
}

# ═══════════════════════════════════════════
# 5. 阶段路由：任务进度 → 档位
# ═══════════════════════════════════════════
# 同一 Agent 任务通常经历 探索→规划→执行→验收，难度随阶段变化。
# 验收阶段必须确定性检查，模型不能自我评价。

STAGE_ROUTES = {
    "explore": {"tier": "efficient",
                "reason": "扫描/收集/读取量大，边界清楚，高效模型足够"},
    "plan": {"tier": "strong",
             "reason": "方案制定=专家会诊，方向错后面全跑偏"},
    "execute": {"tier": "numerical",
                "reason": "照方案执行/机械编辑/数值计算，切回高效档"},
    "recover": {"tier": "strong",
                "reason": "重复失败后带着交接单升级，强模型从已有证据继续"},
    "acceptance": {"tier": "safety_net", "deterministic_check": True,
                   "reason": "验收用确定性检查（退出码/测试/静态扫描），模型不自评"},
    "report_draft": {"tier": "chinese_doc",
                     "reason": "报告撰写阶段，中文公文档"},
}

# 会话黏性：同一执行阶段内，没有新证据就保持当前模型
STICKINESS = {
    "min_stay_steps": 2,        # 最短驻留步骤
    "upgrade_cooldown_sec": 600,  # 升级冷却
    "require_new_evidence": True,  # 切换必须出现新证据
}

# ═══════════════════════════════════════════
# 6. 系统状态（预留接口）
# ═══════════════════════════════════════════
# 调用方可注入：{model_id: {"error_rate": 0.0-1.0, "latency_ms": N, "available": bool}}
# 命中不可用/高错误率 → 跳过该模型走 fallback。
# 初始为空 = 不干预，与 v5 行为一致。

SYSTEM_STATE = {}

# ═══════════════════════════════════════════
# 7. 路由执行器
# ═══════════════════════════════════════════

_route_log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "logs", "routing_trajectory.jsonl")


class Router:
    """四信号路由执行器。

    用法：
        r = Router()
        decision = r.route({
            "agent": "report_writer",            # 可选
            "scenario": "report_writing",        # 可选
            "stage": "plan",                     # 可选：explore/plan/execute/recover/acceptance
            "risk": "report_signing",            # 可选：高风险操作名 → 命中 RISK_POLICY
            "features": ["cross_file_reasoning"],# 可选：任务特征标签
            "context_chars": 150000,             # 可选：上下文长度
            "trajectory": {                      # 可选：轨迹信号
                "same_error_count": 1,
                "no_progress_rounds": 0,
                "tool_call_repeat_count": 0,
            },
            "task_id": "audit-2026-001",         # 可选：任务追踪（升级冷却用）
            "shadow": False,                     # True=影子评测，只建议不切换
        })
        # → {"model": "...", "tier": "...", "method": "risk|cascade|stage|classification|rule",
        #    "reason": "...", "require_approval": bool, "handoff": {...}, "shadow": bool}
    """

    def __init__(self, log_path=None):
        self.log_path = log_path or _route_log_path
        self._upgrade_count = {}   # task_id -> {"count": N, "last_upgrade": ts}
        self._current_model = {}   # task_id -> {"model": ..., "stage": ..., "steps": N}

    # ── 主入口 ──────────────────────────────
    def route(self, req):
        start = time.time()
        req = req or {}
        agent = req.get("agent")
        scenario = req.get("scenario")
        stage = req.get("stage")
        risk_op = req.get("risk")
        features = req.get("features") or []
        context_chars = req.get("context_chars") or 0
        traj = req.get("trajectory") or {}
        task_id = req.get("task_id") or f"task-{int(time.time()*1000)}"
        shadow = bool(req.get("shadow"))

        # ① 风险策略（最高优先，不可被降级覆盖）
        risk_level, risk_meta = self._resolve_risk(risk_op)
        if risk_meta.get("forced_tier"):
            decision = self._build_decision(
                tier=risk_meta["forced_tier"], method="risk",
                reason=f"风险策略[{risk_level}]：{risk_meta['desc']}",
                require_approval=risk_meta.get("require_approval", False),
            )
            self._record(task_id, req, decision, risk_level, start)
            return decision

        # ② 轨迹信号 → 级联升级（起点=规则路由会选的基础档位，升一档推理能力）
        base_tier = self._base_tier(agent, scenario)
        cascade = self._check_cascade(task_id, traj, base_tier)
        if cascade:
            decision = self._build_decision(
                tier=cascade["tier"], method="cascade",
                reason=cascade["reason"],
                handoff=self._build_handoff(task_id, traj),
            )
            self._record(task_id, req, decision, risk_level, start)
            return decision

        # ③ 阶段路由
        if stage and stage in STAGE_ROUTES:
            stage_cfg = STAGE_ROUTES[stage]
            # 会话黏性：同一阶段内保持当前模型
            cur = self._current_model.get(task_id)
            if cur and cur.get("stage") == stage:
                cur["steps"] = cur.get("steps", 0) + 1
                if cur["steps"] >= STICKINESS["min_stay_steps"] and not STICKINESS["require_new_evidence"]:
                    return self._build_decision(tier=cur["tier"], method="stage",
                                                reason=f"阶段[{stage}]会话黏性保持",
                                                deterministic=stage_cfg.get("deterministic_check", False))
            decision = self._build_decision(
                tier=stage_cfg["tier"], method="stage",
                reason=f"阶段[{stage}]：{stage_cfg['reason']}",
                deterministic=stage_cfg.get("deterministic_check", False),
            )
            self._current_model[task_id] = {"stage": stage, "tier": stage_cfg["tier"], "steps": 0}
            self._record(task_id, req, decision, risk_level, start)
            return decision

        # ④ 分类路由：特征标签升档
        for feat in features:
            if feat in TASK_FEATURES_UPGRADE:
                decision = self._build_decision(
                    tier="strong", method="classification",
                    reason=f"特征[{feat}]：{TASK_FEATURES_UPGRADE[feat]}",
                )
                self._record(task_id, req, decision, risk_level, start)
                return decision

        # 长上下文：>128K 直接走长上下文档
        if context_chars > 128000:
            decision = self._build_decision(
                tier="long_context", method="classification",
                reason=f"上下文{context_chars}字符>128K，长上下文档",
            )
            self._record(task_id, req, decision, risk_level, start)
            return decision

        # ⑤ 规则路由：Agent > 场景 > 全局（v5 兼容）
        if agent and agent in AGENT_MODEL_ROUTES:
            route_cfg = AGENT_MODEL_ROUTES[agent]
            tier = self._tier_for_model(route_cfg["primary"]) or "strong"
            decision = self._build_decision(
                tier=tier, method="rule",
                reason=f"Agent[{agent}]：{route_cfg.get('reason', '')}",
                model_override=route_cfg["primary"],
                fallbacks_override=route_cfg["fallbacks"],
            )
            self._record(task_id, req, decision, risk_level, start)
            return decision

        if scenario and scenario in SCENARIO_MODEL_ROUTES:
            route_cfg = SCENARIO_MODEL_ROUTES[scenario]
            tier = SCENARIO_TIERS.get(scenario, "efficient")
            decision = self._build_decision(
                tier=tier, method="rule",
                reason=f"场景[{scenario}]：{route_cfg.get('desc', '')}",
                model_override=route_cfg["primary"],
                fallbacks_override=route_cfg["fallbacks"],
            )
            self._record(task_id, req, decision, risk_level, start)
            return decision

        decision = self._build_decision(tier="efficient", method="rule", reason="全局默认")
        self._record(task_id, req, decision, risk_level, start)
        return decision

    # ── 风险解析 ────────────────────────────
    def _resolve_risk(self, risk_op):
        if not risk_op:
            return "low", RISK_POLICY["low"]
        for level, meta in RISK_POLICY.items():
            if risk_op in meta.get("operations", []):
                return level, meta
        # 未登记的操作名：保守按中风险
        return "medium", {"forced_tier": "strong", "require_approval": False,
                          "desc": f"未登记操作[{risk_op}]，保守按中风险"}

    # ── 基础档位：规则路由会选哪一档（级联升级的起点） ──
    def _base_tier(self, agent, scenario):
        if agent and agent in AGENT_MODEL_ROUTES:
            t = self._tier_for_model(AGENT_MODEL_ROUTES[agent]["primary"])
            if t:
                return t
        if scenario and scenario in SCENARIO_TIERS:
            return SCENARIO_TIERS[scenario]
        return "efficient"

    # ── 级联升级判定 ────────────────────────
    def _check_cascade(self, task_id, traj, base_tier):
        if not traj:
            return None
        rec = self._upgrade_count.get(task_id, {"count": 0, "last_upgrade": 0})
        now = time.time()
        if now - rec["last_upgrade"] < CASCADE_RULES["upgrade_cooldown_sec"]:
            return None  # 冷却期内不重复升级
        if rec["count"] >= CASCADE_RULES["max_upgrades_per_task"]:
            return None  # 单任务升级次数上限

        # 升级目标：基础档位 → 下一档推理能力（本任务已升过则继续往上）
        cur_tier = self._current_model.get(task_id, {}).get("tier")
        if not cur_tier:
            cur_tier = base_tier
        new_tier = CASCADE_UPGRADE_MAP.get(cur_tier, "strong")

        hit = None
        for name, rule in CASCADE_RULES.items():
            if not isinstance(rule, dict):
                continue
            val = traj.get(rule["signal"])
            if val is not None and val >= rule["threshold"]:
                hit = rule["reason"]
                break

        if hit:
            rec["count"] += 1
            rec["last_upgrade"] = now
            self._upgrade_count[task_id] = rec
            self._current_model[task_id] = {"tier": new_tier, "stage": "recover", "steps": 0}
            return {"tier": new_tier,
                    "reason": f"级联升级({rec['count']}/{CASCADE_RULES['max_upgrades_per_task']})：{hit}"}
        return None

    # ── 交接单 ──────────────────────────────
    def _build_handoff(self, task_id, traj):
        """文章要点：转诊带检查报告，不从头量体温。
        结构化交接单字段：目标/已完成修改/错误签名/测试结果/剩余预算。"""
        return {
            "task_id": task_id,
            "goal": traj.get("goal", ""),
            "completed_changes": traj.get("completed_changes", []),
            "error_signatures": traj.get("error_signatures", []),
            "test_results": traj.get("test_results", []),
            "remaining_budget": traj.get("remaining_budget"),
            "accepted_criteria": traj.get("accepted_criteria", []),
        }

    # ── 决策组装 ────────────────────────────
    def _build_decision(self, tier, method, reason, require_approval=False,
                        handoff=None, deterministic=False, model_override=None,
                        fallbacks_override=None):
        pool = MODEL_POOL.get(tier)
        if pool is None:
            pool = MODEL_POOL["efficient"]
        primary = model_override or pool["primary"]
        fallbacks = fallbacks_override or pool["fallbacks"]
        # 系统状态过滤：不可用/高错误率的模型跳过
        chain = [primary] + fallbacks
        filtered = [m for m in chain if self._model_ok(m)]
        if not filtered:
            filtered = [GLOBAL_DEFAULT["primary"]] + GLOBAL_DEFAULT["fallbacks"]
        return {
            "model": filtered[0],
            "chain": filtered,
            "tier": tier,
            "method": method,
            "reason": reason,
            "require_approval": require_approval,
            "handoff": handoff,
            "deterministic_check": deterministic,
        }

    def _model_ok(self, model_id):
        st = SYSTEM_STATE.get(model_id)
        if not st:
            return True
        if st.get("available") is False:
            return False
        if st.get("error_rate", 0) > 0.5:
            return False
        return True

    def _tier_for_model(self, model_id):
        for tier, pool in MODEL_POOL.items():
            if pool.get("primary") == model_id or model_id in pool.get("fallbacks", []):
                return tier
        return None

    # ── 轨迹记录（影子评测的数据基础） ──────
    def _record(self, task_id, req, decision, risk_level, start):
        """每笔路由决策落盘，供事后评估：路由选的对不对、升级有没有改善结果。
        影子模式(decision.shadow)下标记建议模型，实际执行的模型由调用方另记。"""
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            entry = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "task_id": task_id,
                "req": {k: v for k, v in req.items() if k != "trajectory"},
                "trajectory_signals": req.get("trajectory") or {},
                "risk_level": risk_level,
                "decision": {
                    "model": decision["model"],
                    "chain": decision["chain"],
                    "tier": decision["tier"],
                    "method": decision["method"],
                    "reason": decision["reason"],
                    "require_approval": decision["require_approval"],
                    "shadow": req.get("shadow", False),
                },
                "latency_ms": int((time.time() - start) * 1000),
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # 轨迹记录失败不影响路由本身


# ═══════════════════════════════════════════
# 8. 影子评测助手
# ═══════════════════════════════════════════

def shadow_compare(router, req, actual_model, actual_success):
    """影子评测：把路由建议与真实执行结果对比，判断路由器是否错过更好的选择。

    用法（在调用方执行完成后调用）：
        router = Router()
        d = router.route({...request, "shadow": True})
        # ... 实际执行（可能用了别的模型）...
        shadow_compare(router, d, actual_model="deepseek-v4-flash", actual_success=False)
    """
    try:
        os.makedirs(os.path.dirname(_route_log_path), exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "task_id": req.get("task_id"),
            "kind": "shadow_compare",
            "suggested_model": req.get("suggested_model"),
            "actual_model": actual_model,
            "actual_success": actual_success,
        }
        with open(_route_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def stats(log_path=None):
    """路由轨迹统计：各方法调用次数 / 升级率 / 风险拦截数。"""
    import collections
    path = log_path or _route_log_path
    if not os.path.exists(path):
        return {"error": "no trajectory log yet"}
    methods = collections.Counter()
    risks = collections.Counter()
    total = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("kind") == "shadow_compare":
                continue
            total += 1
            methods[e["decision"]["method"]] += 1
            risks[e["risk_level"]] += 1
    return {"total_routes": total, "by_method": dict(methods),
            "by_risk_level": dict(risks),
            "upgrade_rate": round(methods.get("cascade", 0) / total, 3) if total else 0}


# ═══════════════════════════════════════════
# 9. v5 兼容接口（同名同行为，旧代码不用改）
# ═══════════════════════════════════════════

def get_agent_route(agent_name):
    return AGENT_MODEL_ROUTES.get(agent_name, GLOBAL_DEFAULT)


def get_scenario_route(scenario):
    return SCENARIO_MODEL_ROUTES.get(scenario, GLOBAL_DEFAULT)


def get_best_route(agent_name=None, scenario=None):
    """双层路由：Agent优先，场景兜底，全局保底（v5 行为不变）"""
    if agent_name and agent_name in AGENT_MODEL_ROUTES:
        return ("agent", agent_name, AGENT_MODEL_ROUTES[agent_name])
    if scenario and scenario in SCENARIO_MODEL_ROUTES:
        return ("scenario", scenario, SCENARIO_MODEL_ROUTES[scenario])
    return ("global", "default", GLOBAL_DEFAULT)


# 单例：模块级直接用
router = Router()
