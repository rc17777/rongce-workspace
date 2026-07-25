#!/usr/bin/env python3
"""
业务场景5：关联关系/资金链路分析 算法升级
新增 Fraudar 稠密子图挖掘 + 环路检测 + 社区发现
替换：PageRank(单维度) → Fraudar(二部图) + 环路检测 + Louvain社区
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import networkx as nx
import warnings
warnings.filterwarnings('ignore')


@dataclass
class FraudSubgraph:
    """Fraudar发现的稠密子图"""
    nodes: Set[str]           # 嫌疑节点集合
    density: float            # 子图密度
    suspicious_score: float   # 可疑度评分
    node_types: Dict[str, str]  # 节点类型


class FrauDAR:
    """
    Fraudar 稠密子图挖掘
    
    在二部图（如：供应商⇄项目）中发现异常稠密的子结构。
    数学原理：最大化子图的"欺诈度" = 边密度 × log(节点数)
    
    替代 PageRank：PageRank只能告诉你"谁重要"，Fraudar告诉你"谁和谁抱团"。
    
    使用：
    >>> G = nx.bipartite.from_edgelist([
    ...     ('供应商A', '项目1'), ('供应商A', '项目2'),
    ...     ('供应商B', '项目1'), ('供应商B', '项目2'),
    ... ])
    >>> fraudar = FrauDAR()
    >>> result = fraudar.detect(G, left_nodes=['供应商A','供应商B'])
    """
    
    def __init__(self, min_density: float = 0.5, min_size: int = 3):
        self.min_density = min_density
        self.min_size = min_size
    
    def detect(self, G: nx.Graph, 
               left_nodes: List[str]) -> List[FraudSubgraph]:
        """
        Fraudar核心算法
        
        贪心删除低度节点 → 迭代优化子图密度
        """
        subgraphs = []
        working_G = G.subgraph(left_nodes + list(set(G.nodes()) - set(left_nodes))).copy()
        
        while len(working_G) > self.min_size:
            # 计算当前密度和可疑度
            density = nx.density(working_G)
            n_nodes = len(working_G)
            sus_score = density * np.log(n_nodes + 1)
            
            if density >= self.min_density and n_nodes >= self.min_size:
                # 分类节点
                node_types = {}
                for n in working_G.nodes():
                    node_types[n] = '供应商' if n in left_nodes else '项目'
                
                subgraphs.append(FraudSubgraph(
                    nodes=set(working_G.nodes()),
                    density=density,
                    suspicious_score=sus_score,
                    node_types=node_types
                ))
            
            # 贪心删除度数最低的节点
            degrees = dict(working_G.degree())
            if not degrees:
                break
            min_node = min(degrees, key=degrees.get)
            working_G.remove_node(min_node)
        
        # 去重：保留评分最高的不重叠子图
        return self._deduplicate(subgraphs)
    
    def _deduplicate(self, subgraphs: List[FraudSubgraph]) -> List[FraudSubgraph]:
        """去重：保留评分最高，去掉被包含的子图"""
        if not subgraphs:
            return []
        sorted_subs = sorted(subgraphs, key=lambda s: s.suspicious_score, reverse=True)
        kept = []
        used_nodes = set()
        for sub in sorted_subs:
            if len(sub.nodes & used_nodes) < len(sub.nodes) * 0.7:  # 重叠<70%则保留
                kept.append(sub)
                used_nodes.update(sub.nodes)
        return kept
    
    def analyze(self, subgraph: FraudSubgraph) -> Dict:
        """子图详细分析"""
        suppliers = [n for n, t in subgraph.node_types.items() if t == '供应商']
        projects = [n for n, t in subgraph.node_types.items() if t == '项目']
        
        return {
            'suppliers': suppliers,
            'projects': projects,
            'density': round(subgraph.density, 3),
            'suspicious_score': round(subgraph.suspicious_score, 3),
            'interpretation': (
                f"{len(suppliers)}家供应商集中在{len(projects)}个项目上，"
                f"形成异常稠密的关联结构（密度{subgraph.density:.3f}）。"
                f"正常招投标市场中，n×m的二部图密度通常<0.2。"
                f"此子图密度超阈值，建议排查围标串标可能性。"
            ),
            'evidence_level': '🔴 铁证' if subgraph.density > 0.7 else '🟡 强信号' if subgraph.density > 0.4 else '🟢 弱信号'
        }


class CycleDetector:
    """
    资金链路环路检测
    
    刑法第201条的经典场景：A→B→C→A 的资金循环
    """
    
    @staticmethod
    def find_cycles(G: nx.DiGraph, max_length: int = 5) -> List[List[str]]:
        """检测有向图中的环路"""
        cycles = []
        try:
            simple_cycles = list(nx.simple_cycles(G))
            for cycle in simple_cycles:
                if len(cycle) <= max_length:
                    cycles.append(cycle)
        except:
            # Fallback: DFS
            cycles = CycleDetector._dfs_find_cycles(G, max_length)
        
        return sorted(cycles, key=len)
    
    @staticmethod
    def _dfs_find_cycles(G: nx.DiGraph, max_length: int) -> List[List[str]]:
        """DFS环路检测"""
        cycles = []
        visited = set()
        
        def dfs(node, start, path, depth):
            if depth > max_length:
                return
            path.append(node)
            for neighbor in G.successors(node):
                if neighbor == start and len(path) >= 2:
                    cycles.append(path + [start])
                elif neighbor not in path and neighbor not in visited:
                    dfs(neighbor, start, path[:], depth + 1)
        
        for node in G.nodes():
            dfs(node, node, [], 0)
            visited.add(node)
        
        return cycles
    
    @staticmethod
    def shortest_path(G: nx.DiGraph, source: str, target: str) -> Dict:
        """最短资金路径"""
        try:
            path = nx.shortest_path(G, source=source, target=target, weight='amount')
            return {'path': path, 'length': len(path) - 1, 'found': True}
        except nx.NetworkXNoPath:
            return {'path': [], 'length': 0, 'found': False}
    
    @staticmethod
    def flow_summary(G: nx.DiGraph, cycle: List[str]) -> Dict:
        """环路摘要"""
        amounts = []
        for i in range(len(cycle) - 1):
            edge_data = G.get_edge_data(cycle[i], cycle[i+1])
            if edge_data and 'amount' in edge_data:
                amounts.append(edge_data['amount'])
        
        return {
            'cycle': cycle,
            'hop_count': len(cycle) - 1,
            'min_amount': min(amounts) if amounts else None,
            'max_amount': max(amounts) if amounts else None,
            'is_money_laundering_pattern': len(cycle) <= 4,  # 短环路=高嫌疑
        }


class GraphAnalyzer:
    """
    图谱综合分析引擎
    
    组合拳：
    1. Fraudar → 二部图稠密子图（围标串标）
    2. Louvain社区发现 → 利益小团体
    3. 环路检测 → 资金回流
    4. 最短路径 → 资金流向追踪
    5. PageRank → 核心节点识别（保留）
    """
    
    def __init__(self):
        self.G = nx.Graph()
        self.DiG = nx.DiGraph()
    
    def build_from_edgelist(self, edges: List[Tuple[str, str]], 
                            directed: bool = False,
                            edge_attrs: Dict = None):
        """从边列表构建图谱"""
        if directed:
            self.DiG.add_edges_from(edges)
            if edge_attrs:
                for u, v, data in edge_attrs.get('edges', []):
                    self.DiG[u][v].update(data)
        else:
            self.G.add_edges_from(edges)
    
    def analyze_supplier_project(self, project_supplier_edges: List[Tuple[str, str]]) -> Dict:
        """
        供应商-项目二部图分析
        
        Args:
            project_supplier_edges: [(supplier, project), ...]
        """
        G = nx.Graph()
        G.add_edges_from(project_supplier_edges)
        suppliers = list(set(e[0] for e in project_supplier_edges))
        
        # 1. Fraudar
        fraudar = FrauDAR()
        fraud_subgraphs = fraudar.detect(G, suppliers)
        
        # 2. Louvain社区
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G)
        except:
            partition = {n: 0 for n in G.nodes()}
        
        # 3. PageRank
        pr = nx.pagerank(G)
        
        # 4. 基础统计
        density = nx.density(G)
        avg_clustering = nx.average_clustering(G)
        
        return {
            'graph_stats': {
                'nodes': len(G.nodes()),
                'edges': len(G.edges()),
                'density': round(density, 4),
                'avg_clustering': round(avg_clustering, 4),
            },
            'fraud_subgraphs': [
                {
                    'nodes': list(sub.nodes),
                    'density': sub.density,
                    'score': round(sub.suspicious_score, 3),
                    'interpretation': fraudar.analyze(sub)['interpretation'],
                    'evidence_level': fraudar.analyze(sub)['evidence_level']
                }
                for sub in fraud_subgraphs[:5]
            ],
            'communities': len(set(partition.values())),
            'top_influencers': sorted(pr.items(), key=lambda x: x[1], reverse=True)[:10],
        }
    
    def analyze_fund_flow(self, 
                          transactions: List[Tuple[str, str, float]]) -> Dict:
        """
        资金流向分析
        
        Args:
            transactions: [(from_account, to_account, amount), ...]
        """
        G = nx.DiGraph()
        for src, dst, amt in transactions:
            G.add_edge(src, dst, amount=amt)
        
        # 1. 环路检测
        cycles = CycleDetector.find_cycles(G, max_length=5)
        
        # 2. 关键路径
        top_nodes = sorted(dict(G.out_degree()).items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_transactions': len(transactions),
            'total_nodes': len(G.nodes()),
            'cycles_found': len(cycles),
            'suspicious_cycles': [
                CycleDetector.flow_summary(G, cycle)
                for cycle in cycles[:10]
            ],
            'top_outflow_nodes': top_nodes,
        }


# ===== CLI Demo =====
if __name__ == '__main__':
    print("=" * 70)
    print("  关联图谱分析引擎 演示")
    print("=" * 70)
    
    # 模拟供应商-项目二部图（注入串标嫌疑）
    edges = [
        # 正常
        ('供应商A', '项目1'), ('供应商B', '项目2'), ('供应商C', '项目3'),
        ('供应商A', '项目4'), ('供应商D', '项目5'), ('供应商E', '项目6'),
        # 🔴 嫌疑：3家供应商+3项目形成异常稠密子图
        ('供应商X', '项目α'), ('供应商X', '项目β'), ('供应商X', '项目γ'),
        ('供应商Y', '项目α'), ('供应商Y', '项目β'), ('供应商Y', '项目γ'),
        ('供应商Z', '项目α'), ('供应商Z', '项目β'), ('供应商Z', '项目γ'),
    ]
    
    analyzer = GraphAnalyzer()
    result = analyzer.analyze_supplier_project(edges)
    
    print(f"\n【图统计】节点{result['graph_stats']['nodes']}, 边{result['graph_stats']['edges']}")
    print(f"密度: {result['graph_stats']['density']}, 聚类系数: {result['graph_stats']['avg_clustering']}")
    
    print(f"\n【Fraudar 稠密子图】发现 {len(result['fraud_subgraphs'])} 个异常子图:")
    for i, sub in enumerate(result['fraud_subgraphs'], 1):
        print(f"\n  {i}. {sub['evidence_level']}")
        print(f"    供应商: {[n for n in sub['nodes'] if '供应商' in n]}")
        print(f"    项目: {[n for n in sub['nodes'] if '项目' in n]}")
        print(f"    密度: {sub['density']:.3f} (正常<0.2)")
        print(f"    {sub['interpretation'][:100]}...")
    
    print(f"\n【影响力Top3】")
    for node, score in result['top_influencers'][:3]:
        print(f"  {node}: PageRank={score:.4f}")
    
    # 资金环路测试
    print(f"\n【资金链路检测】")
    txns = [
        ('账户A', '账户B', 100000),
        ('账户B', '账户C', 95000),
        ('账户C', '账户A', 90000),  # ← 环路！
        ('账户D', '账户E', 50000),
    ]
    flow = analyzer.analyze_fund_flow(txns)
    print(f"  总交易: {flow['total_transactions']}, 发现环路: {flow['cycles_found']}")
    if flow['suspicious_cycles']:
        for c in flow['suspicious_cycles']:
            print(f"  🔴 疑似资金回流: {' → '.join(c['cycle'])} ({c['hop_count']}跳)")
