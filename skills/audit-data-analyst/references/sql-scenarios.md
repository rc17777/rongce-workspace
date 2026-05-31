# SQL审计查询5大高频场景

基于「数审派」公众号《大数据审计SQL实战技巧：5类高频场景+代码案例》文章整理。

## 场景1：数据关联与交叉比对

**审计目标**：将分散在多个表中的数据进行关联，发现采购合同金额与市场价格偏离、供应商信息不一致等问题。

```sql
-- 案例：采购合同价格与市场参考价对比
SELECT 
    c.contract_id,
    c.supplier_name,
    c.contract_amount,
    c.unit_price,
    m.market_price,
    (c.unit_price - m.market_price) / m.market_price * 100 AS price_deviation_pct
FROM contracts c
LEFT JOIN market_reference m ON c.material_code = m.material_code
WHERE ABS(c.unit_price - m.market_price) / m.market_price > 0.2  -- 偏离20%以上
ORDER BY price_deviation_pct DESC;
```

## 场景2：异常值识别

**审计目标**：识别金额异常、频率异常的交易行为。

```sql
-- 案例2.1：同一供应商单日多笔采购（围标串标特征）
SELECT 
    supplier_id,
    supplier_name,
    DATE(purchase_date) AS purchase_day,
    COUNT(*) AS batch_count,
    SUM(amount) AS daily_total
FROM purchases
GROUP BY supplier_id, supplier_name, DATE(purchase_date)
HAVING COUNT(*) >= 3  -- 单日3笔以上
ORDER BY daily_total DESC;

-- 案例2.2：费用金额恰好卡在审批阈值以下（"踩线"检测）
SELECT 
    expense_id,
    employee_name,
    expense_date,
    amount,
    approval_threshold
FROM expenses e
CROSS JOIN approval_rules a
WHERE e.amount BETWEEN a.threshold * 0.95 AND a.threshold
  AND e.amount < a.threshold  -- 刚好低于审批阈值
ORDER BY e.amount DESC;
```

## 场景3：时间序列分析

**审计目标**：发现资金支出的时间集中度异常、季度末突击支付等问题。

```sql
-- 案例3.1：月度支出趋势与季度末集中度
SELECT 
    YEAR(payment_date) AS year,
    QUARTER(payment_date) AS quarter,
    MONTH(payment_date) AS month,
    COUNT(*) AS payment_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount
FROM payments
GROUP BY YEAR(payment_date), QUARTER(payment_date), MONTH(payment_date)
ORDER BY year, quarter, month;
```

## 场景4：重复数据检测

**审计目标**：发现同一发票多次报销、同一合同重复付款等问题。

```sql
-- 案例：同一发票号多次报销检测
SELECT 
    invoice_no,
    COUNT(*) AS claim_count,
    SUM(claim_amount) AS total_claimed,
    STRING_AGG(employee_name, ',') AS claimants
FROM expense_claims
GROUP BY invoice_no
HAVING COUNT(*) > 1
ORDER BY claim_count DESC;
```

## 场景5：Top-N与排名分析

**审计目标**：识别大额交易、异常排行。

```sql
-- 案例：各科室费用Top 10员工
SELECT 
    department,
    employee_name,
    total_expense,
    ranking
FROM (
    SELECT 
        department,
        employee_name,
        SUM(expense_amount) AS total_expense,
        ROW_NUMBER() OVER (PARTITION BY department ORDER BY SUM(expense_amount) DESC) AS ranking
    FROM expense_claims
    WHERE claim_date BETWEEN '2025-01-01' AND '2025-12-31'
    GROUP BY department, employee_name
) ranked
WHERE ranking <= 10
ORDER BY department, ranking;
```
