---
name: "apriori-audit"
description: >
  Apriori association rule algorithm for audit anomaly detection. Finds frequent co-occurrence patterns in transactional data to detect collusion rings (bid-rigging groups, healthcare fraud gangs, etc.) and missing-relationship anomalies (procedures that should co-occur but don't). Use when audit work involves (1) Finding groups of entities that frequently appear together across transactions, (2) Detecting abnormal co-occurrence patterns in bidding/medical/transaction data, (3) Computing support/confidence/lift metrics for association rules, (4) Identifying missing expected associations (should-be-there-but-isn't), or (5) Building frequent itemset analysis for any audit domain.
business_line: "通用审计方法"
methods: "Apriori关联规则; 频繁项集; 支持度/置信度/提升度"
difficulty: "高级"
keywords: "关联规则, Apriori, 围标识别, 共现分析, 缺失关联"
status: "stable"
---

# Apriori 关联规则审计分析

通用Apriori算法实现，支持两类审计应用方向。

## 快速使用

```bash
# 方向一: 发现频繁结队(不应形成关联却形成)
python scripts/apriori_analysis.py --i 交易数据.xlsx --mode frequent \
  --min-support 3 --min-confidence 0.6 --o 频繁结队疑点.xlsx

# 方向二: 发现缺失关联(应形成关联却未形成) 
python scripts/apriori_analysis.py --i 交易数据.xlsx --mode missing \
  --min-support 0.8 --o 缺失关联疑点.xlsx
```

## 输入数据格式

### 方向一 (频繁结队): 长表格式

| 事务ID | 项 |
|--------|-----|
| 2023-01-01 | P001 |
| 2023-01-01 | P002 |
| 2023-01-01 | P003 |
| 2023-01-02 | P001 |
| 2023-01-02 | P004 |

事务ID = 日期/项目编号等。项 = 患者/供应商/投标人等。

### 方向二 (缺失关联): 同上格式

同一事务内应有A→B的关联但缺失 → 标记疑点。

## 参数指导

| 审计场景 | 支持度阈值 | 置信度阈值 | 频繁项集深度 |
|:------|:--------|:---------|:----------|
| 招投标围标(项目少) | ≥2 | ≥0.6 | 2-4 |
| 招投标围标(项目多) | ≥3 | ≥0.7 | 2-4 |
| 医保骗保 | ≥3 | ≥0.8 | 2-3 |
| 医疗收费合规 | ≥0.8(比例) | ≥0.9 | 2-3 |
| 采购供应商关联 | ≥2 | ≥0.5 | 2-5 |

## 技术背景

详见 [references/methodology.md](references/methodology.md) 获取完整的Apriori算法原理、两类应用方向的详细逻辑和实战案例。

## 工具依赖

- `pandas`, `openpyxl`: 数据处理和Excel输出
- 无需额外包（纯Python实现Apriori）
