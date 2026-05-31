# 审计人员数字技能修炼手册 | 入门篇（二）：SQL基础——数据查询与关联分析

> **来源：** http://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483822&idx=1&sn=426fd65fc07e3243e6acb7181de0655b&chksm=c4c26394f3b5ea82079b8008b8bf47c243cb3d35d3c50a2dff82f4442c644a3b102498bb28db#rd
> **抓取时间：** 2026-05-06 12:12:38 +08:00 (Asia/Shanghai)
> **公众号：** 数审派

---

各位审计同仁，大家好！

上期我们完成了Excel高级功能的学习，掌握了数据透视表、Power Query和VBA这些利器。但你有没有遇到过这种情况：
- • Excel文件大到打开就卡顿？
- • 需要同时分析多个系统的数据，Excel难以合并？
- • 财务系统中的数据量太大，Excel根本装不下？

这时候，SQL**就是你的救星。

## 一、为什么审计人员要学SQL？

### 1.1 审计工作正在数字化转型

越来越多的企业采用ERP系统（如SAP、Oracle、金蝶、用友等）进行财务管理。财务数据存储在数据库中，而不是Excel文件中。

作为审计人员，如果你只会Excel，就只能依赖IT部门帮你导出数据，不仅效率低，还可能遗漏重要信息。掌握SQL，你可以直接查询数据库，自主获取需要的数据。**

### 1.2 SQL的优势

| **| 对比项 | Excel | SQL 
| 数据量 | 百万行级 | 亿级数据轻松应对 
| 多表关联 | VLOOKUP繁琐 | JOIN一键搞定 
| 数据更新 | 手动刷新 | 重新查询即可 
| 自动化 | 依赖宏 | 可编程自动化 
| 多人协作 | 文件传来传去 | 数据库统一管理 

### 1.3 审计应用场景

- • 财务系统数据查询**：直接从SAP/Oracle提取科目余额、凭证信息
- • 业务系统数据关联**：将销售系统、采购系统的数据与财务数据关联分析
- • 日志分析**：查询系统访问日志，发现异常操作行为
- • 大数据量处理**：银行流水、交易记录等大体量数据的高效分析

## 二、SQL基础语法

### 2.1 基本查询语句

SELECT语句是SQL的核心**，用于从数据库表中选取数据。

最基础的查询：**

-- 查询科目余额表的所有数据
SELECT *
FROM GL_BALANCE;`
```

选择特定列：**

-- 只查询科目代码、科目名称和期末余额
SELECT ACCOUNT_CODE,
       ACCOUNT_NAME,
       END_BALANCE
FROM GL_BALANCE;`
```

使用别名让结果更清晰：**

SELECT ACCOUNT_CODE AS 科目代码,
       ACCOUNT_NAME AS 科目名称,
       END_BALANCE AS 期末余额
FROM GL_BALANCE;`
```

### 2.2 筛选条件：WHERE子句

基础筛选：**

-- 查询资产类科目（假设科目代码以1开头）
SELECT *
FROM GL_BALANCE
WHERE ACCOUNT_CODE LIKE '1%';`
```

多条件筛选：**

-- 查询2024年12月且余额大于100万的科目
SELECT *
FROM GL_BALANCE
WHERE PERIOD = '202412'
  AND END_BALANCE > 1000000;`
```

常用运算符：**
| **| 运算符 | 说明 | 示例 
| = | 等于 | PERIOD = '202412'` 
| <> | 不等于 | STATUS <> 'X'` 
| >, < | 大于、小于 | BALANCE > 0` 
| LIKE | 模糊匹配 | NAME LIKE '%银行%'` 
| IN | 在列表中 | ACCOUNT_CODE IN ('1001','1002')` 
| BETWEEN | 在范围内 | BALANCE BETWEEN 10 AND 100` 
| AND | 并且 | A AND B` 
| OR | 或者 | A OR B` 

### 2.3 数据汇总：聚合函数

审计中经常需要对数据进行汇总分析，这就用到聚合函数。

常用聚合函数：**

-- 计算资产总计
SELECT SUM(END_BALANCE) AS 资产总计
FROM GL_BALANCE
WHERE ACCOUNT_CODE LIKE '1%';`
```

-- 按科目大类汇总余额
SELECT ACCOUNT_TYPE AS 科目类别,
       COUNT(*) AS 科目数量,
       SUM(END_BALANCE) AS 余额合计,
       AVG(END_BALANCE) AS 平均余额,
       MAX(END_BALANCE) AS 最大余额,
       MIN(END_BALANCE) AS 最小余额
FROM GL_BALANCE
GROUP BY ACCOUNT_TYPE;`
```

HAVING子句：筛选汇总结果**

WHERE用于筛选原始数据，HAVING用于筛选汇总后的结果。

-- 只显示余额合计超过1000万的科目类别
SELECT ACCOUNT_TYPE,
       SUM(END_BALANCE) AS 余额合计
FROM GL_BALANCE
GROUP BY ACCOUNT_TYPE
HAVING SUM(END_BALANCE) > 10000000;`
```

### 2.4 排序与限制结果

-- 按余额降序排列，只显示前10条
SELECT ACCOUNT_CODE,
       ACCOUNT_NAME,
       END_BALANCE
FROM GL_BALANCE
WHERE PERIOD = '202412'
ORDER BY END_BALANCE DESC
LIMIT 10;`
```

> 

提示**：不同数据库的语法略有不同。SQL Server使用TOP 10`，MySQL/PostgreSQL使用LIMIT 10`，Oracle使用ROWNUM`。

## 三、多表关联：JOIN

这是SQL最核心、也是最重要的部分。审计中，我们经常需要将多个表的数据关联起来分析。

### 3.1 关联的基本概念

假设我们有两张表：

科目余额表（GL_BALANCE）**
| **| ACCOUNT_CODE | ACCOUNT_NAME | END_BALANCE 
| 1001 | 库存现金 | 5000 
| 1002 | 银行存款 | 800000 
| 1122 | 应收账款 | 200000 

部门表（DEPT）**
| **| DEPT_CODE | DEPT_NAME 
| 01 | 销售部 
| 02 | 市场部 
| 03 | 财务部 

### 3.2 INNER JOIN：内连接

只返回两个表中匹配的记录。

-- 将科目余额表与部门表关联（假设部门代码在余额表中有体现）
SELECT gl.ACCOUNT_CODE,
       gl.ACCOUNT_NAME,
       gl.END_BALANCE,
       dp.DEPT_NAME
FROM GL_BALANCE gl
INNER JOIN DEPT dp ON gl.DEPT_CODE = dp.DEPT_CODE;`
```

### 3.3 LEFT JOIN：左连接

返回左表的所有记录，以及右表中匹配的记录。

审计应用场景**：查看所有科目，即使某些科目没有部门关联

SELECT gl.ACCOUNT_CODE,
       gl.ACCOUNT_NAME,
       gl.END_BALANCE,
       dp.DEPT_NAME
FROM GL_BALANCE gl
LEFT JOIN DEPT dp ON gl.DEPT_CODE = dp.DEPT_CODE;`
```

### 3.4 RIGHT JOIN：右连接

返回右表的所有记录，以及左表中匹配的记录。

### 3.5 全连接：FULL OUTER JOIN

返回两个表的所有记录。

-- 即使科目没有部门关联，或部门没有科目关联，都显示
SELECT gl.ACCOUNT_CODE,
       gl.ACCOUNT_NAME,
       dp.DEPT_NAME
FROM GL_BALANCE gl
FULL OUTER JOIN DEPT dp ON gl.DEPT_CODE = dp.DEPT_CODE;`
```

### 3.6 关联多个表

审计中经常需要关联多个表：

-- 关联科目余额表、凭证主表、凭证明细表
SELECT gl.ACCOUNT_CODE,
       gl.ACCOUNT_NAME,
       vm.VOUCHER_DATE,
       vd.DESCRIPTION,
       vd.DEBIT_AMOUNT,
       vd.CREDIT_AMOUNT
FROM GL_BALANCE gl
INNERJOIN VOUCHER_MAIN vm ON gl.VOUCHER_ID = vm.VOUCHER_ID
INNERJOIN VOUCHER_DETAIL vd ON vm.VOUCHER_ID = vd.VOUCHER_ID
WHERE gl.PERIOD ='202412'
AND gl.ACCOUNT_CODE LIKE'1%';`
```

## 四、实战案例

### 案例一：应收账款账龄分析

-- 按客户统计应收账款余额及账龄
SELECT cust.CUSTOMER_NAME AS 客户名称,
       SUM(inv.OPEN_AMOUNT) AS 应收余额,
       SUM(CASE
           WHEN DATEDIFF(CURDATE(), inv.DUE_DATE) <=30THEN inv.OPEN_AMOUNT 
           ELSE0
       END) AS'0-30天',
       SUM(CASE
           WHEN DATEDIFF(CURDATE(), inv.DUE_DATE) BETWEEN31AND60THEN inv.OPEN_AMOUNT 
           ELSE0
       END) AS'31-60天',
       SUM(CASE
           WHEN DATEDIFF(CURDATE(), inv.DUE_DATE) BETWEEN61AND90THEN inv.OPEN_AMOUNT 
           ELSE0
       END) AS'61-90天',
       SUM(CASE
           WHEN DATEDIFF(CURDATE(), inv.DUE_DATE) >90THEN inv.OPEN_AMOUNT 
           ELSE0
       END) AS'90天以上'
FROM AR_INVOICE inv
INNERJOIN CUSTOMER cust ON inv.CUSTOMER_ID = cust.CUSTOMER_ID
WHERE inv.STATUS ='OPEN'
GROUPBY cust.CUSTOMER_NAME
ORDERBYSUM(inv.OPEN_AMOUNT) DESC;`
```

### 案例二：银行对账

-- 查找银行账有但账面没有的记录（未达账项）
SELECT bank.TRANSACTION_ID,
       bank.TRANSACTION_DATE,
       bank.AMOUNT,
       bank.DESCRIPTION
FROM BANK_TRANSACTION bank
LEFT JOIN GL_BANK_MATCH match ON bank.TRANSACTION_ID = match.BANK_TRANS_ID
WHERE match.GL_TRANS_ID IS NULL
  AND bank.TRANSACTION_DATE BETWEEN '2024-01-01' AND '2024-12-31';`
```

### 案例三：异常交易识别

-- 查找同一供应商同一天多笔大额交易（可能需要进一步检查）
SELECT VENDOR_NAME,
       TRANSACTION_DATE,
       COUNT(*) AS 交易笔数,
       SUM(AMOUNT) AS 交易总额,
       AVG(AMOUNT) AS 平均金额
FROM PURCHASE_TRANS
WHERE AMOUNT >50000
GROUPBY VENDOR_NAME, TRANSACTION_DATE
HAVINGCOUNT(*) >3
ORDERBYSUM(AMOUNT) DESC;`
```

## 五、子查询与表表达式

### 5.1 子查询

子查询是嵌套在另一个查询中的查询。

-- 查找余额超过平均余额的科目
SELECT ACCOUNT_CODE,
       ACCOUNT_NAME,
       END_BALANCE
FROM GL_BALANCE
WHERE END_BALANCE > (
    SELECT AVG(END_BALANCE)
    FROM GL_BALANCE
);`
```

### 5.2 WITH子句（公用表表达式）

当查询复杂时，使用WITH可以让代码更清晰：

WITH MonthlySummary AS (
    SELECT ACCOUNT_CODE,
           MONTH,
           SUM(DEBIT_AMOUNT) AS 月借方合计,
           SUM(CREDIT_AMOUNT) AS 月贷方合计
    FROM GL_TRANSACTION
    WHEREYEAR='2024'
    GROUPBY ACCOUNT_CODE, MONTH
),
Variance AS (
    SELECT ACCOUNT_CODE,
           MAX(月借方合计) -MIN(月借方合计) AS 波动幅度
    FROM MonthlySummary
    GROUPBY ACCOUNT_CODE
)
SELECT gl.ACCOUNT_CODE,
       gl.ACCOUNT_NAME,
       v.波动幅度
FROM GL_BALANCE gl
INNERJOIN Variance v ON gl.ACCOUNT_CODE = v.ACCOUNT_CODE
WHERE v.波动幅度 >1000000
ORDERBY v.波动幅度 DESC;`
```

## 六、学习资源

| **| 资源类型 | 推荐 
| 在线教程 | SQLZoo、LeetCode刷题、W3Schools 
| 书籍 | 《SQL必知必会》《深入浅出SQL》 
| 练习平台 | HackerRank、DataCamp 
| 数据库 | MySQL（免费开源，适合学习） 

## 七、实践作业

- 1. 安装MySQL数据库**：下载安装MySQL，安装示例数据库或自建测试库
- 2. 编写查询**：假设有科目余额表和凭证表，编写SQL查询以下内容：

- • 各月费用类科目发生额汇总
- • 期末余额前10大的资产科目
- • 同一科目借贷不平的月份（如果存在）

- 3. 关联分析**：尝试关联多张表，理解表与表之间的关系

## 总结

今天我们学习了SQL的基础知识：
| **| 知识点 | 说明 | 审计应用 
| SELECT | 数据查询 | 基础数据提取 
| WHERE | 条件筛选 | 按科目、期间、金额筛选 
| 聚合函数 | 数据汇总 | 余额汇总、计数统计 
| JOIN | 表关联 | 多表数据关联分析 
| 子查询 | 查询嵌套 | 复杂条件判断 

SQL是审计人员进入数据世界的钥匙。掌握SQL，你可以直接与数据库对话，自主获取和分析数据，不再依赖IT部门的"中间人"。

下期预告**：我们将学习Python爬虫与数据采集**——教你自动从网站获取审计相关数据。敬请期待！

如有问题，欢迎在评论区留言讨论。
