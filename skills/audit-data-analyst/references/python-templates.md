# Python审计分析完整代码模板

基于「数审派」公众号《传统审计还在靠抽样？大数据时代效率翻10倍》文章整理。

## 审计数据分析4步法

### 第1步：数据获取

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 从Excel读取
df = pd.read_excel('审计数据_2025.xlsx', sheet_name='明细数据')

# 从数据库读取（需要SQLAlchemy）
# from sqlalchemy import create_engine
# engine = create_engine('mssql+pymssql://user:pass@server:port/db')
# df = pd.read_sql('SELECT * FROM v_audit_data', engine)

print(f'数据维度: {df.shape}')
print(f'字段列表: {df.columns.tolist()}')
print(df.head())
```

### 第2步：数据清洗

```python
# 去重
df = df.drop_duplicates(subset=['凭证号', '日期', '金额', '摘要'], keep='first')

# 类型转换
df['日期'] = pd.to_datetime(df['日期'])
df['金额'] = pd.to_numeric(df['金额'], errors='coerce')

# 缺失值处理
print(f'缺失值统计:\n{df.isnull().sum()}')

# 异常值初步过滤
df = df[df['金额'] > 0]  # 排除负数或零
```

### 第3步：全量数据分析

```python
# 描述性统计
print(df['金额'].describe())

# 按维度分组统计
summary = df.groupby('供应商名称').agg({
    '金额': ['count', 'sum', 'mean', 'max'],
    '凭证号': 'nunique'
}).round(2)
print(summary.sort_values(('金额', 'sum'), ascending=False).head(20))

# 月度趋势
df['月份'] = df['日期'].dt.to_period('M')
monthly = df.groupby('月份')['金额'].agg(['sum', 'count', 'mean'])
monthly.plot(kind='bar', figsize=(12, 6), title='月度审计数据趋势')
plt.tight_layout()
plt.savefig('月度趋势图.png', dpi=150)
```

### 第4步：异常检测

```python
# Z-score异常检测
def detect_anomalies_zscore(df_group, column='金额', threshold=3):
    mean = df_group[column].mean()
    std = df_group[column].std()
    df_group['z_score'] = (df_group[column] - mean) / std
    df_group['是否异常'] = df_group['z_score'].abs() > threshold
    return df_group

df = detect_anomalies_zscore(df)
anomalies = df[df['是否异常']].sort_values('z_score', ascending=False)
print(f'发现 {len(anomalies)} 条异常记录')
print(anomalies[['日期', '供应商', '金额', 'z_score']])

# IQR四分位法
Q1 = df['金额'].quantile(0.25)
Q3 = df['金额'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
iqr_anomalies = df[(df['金额'] < lower) | (df['金额'] > upper)]
print(f'IQR异常: {len(iqr_anomalies)} 条')
```
