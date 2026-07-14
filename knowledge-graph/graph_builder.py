# -*- coding: utf-8 -*-
"""
融策审计知识图谱 - 图数据库构建模块
基于Neo4j构建知识图谱
"""

import json
import os
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入Schema和抽取模块
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import EntityType, RelationType, KnowledgeGraphSchema, ALL_ENTITIES, RELATION_SCHEMAS
from entity_extractor import ExtractedEntity, EntityExtractor
from relation_extractor import ExtractedRelation, RelationExtractor

# 尝试导入Neo4j
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j驱动未安装，将使用NetworkX作为替代")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX未安装")


class Neo4jGraphBuilder:
    """Neo4j图构建器"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", 
                 password: str = "password"):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.schema = KnowledgeGraphSchema()
        
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(uri, auth=(username, password))
                logger.info(f"已连接到Neo4j: {uri}")
            except Exception as e:
                logger.error(f"连接Neo4j失败: {e}")
                self.driver = None
        else:
            logger.error("Neo4j驱动不可用")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("已关闭Neo4j连接")
    
    def create_indexes(self):
        """创建索引"""
        if not self.driver:
            logger.error("Neo4j未连接")
            return
        
        with self.driver.session() as session:
            for entity_type, entity_schema in ALL_ENTITIES.items():
                for index_field in entity_schema.indexes:
                    try:
                        cypher = f"""
                        CREATE INDEX {entity_schema.label}_{index_field} 
                        FOR (n:{entity_schema.label}) ON (n.{index_field})
                        """
                        session.run(cypher)
                        logger.info(f"创建索引: {entity_schema.label}.{index_field}")
                    except Exception as e:
                        logger.debug(f"索引可能已存在: {e}")
    
    def create_constraints(self):
        """创建约束"""
        if not self.driver:
            logger.error("Neo4j未连接")
            return
        
        with self.driver.session() as session:
            for entity_type, entity_schema in ALL_ENTITIES.items():
                if entity_schema.indexes:
                    primary = entity_schema.indexes[0]
                    try:
                        cypher = f"""
                        CREATE CONSTRAINT {entity_schema.label}_{primary}_unique
                        FOR (n:{entity_schema.label}) REQUIRE n.{primary} IS UNIQUE
                        """
                        session.run(cypher)
                        logger.info(f"创建约束: {entity_schema.label}.{primary}")
                    except Exception as e:
                        logger.debug(f"约束可能已存在: {e}")
    
    def create_node(self, entity: ExtractedEntity) -> bool:
        """创建节点"""
        if not self.driver:
            return False
        
        schema = self.schema.get_entity_schema(entity.entity_type)
        if not schema:
            return False
        
        # 构建属性字典
        props = {}
        for key, value in entity.properties.items():
            if value is not None:
                props[key] = value
        
        # 添加置信度和来源
        props['confidence'] = entity.confidence
        props['source'] = entity.source
        
        # 构建Cypher
        props_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
        cypher = f"MERGE (n:{schema.label} {{name: $name}}) SET n += {{{props_str}}}"
        
        try:
            with self.driver.session() as session:
                session.run(cypher, **props)
                logger.debug(f"创建节点: {schema.label}({entity.name})")
                return True
        except Exception as e:
            logger.error(f"创建节点失败: {e}")
            return False
    
    def create_relation(self, relation: ExtractedRelation) -> bool:
        """创建关系"""
        if not self.driver:
            return False
        
        schema = self.schema.get_relation_schema(relation.relation_type)
        if not schema:
            return False
        
        from_entity_schema = self.schema.get_entity_schema(relation.from_entity.entity_type)
        to_entity_schema = self.schema.get_entity_schema(relation.to_entity.entity_type)
        
        if not from_entity_schema or not to_entity_schema:
            return False
        
        # 构建关系属性
        rel_props = {}
        for key, value in relation.properties.items():
            if value is not None:
                rel_props[key] = value
        
        rel_props['confidence'] = relation.confidence
        rel_props['source'] = relation.source
        
        # 构建Cypher
        rel_props_str = ""
        if rel_props:
            rel_props_str = " { " + ", ".join([f"{k}: ${k}_rel" for k in rel_props.keys()]) + " }"
        
        # 参数
        params = {
            'from_name': relation.from_entity.name,
            'to_name': relation.to_entity.name,
        }
        for k, v in rel_props.items():
            params[f"{k}_rel"] = v
        
        cypher = f"""
        MATCH (a:{from_entity_schema.label} {{name: $from_name}})
        MATCH (b:{to_entity_schema.label} {{name: $to_name}})
        MERGE (a)-[r:{schema.type_name}{rel_props_str}]->(b)
        """
        
        try:
            with self.driver.session() as session:
                session.run(cypher, **params)
                logger.debug(f"创建关系: {schema.type_name}({relation.from_entity.name} -> {relation.to_entity.name})")
                return True
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            return False
    
    def build_graph(self, entities: List[ExtractedEntity], relations: List[ExtractedRelation]):
        """构建完整图谱"""
        logger.info(f"开始构建图谱: {len(entities)} 个实体, {len(relations)} 个关系")
        
        # 创建索引和约束
        self.create_indexes()
        self.create_constraints()
        
        # 创建节点
        success_nodes = 0
        for entity in entities:
            if self.create_node(entity):
                success_nodes += 1
        
        logger.info(f"成功创建 {success_nodes}/{len(entities)} 个节点")
        
        # 创建关系
        success_rels = 0
        for relation in relations:
            if self.create_relation(relation):
                success_rels += 1
        
        logger.info(f"成功创建 {success_rels}/{len(relations)} 个关系")
    
    def clear_graph(self, confirm: bool = False):
        """清空图谱"""
        if not confirm:
            logger.warning("请设置confirm=True以确认清空图谱")
            return
        
        if not self.driver:
            return
        
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("已清空图谱")
    
    def query(self, cypher: str, parameters: Dict = None) -> List[Dict]:
        """执行Cypher查询"""
        if not self.driver:
            return []
        
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]
    
    def get_stats(self) -> Dict:
        """获取图谱统计信息"""
        if not self.driver:
            return {}
        
        stats = {}
        
        # 节点统计
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n) 
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            stats['nodes'] = {record['label']: record['count'] for record in result}
        
        # 关系统计
        with self.driver.session() as session:
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            stats['relations'] = {record['type']: record['count'] for record in result}
        
        return stats


class NetworkXGraphBuilder:
    """NetworkX图构建器（Neo4j不可用时使用）"""
    
    def __init__(self):
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX未安装")
        
        self.graph = nx.DiGraph()
        self.schema = KnowledgeGraphSchema()
        logger.info("已创建NetworkX图")
    
    def add_node(self, entity: ExtractedEntity):
        """添加节点"""
        schema = self.schema.get_entity_schema(entity.entity_type)
        if not schema:
            return
        
        node_id = f"{schema.label}:{entity.name}"
        
        props = dict(entity.properties)
        props['entity_type'] = entity.entity_type.value
        props['type_code'] = entity.entity_type.name
        props['label'] = schema.label
        props['confidence'] = entity.confidence
        props['source'] = entity.source
        
        self.graph.add_node(node_id, **props)
        logger.debug(f"添加节点: {node_id}")
    
    def add_edge(self, relation: ExtractedRelation):
        """添加边"""
        from_schema = self.schema.get_entity_schema(relation.from_entity.entity_type)
        to_schema = self.schema.get_entity_schema(relation.to_entity.entity_type)
        
        if not from_schema or not to_schema:
            return
        
        from_id = f"{from_schema.label}:{relation.from_entity.name}"
        to_id = f"{to_schema.label}:{relation.to_entity.name}"
        
        rel_schema = self.schema.get_relation_schema(relation.relation_type)
        rel_type = rel_schema.type_name if rel_schema else relation.relation_type.name
        
        props = dict(relation.properties)
        props['relation_type'] = relation.relation_type.value
        props['type_code'] = relation.relation_type.name
        props['type_name'] = rel_type
        props['confidence'] = relation.confidence
        props['source'] = relation.source
        props['evidence'] = relation.evidence
        
        self.graph.add_edge(from_id, to_id, **props)
        logger.debug(f"添加边: {from_id} -> {to_id} ({rel_type})")
    
    def build_graph(self, entities: List[ExtractedEntity], relations: List[ExtractedRelation]):
        """构建完整图谱"""
        logger.info(f"开始构建图谱: {len(entities)} 个实体, {len(relations)} 个关系")
        
        for entity in entities:
            self.add_node(entity)
        
        for relation in relations:
            self.add_edge(relation)
        
        logger.info(f"图谱构建完成: {self.graph.number_of_nodes()} 节点, {self.graph.number_of_edges()} 边")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
        }
        
        # 节点类型统计
        node_types = {}
        for node, data in self.graph.nodes(data=True):
            label = data.get('label', 'Unknown')
            node_types[label] = node_types.get(label, 0) + 1
        stats['node_types'] = node_types
        
        # 关系类型统计
        edge_types = {}
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get('type_name', 'Unknown')
            edge_types[rel_type] = edge_types.get(rel_type, 0) + 1
        stats['edge_types'] = edge_types
        
        return stats
    
    def find_paths(self, source: str, target: str, cutoff: int = 5) -> List[List[str]]:
        """查找路径"""
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=cutoff))
            return paths
        except nx.NetworkXNoPath:
            return []
    
    def get_neighbors(self, node: str, depth: int = 1) -> Dict:
        """获取邻居节点"""
        result = {"nodes": [], "edges": []}
        
        if node not in self.graph:
            return result
        
        # 使用BFS
        visited = {node}
        queue = [(node, 0)]
        
        while queue:
            current, level = queue.pop(0)
            
            if level >= depth:
                continue
            
            for successor in self.graph.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, level + 1))
                    result["nodes"].append(successor)
                    
                    edge_data = self.graph.get_edge_data(current, successor)
                    if edge_data:
                        result["edges"].append({
                            "from": current,
                            "to": successor,
                            "data": edge_data
                        })
        
        return result
    
    def export_to_json(self, output_path: str):
        """导出为JSON"""
        data = {
            "nodes": [],
            "edges": []
        }
        
        for node, node_data in self.graph.nodes(data=True):
            data["nodes"].append({
                "id": node,
                **{k: v for k, v in node_data.items() if k != 'source'}
            })
        
        for u, v, edge_data in self.graph.edges(data=True):
            data["edges"].append({
                "source": u,
                "target": v,
                **{k: v for k, v in edge_data.items() if k != 'source'}
            })
        
        Path(output_path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        logger.info(f"已导出图谱到 {output_path}")
    
    def save_to_graphml(self, output_path: str):
        """保存为GraphML格式"""
        nx.write_graphml(self.graph, output_path)
        logger.info(f"已保存GraphML到 {output_path}")


class GraphBuilder:
    """图构建器统一接口"""
    
    def __init__(self, backend: str = "auto", **kwargs):
        """
        初始化图构建器
        
        Args:
            backend: "neo4j", "networkx", 或 "auto"
            **kwargs: Neo4j连接参数
        """
        self.backend = backend
        self.builder = None
        
        if backend == "auto":
            if NEO4J_AVAILABLE:
                try:
                    self.builder = Neo4jGraphBuilder(**kwargs)
                    if self.builder.driver:
                        self.backend = "neo4j"
                    else:
                        self.builder = NetworkXGraphBuilder()
                        self.backend = "networkx"
                except:
                    self.builder = NetworkXGraphBuilder()
                    self.backend = "networkx"
            else:
                self.builder = NetworkXGraphBuilder()
                self.backend = "networkx"
        elif backend == "neo4j":
            self.builder = Neo4jGraphBuilder(**kwargs)
            self.backend = "neo4j"
        elif backend == "networkx":
            self.builder = NetworkXGraphBuilder()
            self.backend = "networkx"
        else:
            raise ValueError(f"不支持的后端: {backend}")
        
        logger.info(f"使用后端: {self.backend}")
    
    def build_from_documents(self, documents: List[str]):
        """从文档构建图谱"""
        entity_extractor = EntityExtractor()
        relation_extractor = RelationExtractor()
        
        all_entities = []
        all_relations = []
        
        for doc_path in documents:
            logger.info(f"处理文档: {doc_path}")
            
            # 抽取实体
            entities = entity_extractor.extract_from_file(doc_path)
            all_entities.extend(entities)
            
            # 抽取关系
            relations = relation_extractor.extract_from_file(doc_path, entities)
            all_relations.extend(relations)
        
        # 构建图谱
        self.builder.build_graph(all_entities, all_relations)
        
        return {
            "entities": len(all_entities),
            "relations": len(all_relations),
        }
    
    def build_from_entities_relations(self, entities: List[ExtractedEntity], 
                                      relations: List[ExtractedRelation]):
        """从实体和关系构建图谱"""
        self.builder.build_graph(entities, relations)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.builder.get_stats()
    
    def query(self, cypher: str = None, **kwargs) -> List[Dict]:
        """查询图谱"""
        if self.backend == "neo4j":
            return self.builder.query(cypher, kwargs)
        else:
            # NetworkX查询
            if "source" in kwargs and "target" in kwargs:
                return self.builder.find_paths(kwargs["source"], kwargs["target"])
            elif "node" in kwargs:
                return self.builder.get_neighbors(kwargs["node"], kwargs.get("depth", 1))
            return []
    
    def export(self, output_path: str, format: str = "json"):
        """导出图谱"""
        if format == "json":
            if self.backend == "networkx":
                self.builder.export_to_json(output_path)
            else:
                # Neo4j导出为JSON
                stats = self.get_stats()
                Path(output_path).write_text(
                    json.dumps(stats, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
        elif format == "graphml":
            if self.backend == "networkx":
                self.builder.save_to_graphml(output_path)
        
        logger.info(f"已导出图谱到 {output_path}")
    
    def close(self):
        """关闭连接"""
        if self.backend == "neo4j":
            self.builder.close()


# ========== 测试 ==========
if __name__ == "__main__":
    # 创建测试数据
    from entity_extractor import EntityExtractor
    from relation_extractor import RelationExtractor
    
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
       提供担保，担保金额5000万元。
    """
    
    # 抽取实体和关系
    entity_extractor = EntityExtractor()
    relation_extractor = RelationExtractor()
    
    entities = entity_extractor.extract_from_text(test_text, source="测试文档")
    relations = relation_extractor.extract_relations_from_text(test_text, entities, source="测试文档")
    
    print(f"实体: {len(entities)}, 关系: {len(relations)}")
    
    # 构建NetworkX图
    builder = GraphBuilder(backend="networkx")
    builder.build_from_entities_relations(entities, relations)
    
    # 统计
    stats = builder.get_stats()
    print(f"\n图谱统计:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    # 导出
    builder.export("test_graph.json", format="json")
    
    builder.close()
