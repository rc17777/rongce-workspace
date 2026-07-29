---
title: "报价规律异常检测"
type: "detection_method"
layer: "L1"
confidence_level: "铁证"
alias: "L1-报价规律"
business_line: "通用"
keywords: [报价, 偏离度, DBSCAN, 聚类, 等差报价, 围标]
dataset_id: "DM-BID-0001"
---

# 报价规律异常检测

## 方法描述
提取所有投标人的报价，计算报价偏离度（对基准价的偏离百分比），使用聚类算法检测异常报价模式。出现等差/等比排列、三家报价围绕某一值对称分布等非自然模式时判定异常。

## 检测逻辑
偏离度 = (投标价 - 基准价) / 基准价 × 100%。对偏离度向量做DBSCAN聚类，eps=3%，min_samples=2。孤立点为异常报价。对异常报价组做报价差值等差数列检测。

## 输入数据
- 必须：开标一览表（含所有投标人报价）, 招标控制价/最高限价
- 可选：历史同类项目中标价, 各投标人分项报价明细

## 技术参数
```python
from sklearn.cluster import DBSCAN
X = deviation_pcts.reshape(-1,1)
clusters = DBSCAN(eps=3, min_samples=2).fit_predict(X)
```

## 误报风险
- 市场行情剧烈波动导致报价自然集中
- 技术门槛低导致多家报出接近底价

## 组合规则
- 与L3文本雷同组合→报价协同+文本同源→铁证
- 与L8工商关联组合→报价协同+关联关系→必查
