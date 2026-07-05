# Python+Pandas 审计分析 × 融策12业务线 场景应用矩阵

> 基于「数审派」《玩转审计数据分析（六）：Python审计分析实战入门》
> 结合融策现有技能库、知识库，按12条业务线逐一映射
> 生成时间：2026-06-30

---

## 总览：pandas 6大核心操作 → 12业务线适配矩阵

| pandas操作 | 经责 | 收支 | 预算 | 专项 | 往来款 | 招投标 | 国企 | 成本 | 能源 | 工程 | 绩效 | 补贴 |
|:---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 读取 read_excel | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 筛选 filter | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 排序 sort_values | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ |
| 分组 groupby | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 合并 merge | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | ✅ | ✅ | ✅ |
| 透视 pivot_table | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 逐业务线场景落地

### 1. 经济责任审计（经责）

**对应技能**: `audit-jingze`（四道关） + `perf-audit-checklist`

**pandas 实战场景**:

#### 场景 A：任期内三公经费趋势分析
```python
# 加载三年三公经费明细
df = pd.read_excel('data/三公经费_2022_2024.xlsx')
df['日期'] = pd.to_datetime(df['日期'])

# 按年度+费用类型汇总
annual = df.groupby([df['日期'].dt.year, '费用类型']).agg(
    笔数=('金额', 'count'),
    总额=('金额', 'sum'),
    平均=('金额', 'mean')
).reset_index()

# 透视：年度×费用类型
pivot = pd.pivot_table(df, values='金额', index='部门',
                       columns=df['日期'].dt.year, aggfunc='sum', margins=True)

# 异常标记：同比增幅>50%
pivot['增幅'] = (pivot[2024] - pivot[2023]) / pivot[2023] * 100
anomaly_depts = pivot[pivot['增幅'] > 50]
```

#### 场景 B：立项决策合规性交叉比对（配合 audit-jingze 四道关第一关）
```python
# 立项审批表 vs 实际执行
df_approval = pd.read_excel('data/立项审批表.xlsx')
df_actual = pd.read_excel('data/项目执行明细.xlsx')

# LEFT JOIN 找"审批有但未执行""无审批但已执行"
merged = pd.merge(df_approval, df_actual, on='项目编号', how='outer', indicator=True)
no_approval = merged[merged['_merge'] == 'right_only']  # 无审批执行
no_exec = merged[merged['_merge'] == 'left_only']        # 审批未执行
```

**可用技能增强**: `audit-meeting-review` 望闻问切分析会议记录 → pandas可批量提取会议纪要关键词

---

### 2. 收支审计

**对应技能**: `financial-fraud-detection`（Benford定律）

**pandas 实战场景**:

#### 场景 A：收支月度趋势异常检测
```python
df = pd.read_excel('data/收支明细_2024.xlsx')
df['日期'] = pd.to_datetime(df['日期'])

# 按月汇总
monthly = df.set_index('日期').resample('M').agg(
    收入=('收入金额', 'sum'),
    支出=('支出金额', 'sum')
)

# 环比波动率
monthly['支出环比'] = monthly['支出'].pct_change() * 100
# 标记波动率>30%的月份
anomaly_months = monthly[abs(monthly['支出环比']) > 30]
```

#### 场景 B：收款方与付款方名称模糊匹配（发现"自己收自己"）
```python
from difflib import get_close_matches

df_payee['疑似关联'] = df_payee['收款方名称'].apply(
    lambda x: get_close_matches(str(x), df_payer['付款方名称'].tolist(), n=1, cutoff=0.7)
)
```

---

### 3. 预算执行审计

**对应技能**: `budget-audit`

**pandas 实战场景**:

#### 场景 A：预算执行偏差全景分析
```python
df_budget = pd.read_excel('data/预算批复.xlsx')
df_actual = pd.read_excel('data/预算执行.xlsx')

# 预算 vs 执行对比
merged = pd.merge(df_budget, df_actual, on=['部门', '预算科目'], how='outer')
merged['执行率'] = merged['执行金额'] / merged['批复金额'] * 100
merged['偏差额'] = merged['执行金额'] - merged['批复金额']

# 分级标记
def rate_level(rate):
    if rate < 50: return '🔴 严重偏低'
    elif rate < 80: return '🟡 偏低'
    elif rate > 120: return '🔴 超预算'
    elif rate > 100: return '🟡 接近上限'
    return '✅ 正常'

merged['风险等级'] = merged['执行率'].apply(rate_level)
```

#### 场景 B：年底突击花钱检测
```python
df['月份'] = df['日期'].dt.month
monthly = df.groupby('月份')['金额'].sum()
# Q4占比
q4_ratio = monthly[10:].sum() / monthly.sum() * 100
print(f"第四季度支出占比: {q4_ratio:.1f}% (正常应<30%)")
```

---

### 4. 专项资金审计

**对应技能**: `special-fund-audit` + `penetrating-audit`

**pandas 实战场景**:

#### 场景 A：资金拨付→使用→结余全链条追踪
```python
df_allocate = pd.read_excel('data/资金拨付.xlsx')
df_spend = pd.read_excel('data/资金使用.xlsx')

# 按项目编号合并
fund_flow = pd.merge(df_allocate, df_spend, on='项目编号', how='left')
fund_flow['结余率'] = (fund_flow['拨付金额'] - fund_flow['使用金额']) / fund_flow['拨付金额'] * 100

# 结余率>20%且拨付金额>100万的项目
risk_projects = fund_flow[(fund_flow['结余率'] > 20) & (fund_flow['拨付金额'] > 1000000)]
```

#### 场景 B：专项资金挪用嫌疑（支出类型与资金用途不匹配）
```python
# 资金用途关键词 vs 实际支出用途
df['用途匹配'] = df.apply(lambda row: 
    row['规定用途'] in str(row['实际支出摘要']), axis=1)
mismatch = df[~df['用途匹配']]
```

---

### 5. 往来款清理

**对应技能**: `data-analyst-cn`

**pandas 实战场景**:

#### 场景 A：账龄分析自动化
```python
df = pd.read_excel('data/往来款明细.xlsx')
df['记账日期'] = pd.to_datetime(df['记账日期'])

# 计算账龄
ref_date = pd.Timestamp('2025-12-31')
df['账龄天数'] = (ref_date - df['记账日期']).dt.days

# 账龄分段
bins = [0, 90, 180, 365, 730, float('inf')]
labels = ['3个月内', '3-6月', '6月-1年', '1-2年', '2年以上']
df['账龄分段'] = pd.cut(df['账龄天数'], bins=bins, labels=labels)

# 按单位汇总账龄分布
aging_summary = df.groupby(['单位名称', '账龄分段'])['余额'].sum().unstack(fill_value=0)
```

#### 场景 B：同名/同账号多笔不同性质的异常
```python
same_acct = df.groupby('银行账号').agg(
    笔数=('金额', 'count'),
    涉及科目数=('会计科目', 'nunique'),
    总额=('金额', 'sum')
).reset_index()
# 同一账号涉及>3个科目的标记异常
anomaly = same_acct[same_acct['涉及科目数'] > 3]
```

---

### 6. 招投标审计

**对应技能**: `procurement-audit-models`（围标串标11层检测）

**pandas 实战场景**:

#### 场景 A：L1报价规律分析（报价梯度/下浮率聚类）
```python
df = pd.read_excel('data/开标一览表.xlsx')

# 各投标人对各标段的报价
df['下浮率'] = (1 - df['投标报价'] / df['控制价']) * 100

# 按标段groupby，看各投标人的下浮率是否呈现"规律性"
pivot = pd.pivot_table(df, values='下浮率', index='标段编号', 
                       columns='投标人', aggfunc='first')

# 同一标段内下浮率极差
pivot['极差'] = pivot.max(axis=1) - pivot.min(axis=1)
# 极差<1%（报价高度趋同）的标段→围标嫌疑
collusion_suspect = pivot[pivot['极差'] < 1]
```

#### 场景 B：L3文本雷同预处理（配合 TF-IDF）
```python
# 提取所有投标文件的核心段落
# pandas 作为数据组织层，把提取结果结构化为可比对矩阵
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

docs = pd.read_csv('data/bid_texts.csv')  # 投标人, 段落文本
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(docs['段落文本'])

# 余弦相似度矩阵
sim_matrix = cosine_similarity(tfidf_matrix)
sim_df = pd.DataFrame(sim_matrix, index=docs['投标人'], columns=docs['投标人'])
# 相似度>0.85的投标人对→涉嫌串标
```

---

### 7. 国企审计

**对应技能**: `financial-fraud-detection` + `audit-knowledge-graph`

**pandas 实战场景**:

#### 场景 A：关联交易全景识别
```python
df_trans = pd.read_excel('data/交易明细.xlsx')
df_related = pd.read_excel('data/关联方清单.xlsx')

# 标记每笔交易是否为关联交易
df_trans['is_related'] = df_trans['交易对手'].isin(df_related['关联方名称'])

# 关联交易汇总
related_summary = df_trans[df_trans['is_related']].groupby('交易对手').agg(
    交易笔数=('金额', 'count'),
    交易总额=('金额', 'sum'),
    交易类型=('交易类型', lambda x: ','.join(x.unique()))
).reset_index().sort_values('交易总额', ascending=False)
```

#### 场景 B：Benford定律+国企费用双重检测
```python
# 费用报销金额首位数分布→Benford检验
def first_digit(x):
    return int(str(abs(x)).strip('0.')[0]) if x > 0 else 0

df['首位数'] = df['报销金额'].apply(first_digit)
observed = df['首位数'].value_counts(normalize=True).sort_index()

# Benford理论分布
import numpy as np
benford = {d: np.log10(1 + 1/d) for d in range(1, 10)}

# 对比observed vs benford → 偏差>20%标记异常
for d in range(1, 10):
    actual = observed.get(d, 0)
    expected = benford[d]
    deviation = abs(actual - expected) / expected * 100
    if deviation > 20:
        print(f"  首位数{d}: 实际{actual:.1%} vs 理论{expected:.1%} | 偏差{deviation:.1f}% ⚠️")
```

---

### 8. 成本效益审计

**对应技能**: `forecast-simulation`

**pandas 实战场景**:

#### 场景 A：单位成本对比分析（同类项目横向比较）
```python
df_cost = pd.read_excel('data/项目成本明细.xlsx')

# 按项目类型分组计算单位成本
unit_cost = df_cost.groupby(['项目类型', '项目编号']).agg(
    总成本=('成本金额', 'sum'),
    产出量=('产出数量', 'max')
).reset_index()
unit_cost['单位成本'] = unit_cost['总成本'] / unit_cost['产出量']

# 同类项目单位成本统计
cost_stats = unit_cost.groupby('项目类型')['单位成本'].agg(['mean', 'std', 'min', 'max'])
unit_cost['Z分数'] = (unit_cost['单位成本'] - unit_cost['项目类型'].map(cost_stats['mean'])) / unit_cost['项目类型'].map(cost_stats['std'])
# Z>2 → 单位成本显著偏高
outliers = unit_cost[abs(unit_cost['Z分数']) > 2]
```

#### 场景 B：投入产出时间序列
```python
df['月份'] = df['日期'].dt.to_period('M')
monthly = df.groupby('月份').agg(投入=('成本金额', 'sum'), 产出=('效益金额', 'sum'))
monthly['投入产出比'] = monthly['产出'] / monthly['投入']
```

---

### 9. 能源审计

**对应技能**: `energy-audit`

**pandas 实战场景**:

#### 场景 A：能耗季节性模式识别
```python
df = pd.read_excel('data/能耗数据_2024.xlsx')
df['日期'] = pd.to_datetime(df['日期'])
df['月份'] = df['日期'].dt.month

# 逐月能耗汇总+同比
monthly = df.groupby('月份')['用电量(kWh)'].agg(['sum', 'mean', 'std'])
monthly['上年同期'] = monthly['sum'].shift(12)  # 如果数据跨年
monthly['同比增幅'] = (monthly['sum'] - monthly['上年同期']) / monthly['上年同期'] * 100
```

#### 场景 B：异常能耗点定位（IQR法）
```python
Q1 = df['日用电量'].quantile(0.25)
Q3 = df['日用电量'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
anomaly_days = df[(df['日用电量'] < lower) | (df['日用电量'] > upper)]
```

---

### 10. 工程竣工决算财务审计

**对应技能**: `engineering-audit` + `bim-engineering-audit`

**pandas 实战场景**:

#### 场景 A：概算→预算→合同→结算四级比对
```python
df_estimate = pd.read_excel('data/概算.xlsx')    # 概算
df_budget = pd.read_excel('data/预算.xlsx')       # 预算
df_contract = pd.read_excel('data/合同.xlsx')     # 合同
df_settlement = pd.read_excel('data/结算.xlsx')   # 结算

# 按费用科目合并四层数据
chain = (df_estimate[['科目编码','概算金额']]
    .merge(df_budget[['科目编码','预算金额']], on='科目编码', how='left')
    .merge(df_contract[['科目编码','合同金额']], on='科目编码', how='left')
    .merge(df_settlement[['科目编码','结算金额']], on='科目编码', how='left')
)

# 超概检测
chain['超概额'] = chain['结算金额'] - chain['概算金额']
chain['超概率'] = chain['超概额'] / chain['概算金额'] * 100
over_budget = chain[chain['超概率'] > 10].sort_values('超概率', ascending=False)
```

---

### 11. 预算绩效管理

**对应技能**: `perf-audit-checklist`

**pandas 实战场景**:

#### 场景 A：绩效目标完成度自评 vs 审计复核
```python
df_self = pd.read_excel('data/自评表.xlsx')
df_audit = pd.read_excel('data/审计复核.xlsx')

# 对比自评与复核
compare = pd.merge(df_self, df_audit, on='指标编码', suffixes=('_自评', '_复核'))
compare['偏差'] = compare['得分_自评'] - compare['得分_复核']
compare['偏差率'] = abs(compare['偏差']) / compare['满分'] * 100

# 偏差>20%的指标
large_diff = compare[compare['偏差率'] > 20]
```

#### 场景 B：绩效指标年度趋势
```python
df['年度'] = df['日期'].dt.year
trend = pd.pivot_table(df, values='指标值', index='指标名称',
                       columns='年度', aggfunc='mean')
trend['变化趋势'] = trend.apply(lambda row: '↑' if row[2024] > row[2023] else '↓', axis=1)
```

---

### 12. 政府补贴审计

**对应技能**: `subsidy-audit`

**pandas 实战场景**:

#### 场景 A：补贴申报资质交叉验证
```python
df_apply = pd.read_excel('data/补贴申报.xlsx')     # 申报表
df_tax = pd.read_excel('data/纳税记录.xlsx')        # 税务数据
df_credit = pd.read_excel('data/信用记录.xlsx')     # 信用数据

# 申报企业 vs 纳税记录 → 找"无纳税但申报补贴"的
merged = pd.merge(df_apply, df_tax, on='统一信用代码', how='left', indicator=True)
no_tax = merged[merged['_merge'] == 'left_only']

# 黑名单/失信企业申报
blacklist_apply = pd.merge(df_apply, df_credit[df_credit['是否失信']=='是'],
                           on='统一信用代码', how='inner')
```

#### 场景 B：同一企业多部门重复申报
```python
dup = df_apply.groupby('统一信用代码').agg(
    申报次数=('项目编号', 'count'),
    申报总额=('申请金额', 'sum'),
    涉及部门=('主管部门', lambda x: ','.join(x.unique()))
).reset_index()
multi_apply = dup[dup['申报次数'] > 1].sort_values('申报次数', ascending=False)
```

---

## 技能联动矩阵：pandas × 融策现有技能

| 现有技能 | pandas可增强的环节 | 增强效果 |
|---------|------------------|---------|
| `audit-jingze` | 四道关数据交叉比对 | groupby+merge替代手工VLOOKUP |
| `financial-fraud-detection` | Benford检验、异常交易 | pandas向量化处理15万行数据 |
| `procurement-audit-models` | L1报价规律、L3文本矩阵 | pivot_table+crosstab替代Excel透视 |
| `perf-audit-checklist` | 绩效指标汇总对比 | groupby.agg批量计算指标 |
| `apriori-audit` | 事务数据预处理 | pandas生成频繁项集输入格式 |
| `audit-knowledge-graph` | 节点关系数据整理 | merge构建边表、关系矩阵 |
| `audit-text-mining` | 关键词批量提取 | .str.contains()向量化搜索 |
| `data-analyst-cn` | 全流程数据分析 | 完整pandas工具链 |
| `penetrating-audit` | 资金链路追踪 | merge链式合并追踪全流程 |
| `spatial-audit-analysis` | 地址数据清洗 | 地址标准化、坐标预处理 |

---

## 落地建议

### 短期（立即可用）
1. **费用审计模板化**: 将"四、完整实战：供应商付款审计分析"代码模板,替换融策项目数据结构后直接套用
2. **pandas速查表打印**: 把文章第五节速查表打印成A4，放每个审计员桌上
3. **Notebook模板**: 为每条业务线建一个 `analysis_template.ipynb`，预置read_excel + head + describe + isnull 骨架

### 中期（1-3个月）
4. **12条业务线 × pandas场景代码库**: 把本文12个场景代码封成 `rongce_audit.py` 工具模块
5. **Jupyter培训**: 安排一次内部培训，按本矩阵带团队走一遍实操
6. **与智析RAG结合**: 将pandas分析结果作为智析知识库的查询上下文

### 长期
7. **launch.py 集成**: 在 `audit-blackboard/launch.py` 的 data_scout Agent 中内嵌 pandas 预处理逻辑
8. **自动化看板**: pandas+matplotlib → 定期自动生成各项目数据分析看板

---

*本文档将存入 RONGCE_AI_HUB，作为技能-场景-技术三层联动的参考索引。*
