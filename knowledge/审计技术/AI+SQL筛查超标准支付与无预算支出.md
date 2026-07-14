---
title: "AI+SQL 筛查超标准支付与无预算支出"
source: "微信公众号"
date: 2026-07
tags: [SQL, AI辅助审计, 预算执行审计, 超标准支付, 无预算支出, 审计模型]
scene: [预算, 收支, 经责]
category: 审计技术
method: [SQL建模, AI代码生成, 数据式审计]
---

## 场景一：AI+SQL 筛查超标准支付

### 单笔超标 SQL
```sql
SELECT p.人员ID, p.费用类型,
       p.支付金额 AS 实际支付金额,
       s.金额上限 AS 标准限额,
       (p.支付金额 - s.金额上限) AS 超标金额
FROM Payment p
JOIN Standard s ON p.费用类型 = s.费用类型
WHERE p.支付金额 > s.金额上限;
```

### 累计超标 SQL（某部门全年差旅费超预算）
```sql
SELECT p.部门名称,
       SUM(p.支付金额) AS 累计实际支出,
       b.核定预算,
       (SUM(p.支付金额) - b.核定预算) AS 超预算金额
FROM Payment p
JOIN Budget b ON p.部门名称 = b.部门名称
WHERE p.支付日期 BETWEEN '2023-01-01' AND '2023-12-31'
  AND p.费用类型 = '差旅费'
GROUP BY p.部门名称, b.核定预算
HAVING SUM(p.支付金额) > b.核定预算;
```

## 场景二：AI+SQL 筛查无预算支出

### 无预算项目 SQL
```sql
SELECT a.*, '无预算项目' AS 疑点类型
FROM Actual_Spend a
LEFT JOIN Budget_Control b ON a.项目编码 = b.项目编码
WHERE b.项目编码 IS NULL;
```

### 综合版（无预算+超预算）
```sql
SELECT COALESCE(a.项目名称, b.项目名称) AS 项目名称,
       COALESCE(a.项目编码, b.项目编码) AS 项目编码,
       b.预算金额,
       SUM(a.支出金额) AS 累计支出,
       CASE 
         WHEN b.项目编码 IS NULL THEN '完全无预算'
         WHEN SUM(a.支出金额) > b.预算金额 THEN '超预算支出'
         ELSE '正常'
       END AS 审计疑点
FROM Actual_Spend a
FULL OUTER JOIN Budget_Control b ON a.项目编码 = b.项目编码
GROUP BY COALESCE(a.项目名称, b.项目名称),
         COALESCE(a.项目编码, b.项目编码),
         b.预算金额
HAVING b.项目编码 IS NULL
    OR (SUM(a.支出金额) > b.预算金额);
```

## 审计师AI使用建议

1. **数据清洗先行**：告诉AI真实字段名，要求加入TRIM()和IS NOT NULL
2. **理解代码逻辑**：AI写的代码可能索引效率低下，需具备SQL复核能力
3. **关注模糊匹配**：用LIKE语句筛查名称相近规避预算的项目
