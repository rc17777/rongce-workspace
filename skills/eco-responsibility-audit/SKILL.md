---
name: eco-responsibility-audit
description: >
  经济责任审计专业技能。提供领导干部经济责任审计全流程的AI辅助能力。
  适用场景：(1) 生成审计重点关注事项清单 (2) 撰写审计报告初稿/段落
  (3) 问题定性与法规引用匹配 (4) 生成审计底稿模板 (5) 撰写整改建议
  (6) 审计方案编制 (7) 访谈提纲生成 (8) 审计证据汇总与分析。
  触发词：经济责任审计、领导干部审计、离任审计、任中审计、审计报告、
  审计底稿、问题定性、整改建议、审计方案。
---

# 经济责任审计技能

## 概述

本技能基于《党政主要领导干部和国有企事业单位主要领导人员经济责任审计规定》
及相关实务经验，为审计人员提供全流程AI辅助。

## 快速开始

根据用户需求，匹配以下任务类型并按对应流程执行：

| 任务 | 用户可能的说法 | 操作 |
|------|--------------|------|
| 审计重点清单 | "帮我列一下审计重点"、"关注事项" | → 参见 [references/audit-focus.md](references/audit-focus.md) |
| 审计报告 | "写个报告初稿"、"报告怎么写" | → 参见 [references/audit-report.md](references/audit-report.md) |
| 问题定性 | "这个问题怎么定性"、"依据什么法规" | → 参见 [references/issue-classification.md](references/issue-classification.md) |
| 审计底稿 | "底稿模板"、"工作记录" | → 参见 [references/working-papers.md](references/working-papers.md) |
| 整改建议 | "提整改建议"、"管理建议" | → 参见 [references/rectification.md](references/rectification.md) |
| 全链SOP | "从政策法规到数据归档怎么做"、"全流程实操指南" | → 参见 [references/full-chain-sop.md](references/full-chain-sop.md) |
| 审计方案 | "做个审计方案"、"怎么安排" | → 参见 [references/audit-plan.md](references/audit-plan.md) |
| 访谈提纲 | "访谈问什么"、"谈话提纲" | → 参见 [references/interview-guide.md](references/interview-guide.md) |

## 通用要求

1. **法规引用**：优先引用现行有效法规，注明条款号。常用法规清单见 [references/laws-index.md](references/laws-index.md)
2. **格式规范**：使用审计行业通用术语，金额保留两位小数，日期格式 YYYY年MM月DD日
3. **用户信息**：如用户提供了被审计单位、人员、任期等信息，直接代入模板；如缺失，先询问再输出
4. **脱敏提醒**：涉及真实案例时提醒用户注意脱敏

## 工作流

1. 确认用户意图（哪个任务类型）
2. 收集必要信息（单位类型、人员职务、任期、预算规模等）
3. 读取对应 references 文件获取模板和指引
4. **如涉及数字化/智慧审计场景，查阅 [digital-eca.md](references/digital-eca.md)**
5. 生成输出，标注需要人工复核的判断点
