---
title: "历史中标模式分析（中标专业户+陪标专业户检测）"
type: "detection_method"
layer: "L15"
confidence_level: "铁证"
alias: "L15-历史模式"
business_line: "通用"
keywords: [历史模式, FP-growth, 中标专业户, 陪标, 伴随投标, 频繁模式]
dataset_id: "DM-BID-0015"
---

# 历史中标模式分析（中标专业户+陪标专业户检测）

## 方法描述
基于3年+招投标台账，使用FP-growth频繁模式挖掘算法检测供应商伴随投标行为。识别：①中标专业户（同一供应商在同一采购人名下中标比例异常高）②陪标专业户（始终参与但从不中标）③固定组合（供应商组反复出现在同一项目中）。要求≥3个项目历史数据。

## 检测逻辑
FP-growth: min_support=3(至少出现3次), min_confidence=0.8。输出频繁项集→识别固定投标组合。单独统计每个供应商的中标率→中标率≥80%为中标专业户，中标率=0%且参与≥5次为陪标专业户。

## 输入数据
- 必须：≥3年招投标台账（含项目名称/投标人/中标人）
- 可选：

## 技术参数
```python
from mlxtend.frequent_patterns import fpgrowth
freq_itemsets = fpgrowth(onehot, min_support=3/len(onehot), use_colnames=True)
```

## 误报风险
- 行业竞争不充分→区域内只有少数供应商→自然伴随
- 框架协议供应商→按轮次轮流中标是正常的

## 组合规则
- 与L1报价组合→伴随+协同报价→系统性围标
- 与L3文本雷同组合→伴随+雷同→陪标产业链
