# 审计异常检测规则集

基于「数审派」公众号《传统审计效率翻10倍》等文章整理。

## 1. Z-score方法

**适用场景**：金额类数据的极端值检测（大额异常支付、异常高额报销）

```python
def zscore_detect(df, column='amount', threshold=3):
    mean = df[column].mean()
    std = df[column].std()
    df['z_score'] = (df[column] - mean) / std
    return df[df['z_score'].abs() > threshold]
```

**规则说明**：
- threshold=2：检出约95%正常范围外的数据（宽松）
- threshold=3：检出约99.7%正常范围外的数据（严格，推荐审计用）
- **审计注意**：分布高度偏斜时（如采购金额长尾），Z-score可能失效，改用IQR

## 2. IQR四分位距法

**适用场景**：金额分布高度偏斜的场景（如供应商付款金额差异极大）

```python
Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
anomalies = df[(df['amount'] < lower) | (df['amount'] > upper)]
```

**审计适用场景**：
- 供应商付款异常：大额远超其他供应商的付款
- 员工报销异常：远超正常费用范围的报销单
- 工程款支付异常：远超同类工程平均单价

## 3. Benford法则（本福特定律）

**适用场景**：检测人为篡改的数据（发票金额、报销金额、合同金额）

**原理**：自然生成的数字中，首位数字为1的概率约30.1%，为9的概率仅4.6%。人为造假的数据往往会使数字分布均匀化。

```python
# Benford法则检测
def benford_test(amounts):
    from collections import Counter
    first_digits = [int(str(abs(a))[0]) for a in amounts if a > 0]
    counts = Counter(first_digits)
    total = len(first_digits)
    
    # 期望分布
    expected = {d: total * np.log10(1 + 1/d) for d in range(1, 10)}
    # 实际分布
    actual = {d: counts[d] for d in range(1, 10)}
    
    return actual, expected
```

**审计注意**：Benford法则适用于大样本数据（建议>500条），小额审计项目效果有限。

## 4. "踩线"检测

**专门针对审计场景**：检测金额恰好卡在审批阈值以下的异常费用。

**规则**：当费用金额在审批阈值95%-100%之间时，标记为"踩线"，需重点核查。

**常见阈值**：5000元（普通审批）、10000元（部门审批）、50000元（分管领导审批）

## 风险等级标注规则

| 等级 | 标识 | 定义 | 处置 |
|------|------|------|------|
| 高风险 | 🔴 | Z-score>4或IQR上界3倍以上或直接违反法规 | 立即核查 |
| 中风险 | 🟡 | Z-score3-4或IQR上界1.5-3倍或Benford异常 | 安排核查 |
| 低风险 | 🟢 | 轻微偏离或单次异常 | 参考关注 |
