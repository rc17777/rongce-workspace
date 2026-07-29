# 融策审计智析Agent v2 — 交易Agent架构借鉴方案

> 2026-06-28 | 基于 TradingAgents / AI Hedge Fund / Agentic Trading 等项目的设计模式迁移

---

## 一、借鉴总览

| 交易Agent模式 | 审计场景映射 | 核心收益 |
|---|---|---|
| 多角色辩论制（多空研究员对抗） | **质疑-验证辩论引擎** | 消除单一视角盲区，模拟审计现场"质疑-解释-再质疑"的博弈过程 |
| 大师Agent人格化（巴菲特/芒格/林奇等） | **审计准则专家群** | 不同审计方法论并行推演，输出多维度结论供审计负责人权衡 |
| 风控Agent独立否决权 | **独立质量复核Agent**（三级复核第三级） | 完全独立的终审关卡，可一票否决不达标结论 |
| LangGraph编排+Checkpoint恢复 | **审计工作流引擎** | 长周期审计项目可中断恢复，并行Agent执行，条件分支路由 |

---

## 二、模式一：质疑-验证辩论引擎

### 2.1 核心思路

借鉴 TradingAgents 的"研究员多空辩论"机制——系统不直接给结论，而是让立场相反的 Agent 先辩论，再收敛。

**交易场景**：Bullish Researcher vs Bearish Researcher → 辩论后输出到 Trader
**审计场景**：信任方 Agent vs 质疑方 Agent → 辩论后输出到审计结论 Agent

### 2.2 Agent 角色设计

```
┌─────────────────────────────────────────────────────────┐
│                    审计数据分析层                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ 合规分析师 │ │ 财务分析师 │ │ 业务分析师 │ │ 数据分析师  │ │
│  │ (Agent)   │ │ (Agent)   │ │ (Agent)   │ │ (Agent)    │ │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬──────┘ │
│        │              │              │              │       │
│        └──────────────┴──────┬───────┴──────────────┘       │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              质疑-验证辩论层                           │  │
│  │  ┌──────────────────┐  ┌──────────────────────────┐  │  │
│  │  │  信任方 Agent      │  │  质疑方 Agent             │  │  │
│  │  │  "数据合理可信"     │  │  "数据需要验证"           │  │  │
│  │  │  找支持证据         │  │  找矛盾、漏洞、异常       │  │  │
│  │  │  论证合规性         │  │  论证风险点               │  │  │
│  │  └────────┬─────────┘  └────────────┬─────────────┘  │  │
│  │           │        辩论对抗          │                │  │
│  │           └──────────┬───────────────┘                │  │
│  │                      ▼                                │  │
│  │              ┌──────────────┐                         │  │
│  │              │ 辩论仲裁 Agent │  ← 决定哪些质疑成立    │  │
│  │              └──────────────┘                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              审计结论层                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │  │
│  │  │ 问题定性  │  │ 风险评级  │  │ 建议生成 Agent    │    │  │
│  │  │ Agent    │  │ Agent    │  │                  │    │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.3 辩论协议

```python
# 核心辩论流程（伪代码）
class AuditDebateEngine:
    """
    信任方与质疑方进行多轮辩论，直到达成一致或触发仲裁
    """
    
    def debate(self, finding: AuditFinding) -> DebateResult:
        max_rounds = 3  # 最多3轮辩论
        
        for round_num in range(1, max_rounds + 1):
            # 信任方论证
            trust_args = self.trust_agent.argue(finding, round_num)
            
            # 质疑方挑战
            challenge_args = self.challenge_agent.challenge(
                finding, trust_args, round_num
            )
            
            # 判断是否需要继续
            if self.arbiter.check_convergence(trust_args, challenge_args):
                return self.arbiter.synthesize(trust_args, challenge_args)
        
        # 未收敛 → 仲裁 Agent 强制裁决
        return self.arbiter.force_decide(trust_args, challenge_args)
```

### 2.4 每个 Agent 的系统提示设计

**信任方 Agent**：
- 角色：你是审计支持方，基于现有证据论证被审计事项的合规性与合理性
- 能力：调用 MCP 接口查询法规/制度/先例；引用 AGR 知识库中的合规案例
- 约束：不得虚构证据；不得忽略已知风险信号

**质疑方 Agent**：
- 角色：你是审计质疑方，以最严格标准审查每一项数据与结论
- 能力：交叉验证多个数据源；检测数据异常模式（本福特定律、异常值检测）；追问"为什么"
- 约束：质疑必须有依据，不得"为质疑而质疑"

**仲裁 Agent**：
- 角色：综合双方论点，判断哪些质疑成立，哪些不成立
- 输出：结构化的辩论结论 → `{论点, 支持方依据, 质疑方依据, 裁定结果, 理由}`

---

## 三、模式二：审计准则专家群

### 3.1 核心思路

借鉴 AI Hedge Fund 的"投资大师人格化"——每个 Agent 代表一位投资大师的哲学。

**审计映射**：每个 Agent 人格化为一种审计方法论/准则体系，对同一审计事项从不同角度输出结论。

### 3.2 审计专家 Agent 群

| Agent | 人格化原型 | 核心方法论 | 适用场景 |
|---|---|---|---|
| **国家审计准则 Agent** | 《审计法》+《国家审计准则》 | 合规性+绩效审计双主线，关注财政资金使用效益 | 政府审计、专项资金审计 |
| **CPA审计准则 Agent** | 中国注册会计师审计准则 | 风险导向审计，关注重大错报风险 | 企业财务报表审计 |
| **内部审计准则 Agent** | 国际内部审计师协会标准 | 治理、风控、合规三位一体 | 企业内部审计 |
| **工程审计 Agent** | 工程量清单计价规范+合同管理 | 工程造价核减、变更签证审核 | 工程咨询、造价审计 |
| **数据审计 Agent** | 大数据审计指引 | 全量数据比对、异常模式挖掘 | IT审计、数据分析 |

### 3.3 多准则并行推演流程

```
                     ┌──────────────────┐
                     │   审计事项输入     │
                     └────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│ 国家审计准则Agent  │ │ CPA准则Agent │ │ 内部审计准则Agent │
│ "财政资金→合规+绩效"│ │ "财报→重大错报"│ │ "内控→三道防线"   │
└────────┬─────────┘ └──────┬───────┘ └────────┬─────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            ▼
                  ┌──────────────────┐
                  │   结论聚合 Agent   │
                  │  对比不同准则下的  │
                  │  风险差异和结论差异 │
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │   审计建议合成     │
                  │  "按最严格准则输出" │
                  └──────────────────┘
```

### 3.4 价值

- **政府审计项目**中，同时用国家审计准则 + CPA 准则推演 → 发现单一准则的盲区
- **工程审计**中，工程审计 Agent + 数据审计 Agent 并行 → 造价审核 + 数据异常检测双重保障
- **跨准则差异报告**本身就是审计发现——"为什么按A准则合规，按B准则就有问题？"

---

## 四、模式三：独立质量复核 Agent（三级复核的AI实现）

### 4.1 核心思路

借鉴 TradingAgents 中 Portfolio Manager 的最终审批权和 AI Hedge Fund 中 Risk Manager 的独立否决能力。

**审计映射**：将三级复核的第三级——独立质量复核——具象化为一个拥有独立否决权的 Agent。

### 4.2 三级复核的 Agent 化

```
┌─────────────────────────────────────────────────────────┐
│              第一级复核：项目组长 Agent                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │ • 审计程序是否执行完整？                              │ │
│  │ • 审计证据是否充分、适当？                            │ │
│  │ • 审计工作底稿是否规范？                              │ │
│  │ • → 通过后进入第二级                                 │ │
│  └────────────────────────────────────────────────────┘ │
│                         ▼                                │
│              第二级复核：部门经理 Agent                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │ • 审计结论是否恰当？                                 │ │
│  │ • 重大问题是否已充分揭示？                            │ │
│  │ • 审计建议是否具有可操作性？                          │ │
│  │ • → 通过后进入第三级                                 │ │
│  └────────────────────────────────────────────────────┘ │
│                         ▼                                │
│           第三级复核：独立质量复核 Agent（否决权）          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ • 与第一、二级 Agent 无上下级关系，完全独立           │ │
│  │ • 不参与前期分析，只做终审                           │ │
│  │ • 权力：一票否决 → 退回重新审计                      │ │
│  │ • 检查维度：                                        │ │
│  │   - 审计结论是否有完整证据链支撑？                    │ │
│  │   - 是否存在未被辩论覆盖的风险盲区？                  │ │
│  │   - 法规引用是否准确、最新？                          │ │
│  │   - 同类项目横向对比是否一致？                        │ │
│  │   - 审计建议是否超出审计范围？                        │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 4.3 否决权设计

```python
class QualityReviewAgent:
    """
    独立质量复核 Agent — 拥有最终否决权
    设计原则：
    1. 与前面所有分析 Agent 隔离（不共享会话上下文）
    2. 只接收最终输出包（结论+证据+底稿），不参与过程
    3. 否决必须给出具体理由，不得空泛否决
    """
    
    VETO_THRESHOLD = 0.85  # 质量评分低于此值 → 否决
    
    def review(self, audit_package: AuditPackage) -> ReviewResult:
        # 独立评估（不依赖前期 Agent 的任何中间结论）
        evidence_chain_score = self._evaluate_evidence_chain(audit_package)
        coverage_score = self._evaluate_risk_coverage(audit_package)
        regulation_score = self._evaluate_regulation_accuracy(audit_package)
        consistency_score = self._evaluate_cross_project_consistency(audit_package)
        
        total_score = weighted_average([
            evidence_chain_score, coverage_score, 
            regulation_score, consistency_score
        ])
        
        if total_score < self.VETO_THRESHOLD:
            return ReviewResult(
                status="REJECTED",
                score=total_score,
                reasons=self._generate_veto_reasons(...),
                required_fixes=self._generate_fix_checklist(...)
            )
        
        return ReviewResult(status="APPROVED", score=total_score)
```

---

## 五、模式四：LangGraph 审计工作流编排

### 5.1 核心思路

TradingAgents 使用 LangGraph 编排多 Agent 协作，支持 Checkpoint 中断恢复——这对审计场景至关重要，因为一个审计项目可能持续数周。

### 5.2 审计工作流状态图

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# 审计状态定义
class AuditState(TypedDict):
    project_id: str
    audit_type: str           # 政府审计 / 企业审计 / 工程审计
    data_sources: list[dict]  # 已接入的数据源
    findings: list[dict]      # 审计发现列表
    debate_results: list[dict] # 辩论结果
    current_phase: str        # 当前阶段
    review_status: dict       # 三级复核状态
    human_intervention: bool  # 是否需要人工介入

# 构建审计工作流
builder = StateGraph(AuditState)

# 节点
builder.add_node("data_collection", data_collection_node)    # 数据采集
builder.add_node("data_analysis", data_analysis_node)        # 数据分析（4个分析师Agent并行）
builder.add_node("debate_trust", debate_trust_node)          # 信任方辩论
builder.add_node("debate_challenge", debate_challenge_node)  # 质疑方辩论
builder.add_node("debate_arbiter", debate_arbiter_node)      # 仲裁
builder.add_node("expert_panel", expert_panel_node)          # 多准则专家群并行
builder.add_node("conclusion", conclusion_node)              # 结论生成
builder.add_node("review_l1", review_level1_node)            # 一级复核
builder.add_node("review_l2", review_level2_node)            # 二级复核
builder.add_node("review_l3", review_level3_node)            # 三级复核（独立质量复核）
builder.add_node("report_gen", report_generation_node)       # 报告生成

# 边（含条件路由）
builder.set_entry_point("data_collection")
builder.add_edge("data_collection", "data_analysis")
builder.add_edge("data_analysis", "debate_trust")
builder.add_edge("debate_trust", "debate_challenge")

# 辩论循环：可能多轮
builder.add_conditional_edges(
    "debate_challenge",
    debate_router,  # 返回 "arbiter" 或 "debate_trust"（再来一轮）
    {"arbiter": "debate_arbiter", "debate_trust": "debate_trust"}
)

builder.add_edge("debate_arbiter", "expert_panel")
builder.add_edge("expert_panel", "conclusion")

# 三级复核链路
builder.add_edge("conclusion", "review_l1")
builder.add_edge("review_l1", "review_l2")
builder.add_edge("review_l2", "review_l3")

# 三级复核结果 → 通过则生成报告，不通过则退回修正
builder.add_conditional_edges(
    "review_l3",
    review_router,  # 返回 "approved" 或 "rejected"
    {"approved": "report_gen", "rejected": "data_analysis"}  # 退回重审
)

builder.add_edge("report_gen", END)

# 启用 Checkpoint（支持中断恢复）
checkpointer = MemorySaver()  # 生产环境用 PostgresSaver
audit_graph = builder.compile(checkpointer=checkpointer)
```

### 5.3 条件路由逻辑

```python
def debate_router(state: AuditState) -> str:
    """辩论路由：判断是否需要更多轮次"""
    current_round = len(state["debate_results"])
    max_rounds = state.get("max_debate_rounds", 3)
    
    # 如果双方差距小于阈值 → 已收敛，进入仲裁
    last_result = state["debate_results"][-1]
    if last_result["divergence_score"] < 0.3:
        return "arbiter"
    
    # 如果已达最大轮次 → 强制仲裁
    if current_round >= max_rounds:
        return "arbiter"
    
    # 否则再来一轮
    return "debate_trust"


def review_router(state: AuditState) -> str:
    """三级复核路由"""
    l3_result = state["review_status"].get("level_3")
    
    if l3_result["status"] == "APPROVED":
        return "approved"
    
    # 根据否决原因决定退回路径
    veto_reason = l3_result["veto_category"]
    if veto_reason in ["evidence_insufficient", "risk_blind_spot"]:
        return "rejected"  # 退回到数据分析重新来
    
    if veto_reason == "regulation_error":
        # 法规引用错误 → 可以只修正结论层
        return "rejected"  # 简化处理：统一退回数据分析
    
    return "approved"  # 兜底通过
```

### 5.4 长周期审计的中断恢复

```python
# 场景：审计项目执行到辩论阶段，需要等人工确认某个证据
# 1. 保存 Checkpoint
config = {"configurable": {"thread_id": "audit-project-2026-001"}}
state = audit_graph.get_state(config)

# 2. 中断 → 系统提示审计人员"请在3个工作日内确认证据A"
# 3. 恢复 → 审计人员确认后，从 Checkpoint 继续
audit_graph.update_state(config, {
    "human_intervention": False,
    "findings": updated_findings
})

# 4. 继续执行（自动从上次中断位置恢复）
result = audit_graph.invoke(None, config)
```

---

## 六、技术架构整合

### 6.1 与现有设计的融合

```
┌────────────────────────────────────────────────────────────┐
│                    融策审计智析Agent v2                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ MCP 接口层    │  │ AGR 知识库    │  │ RAG 检索引擎     │ │
│  │ (数据源接入)  │  │ (审计准则/法规)│  │ (案例/底稿检索)  │ │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
│         └─────────────────┼──────────────────┘            │
│                           ▼                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            LangGraph 审计工作流引擎                    │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  数据分析层 ──→ 辩论引擎 ──→ 专家群 ──→ 结论层  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                         │                            │  │
│  │                         ▼                            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │      三级复核层（含独立否决权 Agent）             │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                │
│  ┌────────────────────────┼────────────────────────────┐  │
│  │        多模型路由层     │                            │  │
│  │  ┌──────┐ ┌──────┐ ┌──┴───┐ ┌──────┐ ┌──────┐     │  │
│  │  │DS V4 │ │ Qwen │ │ Kimi │ │ GLM  │ │本地模型│     │  │
│  │  │ Pro  │ │      │ │      │ │      │ │(Ollama)│    │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │  │
│  │   ↑ 核心分析    ↑ 翻译   ↑ 长文档  ↑ 政策   ↑ 敏感数据 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  Checkpoint 存储：PostgreSQL + MinIO（底稿/证据持久化）      │
└────────────────────────────────────────────────────────────┘
```

### 6.2 模型分配策略

| Agent 类型 | 推荐模型 | 理由 |
|---|---|---|
| 合规分析师 / 财务分析师 | DeepSeek V4 Pro | 核心推理任务，需要最强能力 |
| 信任方 / 质疑方 Agent | DeepSeek V4 Pro | 辩论需要深度推理 |
| 辩论仲裁 Agent | DeepSeek V4 Pro / Claude | 需要综合判断能力 |
| 各准则专家 Agent | DeepSeek V4 Pro / Kimi | 准则类需要长上下文（Kimi 优势） |
| 独立质量复核 Agent | 不同模型（与前期Agent隔离） | 防止同模型偏差 |
| 报告生成 Agent | Qwen / GLM | 中文写作能力 |
| 敏感数据分析 | 本地 Ollama 模型 | 数据不出域 |

---

## 七、实施路线图

### Phase 1：核心辩论引擎（2-3周）
- 实现信任方/质疑方/仲裁 3 个 Agent
- 接入现有 AGR 知识库和 RAG 检索
- 单轮辩论验证可行性

### Phase 2：三级复核链路（1-2周）
- 实现 L1/L2/L3 复核 Agent
- 独立质量复核 Agent 的否决权逻辑
- 复核意见的结构化输出

### Phase 3：专家群 + LangGraph 编排（2-3周）
- 实现至少 3 个准则专家 Agent
- 用 LangGraph 串联完整工作流
- Checkpoint 中断恢复

### Phase 4：生产化（2-3周）
- PostgreSQL Checkpoint 存储
- 多模型路由正式对接
- 人工介入节点（Human-in-the-loop）
- 审计底稿自动归档

---

## 八、注意事项

1. **所有 Agent 的输出都是"参考建议"**，最终决策权在审计人员手中——AI 是"增强"不是"替代"
2. **辩论必须有限深度**：2-3 轮为上限，避免无限递归消耗 token
3. **独立质量复核 Agent 必须与前期 Agent 隔离**：不同会话、不同上下文、理想情况下不同模型
4. **Checkpoint 存储需考虑数据合规**：审计底稿按法规要求保存，Checkpoint 数据应纳入归档范围
5. **成本控制**：多 Agent 辩论的 token 消耗是指数级的，需要在"深度"和"成本"之间找平衡点
