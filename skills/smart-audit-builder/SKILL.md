---
name: smart-audit-builder
description: >
  智能审计系统构建技能。基于数审派公众号文章体系，提供从RAG知识库到Agent助手的完整构建方案。
  适用场景：(1) 搭建审计法规RAG知识库（ChromaDB+text2vec，零成本本地运行）
  (2) 构建Text2SQL审计Agent——自然语言转SQL查询
  (3) 审计Agent开发——从0到1自主搭建
  (4) 向量数据库在审计中的应用
  (5) 零代码/低代码搭建智能审计助手
  触发词：审计RAG、Text2SQL审计、审计Agent、审计知识库、向量数据库审计、
  智能审计系统、审计自动化、审计大模型、审计AI助手、审计法规检索、搭建Agent、RAG知识库建设。
---

# 智能审计系统构建技能

整合数审派公众号技术性干货专辑6篇文章 + 数字化审计AI相关文章。

## 快速入门：审计Agent + RAG知识库

对于中小型事务所，最实用的方案是 **Agent（大脑）+ RAG（资料库）** 的组合：

```
你提问 → Agent助手 → 需要查法规？→ RAG知识库检索 → 生成回答
                  → 需要算数据？→ 调用SQL/Python工具 → 返回结果
                  → 需要出报告？→ 调用模板生成 → 输出Word文档
```

### 你其实已经有了 Agent

OpenClaw本身就是你的Agent平台。我（融策左护法）就是在OpenClaw上运行的审计Agent。
现在只要再加一个 **RAG知识库**，就能让它随时检索审计法规。

## 搭建审计法规RAG知识库（30分钟，零成本）

参考数审派RAG文章 + 文章中的审计法规检索案例，一键搭建脚本见：
- `scripts/build_rag.py` — 审计法规RAG知识库搭建脚本
- `scripts/query_rag.py` — 查询知识库的接口脚本

### 核心架构

```
你的问题
    ↓
[向量化] text2vec-base-chinese（本地嵌入模型）
    ↓
[向量检索] ChromaDB（本地向量数据库）
    ↓ 返回相关法规条款
[大模型] DeepSeek/Claude（根据需要选择）
    ↓
回答 + 法规出处引用
```

### 适用场景

| 场景 | 说明 |
|------|------|
| 现场审计查法规 | 输入"围标串标的认定标准"，秒级找出相关法规条款 |
| 合同风险审查 | 上传合同文本，自动比对相似历史案例中的风险点 |
| 审计底稿辅助 | 半自动生成底稿初稿，引用对应法规依据 |
| 新人培训 | 新人自己查法规，不用每次都问老员工 |

## 进阶：Agent开发能力

如果你需要**自定义Agent**（不只是用我的能力），数审派文章提供了完整方案：

### 极简版Agent（不到60行Python）
原理：规划模块（大模型拆解需求）+ 执行模块（调用工具）+ 反馈模块（自我修正）
参考 `scripts/simple_agent.py`

### 推荐框架
- 小需求：直接用OpenClaw的Agent能力
- 中等需求：用LangChain/LlamaIndex搭建
- 复杂需求：用CrewAI/AutoGen做多Agent协同

## Text2SQL Agent（审计专用）

提供审计人员用自然语言查数据的桥梁：

```python
# 核心Prompt模板
你是一个审计领域SQL专家。请将自然语言需求转换为SQL。
数据库表结构: [表名+字段说明]
审计需求: [用户输入]
输出SQL: SELECT ...
查询逻辑: 解释SQL做了什么
```

## 参考文件

| 文件 | 内容 |
|------|------|
| [RAG构建指南](references/rag-building-guide.md) | 审计RAG完整搭建教程 |
| [Text2SQL审计](references/text2sql-audit.md) | 自然语言转SQL的Prompt模板 |
