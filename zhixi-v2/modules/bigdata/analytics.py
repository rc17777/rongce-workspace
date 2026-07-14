# 智析智能体 v2.0 — 大数据技术服务模块
# 功能：关系图谱挖掘 / 文本挖掘 / 可视化增强
# 资产来源: audit-knowledge-graph (Neo4j图谱) + procurement-audit-models (围标串标)

import networkx as nx
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
import math


class GraphAnalyzer:
    """关系图谱分析 — 资金流向/股权穿透/供应商关联/人员关系"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    # ---- 资金流向图谱 ----
    def build_fund_flow_graph(self, transactions: List[Dict]) -> nx.DiGraph:
        """
        transactions: [{from, to, amount, date, purpose}, ...]
        """
        G = nx.DiGraph()
        for t in transactions:
            G.add_edge(t["from"], t["to"], amount=t.get("amount", 0),
                       date=t.get("date", ""), purpose=t.get("purpose", ""))
        self.graph = G
        return G
    
    def find_fund_loops(self, G: nx.DiGraph = None) -> List[List[str]]:
        """发现资金回流/循环路径"""
        G = G or self.graph
        try:
            cycles = list(nx.simple_cycles(G))
            return [c for c in cycles if len(c) >= 3][:20]  # 只关注3个节点以上的循环
        except:
            return []
    
    def find_key_nodes(self, G: nx.DiGraph = None, top_n: int = 10) -> List[Dict]:
        """发现关键节点（核心资金中转方）"""
        G = G or self.graph
        if G.number_of_nodes() == 0:
            return []
        
        results = []
        # 度数中心性
        deg = nx.degree_centrality(G)
        # 介数中心性
        bet = nx.betweenness_centrality(G) if G.number_of_nodes() > 2 else {n:0 for n in G.nodes()}
        # PageRank
        pr = nx.pagerank(G) if G.number_of_nodes() > 0 else {}
        
        for node in G.nodes():
            results.append({
                "node": node,
                "degree_centrality": round(deg.get(node, 0), 4),
                "betweenness": round(bet.get(node, 0), 4),
                "pagerank": round(pr.get(node, 0), 4),
                "in_amount": sum(G.edges[u, node].get("amount", 0) for u in G.predecessors(node)),
                "out_amount": sum(G.edges[node, v].get("amount", 0) for v in G.successors(node)),
            })
        
        return sorted(results, key=lambda x: x["pagerank"], reverse=True)[:top_n]
    
    # ---- 供应商关联分析（围标串标检测）----
    def build_supplier_graph(self, bid_data: List[Dict]) -> nx.DiGraph:
        """
        bid_data: [{project, bidder, amount, ip, ...}]
        构建供应商-项目-IP的多维关联网络
        """
        G = nx.Graph()
        
        # 按项目分组
        project_bidders = {}
        project_ips = {}
        for b in bid_data:
            proj = b["project"]
            bidder = b["bidder"]
            ip = b.get("ip", "")
            
            if proj not in project_bidders:
                project_bidders[proj] = set()
                project_ips[proj] = set()
            project_bidders[proj].add(bidder)
            if ip:
                project_ips[proj].add(ip)
        
        # 添加边：同项目的供应商之间有潜在关联
        for proj, bidders in project_bidders.items():
            bidders_list = list(bidders)
            for i in range(len(bidders_list)):
                for j in range(i+1, len(bidders_list)):
                    G.add_edge(bidders_list[i], bidders_list[j], relation="co_bid", project=proj)
        
        # IP关联
        bidder_ips = {}
        for b in bid_data:
            ip = b.get("ip", "")
            if ip:
                if ip not in bidder_ips:
                    bidder_ips[ip] = set()
                bidder_ips[ip].add(b["bidder"])
        
        for ip, bidders in bidder_ips.items():
            if len(bidders) > 1:
                bidders_list = list(bidders)
                for i in range(len(bidders_list)):
                    for j in range(i+1, len(bidders_list)):
                        if G.has_edge(bidders_list[i], bidders_list[j]):
                            G[bidders_list[i]][bidders_list[j]]["same_ip"] = True
                        else:
                            G.add_edge(bidders_list[i], bidders_list[j], relation="same_ip", ip=ip)
        
        return G
    
    def find_bid_cartels(self, G: nx.Graph = None, min_clique_size: int = 3) -> List[List[str]]:
        """发现围标团伙（完全子图 = 两两同投过标）"""
        G = G or self.graph
        cliques = list(nx.find_cliques(G))
        return [c for c in cliques if len(c) >= min_clique_size]
    
    # ---- 股权穿透 ----
    @staticmethod
    def equity_penetration(shareholders: List[Dict], target_company: str, max_depth: int = 5) -> Dict:
        """
        shareholders: [{company, shareholder, ratio}, ...]
        向上追溯实际控制人
        """
        # 构建股权树
        edges = {}
        for s in shareholders:
            edges.setdefault(s["company"], []).append(s)
        
        def trace(company, depth=0, path=None):
            if path is None:
                path = []
            if depth >= max_depth:
                return {"company": company, "depth": depth, "path": path, "status": "max_depth_reached"}
            
            if company not in edges:
                return {"company": company, "depth": depth, "path": path, "status": "ultimate"}
            
            children = []
            for s in edges[company]:
                child_path = path + [company]
                children.append({
                    "shareholder": s["shareholder"],
                    "ratio": s.get("ratio", 0),
                    "trace": trace(s["shareholder"], depth+1, child_path)
                })
            return {"company": company, "depth": depth, "path": path, "children": children}
        
        return trace(target_company)
    
    # ---- 导出为可视化格式 ----
    def export_for_vis(self, G: nx.Graph = None) -> Dict:
        """导出为pyvis/ECharts可用的JSON"""
        G = G or self.graph
        nodes = [{"id": n, "label": str(n), "degree": G.degree(n)} for n in G.nodes()]
        edges = [{"from": u, "to": v, **d} for u, v, d in G.edges(data=True)]
        return {"nodes": nodes, "edges": edges}


class TextMiner:
    """文本挖掘 — 词频/共现/热点分析"""
    
    def __init__(self):
        try:
            import jieba
            self.jieba = jieba
        except ImportError:
            self.jieba = None
    
    # 审计停用词
    STOP_WORDS = set("的了一是在有和就都不上也到个之以为及等对所把被这与而能但让要从其因可以后没来说去".split())
    
    def segment(self, text: str) -> List[str]:
        """中文分词"""
        if self.jieba:
            words = self.jieba.cut(text)
            return [w for w in words if len(w.strip()) > 1 and w.strip() not in self.STOP_WORDS]
        # 降级：按标点切分
        import re
        return [w for w in re.split(r"[，。；！？、\s]+", text) if len(w) > 1]
    
    def word_frequency(self, texts: List[str], top_n: int = 30) -> List[Tuple[str, int]]:
        """词频统计"""
        counter = Counter()
        for text in texts:
            counter.update(self.segment(text))
        return counter.most_common(top_n)
    
    def co_occurrence(self, texts: List[str], target_words: List[str], window: int = 10) -> Dict[str, List[Tuple[str, int]]]:
        """共词分析"""
        co_count = {w: Counter() for w in target_words}
        for text in texts:
            words = self.segment(text)
            for i, w in enumerate(words):
                if w in target_words:
                    start = max(0, i - window)
                    end = min(len(words), i + window + 1)
                    context = words[start:i] + words[i+1:end]
                    co_count[w].update(context)
        return {w: c.most_common(15) for w, c in co_count.items()}
    
    def hot_spot_analysis(self, texts: List[Dict[str, str]]) -> List[Dict]:
        """热点分析：按时间/来源/主题聚合"""
        counter = Counter()
        for t in texts:
            words = self.segment(t.get("content", ""))
            counter.update(words)
        
        # 构造TF-IDF近似权重
        total = sum(counter.values())
        results = []
        for word, count in counter.most_common(50):
            results.append({
                "word": word,
                "count": count,
                "weight": round(count / total, 6) if total > 0 else 0,
            })
        return results
    
    def anomaly_text_detection(self, texts: List[str]) -> List[Dict]:
        """异常文本检测 — 查找与大多数文本差异较大的文档"""
        if len(texts) < 3:
            return []
        
        # 简单方法：计算每个文本的词频向量与平均向量的余弦距离
        all_words = set()
        for t in texts:
            all_words.update(self.segment(t))
        
        vectors = []
        for t in texts:
            words = self.segment(t)
            vec = {w: words.count(w) for w in all_words}
            vectors.append(vec)
        
        anomalies = []
        for i, vec in enumerate(vectors):
            # 计算与所有其他文本的相似度
            sims = []
            for j, v2 in enumerate(vectors):
                if i == j:
                    continue
                # 余弦相似度
                dot = sum(vec.get(k, 0) * v2.get(k, 0) for k in all_words)
                norm1 = math.sqrt(sum(x*x for x in vec.values()))
                norm2 = math.sqrt(sum(x*x for x in v2.values()))
                sim = dot / (norm1 * norm2) if norm1 * norm2 > 0 else 0
                sims.append(sim)
            
            avg_sim = sum(sims) / len(sims) if sims else 0
            if avg_sim < 0.3:  # 低于平均相似度30%
                anomalies.append({
                    "index": i,
                    "avg_similarity": round(avg_sim, 4),
                    "preview": texts[i][:100]
                })
        
        return sorted(anomalies, key=lambda x: x["avg_similarity"])


class VisualizationHelper:
    """可视化辅助 — 生成ECharts配置"""
    
    @staticmethod
    def bar_chart(data: Dict[str, float], title: str = "") -> Dict:
        """柱状图配置"""
        return {
            "title": {"text": title},
            "tooltip": {},
            "xAxis": {"data": list(data.keys()), "axisLabel": {"rotate": 45}},
            "yAxis": {},
            "series": [{"type": "bar", "data": list(data.values())}],
        }
    
    @staticmethod
    def pie_chart(data: Dict[str, float], title: str = "") -> Dict:
        """饼图配置"""
        items = [{"name": k, "value": v} for k, v in data.items()]
        return {
            "title": {"text": title},
            "tooltip": {"trigger": "item"},
            "series": [{"type": "pie", "data": items, "radius": "60%"}],
        }
    
    @staticmethod
    def sankey_diagram(nodes: List[str], links: List[Dict], title: str = "") -> Dict:
        """桑基图 — 资金流向"""
        node_map = {n: i for i, n in enumerate(nodes)}
        return {
            "title": {"text": title},
            "series": [{
                "type": "sankey",
                "data": [{"name": n} for n in nodes],
                "links": [{"source": l["from"], "target": l["to"], "value": l.get("value", 1)} for l in links],
            }]
        }
    
    @staticmethod
    def network_graph(graph_data: Dict, title: str = "") -> Dict:
        """关系网络图"""
        return {
            "title": {"text": title},
            "series": [{
                "type": "graph",
                "layout": "force",
                "data": graph_data.get("nodes", []),
                "links": graph_data.get("edges", []),
                "roam": True,
                "label": {"show": True},
                "force": {"repulsion": 500},
            }]
        }
    
    @staticmethod
    def treemap(data: List[Dict], title: str = "") -> Dict:
        """矩形树图 — 数据资源目录"""
        return {
            "title": {"text": title},
            "series": [{
                "type": "treemap",
                "data": [{"name": d["name"], "value": d.get("value", 1)} for d in data],
            }]
        }
    
    @staticmethod
    def heatmap(matrix: List[List[float]], x_labels: List[str], y_labels: List[str], title: str = "") -> Dict:
        """热力图"""
        data = []
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                data.append([j, i, val])
        return {
            "title": {"text": title},
            "xAxis": {"data": x_labels, "axisLabel": {"rotate": 45}},
            "yAxis": {"data": y_labels},
            "series": [{"type": "heatmap", "data": data}],
        }
