"""
RAG Knowledge Bridge for 智析智能体 v2.0
将独立RAG知识库封装为智析可调用的模块
"""
import os
import sys
import json
import pickle
import re
from typing import List, Dict, Optional

# RAG索引路径
INDEX_DIR = r'D:\openclaw-workspace\.rag_index'
INDEX_FILE = os.path.join(INDEX_DIR, 'rag_index.json')
KNOWLEDGE_DIR = r'D:\openclaw-workspace\knowledge'

# Zhipu API 配置
ZHIPU_API = '6fd63d70ad8944e597ab5c2d3609fbf1.U41vqcRuzi8V8EBH'
ZHIPU_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
ZHIPU_MODEL = 'glm-4-plus'

class RAGKnowledgeBridge:
    """RAG知识桥：封装RAG查询能力供智析调用"""
    
    def __init__(self):
        self.vectorizer = None
        self.tfidf_matrix = None
        self.all_chunks = []
        self.texts = []
        self._loaded = False
        self._load_index()
    
    def _load_index(self):
        """加载RAG索引"""
        try:
            if os.path.exists(INDEX_FILE):
                with open(INDEX_FILE, 'rb') as f:
                    data = pickle.load(f)
                self.vectorizer = data['vectorizer']
                self.tfidf_matrix = data['matrix']
                self.texts = data['texts']
                self.all_chunks = data['chunks']
                self._loaded = True
                print(f"[RAG] 索引加载成功: {len(self.all_chunks)} chunks")
            else:
                print(f"[RAG] 索引不存在，请先运行 rag_rebuild.py 构建索引")
        except Exception as e:
            print(f"[RAG] 索引加载失败: {e}")
    
    def search(self, query: str, top_k: int = 5, min_score: float = 0.01) -> List[Dict]:
        """检索最相关的知识片段"""
        if not self._loaded:
            return []
        
        from sklearn.metrics.pairwise import cosine_similarity
        
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.tfidf_matrix)[0]
        
        top_idx = scores.argsort()[::-1][:top_k]
        results = []
        for idx in top_idx:
            if scores[idx] > min_score:
                results.append({
                    'score': float(scores[idx]),
                    'source': self.all_chunks[idx]['source'],
                    'text': self.all_chunks[idx]['text'][:800],
                    'full_text': self.all_chunks[idx]['text']
                })
        return results
    
    def query(self, query: str, top_k: int = 5, generate_answer: bool = True) -> Dict:
        """完整RAG查询：检索 + 生成答案"""
        results = self.search(query, top_k)
        
        response = {
            'query': query,
            'retrieved_count': len(results),
            'results': results,
            'answer': None,
            'sources': []
        }
        
        if not results:
            response['answer'] = "未在知识库中找到相关内容。"
            return response
        
        # 收集来源
        response['sources'] = list(set([r['source'] for r in results]))
        
        # 生成答案
        if generate_answer and ZHIPU_API:
            context = "\n\n---\n\n".join([
                f"【来源：{r['source']}】\n{r['full_text'][:1000]}" 
                for r in results
            ])
            
            prompt = f"""你是四川融策会计师事务所的智能审计助手。请基于以下参考资料，回答用户的问题。

## 参考资料
{context}

## 用户问题
{query}

## 要求
1. 基于参考资料回答，不要编造
2. 如果资料不足，明确说明
3. 回答要专业、简洁、有条理
4. 如涉及政策，注明政策名称和文号

## 回答"""
            
            try:
                import requests
                resp = requests.post(
                    ZHIPU_URL,
                    headers={
                        'Authorization': f'Bearer {ZHIPU_API}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': ZHIPU_MODEL,
                        'messages': [
                            {'role': 'system', 'content': '你是融策审计知识库智能助手'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.3,
                        'max_tokens': 2000
                    },
                    timeout=60
                )
                if resp.status_code == 200:
                    answer = resp.json()['choices'][0]['message']['content']
                    response['answer'] = answer
                else:
                    response['answer'] = f"API调用失败: {resp.status_code}"
            except Exception as e:
                response['answer'] = f"生成答案时出错: {e}"
        
        return response
    
    def quick_query(self, query: str) -> str:
        """快速查询，返回纯文本答案"""
        result = self.query(query, top_k=3, generate_answer=True)
        if result['answer']:
            return result['answer']
        return "未能获取答案"
    
    def get_status(self) -> Dict:
        """获取RAG系统状态"""
        return {
            'loaded': self._loaded,
            'chunks_count': len(self.all_chunks),
            'index_path': INDEX_FILE,
            'knowledge_dir': KNOWLEDGE_DIR,
            'api_available': bool(ZHIPU_API)
        }

# 全局实例（单例模式）
_rag_bridge = None

def get_rag_bridge() -> RAGKnowledgeBridge:
    """获取RAG知识桥实例"""
    global _rag_bridge
    if _rag_bridge is None:
        _rag_bridge = RAGKnowledgeBridge()
    return _rag_bridge

if __name__ == '__main__':
    # 测试
    bridge = get_rag_bridge()
    print(bridge.get_status())
    
    test_query = "专项债券审计应关注哪些要点"
    result = bridge.query(test_query)
    print(f"\nQ: {test_query}")
    print(f"A: {result['answer'][:500]}...")
