---
id: CAS-20260715-5E69
type: ""
source: "微信公众号"
source_url: "C:\Users\scrccpa\.openclaw\workspace\knowledge\审计技术\AI+SQL筛查超标准支付与无预算支出.md"
date: "2026-07"
date_collected: "2026-07-15 16:48"
tags: [[SQL, AI辅助审计, 预算执行审计, 超标准支付, 无预算支出, 审计模型]]
related_laws: []
related_policies: []
severity: ""
industry: ""
region: ""
audit_type: ""
amount_involved: ""
---

# AI+SQL 筛查超标准支付与无预算支出

## 案例概述

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
FROM Actua

## 审计发现

（暂无）

## 审计方法

（暂无）

## 问题定性

（暂无）

## 处理结果

（暂无）

## 适用法规

（暂无）

## 可借鉴经验

（暂无）

---

*来源: [微信公众号](C:\Users\scrccpa\.openclaw\workspace\knowledge\审计技术\AI+SQL筛查超标准支付与无预算支出.md) | 采集于 2026-07-15 16:48*
