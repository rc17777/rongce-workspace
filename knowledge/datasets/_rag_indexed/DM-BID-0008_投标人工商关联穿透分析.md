---
title: "投标人工商关联穿透分析"
type: "detection_method"
layer: "L8"
confidence_level: "铁证"
alias: "L8-工商关联"
business_line: "通用"
keywords: [工商关联, 股权穿透, 实际控制人, 高管重叠, 天眼查, 围标]
dataset_id: "DM-BID-0008"
---

# 投标人工商关联穿透分析

## 方法描述
获取全部投标人/中标人的统一社会信用代码，通过天眼查/企查查API做股权穿透，检测：同一实际控制人、交叉持股、高管重叠、同一注册地址/电话/邮箱、历史共同投标记录。构建供应商关联网络图谱，识别隐藏的关联投标人组。

## 检测逻辑
输入全部投标人名称→API查询→构建关联图(G=(V,E))→检测联通分量→每个联通分量(≥2节点)即为关联投标人组。

## 输入数据
- 必须：全部投标人/中标人公司全称列表
- 可选：统一社会信用代码, 历史投标台账(≥3年)

## 技术参数
```python
import networkx as nx
G = nx.Graph()
# 边: company1 --[share/executive/address]-- company2
components = list(nx.connected_components(G))
```

## 误报风险
- 同行业正常商业合作→需结合投标行为判断
- 大型集团内部子公司独立投标→集团内部投标需看是否合规

## 组合规则
- 与L1报价组合→关联+协同报价→围标铁证
- 与L3文本雷同组合→关联+雷同→串标铁证
