---
name: first-principles-audit
description: First Principles Thinking for audit platform design and task analysis. Decompose any audit task into atomic elements, classify automation potential (✓ full / △ assisted / ✗ human-only), and generate an automation strategy. Use when designing audit workflows, evaluating which tasks to automate, or planning audit platform features.
---

# 审计第一性原理分析

基于马斯克第一性原理，将审计任务分解为原子要素，判断自动化可行性。

## 核心框架

### 六原子要素模型

| 要素 | 自动化 | 融策工具 |
|:------|:------|:--------|
| 信息收集 | ✅ 全自动 | unstructured-audit-data / OCR / RAG |
| 风险评估 | △ 半自动 | procurement-audit-models / apriori-audit |
| 证据获取 | △ 半自动 | audit_finding_processor |
| 证据评价 | ✗ 人工 | Human-in-the-loop |
| 结论形成 | ✗ 人工 | Human-in-the-loop |
| 工作记录 | ✅ 全自动 | report-writer / analysis-report |

### 审计底稿 = 证据链 + 工作记录 + 复核轨迹

## 使用方式

```bash
# 分析给定审计任务，输出自动化策略
python scripts/decompose_task.py "投标文件审查"
python scripts/decompose_task.py "专项资金审计" --o 自动化策略.xlsx
```

## 参考

- [references/framework.md](references/framework.md) — 完整框架说明
- 来源: 田川不是四川《审计平台开发_第一性原理分析（技能蒸馏版）》(2026-05-18)
