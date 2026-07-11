"""
工具1：text_hotword_analysis — TF-IDF会议纪要热词提取

场景：经济责任审计中，批量读取会议纪要，提取高频决策关键词，
     快速锁定测绘费、工程外包、补贴发放、资产处置等高危审计领域
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

from .utils import clean_text, load_stopwords, infer_audit_type, infer_focus_areas


@dataclass
class Hotword:
    word: str
    weight: float
    audit_relevance: str = ""  # 与审计的相关性说明
    risk_signal: bool = False  # 是否为风险信号


@dataclass
class HotwordResult:
    hotwords: List[Hotword]
    audit_focus: List[str]
    audit_type: str
    doc_count: int
    total_tokens: int
    wordcloud_data: Dict[str, float] = field(default_factory=dict)


class TextHotwordAnalyzer:
    """TF-IDF热词分析器"""

    def __init__(self):
        self._tfidf = None
        self._initialized = False

    def _init_tfidf(self):
        """延迟加载sklearn"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._tfidf = TfidfVectorizer
            self._initialized = True
        except ImportError:
            raise ImportError(
                "需要安装 scikit-learn: pip install scikit-learn"
            )

    def _segment(self, text: str) -> List[str]:
        """jieba分词"""
        try:
            import jieba
        except ImportError:
            # 降级：简单按空白+标点切分
            return re.findall(r"[\u4e00-\u9fff\w]+", text)
        return jieba.lcut(text)

    def analyze(
        self,
        documents: List[str],
        doc_type: str = "meeting_minutes",
        top_n: int = 20,
        custom_stopwords: Optional[List[str]] = None,
        audit_focus: Optional[str] = None,
    ) -> HotwordResult:
        """
        TF-IDF热词分析

        Args:
            documents: 文本数组
            doc_type: 文档类型 (meeting_minutes | policy | report)
            top_n: 返回热词数量
            custom_stopwords: 自定义停用词
            audit_focus: 审计重点类型，自动推断为空

        Returns:
            HotwordResult: 热词分析结果
        """
        if not self._initialized:
            self._init_tfidf()

        if not documents:
            raise ValueError("documents不能为空")

        # 推断审计类型
        inferred_type = audit_focus or infer_audit_type(documents)

        # 加载停用词
        stopwords = load_stopwords(inferred_type, custom_stopwords)

        # 分词 + 去停用词
        import jieba
        segmented_docs = []
        for doc in documents:
            cleaned = clean_text(doc)
            words = jieba.lcut(cleaned)
            filtered = [w for w in words if w not in stopwords and len(w) > 1]
            segmented_docs.append(" ".join(filtered))

        total_tokens = sum(len(d.split()) for d in segmented_docs)

        # TF-IDF计算
        vectorizer = self._tfidf(max_features=top_n * 2)
        tfidf_matrix = vectorizer.fit_transform(segmented_docs)
        feature_names = vectorizer.get_feature_names_out()

        # 取全局平均TF-IDF权重
        import numpy as np
        avg_weights = np.array(tfidf_matrix.mean(axis=0)).flatten()
        top_indices = np.argsort(avg_weights)[::-1][:top_n]

        # 审计风险词库（用于标注风险信号）
        risk_words = {
            "经济责任": {"外包", "采购", "处置", "变卖", "挪用", "私设", "账外", "套取",
                       "超标", "违规", "虚列", "冒领", "截留", "滞留", "预付", "垫付",
                       "借款", "担保", "投资", "担保", "抵押", "转让", "划转"},
            "预算执行": {"超支", "追加", "调整", "挪用", "拆借", "暂付", "挂账",
                       "垫付", "白条", "冲销", "虚列", "空转"},
            "工程项目": {"转包", "分包", "挂靠", "围标", "串标", "陪标", "变更",
                       "签证", "索赔", "追加", "漏项", "偷工减料"},
            "民生资金": {"重复", "冒领", "截留", "挪用", "优亲厚友", "虚报",
                       "骗取", "套取", "滞留"},
        }
        all_risk_words = set()
        for rw_set in risk_words.values():
            all_risk_words.update(rw_set)

        # 组装结果
        hotwords = []
        for idx in top_indices:
            word = feature_names[idx]
            weight = float(avg_weights[idx])
            is_risk = word in all_risk_words

            # 审计相关性说明
            relevance = self._describe_relevance(word, is_risk, inferred_type)

            hotwords.append(Hotword(
                word=word,
                weight=round(weight, 4),
                audit_relevance=relevance,
                risk_signal=is_risk,
            ))

        # 词云数据
        wordcloud = {hw.word: hw.weight for hw in hotwords}

        return HotwordResult(
            hotwords=hotwords,
            audit_focus=infer_focus_areas(inferred_type),
            audit_type=inferred_type,
            doc_count=len(documents),
            total_tokens=total_tokens,
            wordcloud_data=wordcloud,
        )

    def _describe_relevance(
        self, word: str, is_risk: bool, audit_type: str
    ) -> str:
        """生成审计相关性说明"""
        if not is_risk:
            return f"高频词，建议在{audit_type}审计中关注相关业务"

        risk_descriptions = {
            "外包": "工程/服务外包可能是规避招标的手段",
            "采购": "高频采购需关注集中度和合规性",
            "处置": "资产处置是否经过评估和审批程序",
            "变卖": "国有资产变卖是否存在流失风险",
            "挪用": "资金挪用是严重违规行为",
            "套取": "虚构交易套取资金涉嫌舞弊",
            "虚列": "虚列支出可能存在设立账外资金",
            "冒领": "冒领补贴资金的典型舞弊手法",
            "截留": "截留应缴财政资金",
            "超标": "超过规定标准可能涉及奢侈浪费",
            "违规": "需核查违规具体事项和责任人",
            "转包": "工程转包违反建筑法，需追查实际施工方",
            "围标": "围标串标涉嫌违法，需联动公安机关",
            "变更": "高频变更可能存在围标后追加利润",
            "预付": "大额预付款需关注资金安全",
            "借款": "违规对外借款可能存在利益输送",
        }
        return risk_descriptions.get(
            word, f"标记为风险信号词，{audit_type}审计中需重点关注"
        )


# ── MCP工具接口 ──────────────────────────────────────────────

def text_hotword_analysis(
    documents: List[str],
    doc_type: str = "meeting_minutes",
    top_n: int = 20,
    custom_stopwords: Optional[List[str]] = None,
    audit_focus: Optional[str] = None,
) -> dict:
    """MCP工具接口：text_hotword_analysis"""
    analyzer = TextHotwordAnalyzer()
    result = analyzer.analyze(
        documents=documents,
        doc_type=doc_type,
        top_n=top_n,
        custom_stopwords=custom_stopwords,
        audit_focus=audit_focus,
    )
    return {
        "hotwords": [asdict(hw) for hw in result.hotwords],
        "suggested_audit_focus": result.audit_focus,
        "audit_type": result.audit_type,
        "doc_count": result.doc_count,
        "total_tokens": result.total_tokens,
        "wordcloud_data": result.wordcloud_data,
    }
