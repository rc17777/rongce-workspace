"""
融策知识Agent — 知识运营工具集
==============================
多源采集 → 智能摘要 → 归档 → 生命周期管理 → 调度

直接导入子模块:
    from tools.knowledge.collector import Collector, Article
    from tools.knowledge.pipeline import run_pipeline
"""

__all__ = [
    "Collector", "Article",
    "summarize", "SummarizedArticle",
    "archive",
    "run_lifecycle_check",
    "run_pipeline",
    "run_once", "run_daemon",
]
