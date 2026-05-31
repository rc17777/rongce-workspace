# -*- coding: utf-8 -*-
"""
审计RAG知识库查询工具
配合 build_audit_rag.py 使用
"""

import os
import sys

def query_rag(query_text, top_k=3):
    """
    查询审计法规知识库
    用法: query_rag("政府采购的主要方式")
    """
    from sentence_transformers import SentenceTransformer
    import chromadb
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "audit_rag_db")
    
    if not os.path.exists(db_path):
        return {"error": "请先运行 build_audit_rag.py 搭建知识库"}
    
    model = SentenceTransformer('shibing624/text2vec-base-chinese')
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("audit_knowledge")
    
    q_embedding = model.encode([query_text]).tolist()
    results = collection.query(
        query_embeddings=q_embedding,
        n_results=top_k
    )
    
    output = []
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        output.append({
            "rank": i + 1,
            "source": meta.get("title", "未知"),
            "status": meta.get("status", "未知"),
            "content": doc[:200]
        })
    
    return {"query": query_text, "results": output}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "政府采购的主要方式是什么"
    
    import json
    result = query_rag(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
