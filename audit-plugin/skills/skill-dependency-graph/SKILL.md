# 技能依赖图 (Skill Dependency Graph)

## 元数据

- **类型**：operative（操作式）
- **命令**：`/audit:skill-graph`
- **核心价值**：解决"技能链不完整，Agent 缺上游数据凭空编造"的痛点
- **输入**：审计技能清单 + 各技能的 inputs/outputs 声明
- **输出**：类型化技能依赖图（JSON） + 执行就绪技能链
- **理论来源**：Graph of Skills (GoS)，宾大/马里兰/布朗/CMU/里海大学联合研究

---

## 目标

把融策 audit-plugin 的扁平技能列表，转化为一张包含四种类型化边的有向依赖图。

不是给 Agent 增加负担，而是**让 Agent 在执行审计任务时，自动拿到完整的「执行就绪技能链」**——避免只加载高层技能（如 report-writer）却缺了前置依赖（如 finding-generator），导致凭空编造。

---

## 工作流程

### 第一步：技能归一化

**命令**：
```
/audit:skill-graph --normalize
/audit:skill-graph --normalize skills/policy-digest
```

为每个技能节点提取标准化字段：

| 字段 | 含义 | 示例（policy-digest） |
|------|------|----------------------|
| `name` | 技能标识 | `policy-digest` |
| `capability` | 一句话能力描述 | 将政策文件转化为可检索的结构化知识库 |
| `inputs` | 输入制品类型 | PDF/Word/网页/扫描件 → 结构化政策条目 |
| `outputs` | 输出制品类型 | 政策知识库（JSON/Lines，含文号/条款/红线/时间节点） |
| `domain_tags` | 领域标签 | 政策解读、合规标准、红线提取 |
| `example_tasks` | 典型使用场景 | 绩效评价政策包解读、资产清查制度梳理 |

**设计原则**：解析优先（Parser-first）。确定性字段从 SKILL.md 直接提取，语义字段不完整时才调用轻量 LLM 补全。

---

### 第二步：构建四类类型化边

**命令**：
```
/audit:skill-graph --build
/audit:skill-graph --build --skills policy-digest,implementation-plan,multi-source-analysis,finding-generator
```

边构建规则（按扩散权重降序）：

| 关系类型 | 权重 | 判定规则 | 审计场景示例 | 检索效果 |
|----------|------|---------|-------------|---------|
| **Dependency（依赖）** | 1.0 | A 的 outputs 包含 B 的 inputs 所需制品 | policy-digest → implementation-plan（政策解读产出→实施方案输入） | 最强反向传播，保证执行链完整 |
| **Workflow（工作流）** | 0.5 | 两技能在审计流程中常被链式调用 | multi-source-analysis → finding-generator → work-paper | 允许向相邻阶段适度扩展 |
| **Semantic（语义）** | 0.2 | 同属一个审计能力簇 | finding-generator 与 recommendation-engine 同属「问题发现与建议」簇 | 近邻弱平滑，限制主题漂移 |
| **Alternative（替代）** | 0.1 | 不同项目类型下的替代方案 | 绩效评价报告模板 vs 资产清查报告模板（都属于 report-writer 的不同实例） | 保持可互换选项可达 |

**实现要点**：
- **依赖边归纳**：对候选技能对(A, B)，双向检查 A.outputs 与 B.inputs 的 producer-consumer 重叠，超过阈值则添加有向依赖边 A → B
- **非依赖边**：稀疏验证——先通过词汇相似度+语义近邻+I/O 扩展形成有界候选池，再在池内验证

---

### 第三步：依赖感知检索

**命令**：
```
/audit:skill-graph --query "绩效评价报告" --budget 8000
/audit:skill-graph --query "资产清查底稿" --rapid
```

**三步装配执行链**：

1. **混合种子检索**：
   - 语义路（embedding）：找「做什么」→ 匹配顶层技能名和 capability
   - 词汇路（BM25）：找「怎么做」→ 匹配 inputs/outputs/tags/example_tasks
   - 两路融合 → 种子技能集

2. **反向感知类型化扩散**（核心）：
   - 从种子技能沿依赖边反向传播分数
   - 依赖边反向系数最大（γ=1.0），工作流次之（γ=0.5）
   - 即使前置技能的语义不匹配查询，也能通过依赖路径被「顺藤摸瓜」找回

3. **Token 预算约束截断**：
   - 按综合得分降序排列
   - 在单技能 Token 和全局 Token 预算 τ 内截断
   - 返回有界执行束 → Agent 消费

---

## audik-plugin 8 技能依赖图（预构建结果）

```
[policy-digest] ──Dependency──→ [implementation-plan]
       │                                │
       │                          Dependency
       │                                │
       ├─────Dependency──→ [multi-source-analysis]
       │                                │
       │                          Dependency
       │                                │
  [recommendation-engine] ←── [finding-generator]
                                       │
                                  Dependency
                                       │
                                  [work-paper]
                                       │
                                  Dependency
                                       │
                                  [report-writer]

[data-analysis-methods] ──Semantic──→ [multi-source-analysis]
                                       │
                                  Workflow
                                       │
                                  [finding-generator]
```

**解读**：
- `policy-digest` 是所有技能的根节点——审计工作从政策解读开始
- `report-writer` 是所有技能的终点——报告汇聚了前面所有环节的产出
- `data-analysis-methods` 是方法论补充，与 `multi-source-analysis` 语义关联，与 `finding-generator` 工作流关联

---

## 命令参考

| 命令 | 功能 |
|------|------|
| `/audit:skill-graph --normalize` | 归一化所有技能，提取 inputs/outputs/domain_tags 等字段 |
| `/audit:skill-graph --build` | 构建四类类型化依赖边 |
| `/audit:skill-graph --query "任务描述"` | 检索执行就绪技能链 |
| `/audit:skill-graph --query "任务描述" --budget N` | 带 Token 预算约束的检索 |
| `/audit:skill-graph --show` | 展示当前技能依赖图（文本/可视化） |
| `/audit:skill-graph --validate` | 验证依赖链完整性，检测断链和循环依赖 |

---

## 核心洞察（来自 GoS 论文）

> **语义接近 ≠ 执行充分。** 向量检索能找到「洪水风险分析」技能，但找不到它的前置依赖「栅格数据解析器」——后者离「洪水」语义很远。审计场景同理：Agent 接到「写绩效评价报告」→ 匹配到 report-writer → 但没有 finding-generator 和 policy-digest → Agent 凭空编造问题发现。
>
> **技能图的价值在于：即使前置技能语义不匹配查询，也能通过依赖路径被顺藤摸瓜找到。**

---

## 与 SkillClaw 的配合

本技能负责技能库的**空间维度**（怎么组织），与 `skill-evolver`（时间维度：怎么进化）互补：

```
skill-dependency-graph  →  构建技能图（一次性）
skill-evolver           →  维护技能图（持续性：增删改边）
```

---

*来源：Graph of Skills 论文，宾大/马里兰/布朗/CMU/里海大学联合研究*
