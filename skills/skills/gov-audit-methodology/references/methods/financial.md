# 财务审计方法

## 财务报表快速理解（#59）

### 三张报表

| 报表 | 昵称 | 比喻 | 核心公式 |
|------|------|------|---------|
| 资产负债表 | 底子 | 照相机(时点快照) | 资产=负债+所有者权益 |
| 利润表 | 面子 | 摄像机(时段录像) | 利润=收入-成本费用 |
| 现金流量表 | 日子 | 摄像机(现金变化) | 净流量=流入-流出 |

### 比率分析

| 维度 | 指标 | 判断 |
|------|------|------|
| 盈利能力 | 净利润率 | 高=盈利能力强 |
| 营运能力 | 总资产周转率 | 高=销售能力强 |
| 偿债能力 | 流动比率/速动比率 | 高=短期偿债能力强 |
| 投资回报 | 净资产收益率 | 高=股东收益高 |

## 孤立点分析（#68）

K-Means聚类发现异常财务数据：
```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# 标准化
scaler = StandardScaler()
data_scaled = scaler.fit_transform(财务数据[['金额','频次','账户数']])

# 聚类
kmeans = KMeans(n_clusters=3)
labels = kmeans.fit_predict(data_scaled)

# 计算各点到簇中心的距离
from scipy.spatial.distance import cdist
distances = cdist(data_scaled, kmeans.cluster_centers_, 'euclidean')
outlier_scores = distances.min(axis=1)
# outlier_scores 前5%的点 = 疑点
```

## FS-LDM十大主题（#51）

用于快速理解被审计单位数据结构：
1. 当事人(Party) → 客户/供应商/员工
2. 产品(Product) → 提供的服务/商品
3. 协议(Agreement) → 合同/账户
4. 事件(Event) → 交易记录
5. 资产(Asset) → 客户资产/负债信息
6. 财务(Finance) → 总账/科目
7. 内部组织(Internal Org) → 部门/机构
8. 地域(Location) → 地址/区域
9. 营销(Campaign) → 营销活动
10. 渠道(Channel) → 交易渠道

数据按十大主题归类后，思考就有了方向。
