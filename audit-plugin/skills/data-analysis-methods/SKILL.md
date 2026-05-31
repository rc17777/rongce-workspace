# 审计数据分析方法 (Data Analysis Methods)

## 元数据

- **类型**: interactive（交互式）
- **命令**: `/audit:data-analysis-methods`
- **前置条件**: CLAUDE.md（审计问题 + 数据源）
- **输入**: 待分析数据 + 审计问题（财务/业务/非结构化）
- **输出**: 分析方案 + 方法选择建议 + Python代码模板 + 分析底稿框架

---

## 目标

不是教审计人员学Python，是 **把"我要查什么"翻译成"用什么方法查、用什么工具查、查完怎么下结论"**。

核心逻辑: 审计问题 → 选择分析方法 → 选择工具 → 执行分析 → 判读结果。

---

## 一、审计数据分析五步法

> 无论用什么工具，这五步是固定流程。工具可以换，流程不会变。

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ ①提出问题 │ →  │ ②获取数据 │ →  │ ③清洗处理 │ →  │ ④分析建模 │ →  │ ⑤得出结论 │
│  (方向)   │    │  (地基)   │    │  (质量关) │    │  (核心)   │    │  (交付)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
 审计问题即分析目标  明确取什么/从哪取   60-80%时间      方法×工具        审计判断
```

### 每步核心要点

| 步骤 | 关键动作 | 常见错误 | 检查点 |
|------|---------|---------|--------|
| **①提出问题** | 用一句话写下审计假设 | 问得太笼统（"看看数据有没有问题"） | 能写出明确假设吗？ |
| **②获取数据** | 列数据需求清单，标来源和格式 | 不加选择地"全导出来" | 每项数据都有用途吗？ |
| **③清洗处理** | 验完整性→去重复→标异常→统格式 | 清洗时直接删除异常值 | 异常=线索，标记≠删除 |
| **④分析建模** | 选方法→写代码→跑结果 | 工具炫技，忘了审计目标 | 分析结果能回答第①步的问题吗？ |
| **⑤得出结论** | 数据异常→业务解释→审计判断 | 把统计相关当成因果 | CPA专业判断确认了吗？ |

---

## 二、七大核心分析方法

> 每种方法附：适用问题类型 + 审计场景 + Python代码模板 + 结果解读

### 1. 描述性统计分析

| 维度 | 内容 |
|------|------|
| **适用问题** | "数据整体长什么样？有没有异常集中或分散？" |
| **审计场景** | 进场了解数据分布；找出金额/频次异常的科目和区间 |
| **核心指标** | 均值、中位数、标准差、四分位数、集中度 |

```python
import pandas as pd
df = pd.read_excel('payments.xlsx')

# 按供应商汇总付款，看集中度
vendor_stats = df.groupby('vendor_name')['amount'].agg(['sum','count','mean','std'])
top10 = vendor_stats.nlargest(10, 'sum')   # 前10大供应商
concentration = top10['sum'].sum() / df['amount'].sum()  # 前10占比
print(f"前10大供应商付款占比: {concentration:.1%}")
```

### 2. 相关性分析

| 维度 | 内容 |
|------|------|
| **适用问题** | "两个变量之间有没有关系？关系强不强？" |
| **审计场景** | 投标报价与市场价的关联度；费用与收入增长的匹配度 |

```python
import scipy.stats as stats
# 投标报价 vs 市场价的相关性
r, p = stats.pearsonr(df['bid_price'], df['market_price'])
if abs(r) < 0.5:
    print(f"⚠️ 报价与市场价弱相关(r={r:.2f})，可能存在非市场因素")
```

### 3. 回归分析

| 维度 | 内容 |
|------|------|
| **适用问题** | "A的变化在多大程度上能解释B的变化？" |
| **审计场景** | 收入预测模型识别虚增；费用异常的定量判定 |

```python
from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# 残差异常=审计线索
residuals = abs(y_test - y_pred)
outliers = residuals[residuals > 2 * residuals.std()]
print(f"异常偏离记录: {len(outliers)}条")
```

### 4. 聚类分析

| 维度 | 内容 |
|------|------|
| **适用问题** | "这些数据可以自然分成哪几类？有没有不合群的点？" |
| **审计场景** | 供应商分群识别异常供应商；费用报销模式分类 |

```python
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=3).fit(df[['amount','frequency']])
df['cluster'] = kmeans.labels_

# 孤立的点=审计线索
small_clusters = df['cluster'].value_counts().nsmallest(1)
print(f"最小群组（孤立点）: {small_clusters.index[0]}，共{small_clusters.values[0]}条")
```

### 5. 异常检测

| 维度 | 内容 |
|------|------|
| **适用问题** | "哪些记录在统计意义上明显不符合正常模式？" |
| **审计场景** | 虚假交易识别；Benford定律验数；费用报销异常 |
| **核心方法** | 孤立森林、LOF、Benford法则、Z-score |

```python
from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.05).fit(df[['amount']])
df['anomaly'] = iso.predict(df[['amount']])
anomalies = df[df['anomaly'] == -1]
print(f"孤立森林检出异常: {len(anomalies)}条")

# Benford法则检验
def benford_test(series):
    first_digits = series.astype(str).str[0].astype(int)
    observed = first_digits.value_counts(normalize=True).sort_index()
    expected = pd.Series([np.log10(1+1/d) for d in range(1,10)], index=range(1,10))
    return observed, expected
```

### 6. 关联规则 / 网络分析

| 维度 | 内容 |
|------|------|
| **适用问题** | "哪些实体之间隐藏着不正常的关联关系？" |
| **审计场景** | 围标串标识别（多家投标→同一控制人→同一地址→同一联系方式）；关联方交易发现 |

```python
import networkx as nx
G = nx.Graph()
# 供应商-员工网络
for _, row in df.iterrows():
    G.add_edge(row['vendor'], row['employee'])

# 找紧密关联子图
from networkx.algorithms.community import greedy_modularity_communities
communities = list(greedy_modularity_communities(G))
print(f"发现{len(communities)}个关联群组")
```

### 7. 时间序列分析

| 维度 | 内容 |
|------|------|
| **适用问题** | "数据随时间怎么变？有没有不合理的突变或规律？" |
| **审计场景** | 年末突击花钱；费用时间分布异常规律；收入跨期调节 |

```python
# 按月汇总，找突变
monthly = df.set_index('date').resample('M')['amount'].sum()
monthly_pct_change = monthly.pct_change()
abnormal_months = monthly_pct_change[abs(monthly_pct_change) > 0.3]  # 月度波动>30%
print(f"异常波动月份: {len(abnormal_months)}个")
```

---

## 三、审计问题 → 分析方法 → 工具 选择矩阵

| 我要查什么 | 首选方法 | 次选方法 | 推荐工具 |
|-----------|---------|---------|---------|
| 数据整体情况摸底 | 描述性统计 | 对比分析 | Excel透视表 / Python pandas |
| 是否存在围标串标 | 关联规则+网络分析 | 聚类分析 | Python networkx |
| 费用是否异常 | 异常检测+Benford | 对比分析 | Python sklearn |
| 收入是否被操纵 | 时间序列+回归 | 对比分析 | Python statsmodels |
| 供应商是否关联 | 网络分析+关联规则 | 聚类分析 | Python networkx |
| 资金拨付是否合规 | 对比分析+描述性统计 | 时间序列 | SQL + Python |
| 工程造价是否合理 | 回归分析+对比分析 | 异常检测 | Python + Excel |
| 是否存在重复报销 | 关联规则（精确匹配） | 异常检测 | SQL GROUP BY + HAVING |
| 进度与拨款是否匹配 | 时间序列+对比分析 | 相关性分析 | Python pandas |
| 数据有没有造假痕迹 | Benford+异常检测 | 时间序列 | Python scipy/sklearn |

---

## 四、工具选型速查

| 场景 | 推荐工具 | 典型耗时 | 学习门槛 |
|------|---------|---------|---------|
| 数据<10万行，一次性分析 | Excel + Power Query | 分钟级 | ⭐ |
| 数据在数据库里 | SQL | 分钟级 | ⭐⭐ |
| 数据>20万行，需要复用 | Python pandas | 小时级 | ⭐⭐⭐ |
| 要出可视化看板 | Power BI / Tableau | 小时级 | ⭐⭐ |
| 商业审计专用功能 | IDEA / ACL | 分钟级 | ⭐⭐ |

---

## 五、数据清洗审计特别要点

| 问题类型 | 常规处理 | 审计处理 | 原因 |
|---------|---------|---------|------|
| 缺失值 | 填充均值或删除 | 标记 + 了解原因 + 评估影响 | 缺失本身可能是问题信号 |
| 重复值 | 直接去重 | 先理解业务逻辑再判断 | 可能不是错误而是业务有重复 |
| 异常值 | 删除或截断 | **重点标记，深入核查** | 异常=审计线索 |
| 格式不统一 | 标准化 | 标准化 + 记录原始格式 | 需要追溯原始记录 |

数据完整性验证六项：
1. 记录总数是否与来源系统一致？
2. 金额合计是否与报表勾稽？
3. 时间范围是否覆盖审计期间？
4. 唯一标识是否无重复无空值？
5. 关键字段取值是否在合理范围？
6. 跨系统数据能否关联匹配？

---

## 六、思维融合：审计+数据双螺旋

```
审计思维（方向）             数据思维（视野）
    ↓                           ↓
风险→假设→证据→结论      探索→发现→挖掘→解读
    ↘         ↙
    融合思维（四轮法）
    ↓
①自上而下：经验定方向，设假设
②自下而上：数据开放探索，验证+发现新线索
③收敛聚焦：将数据发现对齐审计目标，筛出真问题
④专业判断：结合业务背景+审计准则下结论
```

---

## 参数

```
/audit:data-analysis-methods                         → 完整方法指南
/audit:data-analysis-methods --task <审计任务描述>      → 给具体任务推荐方法+工具
/audit:data-analysis-methods --code <方法名>           → 输出该方法的Python代码模板
/audit:data-analysis-methods --tool <工具名>           → 该工具在审计中的最佳实践
```

---

## 信任层

- ⚠️ 所有分析方法输出的是**疑点**，不是结论
- 📌 数据分析异常必须经过现场核实和业务验证
- 🔍 "垃圾进垃圾出"→必须先验证数据质量
- 🚪 重大异常发现需CPA确认后方可写入报告
