# 审计AI-SQL实战模板：五大场景

> 来源：数审派《审计人员如何用AI生成SQL，提高数据分析效率？》(2026-06-30)
> 归档：融策知识库 knowledge/audit-sql-templates/
> 使用：每个场景含「审计场景→表结构→SQL模板→验证要点」

---

## 场景一：科目余额异常检测

### 审计场景
从科目余额表中快速识别余额方向异常或金额异常的一级科目。

### 表结构
```sql
-- acct_balance（科目余额表）
-- company_code   VARCHAR  公司代码
-- account_code   VARCHAR  科目编码（4位=一级科目）
-- account_name   VARCHAR  科目名称
-- period         VARCHAR  期间，格式YYYY-MM
-- debit_amt      DECIMAL  借方金额
-- credit_amt     DECIMAL  贷方金额
-- balance        DECIMAL  余额（正=借方余额，负=贷方余额）
```

### AI生成SQL
```sql
SELECT
    company_code,
    account_code,
    account_name,
    balance,
    ABS(balance) AS abs_balance
FROM acct_balance
WHERE period = '2026-06'
  AND balance < -1000000          -- 余额为负数且超过100万
  AND LENGTH(account_code) = 4    -- 一级科目
ORDER BY abs_balance DESC;
```

### 变体：区分资产/负债类科目方向异常
```sql
-- 资产类科目（1开头）出现贷方余额
SELECT * FROM acct_balance
WHERE period = '2026-06'
  AND account_code LIKE '1%'
  AND balance < 0
  AND ABS(balance) > 1000000;

-- 负债类科目（2开头）出现借方余额
SELECT * FROM acct_balance
WHERE period = '2026-06'
  AND account_code LIKE '2%'
  AND balance > 0
  AND ABS(balance) > 1000000;
```

### 验证要点
- [ ] 确认科目编码长度=一级科目的规则（用友NC为4位，部分系统为3位）
- [ ] 确认balance字段的正负号含义（是借方余额还是贷方余额）
- [ ] 100万阈值可根据被审计单位规模调整
- [ ] 抽查5个科目，与财务系统余额表核对

---

## 场景二：往来款账龄自动分层

### 审计场景
按客户汇总应收账款未回款金额，并按标准账龄分层统计。

### 表结构
```sql
-- ar_detail（应收账款明细）
-- customer_id      VARCHAR  客户ID
-- customer_name    VARCHAR  客户名称
-- invoice_no       VARCHAR  发票号
-- invoice_date     DATE     开票日期
-- amount           DECIMAL  开票金额
-- received_amt     DECIMAL  已回款金额
```

### AI生成SQL
```sql
SELECT
    customer_id,
    customer_name,
    SUM(CASE WHEN DATEDIFF('2026-06-30', invoice_date) <= 90
        THEN amount - received_amt ELSE 0 END) AS aging_0_90,
    SUM(CASE WHEN DATEDIFF('2026-06-30', invoice_date) BETWEEN 91 AND 180
        THEN amount - received_amt ELSE 0 END) AS aging_91_180,
    SUM(CASE WHEN DATEDIFF('2026-06-30', invoice_date) BETWEEN 181 AND 365
        THEN amount - received_amt ELSE 0 END) AS aging_181_365,
    SUM(CASE WHEN DATEDIFF('2026-06-30', invoice_date) > 365
        THEN amount - received_amt ELSE 0 END) AS aging_over_365,
    SUM(amount - received_amt) AS total_outstanding
FROM ar_detail
WHERE amount > received_amt       -- 只统计未回款的
GROUP BY customer_id, customer_name
ORDER BY total_outstanding DESC;
```

### 数据库方言适配
```sql
-- MySQL: DATEDIFF(date1, date2)
-- SQL Server: DATEDIFF(DAY, invoice_date, '2026-06-30')
-- Oracle: ('2026-06-30' - invoice_date)
-- PostgreSQL: ('2026-06-30'::DATE - invoice_date)
```

### 验证要点
- [ ] 确认账龄计算基准日期
- [ ] 确认DATEDIFF函数在目标数据库的语法
- [ ] 已全额回款的记录应排除
- [ ] 与财务系统应收账款余额表交叉验证

---

## 场景三：关联方交易识别与汇总

### 审计场景
识别被审计单位与关联方之间的所有交易，汇总借贷方金额，发现借贷不平异常。

### 表结构
```sql
-- voucher_detail（凭证明细）
-- voucher_id       VARCHAR  凭证ID
-- company_code     VARCHAR  公司代码
-- counterparty     VARCHAR  对方单位
-- dr_amt           DECIMAL  借方金额
-- cr_amt           DECIMAL  贷方金额
-- posting_date     DATE     记账日期

-- related_party（关联方清单）
-- party_name       VARCHAR  关联方名称
-- relation_type    VARCHAR  关联关系类型
```

### AI生成SQL
```sql
SELECT
    v.company_code,
    v.counterparty,
    r.relation_type,
    COUNT(DISTINCT v.voucher_id) AS voucher_count,
    SUM(v.dr_amt) AS total_dr,
    SUM(v.cr_amt) AS total_cr,
    SUM(v.dr_amt) - SUM(v.cr_amt) AS net_amount
FROM voucher_detail v
INNER JOIN related_party r ON v.counterparty = r.party_name
WHERE v.posting_date BETWEEN '2026-01-01' AND '2026-06-30'
GROUP BY v.company_code, v.counterparty, r.relation_type
HAVING ABS(SUM(v.dr_amt) - SUM(v.cr_amt)) > 0  -- 借贷不平的异常
ORDER BY net_amount DESC;
```

### 扩展：识别未披露的疑似关联方
```sql
-- 摘要含"兄弟公司""同一集团""内部"等关键词但不在关联方清单中的交易
SELECT
    company_code, counterparty, summary,
    SUM(dr_amt) AS total_dr, SUM(cr_amt) AS total_cr
FROM voucher_detail
WHERE (summary LIKE '%兄弟%' OR summary LIKE '%集团内%' OR summary LIKE '%内部%')
  AND counterparty NOT IN (SELECT party_name FROM related_party)
  AND posting_date BETWEEN '2026-01-01' AND '2026-06-30'
GROUP BY company_code, counterparty, summary
ORDER BY total_dr + total_cr DESC;
```

### 验证要点
- [ ] 关联方清单是否完整（是否包含隐性关联方）
- [ ] counterparty名称匹配是否有空格/全半角问题
- [ ] 借贷不平的阈值是否需要调整（考虑尾差）
- [ ] 抽查3-5笔关联交易，核对原始凭证

---

## 场景四：审计抽样（分层抽样/MUS）

### 审计场景
按金额分层对凭证进行随机抽样，大额全覆盖、小额随机抽。

### 表结构
```sql
-- voucher_header（凭证主表）
-- voucher_id       VARCHAR  凭证ID
-- amount           DECIMAL  凭证金额
-- posting_date     DATE     记账日期
```

### AI生成SQL（Hive SQL / MySQL 8.0+窗口函数）
```sql
SELECT voucher_id, amount, posting_date, amount_stratum
FROM (
    SELECT
        voucher_id, amount, posting_date,
        CASE
            WHEN amount < 10000 THEN '小额(<1万)'
            WHEN amount < 100000 THEN '中额(1-10万)'
            WHEN amount < 1000000 THEN '大额(10-100万)'
            ELSE '超大额(>100万)'
        END AS amount_stratum,
        ROW_NUMBER() OVER (
            PARTITION BY CASE
                WHEN amount < 10000 THEN 1
                WHEN amount < 100000 THEN 2
                WHEN amount < 1000000 THEN 3
                ELSE 4
            END
            ORDER BY RAND()
        ) AS rn
    FROM voucher_header
    WHERE posting_date BETWEEN '2026-04-01' AND '2026-06-30'
) t
WHERE rn <= 5;   -- 每层随机抽取5笔
```

### 数据库方言适配
```sql
-- SQL Server: ORDER BY NEWID()
-- Oracle: ORDER BY DBMS_RANDOM.VALUE
-- MySQL 5.7（无窗口函数）：
SELECT * FROM voucher_header
WHERE posting_date BETWEEN '2026-04-01' AND '2026-06-30'
  AND amount < 10000
ORDER BY RAND() LIMIT 5;
-- 每层分别执行，修改amount条件
```

### 验证要点
- [ ] 确认RAND()函数在目标数据库的可用性
- [ ] 分层阈值根据被审计单位规模调整
- [ ] 超大额(>100万)建议100%检查而非抽样
- [ ] 补充：制单人=审核人的凭证应额外抽样

---

## 场景五：收入截止性测试

### 审计场景
识别资产负债表日前后可能存在的跨期收入确认。

### 表结构
```sql
-- revenue（收入确认表）
-- order_no         VARCHAR  订单号
-- revenue_date     DATE     收入确认日期
-- invoice_date     DATE     开票日期
-- amount           DECIMAL  金额
```

### AI生成SQL
```sql
SELECT
    order_no,
    revenue_date,
    invoice_date,
    amount,
    CASE
        WHEN revenue_date < invoice_date THEN '提前确认收入'
        WHEN revenue_date > invoice_date THEN '推迟确认收入'
    END AS cutoff_risk
FROM revenue
WHERE (DATE_FORMAT(revenue_date, '%Y-%m') = '2025-12'
       AND DATE_FORMAT(invoice_date, '%Y-%m') = '2026-01')
   OR (DATE_FORMAT(revenue_date, '%Y-%m') = '2026-01'
       AND DATE_FORMAT(invoice_date, '%Y-%m') = '2025-12')
ORDER BY ABS(DATEDIFF(revenue_date, invoice_date)) DESC;
```

### 数据库方言适配
```sql
-- MySQL: DATE_FORMAT(date, '%Y-%m')
-- SQL Server: FORMAT(date, 'yyyy-MM')
-- Oracle: TO_CHAR(date, 'YYYY-MM')
-- PostgreSQL: TO_CHAR(date, 'YYYY-MM')
```

### 扩展：跨期支出检测
```sql
-- 支出截止性：费用发票跨期入账
SELECT
    order_no, expense_date, invoice_date, amount,
    CASE
        WHEN expense_date < invoice_date THEN '提前确认费用'
        WHEN expense_date > invoice_date THEN '推迟确认费用'
    END AS cutoff_risk
FROM expense
WHERE (DATE_FORMAT(expense_date, '%Y-%m') = '2025-12'
       AND DATE_FORMAT(invoice_date, '%Y-%m') = '2026-01')
   OR (DATE_FORMAT(expense_date, '%Y-%m') = '2026-01'
       AND DATE_FORMAT(invoice_date, '%Y-%m') = '2025-12')
ORDER BY ABS(DATEDIFF(expense_date, invoice_date)) DESC;
```

### 验证要点
- [ ] 截止日前后至少各取一个月数据
- [ ] 大额跨期（>重要性水平）应逐笔查验合同和验收单
- [ ] 注意：部分行业（如工程）收入确认与发票天然有时滞
- [ ] 结合合同约定的收入确认条件综合判断

---

## 附录：数据库方言速查

| 函数 | MySQL | SQL Server | Oracle | PostgreSQL | Hive |
|------|-------|-----------|--------|------------|------|
| 日期差 | DATEDIFF(d1,d2) | DATEDIFF(DAY,d2,d1) | d1-d2 | d1::DATE-d2::DATE | DATEDIFF(d1,d2) |
| 日期格式 | DATE_FORMAT(d,'%Y-%m') | FORMAT(d,'yyyy-MM') | TO_CHAR(d,'YYYY-MM') | TO_CHAR(d,'YYYY-MM') | DATE_FORMAT(d,'yyyy-MM') |
| 随机排序 | RAND() | NEWID() | DBMS_RANDOM.VALUE | RANDOM() | RAND() |
| NULL处理 | IFNULL(x,0) | ISNULL(x,0) | NVL(x,0) | COALESCE(x,0) | COALESCE(x,0) |
| 字符串长度 | CHAR_LENGTH(s) | LEN(s) | LENGTH(s) | LENGTH(s) | LENGTH(s) |
| 当前日期 | CURDATE() | GETDATE() | SYSDATE | CURRENT_DATE | CURRENT_DATE() |
| 窗口函数 | 8.0+ ✅ | ✅ | ✅ | ✅ | ✅ |

---

> 📌 本文归档：knowledge/audit-sql-templates/五个场景SQL模板.md
> 📌 Prompt模板：knowledge/审计SQL提示词模板.md
