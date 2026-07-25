#!/usr/bin/env python3
"""
arXiv 学术追踪 — 算法雷达配套（v2：HTML搜索版）
通过arXiv搜索页面（非API）追踪最新论文，绕过GFW限制

使用：
    python scripts/algorithm_quality/arxiv_tracker.py              # 全主题扫描
    python scripts/algorithm_quality/arxiv_tracker.py --topic fraud  # 单主题
    python scripts/algorithm_quality/arxiv_tracker.py --report     # 仅出报告
"""

import urllib.request, urllib.parse
import json, os, re, time, ssl
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field, asdict

# Windows SSL兼容
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# ============================================================
#  融策7大审计学术主题
# ============================================================
TOPICS = {
    "fraud": {
        "name": "反舞弊与欺诈检测",
        "query": "fraud+detection+machine+learning",
        "keywords": ["fraud", "collusion", "bid", "procurement", "anomaly", "graph"],
        "radar_category": "图分析",
        "priority": "P0",
    },
    "anomaly": {
        "name": "多维异常检测",
        "query": "anomaly+detection+financial+unsupervised",
        "keywords": ["anomaly", "outlier", "isolation forest", "LOF", "unsupervised", "financial"],
        "radar_category": "统计",
        "priority": "P0",
    },
    "chinese_nlp": {
        "name": "中文自然语言处理",
        "query": "Chinese+NLP+information+extraction+embedding",
        "keywords": ["chinese", "embedding", "NER", "information extraction", "BGE", "text similarity"],
        "radar_category": "NLP",
        "priority": "P1",
    },
    "graph_mining": {
        "name": "图挖掘与关联分析",
        "query": "graph+neural+network+fraud+anomaly+detection",
        "keywords": ["graph", "GNN", "Fraudar", "community", "dense subgraph", "network"],
        "radar_category": "图分析",
        "priority": "P0",
    },
    "audit_automation": {
        "name": "审计自动化与AI审计",
        "query": "audit+artificial+intelligence+machine+learning+automation",
        "keywords": ["audit", "automation", "AI", "RPA", "continuous auditing"],
        "radar_category": "多模型",
        "priority": "P1",
    },
    "time_series": {
        "name": "时序分析与预测",
        "query": "time+series+anomaly+detection+change+point",
        "keywords": ["time series", "forecast", "prophet", "STL", "change point", "trend"],
        "radar_category": "时序",
        "priority": "P2",
    },
    "document_understanding": {
        "name": "文档理解与版面分析",
        "query": "document+understanding+layout+analysis+OCR+deep+learning",
        "keywords": ["document", "layout", "OCR", "invoice", "receipt", "table extraction"],
        "radar_category": "NLP",
        "priority": "P2",
    },
}


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: List[str]
    summary: str
    published: str
    pdf_url: str
    topic: str = ""
    relevance_score: float = 0.0
    actionable: bool = False
    suggested_algorithm: str = ""


class ArxivTracker:
    """arXiv学术追踪引擎（HTML搜索版）"""
    
    BASE_URL = "https://arxiv.org/search/?"
    
    def __init__(self, output_dir: str = ""):
        if not output_dir:
            output_dir = os.path.join(
                os.path.dirname(__file__), "..", "..",
                "config", "algorithm_quality"
            )
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.papers: List[ArxivPaper] = []
        self.history_file = os.path.join(output_dir, "arxiv_history.json")
        self._load_history()
    
    def _load_history(self):
        self.seen_ids = set()
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.seen_ids = set(data.get("seen_ids", []))
    
    def _save_history(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump({
                "last_scan": datetime.now().isoformat(),
                "seen_ids": list(self.seen_ids),
                "total_tracked": len(self.seen_ids),
            }, f, ensure_ascii=False, indent=2)
    
    def _fetch_html(self, query: str, max_results: int = 15) -> str:
        """抓取arXiv搜索页面HTML"""
        params = urllib.parse.urlencode({
            "searchtype": "all",
            "query": query,
            "start": 0,
        })
        url = f"{self.BASE_URL}{params}"
        
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; RongceAudit/1.0)"
        })
        try:
            resp = urllib.request.urlopen(req, timeout=30, context=ssl_ctx)
            return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"    ⚠️ arXiv抓取失败: {e}")
            return ""
    
    def _parse_search_results(self, html: str) -> List[ArxivPaper]:
        """解析arXiv搜索页面HTML"""
        papers = []
        
        # 提取每个论文条目
        # arXiv搜索页面结构：<li class="arxiv-result"> 包含标题、作者、摘要
        entries = re.split(r'<li class="arxiv-result"', html)[1:]
        
        for entry in entries:
            try:
                # 标题
                title_m = re.search(r'<p class="title is-5 mathjax">\s*(.*?)\s*</p>', entry, re.DOTALL)
                if not title_m:
                    continue
                title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
                title = re.sub(r'\s+', ' ', title)
                
                # 作者
                authors = []
                author_matches = re.findall(r'<a href="/search/\?searchtype=author[^"]*">([^<]+)</a>', entry)
                authors = [a.strip() for a in author_matches]
                
                # 摘要
                abstract_m = re.search(r'<span class="abstract-full[^"]*">(.*?)</span>', entry, re.DOTALL)
                if not abstract_m:
                    abstract_m = re.search(r'Abstract:</span>\s*(.*?)(?:</p>|</span>)', entry, re.DOTALL)
                summary = ""
                if abstract_m:
                    summary = re.sub(r'<[^>]+>', '', abstract_m.group(1)).strip()[:500]
                    summary = re.sub(r'\s+', ' ', summary)
                
                # arXiv ID
                id_m = re.search(r'/abs/(\d+\.\d+)', entry)
                if not id_m:
                    id_m = re.search(r'arXiv:(\d+\.\d+)', entry)
                arxiv_id = id_m.group(1) if id_m else ""
                if not arxiv_id:
                    continue
                
                # 日期
                date_m = re.search(r'Submitted\s+(\d+)\s+(\w+),\s+(\d{4})', entry)
                if date_m:
                    published = f"{date_m.group(3)}-{self._month_num(date_m.group(2))}-{date_m.group(1).zfill(2)}"
                else:
                    published = "2026-01-01"
                
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
                
                papers.append(ArxivPaper(
                    arxiv_id=arxiv_id,
                    title=title,
                    authors=authors,
                    summary=summary,
                    published=published,
                    pdf_url=pdf_url,
                ))
            except Exception:
                continue
        
        return papers
    
    def _month_num(self, month_str: str) -> str:
        months = {"January":"01","February":"02","March":"03","April":"04",
                  "May":"05","June":"06","July":"07","August":"08",
                  "September":"09","October":"10","November":"11","December":"12"}
        return months.get(month_str, "01")
    
    def search(self, query: str, max_results: int = 15) -> List[ArxivPaper]:
        """搜索arXiv（HTML页面）"""
        html = self._fetch_html(query, max_results)
        if not html:
            return []
        papers = self._parse_search_results(html)
        return papers[:max_results]
    
    def scan_all_topics(self, max_per_topic: int = 10) -> Dict[str, List[ArxivPaper]]:
        """扫描所有7个主题"""
        results = {}
        for topic_id, topic_info in TOPICS.items():
            print(f"  🔍 {topic_info['name']} ...", end=" ")
            papers = self.search(topic_info["query"], max_per_topic)
            
            scored = []
            for paper in papers:
                paper.topic = topic_id
                paper.relevance_score = self._score_relevance(paper, topic_info)
                if paper.relevance_score > 0.3:
                    paper.actionable = paper.relevance_score > 0.7
                    paper.suggested_algorithm = self._extract_algorithm(paper)
                    scored.append(paper)
            
            results[topic_id] = scored
            print(f"{len(papers)}篇 → 筛选{len(scored)}篇相关")
            time.sleep(2)  # arXiv限速
        
        return results
    
    def _score_relevance(self, paper: ArxivPaper, topic: Dict) -> float:
        text = f"{paper.title} {paper.summary}".lower()
        keywords = topic["keywords"]
        hits = sum(1 for kw in keywords if kw.lower() in text)
        kw_score = min(hits / max(len(keywords) * 0.5, 1), 1.0)
        try:
            days_ago = (datetime.now() - datetime.strptime(paper.published, "%Y-%m-%d")).days
        except:
            days_ago = 90
        time_score = max(0, 1 - days_ago / 365)
        title_hits = sum(1 for kw in keywords if kw.lower() in paper.title.lower())
        title_bonus = min(title_hits * 0.2, 0.4)
        return min(0.4 * kw_score + 0.3 * time_score + title_bonus + 0.3, 1.0)
    
    def _extract_algorithm(self, paper: ArxivPaper) -> str:
        text = f"{paper.title} {paper.summary}"
        algo_patterns = [
            (r"Isolation\s*Forest", "Isolation Forest"),
            (r"LOF|Local\s*Outlier\s*Factor", "LOF"),
            (r"GraphSAGE|Graph\s*SAGE", "GraphSAGE"),
            (r"GAT|Graph\s*Attention", "GAT"),
            (r"Fraudar", "Fraudar"),
            (r"BGE|BAAI.*Embedding", "BGE"),
            (r"XGBoost|XGB", "XGBoost"),
            (r"AutoEncoder|Auto-Encoder", "AutoEncoder"),
            (r"GNN|Graph\s*Neural\s*Network", "GNN"),
            (r"Transformer", "Transformer"),
            (r"Contrastive\s*Learning|SimCSE", "Contrastive Learning"),
            (r"LLM|Large\s*Language\s*Model", "LLM"),
            (r"Reinforcement\s*Learning|DQN", "Reinforcement Learning"),
            (r"XAI|Explainable|Explanation", "XAI"),
        ]
        found = []
        for pattern, name in algo_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(name)
        return " + ".join(found[:2]) if found else ""
    
    def generate_report(self, results: Dict[str, List[ArxivPaper]]) -> str:
        lines = [
            "=" * 70,
            f"  " + "=" * 68,
            f"  📡 融策 · arXiv 学术追踪报告",
            f"  扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"  追踪主题: {len(TOPICS)}个 | 算法雷达配套",
            "=" * 70,
            "",
        ]
        
        total = 0
        actionable_total = 0
        new_papers = []
        
        for topic_id, papers in results.items():
            topic_info = TOPICS[topic_id]
            icon = {"P0":"🔴","P1":"🟡","P2":"🟢"}.get(topic_info["priority"], "⚪")
            new = [p for p in papers if p.arxiv_id not in self.seen_ids]
            actionable = [p for p in new if p.actionable]
            
            total += len(new)
            actionable_total += len(actionable)
            
            lines.append(f"  {icon} {topic_info['name']} [{topic_info['priority']}]")
            lines.append(f"     新论文: {len(new)}篇 | 高价值: {len(actionable)}篇")
            
            for p in actionable[:3]:
                lines.append(f"     📄 {p.title[:90]}")
                lines.append(f"        {', '.join(p.authors[:3])} | {p.published} | arXiv:{p.arxiv_id}")
                if p.suggested_algorithm:
                    lines.append(f"        🏷️ {p.suggested_algorithm}")
                lines.append("")
            
            for p in new:
                self.seen_ids.add(p.arxiv_id)
                new_papers.append(p)
            
            lines.append("")
        
        lines.append(f"  合计: {total}篇新论文 | {actionable_total}篇高价值")
        lines.append(f"  累计追踪: {len(self.seen_ids)}篇")
        
        self._save_history()
        
        if new_papers:
            detail_file = os.path.join(self.output_dir, "arxiv_last_scan.json")
            with open(detail_file, "w", encoding="utf-8") as f:
                json.dump([asdict(p) for p in new_papers], f, ensure_ascii=False, indent=2)
        
        return "\n".join(lines)
    
    def suggest_radar_updates(self, results: Dict[str, List[ArxivPaper]]) -> List[str]:
        suggestions = []
        all_new = []
        for papers in results.values():
            all_new.extend([p for p in papers if p.arxiv_id not in self.seen_ids])
        
        algo_counts = {}
        for p in all_new:
            algo = p.suggested_algorithm
            if algo:
                algo_counts[algo] = algo_counts.get(algo, 0) + 1
        
        for algo, count in sorted(algo_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 2:
                suggestions.append(f"  → {algo}: {count}篇新论文提及，建议加入雷达观察")
        
        return suggestions


# ===== CLI =====
if __name__ == "__main__":
    import sys
    
    tracker = ArxivTracker()
    
    topic_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--topic="):
            topic_filter = arg.split("=")[1]
    
    print("=" * 70)
    print("  📡 融策 · arXiv 学术追踪（HTML搜索版）")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    if topic_filter and topic_filter in TOPICS:
        print(f"\n  🎯 单主题: {TOPICS[topic_filter]['name']}")
        papers = tracker.search(TOPICS[topic_filter]["query"], 15)
        for p in papers:
            p.topic = topic_filter
            p.relevance_score = tracker._score_relevance(p, TOPICS[topic_filter])
            p.actionable = p.relevance_score > 0.7
            p.suggested_algorithm = tracker._extract_algorithm(p)
        results = {topic_filter: [p for p in papers if p.relevance_score > 0.3]}
    else:
        print(f"\n  🔍 全主题扫描 ({len(TOPICS)}个主题，预计60秒)...")
        results = tracker.scan_all_topics(10)
    
    report = tracker.generate_report(results)
    print(f"\n{report}")
    
    suggestions = tracker.suggest_radar_updates(results)
    if suggestions:
        print("\n  💡 雷达更新建议:")
        for s in suggestions:
            print(s)
    else:
        print("\n  ✅ 当前无可触发雷达更新的新趋势")
