#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融策审计驾驶舱 ←→ RAG知识库桥接
让驾驶舱的AI助手能真正查询法规、准则、案例
"""
import sys, os, json
import requests

RAG_URL = "http://localhost:5000"  # 智析v2 RAG服务

def query_rag(question, top_k=5):
    """查询RAG知识库"""
    try:
        resp = requests.post(
            f"{RAG_URL}/api/rag/query",
            json={"question": question, "top_k": top_k},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        pass
    return None

def get_knowledge_context(question):
    """获取知识库上下文，用于增强AI回答"""
    result = query_rag(question)
    if result and result.get('chunks'):
        chunks = result['chunks'][:5]
        context = "【知识库参考】\n"
        for i, c in enumerate(chunks):
            context += f"{i+1}. {c.get('text', '')[:300]}\n"
            if c.get('source'):
                context += f"   来源: {c['source']}\n"
        return context
    return None

def rag_status():
    """检查RAG服务是否在线"""
    try:
        resp = requests.get(RAG_URL, timeout=3)
        return resp.status_code == 200
    except:
        return False

def search_regulation(keyword):
    """搜索特定法规"""
    try:
        resp = requests.post(
            f"{RAG_URL}/api/rag/query",
            json={"question": keyword, "top_k": 8},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            regulations = []
            for c in data.get('chunks', []):
                regulations.append({
                    "title": c.get('source', '未知来源'),
                    "text": c.get('text', '')[:200],
                    "score": c.get('score', 0),
                })
            return regulations
    except:
        pass
    return []

if __name__ == '__main__':
    # 测试
    print("RAG状态:", "在线" if rag_status() else "离线")
    if rag_status():
        ctx = get_knowledge_context("专项资金审计要点")
        if ctx:
            print(ctx[:500])
