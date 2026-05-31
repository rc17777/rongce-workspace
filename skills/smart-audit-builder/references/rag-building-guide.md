# 审计RAG知识库实战指南

基于「数审派」公众号《RAG知识库实战指南：从架构设计到审计法规检索案例》文章整理。

## 为什么审计需要RAG？

审计工作涉及大量法规、合同、标准、历史案例等非结构化文本数据。传统搜索依赖关键词匹配，无法理解语义。RAG（检索增强生成）通过「向量检索+大模型生成」实现精准的语义匹配。

## 审计RAG架构

```
用户提问 → 向量化(embedding) → 检索相似文档 → LLM生成回答
                ↓                    ↓
          法规/合同/底稿          原文出处引用
          向量数据库
```

## 快速实现（本地部署，零成本）

```python
# pip install chromadb sentence-transformers

from sentence_transformers import SentenceTransformer
import chromadb

# 1. 初始化嵌入模型和向量数据库
model = SentenceTransformer('shibing624/text2vec-base-chinese')
client = chromadb.PersistentClient(path="./audit_rag_db")
collection = client.get_or_create_collection("audit_knowledge")

# 2. 导入审计知识
laws = [
    "政府采购法第二十六条：公开招标应作为政府采购的主要采购方式...",
    "审计法实施条例第三十二条：审计机关有权要求被审计单位提供...",
    "财政违法行为处罚处分条例第十四条：...",
]
collection.add(
    documents=laws,
    ids=["law_001", "law_002", "law_003"]
)

# 3. 语义检索
query = "围标串标的定义和处罚标准"
results = collection.query(query_texts=[query], n_results=3)

# 4. 将检索结果作为上下文发给LLM生成回答
context = "\n".join(results['documents'][0])
# 调用大模型API，prompt: f"基于以下法规回答：{context}\n\n问题：{query}"
```

## 适用场景

| 场景 | 效果 | 数据来源 |
|------|------|---------|
| 审计人员查法规 | 秒级定位相关条款 | 审计法/政府采购法/财政处罚条例等 |
| 合同条款风险审查 | 自动匹配相似案例 | 历史合同 + 审计案例库 |
| 底稿智能填写 | 半自动生成底稿初稿 | 审计底稿模板库 |
| 审计问题定性 | 匹配类似问题的处理方式 | 历史审计发现库 |
