# -*- coding: utf-8 -*-
"""
融策审计知识图谱 - 查询和可视化接口
提供图谱查询、分析和可视化功能
"""

import json
import os
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入模块
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import EntityType, RelationType, KnowledgeGraphSchema
from graph_builder import GraphBuilder, Neo4jGraphBuilder, NetworkXGraphBuilder

# 尝试导入可视化库
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("可视化库未安装，将使用文本输出")


class GraphQuery:
    """图谱查询器"""
    
    def __init__(self, builder: GraphBuilder):
        self.builder = builder
        self.schema = KnowledgeGraphSchema()
    
    # ========== 基础查询 ==========
    
    def find_entity(self, name: str, entity_type: EntityType = None) -> List[Dict]:
        """查找实体"""
        if self.builder.backend == "neo4j":
            if entity_type:
                schema = self.schema.get_entity_schema(entity_type)
                cypher = f"""
                MATCH (n:{schema.label} {{name: $name}})
                RETURN n, labels(n) as labels
                """
            else:
                cypher = """
                MATCH (n {name: $name})
                RETURN n, labels(n) as labels
                """
            return self.builder.query(cypher, {"name": name})
        else:
            # NetworkX查询
            results = []
            for node, data in self.builder.builder.graph.nodes(data=True):
                if data.get('name') == name:
                    if entity_type is None or data.get('type_code') == entity_type.name:
                        results.append({"node": node, "data": data})
            return results
    
    def find_neighbors(self, name: str, depth: int = 1, 
                       relation_types: List[RelationType] = None) -> Dict:
        """查找邻居"""
        if self.builder.backend == "neo4j":
            rel_filter = ""
            if relation_types:
                rel_names = [self.schema.get_relation_schema(rt).type_name for rt in relation_types]
                rel_filter = f"AND type(r) IN {json.dumps(rel_names)}"
            
            cypher = f"""
            MATCH path = (n {{name: $name}})-[r*1..{depth}]-(m)
            WHERE 1=1 {rel_filter}
            RETURN path
            LIMIT 100
            """
            return self.builder.query(cypher, {"name": name})
        else:
            # NetworkX查询
            node_id = None
            for node, data in self.builder.builder.graph.nodes(data=True):
                if data.get('name') == name:
                    node_id = node
                    break
            
            if not node_id:
                return {"nodes": [], "edges": []}
            
            return self.builder.builder.get_neighbors(node_id, depth)
    
    def find_path(self, from_name: str, to_name: str, 
                  max_depth: int = 5) -> List[Dict]:
        """查找路径"""
        if self.builder.backend == "neo4j":
            cypher = f"""
            MATCH path = shortestPath(
                (a {{name: $from_name}})-[*1..{max_depth}]-(b {{name: $to_name}})
            )
            RETURN path
            """
            return self.builder.query(cypher, {"from_name": from_name, "to_name": to_name})
        else:
            # NetworkX查询
            from_id = None
            to_id = None
            
            for node, data in self.builder.builder.graph.nodes(data=True):
                if data.get('name') == from_name:
                    from_id = node
                if data.get('name') == to_name:
                    to_id = node
            
            if not from_id or not to_id:
                return []
            
            paths = self.builder.builder.find_paths(from_id, to_id, max_depth)
            return [{"path": p} for p in paths]
    
    # ========== 审计专用查询 ==========
    
    def find_related_companies(self, company_name: str, depth: int = 2) -> List[Dict]:
        """查找关联公司（围标串标分析）"""
        if self.builder.backend == "neo4j":
            cypher = f"""
            MATCH path = (c:Company {{name: $name}})-[r*1..{depth}]-(related:Company)
            RETURN DISTINCT related.name as company, 
                   related.reg_capital as capital,
                   length(path) as distance
            ORDER BY distance
            """
            return self.builder.query(cypher, {"name": company_name})
        else:
            # NetworkX实现
            node_id = None
            for node, data in self.builder.builder.graph.nodes(data=True):
                if data.get('name') == company_name and data.get('label') == 'Company':
                    node_id = node
                    break
            
            if not node_id:
                return []
            
            results = []
            neighbors = self.builder.builder.get_neighbors(node_id, depth)
            for n in neighbors.get("nodes", []):
                data = self.builder.builder.graph.nodes[n]
                if data.get('label') == 'Company':
                    results.append({
                        "company": data.get('name'),
                        "capital": data.get('reg_capital'),
                    })
            return results
    
    def find_equity_chain(self, company_name: str, direction: str = "up") -> List[Dict]:
        """股权穿透分析"""
        if self.builder.backend == "neo4j":
            if direction == "up":
                # 向上穿透（找股东）
                cypher = """
                MATCH path = (c:Company {name: $name})<-[:HOLD|INVEST|CONTROL*1..5]-(holder)
                RETURN path
                """
            else:
                # 向下穿透（找子公司）
                cypher = """
                MATCH path = (c:Company {name: $name})-[:HOLD|INVEST|CONTROL*1..5]->(subsidiary)
                RETURN path
                """
            return self.builder.query(cypher, {"name": company_name})
        else:
            # NetworkX实现
            results = []
            node_id = None
            for node, data in self.builder.builder.graph.nodes(data=True):
                if data.get('name') == company_name and data.get('label') == 'Company':
                    node_id = node
                    break
            
            if not node_id:
                return []
            
            if direction == "up":
                # 找前驱节点
                for pred in self.builder.builder.graph.predecessors(node_id):
                    edge_data = self.builder.builder.graph.get_edge_data(pred, node_id)
                    if edge_data and edge_data.get('type_name') in ['HOLD', 'INVEST', 'CONTROL']:
                        pred_data = self.builder.builder.graph.nodes[pred]
                        results.append({
                            "holder": pred_data.get('name'),
                            "relation": edge_data.get('type_name'),
                            "ratio": edge_data.get('ratio'),
                        })
            else:
                # 找后继节点
                for succ in self.builder.builder.graph.successors(node_id):
                    edge_data = self.builder.builder.graph.get_edge_data(node_id, succ)
                    if edge_data and edge_data.get('type_name') in ['HOLD', 'INVEST', 'CONTROL']:
                        succ_data = self.builder.builder.graph.nodes[succ]
                        results.append({
                            "subsidiary": succ_data.get('name'),
                            "relation": edge_data.get('type_name'),
                            "ratio": edge_data.get('ratio'),
                        })
            
            return results
    
    def find_collusion_risk(self, project_name: str = None) -> List[Dict]:
        """围标串标风险识别"""
        if self.builder.backend == "neo4j":
            if project_name:
                cypher = """
                MATCH (p:AuditProject {name: $project})
                MATCH (c1:Company)-[:BID_FOR]->(p)<-[:BID_FOR]-(c2:Company)
                WHERE c1 <> c2
                MATCH path = (c1)-[*1..3]-(c2)
                RETURN c1.name as bidder1, c2.name as bidder2, 
                       length(path) as connection_depth
                """
                return self.builder.query(cypher, {"project": project_name})
            else:
                cypher = """
                MATCH (c1:Company)-[:BID_FOR]->(p:AuditProject)<-[:BID_FOR]-(c2:Company)
                WHERE c1 <> c2
                MATCH path = (c1)-[*1..3]-(c2)
                RETURN c1.name as bidder1, c2.name as bidder2, 
                       p.name as project, length(path) as connection_depth
                """
                return self.builder.query(cypher)
        else:
            # NetworkX实现 - 查找同一项目的投标人之间的关联
            results = []
            graph = self.builder.builder.graph
            
            # 找到所有项目节点
            project_nodes = [n for n, d in graph.nodes(data=True) 
                           if d.get('label') == 'AuditProject']
            
            for proj in project_nodes:
                if project_name and graph.nodes[proj].get('name') != project_name:
                    continue
                
                # 找到投标该项目的公司
                bidders = []
                for pred in graph.predecessors(proj):
                    edge_data = graph.get_edge_data(pred, proj)
                    if edge_data and edge_data.get('type_name') == 'BID_FOR':
                        bidders.append(pred)
                
                # 检查投标人之间的关联
                for i in range(len(bidders)):
                    for j in range(i + 1, len(bidders)):
                        try:
                            paths = list(nx.all_simple_paths(graph, bidders[i], bidders[j], cutoff=3))
                            if paths:
                                results.append({
                                    "bidder1": graph.nodes[bidders[i]].get('name'),
                                    "bidder2": graph.nodes[bidders[j]].get('name'),
                                    "project": graph.nodes[proj].get('name'),
                                    "connection_depth": len(paths[0]) - 1,
                                })
                        except:
                            pass
            
            return results
    
    def find_risk_propagation(self, risk_name: str, depth: int = 3) -> List[Dict]:
        """风险传导分析"""
        if self.builder.backend == "neo4j":
            cypher = f"""
            MATCH path = (r:Risk {{name: $name}})-[:CAUSE*1..{depth}]->(affected)
            RETURN affected.name as affected_entity, 
                   labels(affected)[0] as entity_type,
                   length(path) as propagation_depth
            """
            return self.builder.query(cypher, {"name": risk_name})
        else:
            # NetworkX实现
            results = []
            node_id = None
            for node, data in self.builder.builder.graph.nodes(data=True):
                if data.get('name') == risk_name and data.get('label') == 'Risk':
                    node_id = node
                    break
            
            if not node_id:
                return []
            
            # BFS查找风险传导
            visited = {node_id}
            queue = [(node_id, 0)]
            
            while queue:
                current, level = queue.pop(0)
                
                if level >= depth:
                    continue
                
                for succ in self.builder.builder.graph.successors(current):
                    edge_data = self.builder.builder.graph.get_edge_data(current, succ)
                    if edge_data and edge_data.get('type_name') == 'CAUSE':
                        if succ not in visited:
                            visited.add(succ)
                            queue.append((succ, level + 1))
                            succ_data = self.builder.builder.graph.nodes[succ]
                            results.append({
                                "affected_entity": succ_data.get('name'),
                                "entity_type": succ_data.get('label'),
                                "propagation_depth": level + 1,
                            })
            
            return results
    
    # ========== 统计分析 ==========
    
    def get_centrality_analysis(self) -> Dict:
        """中心度分析"""
        if self.builder.backend == "networkx":
            graph = self.builder.builder.graph
            
            # 度中心性
            degree_centrality = nx.degree_centrality(graph)
            
            # 中介中心性
            betweenness_centrality = nx.betweenness_centrality(graph)
            
            # 接近中心性
            try:
                closeness_centrality = nx.closeness_centrality(graph)
            except:
                closeness_centrality = {}
            
            # 排序
            top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "degree_centrality": [
                    {"node": node, "score": score, "name": graph.nodes[node].get('name', node)}
                    for node, score in top_degree
                ],
                "betweenness_centrality": [
                    {"node": node, "score": score, "name": graph.nodes[node].get('name', node)}
                    for node, score in top_betweenness
                ],
            }
        else:
            # Neo4j使用GDS插件
            logger.warning("Neo4j中心度分析需要GDS插件")
            return {}
    
    def get_community_detection(self) -> List[Dict]:
        """社区发现"""
        if self.builder.backend == "networkx":
            graph = self.builder.builder.graph
            
            try:
                # 转换为无向图进行社区发现
                undirected = graph.to_undirected()
                communities = nx.community.greedy_modularity_communities(undirected)
                
                results = []
                for i, community in enumerate(communities):
                    members = []
                    for node in community:
                        data = graph.nodes[node]
                        members.append({
                            "name": data.get('name', node),
                            "type": data.get('label', 'Unknown'),
                        })
                    
                    results.append({
                        "community_id": i,
                        "size": len(community),
                        "members": members,
                    })
                
                return results
            except Exception as e:
                logger.error(f"社区发现失败: {e}")
                return []
        else:
            logger.warning("Neo4j社区发现需要GDS插件")
            return []


class GraphVisualizer:
    """图谱可视化器"""
    
    def __init__(self, builder: GraphBuilder):
        self.builder = builder
        self.schema = KnowledgeGraphSchema()
    
    def visualize_subgraph(self, center_node: str, depth: int = 2, 
                          output_path: str = "subgraph.png"):
        """可视化子图"""
        if not VISUALIZATION_AVAILABLE:
            logger.error("可视化库未安装")
            return
        
        if self.builder.backend == "networkx":
            graph = self.builder.builder.graph
            
            # 找到中心节点
            center_id = None
            for node, data in graph.nodes(data=True):
                if data.get('name') == center_node:
                    center_id = node
                    break
            
            if not center_id:
                logger.error(f"未找到节点: {center_node}")
                return
            
            # 提取子图
            neighbors = self.builder.builder.get_neighbors(center_id, depth)
            nodes_to_draw = [center_id] + neighbors.get("nodes", [])
            
            subgraph = graph.subgraph(nodes_to_draw)
            
            # 绘制
            plt.figure(figsize=(16, 12))
            pos = nx.spring_layout(subgraph, k=2, iterations=50)
            
            # 节点颜色
            node_colors = []
            for node in subgraph.nodes():
                label = subgraph.nodes[node].get('label', 'Unknown')
                color_map = {
                    'Company': '#0A1F3F',
                    'GovDept': '#1A5C6E',
                    'Person': '#C5955C',
                    'AuditProject': '#F5F2EC',
                    'Risk': '#E74C3C',
                    'Contract': '#3498DB',
                    'Bid': '#2ECC71',
                }
                node_colors.append(color_map.get(label, '#95A5A6'))
            
            # 绘制节点
            nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, 
                                   node_size=2000, alpha=0.9)
            
            # 绘制边
            nx.draw_networkx_edges(subgraph, pos, edge_color='#C5955C', 
                                   width=1.5, alpha=0.7, arrows=True,
                                   arrowsize=15, arrowstyle='->')
            
            # 绘制标签
            labels = {node: subgraph.nodes[node].get('name', node)[:10] 
                     for node in subgraph.nodes()}
            nx.draw_networkx_labels(subgraph, pos, labels, font_size=8, 
                                   font_color='white', font_weight='bold')
            
            plt.title(f"知识图谱子图: {center_node}", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"子图已保存到: {output_path}")
        else:
            logger.warning("Neo4j可视化请使用Neo4j Browser")
    
    def visualize_equity_structure(self, company_name: str, 
                                   output_path: str = "equity_structure.png"):
        """可视化股权结构"""
        if not VISUALIZATION_AVAILABLE:
            logger.error("可视化库未安装")
            return
        
        if self.builder.backend == "networkx":
            graph = self.builder.builder.graph
            
            # 找到公司节点
            company_id = None
            for node, data in graph.nodes(data=True):
                if data.get('name') == company_name and data.get('label') == 'Company':
                    company_id = node
                    break
            
            if not company_id:
                logger.error(f"未找到公司: {company_name}")
                return
            
            # 收集股权关系节点
            nodes_to_draw = [company_id]
            edges_to_draw = []
            
            # 向上查找股东
            for pred in graph.predecessors(company_id):
                edge_data = graph.get_edge_data(pred, company_id)
                if edge_data and edge_data.get('type_name') in ['HOLD', 'INVEST', 'CONTROL']:
                    nodes_to_draw.append(pred)
                    edges_to_draw.append((pred, company_id, edge_data))
            
            # 向下查找子公司
            for succ in graph.successors(company_id):
                edge_data = graph.get_edge_data(company_id, succ)
                if edge_data and edge_data.get('type_name') in ['HOLD', 'INVEST', 'CONTROL']:
                    nodes_to_draw.append(succ)
                    edges_to_draw.append((company_id, succ, edge_data))
            
            # 绘制
            plt.figure(figsize=(14, 10))
            subgraph = graph.subgraph(nodes_to_draw)
            pos = nx.spring_layout(subgraph, k=3, iterations=50)
            
            # 节点颜色
            node_colors = []
            for node in subgraph.nodes():
                if node == company_id:
                    node_colors.append('#E74C3C')  # 目标公司红色
                else:
                    node_colors.append('#0A1F3F')  # 其他公司深蓝
            
            nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, 
                                   node_size=3000, alpha=0.9)
            
            # 绘制边
            for u, v, data in edges_to_draw:
                ratio = data.get('ratio', '')
                nx.draw_networkx_edges(subgraph, pos, edgelist=[(u, v)], 
                                       edge_color='#C5955C', width=2, 
                                       arrows=True, arrowsize=20)
                
                # 添加持股比例标签
                mid_x = (pos[u][0] + pos[v][0]) / 2
                mid_y = (pos[u][1] + pos[v][1]) / 2
                if ratio:
                    plt.text(mid_x, mid_y, f"{ratio}%", fontsize=10, 
                            ha='center', va='center',
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            labels = {node: subgraph.nodes[node].get('name', node)[:12] 
                     for node in subgraph.nodes()}
            nx.draw_networkx_labels(subgraph, pos, labels, font_size=9, 
                                   font_color='white', font_weight='bold')
            
            plt.title(f"股权结构图: {company_name}", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"股权结构图已保存到: {output_path}")
        else:
            logger.warning("Neo4j可视化请使用Neo4j Browser")
    
    def generate_report(self, output_path: str = "graph_report.html"):
        """生成HTML报告"""
        stats = self.builder.get_stats()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>融策审计知识图谱报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #0A1F3F; }}
        h2 {{ color: #1A5C6E; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #F5F2EC; padding: 20px; border-radius: 8px; min-width: 150px; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #0A1F3F; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background: #0A1F3F; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:nth-child(even) {{ background: #F5F2EC; }}
    </style>
</head>
<body>
    <h1>融策审计知识图谱报告</h1>
    
    <h2>图谱概览</h2>
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats.get('nodes', stats.get('节点数', 0))}</div>
            <div class="stat-label">节点数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.get('edges', stats.get('边数', 0))}</div>
            <div class="stat-label">关系数</div>
        </div>
    </div>
    
    <h2>节点类型分布</h2>
    <table>
        <tr><th>类型</th><th>数量</th></tr>
"""
        
        node_types = stats.get('node_types', {})
        for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
            html += f"<tr><td>{node_type}</td><td>{count}</td></tr>\n"
        
        html += """
    </table>
    
    <h2>关系类型分布</h2>
    <table>
        <tr><th>类型</th><th>数量</th></tr>
"""
        
        edge_types = stats.get('edge_types', {})
        for edge_type, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
            html += f"<tr><td>{edge_type}</td><td>{count}</td></tr>\n"
        
        html += """
    </table>
</body>
</html>
"""
        
        Path(output_path).write_text(html, encoding='utf-8')
        logger.info(f"HTML报告已保存到: {output_path}")


# ========== 统一接口 ==========
class KnowledgeGraphAPI:
    """知识图谱API统一接口"""
    
    def __init__(self, backend: str = "auto", **kwargs):
        self.builder = GraphBuilder(backend=backend, **kwargs)
        self.query_engine = GraphQuery(self.builder)
        self.visualizer = GraphVisualizer(self.builder)
    
    def build_from_documents(self, documents: List[str]) -> Dict:
        """从文档构建图谱"""
        return self.builder.build_from_documents(documents)
    
    def build_from_data(self, entities: List[ExtractedEntity], 
                       relations: List[ExtractedRelation]) -> Dict:
        """从数据构建图谱"""
        self.builder.build_from_entities_relations(entities, relations)
        return self.builder.get_stats()
    
    # 查询接口
    def find_entity(self, name: str, entity_type: EntityType = None) -> List[Dict]:
        return self.query_engine.find_entity(name, entity_type)
    
    def find_neighbors(self, name: str, depth: int = 1) -> Dict:
        return self.query_engine.find_neighbors(name, depth)
    
    def find_path(self, from_name: str, to_name: str, max_depth: int = 5) -> List[Dict]:
        return self.query_engine.find_path(from_name, to_name, max_depth)
    
    def find_related_companies(self, company_name: str, depth: int = 2) -> List[Dict]:
        return self.query_engine.find_related_companies(company_name, depth)
    
    def find_equity_chain(self, company_name: str, direction: str = "up") -> List[Dict]:
        return self.query_engine.find_equity_chain(company_name, direction)
    
    def find_collusion_risk(self, project_name: str = None) -> List[Dict]:
        return self.query_engine.find_collusion_risk(project_name)
    
    def find_risk_propagation(self, risk_name: str, depth: int = 3) -> List[Dict]:
        return self.query_engine.find_risk_propagation(risk_name, depth)
    
    # 分析接口
    def analyze_centrality(self) -> Dict:
        return self.query_engine.get_centrality_analysis()
    
    def detect_communities(self) -> List[Dict]:
        return self.query_engine.get_community_detection()
    
    # 可视化接口
    def visualize(self, center_node: str, depth: int = 2, output_path: str = "graph.png"):
        self.visualizer.visualize_subgraph(center_node, depth, output_path)
    
    def visualize_equity(self, company_name: str, output_path: str = "equity.png"):
        self.visualizer.visualize_equity_structure(company_name, output_path)
    
    def generate_report(self, output_path: str = "report.html"):
        self.visualizer.generate_report(output_path)
    
    # 导出接口
    def export(self, output_path: str, format: str = "json"):
        self.builder.export(output_path, format)
    
    def get_stats(self) -> Dict:
        return self.builder.get_stats()
    
    def close(self):
        self.builder.close()


# ========== 测试 ==========
if __name__ == "__main__":
    from entity_extractor import EntityExtractor
    from relation_extractor import RelationExtractor
    
    # 测试数据
    test_text = """
    关于XX市2023年度预算执行绩效评价项目的审计报告
    
    被审计单位：XX市财政局
    审计项目：2023年度预算执行绩效评价
    
    一、基本情况
    XX市城市建设投资有限公司（注册资本：50000万元）
    由XX市财政局控股，持股比例为100%。
    
    XX市交通发展集团有限公司（注册资本：30000万元）
    由XX市城市建设投资有限公司持有60%股权。
    
    二、审计发现
    1. XX市城市建设投资有限公司向XX建筑工程有限公司
       支付工程款8500万元；
    2. XX建筑工程有限公司中标"XX市2023年道路改造工程"，
       中标金额8500万元；
    3. 张三为XX市城市建设投资有限公司法定代表人；
    4. 李四担任XX建筑工程有限公司董事；
    5. XX市城市建设投资有限公司为XX市交通发展集团有限公司
       提供担保，担保金额5000万元；
    6. 预算编制不规范导致资金使用效率低下。
    """
    
    # 抽取实体和关系
    entity_extractor = EntityExtractor()
    relation_extractor = RelationExtractor()
    
    entities = entity_extractor.extract_from_text(test_text, source="测试文档")
    relations = relation_extractor.extract_relations_from_text(test_text, entities, source="测试文档")
    
    # 创建API
    api = KnowledgeGraphAPI(backend="networkx")
    
    # 构建图谱
    stats = api.build_from_data(entities, relations)
    print(f"\n图谱构建完成:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    # 查询测试
    print("\n查询XX市城市建设投资有限公司的邻居:")
    neighbors = api.find_neighbors("XX市城市建设投资有限公司", depth=2)
    print(json.dumps(neighbors, ensure_ascii=False, indent=2))
    
    # 股权穿透
    print("\n股权穿透分析:")
    equity = api.find_equity_chain("XX市城市建设投资有限公司", direction="up")
    print(json.dumps(equity, ensure_ascii=False, indent=2))
    
    # 生成报告
    api.generate_report("test_report.html")
    
    # 可视化
    if VISUALIZATION_AVAILABLE:
        api.visualize("XX市城市建设投资有限公司", depth=2, output_path="test_graph.png")
        api.visualize_equity("XX市城市建设投资有限公司", output_path="test_equity.png")
    
    api.close()
