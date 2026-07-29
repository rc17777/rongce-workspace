---
title: book-to-skill—开源Agent知识编译管线分析
source: 微信公众号（极客之家）/ GitHub virgiliojr94/book-to-skill (5.3k⭐)
author: 丛林
date: 2026-06-14
scene: AI基础设施
tags: [book-to-skill, Agent Skill, 知识编译, Token优化, RAG互补]
keywords: [book-to-skill, PDF转Skill, 按需加载, 章节索引, Token节省, Docling]
---

# book-to-skill：把任何书籍/文档编译为Agent Skill

> 来源：GitHub virgiliojr94/book-to-skill (5.3k⭐) | 入库日期：2026-07-29

## 核心能力

**不是PDF阅读器**，是编译管线：把书籍/文档/论文/手册 → 结构化Agent Skill，按需加载。

### 输出结构

| 文件 | 大小 | 作用 |
|:--|:--|:--|
| SKILL.md | ~4000 token | 核心心智模型 + 章节索引 |
| chapters/ | 800-1200 token/章 | 每章摘要，按需加载 |
| glossary.md | — | 关键术语 + 章节出处 |
| patterns.md | — | 技术模式/算法/设计模式 |
| cheatsheet.md | — | 决策表/速查规则 |

### Token优化数据

| 对比 | 节省倍率 |
|:--|:--|
| vs 全文灌上下文 | **24-51倍** |
| vs Agent自己翻书 | **2.4-15.6倍** |
| 单次查询只加载 | 5K（核心4K + 章节1K） |
| 单本书转换成本 | $0.88-$1.42（一次性） |

### 核心设计

- **按需加载**：不问第五章，第五章就不占token
- **智能提取**：技术书走Docling（保留表格/代码块），纯文本走pdftotext
- **增量更新**：新论文/新版本可直接fold进已有skill
- **格式支持**：PDF/EPUB/DOCX/TXT/Markdown/HTML/MOBI等
- **跨Agent**：支持Claude Code/Copilot CLI/Amp/OpenClaw

## 融策直接应用场景

| 场景 | 输入 | 输出Skill |
|:--|:--|:--|
| 审计准则 | 中国注册会计师审计准则PDF | 审计准则查询Skill |
| 法规库 | 政府采购法/招标投标法/印花税法 | 法规条文检索Skill |
| 审计技巧 | 杂志OCR文章集（900+篇） | 审计知识技能库 |
| 绩效评价 | 绩效评价方法论文档 | 绩效评价方法论Skill |
| 报表模板 | 审计报告模板/底稿模板 | 模板生成Skill |
