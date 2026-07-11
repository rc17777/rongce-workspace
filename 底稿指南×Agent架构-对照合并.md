# 底稿编制指南 × 融策审计智析Agent v2 — 架构对照合并

> 2026-06-28 | 将《审计底稿编制指南》的知识体系映射到 v2 架构中
> 对照源：`融策审计智析Agent-v2-交易Agent架构借鉴.md`

---

## 一、概念映射总表

| 底稿指南概念 | v2 架构对应模块 | 映射关系 | 现有覆盖度 |
|-------------|----------------|---------|-----------|
| 程峰标准（四标准） | L1 复核 + WorkpaperScorer | 标准 → 评分维度 | ❌ v2 未细化到维度级 |
| 目标明确（认定对应） | 数据分析层 → 合规分析师 Agent | Agent 应输出目标段 | ❌ Agent 系统提示未明确要求 |
| 过程清晰（抽样方法） | 数据分析层 Agent 输出 | 过程应结构化记录 | ❌ 未定义过程输出格式 |
| 结论有据（证据链） | L3 独立质量复核 → evidence_chain_score | 已有概念，缺细则 | 🟡 有框架但无评分标准 |
| 索引完整（交叉引用） | 底稿归档系统 | 索引→底稿检索 | ❌ 未设计索引子系统 |
| 有数无说 | 数据分析层 Agent 输出 | Agent 输出质量检查 | ❌ 未设置输出质量规则 |
| 有论无据 | L3 evidence_chain_score | 与现有逻辑一致 | 🟡 需细化检测规则 |
| 照抄上年 | L3 consistency_score | 部分覆盖（横向对比） | 🟡 缺纵向（年度对比） |
| 三级复核制 | 三级复核 Agent 层 | 完全吻合 | ✅ 设计一致 |
| 被Q后的处理 | Human-in-the-loop 节点 | 人工介入流程 | 🟡 已设计但未细化 |

**覆盖率：完全覆盖 1/10，部分覆盖 4/10，未覆盖 5/10**

---

## 二、需要增强的模块

### 增强 1：L1 复核 Agent — 集成底稿质量评分引擎

**现状**：v2 中 L1 复核只描述了"程序是否执行到位、证据是否充分、结论是否合理"，没有具体评分维度。

**增强方案**：集成 `审计底稿质量自动评分规则.md` 中的 WorkpaperScorer 引擎。

```python
# 增强后的 L1 复核节点
def review_level1_node(state: AuditState) -> AuditState:
    scorer = WorkpaperScorer()
    workpapers = state["workpapers"]
    
    for wp in workpapers:
        prev_year_wp = self._load_previous_year(wp.id)  # 新增：加载上年底稿
        report = scorer.score(wp, previous_year=prev_year_wp)  # 新增：照抄检测
        
        if report.final_score < 70:
            state["review_status"]["level_1"]["issues"].append({
                "workpaper_id": wp.id,
                "score": report.final_score,
                "grade": report.grade,
                "risk_flags": report.risk_flags,
                "checklist": report.improvement_checklist
            })
    
    # 如果存在不合格底稿 → 标记需退回
    state["review_status"]["level_1"]["passed"] = all(
        r.final_score >= 70 for r in reports
    )
    
    return state
```

---

### 增强 2：数据分析层 Agent — 输出格式结构化

**现状**：数据分析 Agent 输出什么格式未定义。

**增强方案**：每个分析 Agent 的输出必须包含四个标准段。

```
分析 Agent 输出 JSON Schema：
{
  "target": "本程序针对 [认定名称] 认定，验证 [具体目标]",
  "process": {
    "sampling_method": "随机抽样 | 分层抽样 | 大额优先 | PPS抽样",
    "selection_logic": "选取依据的文字描述",
    "sample_size": 25,
    "coverage_ratio": "72%",
    "test_procedures": ["核对合同", "核对出库单", ...],
    "documents_reviewed": ["销售合同", "客户签收单", "发票"]
  },
  "conclusion": {
    "statement": "结论文字",
    "evidence_refs": ["索引A-1", "索引A-2"],
    "exceptions": [
      {
        "description": "例外描述",
        "resolution": "处理方式",
        "impact": "对结论的影响"
      }
    ]
  },
  "cross_refs": {
    "ledger_ref": "明细表索引",
    "contract_refs": ["合同索引"],
    "related_wps": ["关联底稿索引"]
  }
}
```

---

### 增强 3：独立的索引子系统

**现状**：v2 未设计索引子系统。

**增强方案**：在底稿归档层增加索引管理。

```
索引类型：
1. 凭证索引 → 指向原始凭证编号
2. 合同索引 → 指向合同编号及存储位置
3. 底稿交叉索引 → 指向其他底稿编号
4. 法规索引 → 指向 AGR 知识库条目

索引验证规则：
- 每个索引引用必须有对应的目标存在
- 交叉引用必须形成闭环（A→B→A 或 A→B→C→A）
- 孤立的索引（指向不存在的目标）标记为 broken_link
```

在 LangGraph 工作流中增加索引验证节点：

```python
builder.add_node("index_validation", index_validation_node)

# 在底稿生成后、L1复核前验证索引
builder.add_edge("data_analysis", "index_validation")
builder.add_edge("index_validation", "review_l1")
```

---

### 增强 4：年度对比检测模块

**现状**：L3 consistency_score 做横向（同类项目间）一致性检查。

**增强方案**：增加纵向（同项目不同年度）对比。

```python
class YearOverYearComparator:
    """
    检测照抄嫌疑和异常年度变化
    """
    
    def compare(self, current_wp: Workpaper, previous_wp: Workpaper) -> YoYReport:
        # 1. 文本相似度检测（照抄嫌疑）
        similarity = cosine_similarity(
            self._embed(current_wp.text),
            self._embed(previous_wp.text)
        )
        
        # 2. 程序变化检测（是否因风险评估变化而调整）
        program_diff = self._diff_programs(
            current_wp.programs, previous_wp.programs
        )
        
        # 3. 异常年度变化（如科目余额变化但程序不变）
        risk_mismatch = self._check_risk_program_mismatch(
            current_wp.risk_assessment,
            current_wp.programs,
            previous_wp.programs
        )
        
        return YoYReport(
            copycat_risk=similarity > 0.85 and not program_diff.has_changes,
            program_diff=program_diff,
            risk_mismatch=risk_mismatch
        )
```

---

### 增强 5：知识库注入 — 在 Agent 系统提示中嵌入底稿标准

**现状**：Agent 系统提示中没有底稿质量标准。

**增强方案**：将知识库中的核心概念注入 Agent 系统提示。

**注入位置与内容**：

| Agent | 注入内容 | 来源 KB |
|-------|---------|---------|
| 合规分析师 | 目标明确要求（认定对应） | KB-003 |
| 财务分析师 | 过程清晰要求（抽样方法） | KB-004 |
| 数据分析师 | 有数无说防范 | KB-007 |
| 信任方 Agent | 结论有据要求 | KB-005, KB-008 |
| 质疑方 Agent | 证据链检验标准 | KB-005 |
| 仲裁 Agent | 四条标准综合评判 | KB-002 |
| L1 复核 Agent | 完整评分规则 | 评分规则文档 |
| L3 复核 Agent | 否决权+自查清单 | KB-011 |

---

## 三、工作流增强后的 LangGraph 图

```
                    ┌──────────────────┐
                    │   data_collection │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
         ┌──────────│   data_analysis   │──────────┐
         │          │ (含底稿结构化输出) │          │
         │          └────────┬─────────┘          │
         │                   │                    │
         ▼                   ▼                    ▼
  ┌────────────┐    ┌──────────────┐    ┌──────────────┐
  │ 合规分析师  │    │  财务分析师   │    │  业务分析师   │
  │ [KB-003注入]│   │ [KB-004注入]  │    │              │
  └─────┬──────┘    └──────┬───────┘    └──────┬───────┘
        │                  │                   │
        └──────────────────┼───────────────────┘
                           │
                  ┌────────▼─────────┐
                  │ index_validation  │  ← 新增：索引闭环验证
                  │  (新增节点)       │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │  辩论引擎         │
                  │ trust ↔ challenge │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │  专家群           │
                  │ 5准则并行推演     │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │  conclusion       │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │  L1 复核          │
                  │ WorkpaperScorer   │  ← 增强：集成评分引擎
                  │ ≥70分通过         │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │  L2 复核          │
                  │ 关键事项 ≥80分    │  ← 增强：关注高风险域
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┘
                  │  L3 独立复核       │
                  │ 否决阈值 <0.85     │
                  │ + 年度对比检测     │  ← 增强：YoY comparator
                  └────────┬─────────┘
                      ┌────┴────┐
                   ✅通过      ❌退回
                      │          │
                      ▼          ▼
                 report_gen   data_analysis
                             (带修正清单)
```

---

## 四、实施优先级

| 优先级 | 增强项 | 理由 | 预估工时 |
|--------|--------|------|---------|
| P0 | 增强1：L1 评分引擎集成 | 直接提升底稿质量，立竿见影 | 3天 |
| P0 | 增强2：Agent 输出结构化 | 是评分引擎工作的前提 | 2天 |
| P1 | 增强5：系统提示注入 | 低成本高收益 | 1天 |
| P1 | 增强4：年度对比检测 | 解决"照抄上年"痛点 | 2天 |
| P2 | 增强3：索引子系统 | 需要完整底稿归档体系配合 | 5天 |

---

## 五、与原文对照验证

以下逐条验证底稿指南的三级复核描述与 v2 设计的一致性：

| 指南描述 | v2 设计 | 一致性 | 备注 |
|---------|---------|--------|------|
| L1: 逐页检查程序/证据/结论 | L1 项目组长 Agent + 评分引擎 | ✅ 完全一致 | 增强后更具体 |
| L2: 重点看重大事项和高风险 | L2 部门经理 Agent | ✅ 完全一致 | 无需调整 |
| L3: 事务所层面独立复核 | L3 独立质量复核 Agent（否决权） | ✅ 完全一致 | 设计更严谨 |
| 被Q后补程序加证据 | Human-in-the-loop | ✅ 已规划 | 需细化交互 |

**结论**：v2 三级复核架构与行业标准完全吻合，不需要修改架构，只需按本方案增强执行层细节。
