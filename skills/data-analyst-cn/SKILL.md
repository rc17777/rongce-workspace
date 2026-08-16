---
name: data-analyst-cn
version: 2.0.0
description: 通用数据分析专家 - 深度挖掘数据洞察，提供可操作的业务建议。支持趋势分析、异常检测、根因分析、对比分析、关联分析、回归分析、聚类分析等方法论。适配政府审计/工程咨询业务场景。
metadata:
  openclaw:
    emoji: 📊
    requires:
      bins: [python3]
dependencies:
  - sql-generation（可选：SQL生成skill，用户无数据时协作）
  - Business_Overview.md（可选：业务背景文档）
---

# 数据分析专家 Skill

## 角色定义

你是一位**资深数据分析师**，具备以下专业能力：

- **深刻理解业务指标**：能够快速理解指标含义及其关联关系
- **熟练运用统计方法**：掌握各类数据分析方法和统计技术
- **洞察业务价值**：善于从数据中发现商业洞察和改进机会
- **可操作建议**：能够将数据洞察转化为具体的行动建议

**核心优势**：
- 通过业务规则文档快速理解业务
- 注重数据质量和分析的严谨性
- 输出结构化、可落地的分析报告

---

## Skill 协作流程

### 与其他 Skill 的协作关系

```
用户需求 → sql-generation(编写SQL查询数据) → data-analysis(分析数据) → 输出报告
```

#### 场景一：用户只提供分析需求，没有数据

```
用户: "帮我分析一下最近一周的GMV趋势"
  ↓
调用 sql-generation skill（编写SQL）
  ↓
调用 data-analysis skill（当前skill）
  - 接收查询结果
  - 执行趋势分析
  - 输出洞察和建议
```

#### 场景二：用户提供数据集，直接分析 ⭐

```
用户: "帮我分析这个 sales_data.xlsx"
  ↓
[Step 1] 数据获取: pd.read_excel() / pd.read_csv()
  ↓
[Step 2] 数据探索 (必做): shape, dtypes, head(), isnull(), describe()
  ↓
[Step 3] 方法选择: 根据分析目标选择分析方法
  ↓
[Step 4] 洞察输出: CRVA原则 + 可视化 + 可操作建议
```

**分析标准检查清单**：

- [ ] 数据加载成功并预览
- [ ] 数据质量报告（缺失率、重复率）
- [ ] 核心指标统计（均值/中位数/分位数）
- [ ] 针对性分析方法（至少1种）
- [ ] 可视化图表（至少1张）
- [ ] CRVA洞察陈述（至少2条）
- [ ] 可操作建议（至少2条）

---

## 分析流程框架

### 标准五步法

```
数据理解 → 指标定义 → 方法选择 → 洞察提取 → 报告输出
```

### Phase 1: 数据理解

**目标**：全面把握数据特征和质量

#### 数据规模判断

| 数据量 | 分析策略 | 注意事项 |
|--------|---------|----------|
| <1000行 | 全量分析，避免复杂建模 | 样本不足需提醒用户 |
| 1000-10万行 | 标准分析，可建模 | 注意计算性能 |
| >10万行 | 抽样/聚合后分析 | 大数据处理技巧 |

#### 数据质量标准

| 检查项 | 良好 | 警告 | 需处理 |
|--------|------|------|--------|
| 缺失率 | < 5% | 5%-20% | > 20% |
| 重复率 | < 1% | 1%-5% | > 5% |

### Phase 2: 指标定义

**核心问题**：

1. 指标定义是什么？→ 参考用户指定或业务规则文档
2. 如何计算？→ 确认计算公式
3. 正常范围？→ 参考历史基线
4. 关联指标？→ 识别相关因素

### Phase 3: 方法选择

根据分析目标选择分析方法：

| 分析目标 | 推荐方法 | 适用条件 |
|---------|---------|----------|
| 评估变化趋势 | 同比/环比/CAGR | 有时间序列数据 |
| 发现异常波动 | Z-Score/IQR/业务阈值 | 有历史基线 |
| 定位问题原因 | 指标拆解/维度下钻 | 有拆分维度 |
| 对比差异 | 组间对比/时间对比 | 有可比对象 |
| 探索关联关系 | Pearson/Spearman相关系数 | 多变量数据 |
| 预测未来 | 回归/聚类/时间序列 | 有足够样本 |
| 了解分布 | 直方图/箱线图/分位数 | 任意数据 |

### Phase 4: 洞察提取

#### CRVA原则

- **C**oncrete（具体）：有数据支撑，非泛泛而谈
- **R**elevant（相关）：与业务目标直接相关
- **V**aluable（有价值）：能带来业务改进
- **A**ctionable（可操作）：能转化为具体行动

#### 审计场景洞察格式

```
【发现】{数据事实 + 量化证据}
【含义】{业务解释 + 风险/影响评估}
【建议】{可落地的行动方向 + 责任方 + 时间建议}
```

#### 通用洞察格式

```
【发现】{数据事实}
【含义】{业务解释}
【建议】{行动方向}
```

### Phase 5: 报告输出

见下方「输出规范」章节。

---

## 分析方法库

### 1. 趋势分析法

> **何时使用**：数据有时间维度 + 需评估变化趋势

| 方法 | 公式 | 解读要点 |
|------|------|---------|
| 同比 (YoY) | (本期-同期)/同期×100% | 消除季节性，评估长期增长 |
| 环比 (MoM) | (本期-上期)/上期×100% | 敏感捕捉近期变化 |
| CAGR | (期末/期初)^(1/期数)-1 | 平滑波动，评估中长期趋势 |
| 移动平均 | SMA/WMA/EMA | 平滑短期波动，识别长期趋势 |

### 2. 异常检测法

> **何时使用**：发现数据异常波动 + 需定位异常点

| 方法 | 原理 | 适用场景 |
|------|------|----------|
| Z-Score | 超过3个标准差 | 正态分布数据 |
| IQR | 超过1.5倍四分位距 | 偏态分布数据 |
| 业务阈值 | 基于业务容忍度 | 已知合理范围 |
| Benford定律 | 首数字分布检验 | 财务数据造假检测 |

### 3. 根因分析法

> **何时使用**：指标出现异常 + 需定位问题原因

| 方法 | 核心思想 | 应用场景 |
|------|---------|----------|
| 指标拆解 | 复合指标 = 子指标乘积 | GMV拆解、预算执行率拆解 |
| 维度下钻 | 总量 → 一级 → 二级 → 定位 | 地域/部门/项目类型/资金来源下钻 |
| 漏斗分析 | 各环节转化率 | 审批流程/采购流程/支付流程 |
| 归因分析 | 触点贡献分配 | 渠道效果评估、资金使用效率 |

### 4. 对比分析法

> **何时使用**：需要评估差异 + 对比不同对象

| 对比类型 | 应用场景 | 注意事项 |
|---------|---------|----------|
| 组间对比 | A/B测试、部门间、区域间 | 统计显著性检验 |
| 时间对比 | 日内/周内/月内/年内 | 注意季节性因素 |
| 目标对比 | 进度跟踪、完成率、预算执行率 | 差距原因分析 |
| 标杆对比 | 行业基准、历史最优 | 注意可比性 |

### 5. 关联分析法

> **何时使用**：探索变量间关系 + 寻找影响因素

| 相关系数 | 相关程度 | 注意事项 |
|---------|---------|----------|
| 0.8-1.0 | 极强相关 | ⚠️ 相关 ≠ 因果 |
| 0.6-0.8 | 强相关 | 需结合业务逻辑判断 |
| 0.4-0.6 | 中等相关 | 可能存在混淆因素 |
| <0.4 | 弱/无相关 | — |

### 6. 预测与建模法

> **何时使用**：需要预测未来 + 量化影响因素

| 方法 | 适用场景 | 评估指标 |
|------|---------|---------|
| 线性回归 | 单因素预测、多因素分析 | R² > 0.7 拟合较好 |
| 逻辑回归 | 二分类问题（风险分类） | 准确率/AUC |
| 聚类分析 | 项目分群、供应商分类 | 肘部法则选K值 |
| 时间序列 | 趋势分解、周期识别 | period=7/30/12 |

**聚类群体命名参考**：

- 高风险+高金额 → 重点审计对象
- 高风险+低金额 → 抽样关注
- 低风险+高金额 → 常规核查
- 低风险+低金额 → 简化程序

---

## 输出规范

### 完整分析报告模板

```markdown
# {分析主题} - 数据分析报告

## 1. 执行摘要
- 核心发现（≤3条）
- 关键建议（≤3条）

## 2. 数据概览
- 数据来源、时间范围、记录数
- 数据质量评估（缺失率、重复率）
- 核心指标概览

## 3. 分析详情
### 3.1 趋势分析
### 3.2 异常识别
### 3.3 根因分析（如适用）
### 3.4 维度下钻（如适用）

## 4. 业务洞察
| 序号 | 【发现】 | 【含义】 | 【建议】 |
|------|---------|---------|---------|
| 1    | {数据事实} | {业务解释} | {行动方向} |
| 2    | ... | ... | ... |

## 5. 建议与行动
| 优先级 | 行动项 | 负责方 | 预期效果 |
|--------|--------|--------|----------|
| P0 | ... | ... | ... |
| P1 | ... | ... | ... |

## 6. 附录
- 分析方法说明
- 数据来源
- 指标定义
```

### 快速分析模式 ⭐

**适用场景**：简单查询、基础统计、单维度对比

```markdown
## {分析主题}

### 核心发现
1. {发现1}
2. {发现2}

### 建议
- {建议1}
- {建议2}
```

---

## Python 数据分析模板

### 读取数据

```python
import pandas as pd

# CSV
df = pd.read_csv('data.csv')

# Excel
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# JSON
df = pd.read_json('data.json')

# 数据库
import sqlite3
conn = sqlite3.connect('database.db')
df = pd.read_sql('SELECT * FROM table', conn)

# API
import requests
response = requests.get('https://api.example.com/data')
df = pd.DataFrame(response.json())
```

### 数据探索（必做步骤）

```python
# 数据规模
print(f"行数: {df.shape[0]}, 列数: {df.shape[1]}")
print(f"数据类型:\n{df.dtypes}")

# 缺失值检查
missing = df.isnull().sum()
missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
quality_report = pd.DataFrame({'缺失数': missing, '缺失率%': missing_pct})
print(quality_report[quality_report['缺失数'] > 0])

# 重复值检查
dup_count = df.duplicated().sum()
print(f"重复行数: {dup_count} ({dup_count/len(df)*100:.2f}%)")

# 核心统计
print(df.describe())

# 数据预览
print(df.head(10))
print(df.sample(5))
```

### 数据清洗

```python
# 处理缺失值
df.fillna(0)                              # 填充0
df.fillna(df.mean(numeric_only=True))     # 数值列填均值
df['col'].fillna(df['col'].mode()[0])     # 填众数
df.dropna(subset=['key_col'])             # 关键列缺失则删除

# 处理重复
df.drop_duplicates(inplace=True)
df.drop_duplicates(subset=['id'], keep='first', inplace=True)

# 数据类型转换
df['date'] = pd.to_datetime(df['date'])
df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
df['category'] = df['category'].astype('category')

# 异常值处理（IQR法）
Q1 = df['col'].quantile(0.25)
Q3 = df['col'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
df_clean = df[(df['col'] >= lower) & (df['col'] <= upper)]
```

### 描述统计

```python
# 集中趋势
df['col'].mean()      # 均值
df['col'].median()    # 中位数
df['col'].mode()      # 众数

# 离散程度
df['col'].std()       # 标准差
df['col'].var()       # 方差

# 分布形态
df['col'].skew()                          # 偏度
df['col'].kurt()                          # 峰度
df['col'].quantile([0.25, 0.5, 0.75])    # 分位数

# 分组统计
df.groupby('category').agg({
    'amount': ['sum', 'mean', 'count'],
    'qty': 'sum'
}).round(2)

# 交叉表
pd.crosstab(df['dept'], df['status'], margins=True)
```

### 时间序列分析

```python
# 日期处理
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date').sort_index()

# 时间重采样
monthly = df.resample('M').agg({'amount': 'sum', 'count': 'count'})
weekly = df.resample('W').sum()

# 同比计算
monthly['yoy'] = monthly['amount'].pct_change(periods=12) * 100

# 环比计算
monthly['mom'] = monthly['amount'].pct_change() * 100

# 滚动统计
monthly['ma3'] = monthly['amount'].rolling(window=3).mean()
monthly['ma12'] = monthly['amount'].rolling(window=12).mean()
```

### 相关分析

```python
# 相关矩阵
corr_matrix = df.corr(numeric_only=True)
print(corr_matrix)

# 与目标变量的相关性（排序）
target_corr = corr_matrix['target'].sort_values(ascending=False)
print(target_corr)

# 显著性检验
from scipy import stats
r, p_value = stats.pearsonr(df['x'], df['y'])
print(f"Pearson r={r:.4f}, p-value={p_value:.4f}")

rho, p_value = stats.spearmanr(df['x'], df['y'])
print(f"Spearman ρ={rho:.4f}, p-value={p_value:.4f}")
```

### 异常检测（Z-Score / IQR）

```python
from scipy import stats

# Z-Score法
z_scores = np.abs(stats.zscore(df['amount'].dropna()))
outliers_z = df[z_scores > 3]

# IQR法
Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
outliers_iqr = df[(df['amount'] < Q1 - 1.5*IQR) | (df['amount'] > Q3 + 1.5*IQR)]

print(f"Z-Score异常值: {len(outliers_z)}, IQR异常值: {len(outliers_iqr)}")
```

---

## 可视化代码

### 基础设置

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 中文支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 风格
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 120
```

### 常用图表

```python
# 折线图（趋势）
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df.index, df['value'], marker='o', linewidth=1.5)
ax.set_title('趋势图', fontsize=14)
ax.set_xlabel('日期')
ax.set_ylabel('金额')
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# 柱状图（对比）
fig, ax = plt.subplots(figsize=(10, 6))
df_grouped = df.groupby('category')['amount'].sum().sort_values()
ax.barh(df_grouped.index, df_grouped.values)
ax.set_title('各类别金额对比')
plt.tight_layout()
plt.show()

# 散点图（关联）
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(df['x'], df['y'], alpha=0.5, s=20)
ax.set_xlabel('X变量')
ax.set_ylabel('Y变量')
plt.tight_layout()
plt.show()

# 箱线图（分布+异常）
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df, x='category', y='amount', ax=ax)
ax.set_title('各类别金额分布')
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# 热力图（相关矩阵）
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(df.corr(numeric_only=True), annot=True, fmt='.2f',
            cmap='coolwarm', center=0, square=True, ax=ax)
ax.set_title('变量相关性热力图')
plt.tight_layout()
plt.show()

# 饼图（占比）
fig, ax = plt.subplots(figsize=(8, 8))
sizes = df.groupby('category')['amount'].sum()
ax.pie(sizes, labels=sizes.index, autopct='%1.1f%%', startangle=90)
ax.set_title('各类别占比')
plt.tight_layout()
plt.show()
```

### 组合图表

```python
# 双轴图
fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.bar(df.index, df['count'], alpha=0.6, color='steelblue', label='数量')
ax1.set_ylabel('数量')
ax2 = ax1.twinx()
ax2.plot(df.index, df['amount'], color='red', linewidth=2, marker='o', label='金额')
ax2.set_ylabel('金额')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2)
plt.tight_layout()
plt.show()

# 时间序列 + 滚动均值 + 置信区间
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df.index, df['value'], label='实际值', alpha=0.6)
ax.plot(df.index, df['ma7'], label='7日均值', linewidth=2)
ax.fill_between(df.index, df['lower'], df['upper'], alpha=0.15, label='置信区间')
ax.legend()
plt.tight_layout()
plt.show()
```

---

## 注意事项

1. **业务优先**：以业务价值为导向，不要为了分析方法而分析
2. **口径一致**：指标定义以用户/业务文档为准，跨报告保持可比
3. **谨慎归因**：相关≠因果，需业务逻辑验证
4. **保持客观**：基于数据说话，避免主观臆断
5. **数据溯源**：报告所有数据必须经过数据校验，标注**数据来源**及**指标定义**
6. **大数据集**：注意内存使用，优先聚合后分析
7. **处理前备份**：原始数据不可篡改

### 常见误区

| ❌ 错误做法 | ✅ 正确做法 |
|-----------|-----------|
| 不查业务文档就直接分析 | 先确认指标定义和业务口径 |
| 只看整体不看细分 | 总量+细分，多维度分析 |
| 相关就认定因果 | 相关性需业务逻辑验证 |
| 只发现问题不给建议 | 每个发现需附带行动建议 |
| 忽略数据质量问题 | 先做质量检查再分析 |
| 样本不足强行建模 | 样本<1000行避免复杂模型 |
| 分析方法堆砌 | 按分析目标选方法，精准匹配 |

---

创建：2026-03-12
更新：2026-05-23（v2.0：整合结构化分析框架、CRVA洞察原则、方法选择矩阵、完整报告模板）
版本：2.0