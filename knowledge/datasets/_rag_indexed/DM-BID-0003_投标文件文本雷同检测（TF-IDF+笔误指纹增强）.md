---
title: "投标文件文本雷同检测（TF-IDF+笔误指纹增强）"
type: "detection_method"
layer: "L3"
confidence_level: "铁证"
alias: "L3-文本雷同"
business_line: "通用"
keywords: [TF-IDF, 余弦相似度, 错别字, 笔误指纹, 文本雷同, 串标, 同人撰写]
dataset_id: "DM-BID-0003"
---

# 投标文件文本雷同检测（TF-IDF+笔误指纹增强）

## 方法描述
对投标文件技术方案全文做TF-IDF向量化，计算两两余弦相似度。增强版新增'共同错别字并集分析'：排除模板化套话后，检测多份文件中的共同笔误（错别字、不规范缩写、术语偏好），人的语言习惯无法伪造。

## 检测逻辑
TF-IDF: 相似度≥0.75→雷同。笔误增强: jieba分词→停用词+模板词去除→多文件错别字交集≥3个→同人撰写。

## 输入数据
- 必须：投标文件技术方案全文（电子版）
- 可选：投标文件商务标

## 技术参数
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
vec = TfidfVectorizer(max_features=5000).fit_transform(docs)
sim = cosine_similarity(vec)
```

## 误报风险
- 招标文件提供了技术方案模板→模板化套话会制造假阳性
- 同行业通用术语→不是笔误是行业习惯

## 组合规则
- 与L4图片哈希组合→文本+图片都雷同→铁证定案
- 与L5元数据组合→文本+元数据同源→铁证定案
