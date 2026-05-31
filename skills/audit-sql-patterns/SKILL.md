---
name: audit-sql-patterns
description: 需要用SQL对审计数据进行查询分析
version: 1.0.0
author: 融策会计师事务所·审计一部
tags: SQL, 数据分析, 模板
source: 数审派公众号文章 / 审计SQL实战系列 / 审计SQL技能应用指南
---

# 审计SQL分析模板库

内置10+审计常用SQL分析模板：重复支付检测、拆分支付规避招标检测、供应商关联关系分析、资金流向追踪、异常时间模式检测等。即改即用。

## 适用场景

- 需要用SQL对审计数据进行查询分析

## 执行步骤

### 步骤 1
选择分析场景（重复支付/拆分支付/供应商分析/资金流向/时间异常/地址异常）

### 步骤 2
根据数据表结构调整SQL模板中的字段名

### 步骤 3
执行查询，获得结果

### 步骤 4
对结果进行解读和建议后续审计步骤


## 输出格式

```
-- 【拆分支付检测模板】检测同一供应商、同日、多笔金额之和=整数的记录
SELECT supplier, pay_date, SUM(amount) as total, COUNT(*) as cnt
FROM payments WHERE pay_date='2025-03-15'
GROUP BY supplier, pay_date
HAVING COUNT(*) >= 2 AND SUM(amount) % 10000 = 0
ORDER BY total DESC;

-- 结果：3条疑似拆分支付记录，合计金额XX万元
-- 建议：逐条核查合同约定支付方式与实际情况是否一致
```

## 来源

数审派公众号文章 / 审计SQL实战系列 / 审计SQL技能应用指南
