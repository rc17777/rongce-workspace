---
title: RAG 评估体系：5 个指标让知识库从「盲飞」到「可量化」
source: 微信公众号「LLM大模型Seven」
url: https://mp.weixin.qq.com/s/q7GCFocKakDJzqcDpiqsLA
date: 2026-07-16
ingested: 2026-07-20
tags: [RAG, 评估, 召回率, 忠实度, 审盾]
scene: 审盾一期复核质量评估
---

# RAG 评估体系：5 个指标

## 核心问题
70% 的 RAG 系统缺乏评估体系。大多数知识库以"感觉还不错"为唯一质量标准。

## RAG 评估的四个难点
1. 正确答案不唯一：BLEU/ROUGE 不适合语义评估
2. 评估本身需要"理解"：依赖 LLM 带来额外成本和偏差
3. 检索和生成耦合：答案不好不知道问题出在哪一层
4. 没有标准测试集：需要自己建（问题, 标准答案, 上下文）三元组

## 5 个核心指标

### 第一层：检索质量
- **Context Precision**：检索到的内容有多少是有用的（带位置权重）
  - AP = Σ (Precision@k × is_relevant@k) / total_relevant
  - Precision 低 → Reranker 差或分块太大
- **Context Recall**：需要的内容有多少被检索到了
  - 标准答案拆原子陈述 → 逐条检查上下文支撑
  - Recall 低 → top-K 太小、分块切断了关键信息

### 第二层：生成忠实性
- **Faithfulness**：有没有在"脑补"——答案拆原子陈述，逐条检查是否有上下文支撑
  - 专门测幻觉

### 第三层：答案质量
- **Answer Relevancy**：切题程度
- **Answer Correctness**：事实正确性（需要 ground truth）

## 诊断组合

| 症状 | 意味着 | 先做什么 |
|:--|:--|:--|
| Precision 高 + Recall 低 | 找到的质量好但覆盖不全 | 调大 top-K |
| Precision 低 + Recall 高 | 覆盖全了但噪声太多 | 加 Reranker 或改分块 |
| 两个都低 | 检索架构有问题 | 先查语料质量 |

## 对审盾一期的价值
**审盾一期最缺的就是这套评估体系。** 当前所有复核规则都是"规则引擎 + LLM 判断"，但没有量化指标来回答"我的复核器今天表现怎么样"。建议一期验收标准中引入此框架：
- 审盾复核器输出 = 生成答案
- 审计经理复核意见 = 标准答案
- 5 个指标逐一量化，作为验收核心标准