# 采购审计方法

> 与 procurement-audit-models 技能互补，此处聚焦「数据化审计」文章中的补充方法。

## 供应商关联关系识别

### 数据挖掘方法
- 工商信息交叉比对（股东/法人/高管/监事/地址/电话）
- NLP企业名称模糊匹配
- 企业依存度计算（资金往来/交易频次）
- 社交网络分析（SNA）挖围标线索

## TF-IDF文本雷同检测

用于检测投标文件是否由同一来源制作：
```python
from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(投标文件文本列表)
# 余弦相似度矩阵
from sklearn.metrics.pairwise import cosine_similarity
similarity = cosine_similarity(tfidf_matrix)
```

阈值：≥80%高度可疑，≥90%基本认定雷同
注意：排除招标文件要求的模板化承诺函

## 空间维度分析（#79）

QGIS分析供应商/投标人地理分布：
- 同一地址多家供应商 → 围标信号
- 异常集中的投标人地域分布 → 疑似围标团伙
- 项目所在地与中标方距离异常 → 可能为转包/挂靠

## Excel多关键词检索（#62）

```python
import pandas as pd
import glob

keywords = '|'.join(['回扣','好处费','返点','佣金'])
for f in glob.iglob('**/*.xlsx', recursive=True):
    df = pd.read_excel(f, sheet_name=None)
    for sheet_name, sheet_data in df.items():
        for col in sheet_data.columns:
            mask = sheet_data[col].astype(str).str.contains(keywords, na=False)
            if mask.any():
                print(f"命中: {f} → {sheet_name} → {col}")
```
