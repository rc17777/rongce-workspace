# 审计机器学习案例集

基于「数审派」公众号《大数据审计实战：3个机器学习案例详解》文章整理。

## 案例1：聚类分析识别异常交易模式

**算法**：KMeans聚类

**场景**：将供应商/交易按特征分组，识别孤立模式

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

# 特征工程
features = df[['交易金额', '交易频率', '交易时间间隔', '供应商注册时长']]
scaler = StandardScaler()
X = scaler.fit_transform(features)

# 聚类
kmeans = KMeans(n_clusters=5, random_state=42)
df['cluster'] = kmeans.fit_predict(X)

# 识别小簇（异常供应商）
cluster_counts = df['cluster'].value_counts()
small_clusters = cluster_counts[cluster_counts < len(df) * 0.05].index
anomalies = df[df['cluster'].isin(small_clusters)]
```

## 案例2：Isolation Forest异常检测

**适用场景**：高维数据、无明显分布假设的异常检测

```python
from sklearn.ensemble import IsolationForest

model = IsolationForest(contamination=0.05, random_state=42)
df['anomaly'] = model.fit_predict(X)

# -1为异常，1为正常
anomalies = df[df['anomaly'] == -1]
```

## 案例3：XGBoost风险预测模型

**适用场景**：基于历史审计结果，预测新交易的风险等级

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split

# 准备特征和标签
X = df[['金额', '供应商交易次数', '账龄', '价格偏离度']]
y = df['is_risk']  # 历史标注：1高风险 0低风险

# 训练
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1)
model.fit(X_train, y_train)

# 特征重要性排序
importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
```

**审计注意**：ML模型需要标注数据训练，初始阶段可用规则引擎+人工标注积累数据，待数据量足够后再切换ML。
