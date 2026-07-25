#!/usr/bin/env python3
"""
业务场景3-4：中文文本分析算法升级
替换 Sentence-BERT → BGE-M3 (中文SOTA) + SimCSE-chinese
新增 UIE通用信息抽取 接口
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import json


@dataclass 
class TextSimilarityResult:
    """文本相似度分析结果"""
    doc_a: str
    doc_b: str
    cosine_similarity: float
    keywords_overlap: float    # TF-IDF关键词重叠率
    semantic_similarity: float  # BGE-M3语义相似度
    combined_score: float       # 综合相似度
    is_suspicious: bool = False


class ChineseTextEngine:
    """
    中文文本分析引擎
    
    三层检测：
    L1: TF-IDF字面重叠 (快速粗筛)
    L2: BGE-M3语义相似 (精准判断)
    L3: 关键词/实体重叠 (证据链)
    
    使用：
    >>> engine = ChineseTextEngine(model_name='BAAI/bge-m3')
    >>> result = engine.compare("合同A全文...", "合同B全文...")
    >>> print(f"相似度: {result.combined_score:.3f}")
    """
    
    def __init__(self, model_name: str = 'BAAI/bge-m3'):
        self.model_name = model_name
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """延迟加载embedding模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ 已加载: {self.model_name}")
        except ImportError:
            print("⚠️ sentence-transformers未安装，使用简易模式")
            print("   pip install sentence-transformers")
        except Exception as e:
            print(f"⚠️ 模型加载失败: {e}，使用简易模式")
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """中文文本向量化"""
        if self.model:
            return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        else:
            # 简易模式：TF-IDF + 白化
            return self._simple_encode(texts)
    
    def _simple_encode(self, texts: List[str]) -> np.ndarray:
        """简易向量化（无BGE-M3时的fallback）"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        return vec.fit_transform(texts).toarray()
    
    def compare(self, doc_a: str, doc_b: str) -> TextSimilarityResult:
        """两个文档的全面相似度分析"""
        # L1: TF-IDF字面重叠
        tfidf_score = self._tfidf_similarity(doc_a, doc_b)
        
        # L2: 语义相似度 (BGE-M3)
        semantic = 0.0
        try:
            embeddings = self.encode([doc_a[:2000], doc_b[:2000]])
            semantic = float(np.dot(embeddings[0], embeddings[1]))
        except:
            semantic = tfidf_score  # fallback
        
        # L3: 关键词重叠
        kw_overlap = self._keyword_overlap(doc_a, doc_b)
        
        # 综合评分 (权重可调)
        combined = 0.25 * tfidf_score + 0.50 * semantic + 0.25 * kw_overlap
        
        # 疑点判断阈值
        is_suspicious = combined > 0.70
        
        return TextSimilarityResult(
            doc_a=doc_a[:100],
            doc_b=doc_b[:100],
            cosine_similarity=tfidf_score,
            keywords_overlap=kw_overlap,
            semantic_similarity=semantic,
            combined_score=combined,
            is_suspicious=is_suspicious
        )
    
    def batch_compare(self, docs: List[str]) -> np.ndarray:
        """批量文档对相似度矩阵"""
        n = len(docs)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                result = self.compare(docs[i], docs[j])
                matrix[i][j] = matrix[j][i] = result.combined_score
        return matrix
    
    def find_similar_pairs(self, docs: List[str], threshold: float = 0.75) -> List[Tuple[int, int, float]]:
        """找高相似度文档对"""
        pairs = []
        n = len(docs)
        for i in range(n):
            for j in range(i+1, n):
                result = self.compare(docs[i], docs[j])
                if result.combined_score > threshold:
                    pairs.append((i, j, result.combined_score))
        return sorted(pairs, key=lambda x: x[2], reverse=True)
    
    def _tfidf_similarity(self, a: str, b: str) -> float:
        """TF-IDF余弦相似度"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vec = TfidfVectorizer(ngram_range=(1, 3))
        try:
            tfidf = vec.fit_transform([a, b])
            return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        except:
            return 0.0
    
    def _keyword_overlap(self, a: str, b: str) -> float:
        """关键词重叠率"""
        import re
        def extract_keywords(text):
            # 提取审计相关关键词: 金额/日期/数字/特殊词汇
            keywords = set()
            keywords.update(re.findall(r'[\d,]+\.?\d*\s*[万元亿元]', text))
            keywords.update(re.findall(r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}', text))
            keywords.update(re.findall(r'[\u4e00-\u9fff]{4,10}(?:合同|条款|规定|要求)', text))
            return keywords
        
        kw_a = extract_keywords(a)
        kw_b = extract_keywords(b)
        if not kw_a or not kw_b:
            return 0.0
        return len(kw_a & kw_b) / max(len(kw_a), len(kw_b))


class UIEInfoExtractor:
    """
    PaddleNLP UIE 通用信息抽取接口
    
    一条prompt，同时抽取审计关键信息：
    金额、日期、文号、甲乙双方、履约期限、合同标的
    
    使用：
    >>> extractor = UIEInfoExtractor()
    >>> result = extractor.extract("合同总金额4.07万元，履约日期2025年1月至12月")
    """
    
    SCHEMA = [
        '金额', '日期', '文号', '甲方', '乙方',
        '履约期限', '合同标的', '付款方式',
        '违约责任', '验收标准', '项目名称'
    ]
    
    def __init__(self):
        self.extractor = None
        try:
            from paddlenlp import Taskflow
            self.extractor = Taskflow("information_extraction", schema=self.SCHEMA)
            print("✅ UIE信息抽取已就绪")
        except ImportError:
            print("⚠️ PaddleNLP未安装: pip install paddlenlp")
        except Exception as e:
            print(f"⚠️ UIE加载失败: {e}")
    
    def extract(self, text: str) -> Dict[str, List]:
        """抽取审计关键信息"""
        if self.extractor:
            return self.extractor(text)
        else:
            return self._rule_extract(text)
    
    def _rule_extract(self, text: str) -> Dict:
        """规则兜底（无UIE时）"""
        import re
        result = {}
        patterns = {
            '金额': r'[\d,]+\.?\d*\s*[万元亿元]',
            '日期': r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日号]',
            '文号': r'[财国发川成][\u4e00-\u9fa5]{1,3}\s*〔?\s*\d{4}\s*〕?\s*\d+\s*号',
        }
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                result[key] = [{'text': m} for m in matches]
        return result


# ===== CLI Demo =====
if __name__ == '__main__':
    print("=" * 70)
    print("  中文文本分析引擎 演示")
    print("=" * 70)
    
    # 测试相似度
    doc_a = """
    项目名称：基层食品安全监管工作经费
    预算金额：4.07万元
    履约期限：2025年1月1日至2025年12月31日
    乙方：成都某食品安全检测有限公司
    合同标的：食品安全抽样检测服务
    """
    
    doc_b = """
    项目名称：基层食品安全监管工作经费
    预算金额：4.07万元
    履约期限：2025年1月1日至2025年12月31日  
    乙方：成都某食品检测有限公司
    合同标的：食品安全抽检服务
    """
    
    doc_c = """
    项目名称：道路安全综合治理工作经费
    预算金额：8万元
    履约期限：2025年度
    乙方：成都市某市政工程有限公司
    合同标的：道路维护及安全设施安装
    """
    
    engine = ChineseTextEngine()
    
    # 相似 vs 不相似
    r1 = engine.compare(doc_a, doc_b)
    r2 = engine.compare(doc_a, doc_c)
    
    print(f"\n【文本相似度】")
    print(f"A vs B (雷同合同): 综合={r1.combined_score:.3f} {'⚠️ 疑点' if r1.is_suspicious else '✅ 无问题'}")
    print(f"  TF-IDF={r1.cosine_similarity:.3f} 语义={r1.semantic_similarity:.3f} 关键词重叠={r1.keywords_overlap:.3f}")
    
    print(f"\nA vs C (不同合同): 综合={r2.combined_score:.3f} {'⚠️ 疑点' if r2.is_suspicious else '✅ 无问题'}")
    print(f"  TF-IDF={r2.cosine_similarity:.3f} 语义={r2.semantic_similarity:.3f} 关键词重叠={r2.keywords_overlap:.3f}")
    
    # 测试信息抽取
    print(f"\n【UIE信息抽取】")
    extractor = UIEInfoExtractor()
    sample = "合同编号：RHJD-2025-001，甲方：成都市郫都区红光街道办事处，合同金额：肆万零柒佰贰拾捌元整（¥40,728.00），履约期限：2025年1月1日至2025年12月31日，付款方式：分期付款，乙方：成都检测公司"
    result = extractor.extract(sample)
    print(json.dumps(result, ensure_ascii=False, indent=2))
