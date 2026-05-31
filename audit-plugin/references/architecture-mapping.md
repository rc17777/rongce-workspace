# claude-for-legal → audit-plugin 架构映射（政府专项审计版）

> 更新日期：2026-05-15
> 架构版本：v2.0（政府专项审计）

---

## 一、为什么从 v1 改到 v2

| | v1.0（财务审计模式） | v2.0（政府专项审计模式） |
|---|---|---|
| **定位** | 对标 claude-for-legal 合同审查 | 对标 融策 政府专项审计真实流程 |
| **核心痛点** | 凭证抽查效率 | 政策吃不透、问题深度广度不够 |
| **CLAUDE.md** | 审计参数配置 | 政策知识库 + 审计方案 |
| **起点** | 冷启动面试（问审计方法论） | 政策文件解读（喂政策文件） |
| **分析核心** | 记账凭证 vs 原始凭证 | 政策要求 vs 实际执行 vs 资金 vs 效果 |
| **输出重点** | 差异/异常清单 | 问题定性+政策依据+可落地建议 |

---

## 二、流程映射

```
政府专项审计流程               claude-for-legal 映射          audit-plugin v2
─────────────────────────────────────────────────────────────────────────────
① 学习政策文件       ←→   冷启动面试（学方法论）      →   policy-digest
② 写实施方案         ←→   （无直接对应）              →   implementation-plan
③ 数据分析           ←→   NDA/合同审查               →   multi-source-analysis
   （多种方法）
④ 底稿+报告+汇报     ←→   输出草稿+备忘录             →   finding-generator
                                                          recommendation-engine
                                                          work-paper
                                                          report-writer
```

---

## 三、三个核心设计原则的迁移

### 1. 冷启动 → 政策文件喂入

```
法律：律所方法论 → CLAUDE.md 实务档案
审计：政策文件   → CLAUDE.md 政策知识库

同一个插件，A项目和B项目行为完全不同
→ 因为它们的政策依据和审计重点不同
```

### 2. 串上下文不串流程

```
policy-digest 写的政策知识库
    ↓ 所有后续 Agent 都读
implementation-plan 基于政策知识库推导重点
multi-source-analysis 基于重点和方法分析数据
finding-generator 基于分析结果和政策红线找问题
recommendation-engine 基于问题和政策框架提建议
```

**新加一个审计方法 → 只改 multi-source-analysis；新加一个数据分析子方法 → 只改 data-analysis-methods。其它不动。**

### 3. 输出永远是草稿

完全保留，且对政府审计更重要：
- 问题定性 → 涉及被审计单位责任，必须CPA确认
- 移送建议 → 法律后果严重，必须合伙人和法律顾问会签
- 所有建议 → 标注"是否采纳由业主决定"

---

## 四、7个 Skill 的定位

| Skill | 角色 | 核心价值 |
|-------|------|---------|
| **policy-digest** | 🔑 入口 | 把一堆政策文件变成可用的审计标准 |
| **data-analysis-methods** | 🧰 工具箱 | 审计问题→分析方法→工具→代码（🆕） |
| **implementation-plan** | 方案 | 从政策要求推导审计重点和方法 |
| **multi-source-analysis** | 引擎 | 财务+业务+文本交叉分析（嵌入五步法） |
| **data-analysis-methods** | 工具箱 | 7大方法+工具选型+代码模板（🆕 v2.0.1） |
| **finding-generator** | 大脑 | 四层递进挖出深度问题 |
| **recommendation-engine** | 输出 | 可落地、可考核的具体建议 |
| **work-paper** | 存档 | 标准化的审计底稿 |
| **report-writer** | 交付 | 审计报告+PPT+汇报话术 |
