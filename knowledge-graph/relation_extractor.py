# -*- coding: utf-8 -*-
"""
融策审计知识图谱 - 关系识别模块
基于规则和NLP识别实体间关系
"""

import re
import json
import os
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入Schema和实体抽取
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import EntityType, RelationType, KnowledgeGraphSchema
from entity_extractor import ExtractedEntity


@dataclass
class ExtractedRelation:
    """抽取的关系"""
    relation_type: RelationType
    from_entity: ExtractedEntity
    to_entity: ExtractedEntity
    properties: Dict[str, Any]
    confidence: float = 1.0
    source: str = ""  # 来源文档
    evidence: str = ""  # 证据文本


class RelationExtractor:
    """关系抽取器 - 基于规则+共现分析"""
    
    def __init__(self):
        self.schema = KnowledgeGraphSchema()
        
        # 关系规则定义
        self.rules = self._define_rules()
    
    def _define_rules(self) -> List[Dict]:
        """定义关系抽取规则"""
        rules = []
        
        # ===== 股权关系规则 =====
        rules.append({
            "relation_type": RelationType.HOLD,
            "name": "控股关系",
            "patterns": [
                r"(.{2,30}?)持有(.{2,30}?)\s*(\d+(?:\.\d+)?)%\s*股权",
                r"(.{2,30}?)控股(.{2,30}?)",
                r"(.{2,30}?)对(.{2,30}?)的持股比例为\s*(\d+(?:\.\d+)?)%",
            ],
            "from_group": 1,
            "to_group": 2,
            "prop_groups": {"ratio": 3},
            "context_window": 200,
        })
        
        rules.append({
            "relation_type": RelationType.CONTROL,
            "name": "实际控制",
            "patterns": [
                r"(.{2,30}?)为(.{2,30}?)实际控制人",
                r"(.{2,30}?)实际控制(.{2,30}?)",
                r"(.{2,30}?)是(.{2,30}?)的实际控制人",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 200,
        })
        
        # ===== 交易关系规则 =====
        rules.append({
            "relation_type": RelationType.TRADE,
            "name": "交易关系",
            "patterns": [
                r"(.{2,30}?)向(.{2,30}?)支付\s*([\d,\.]+)\s*万元",
                r"(.{2,30}?)收到(.{2,30}?)\s*([\d,\.]+)\s*万元",
                r"(.{2,30}?)与(.{2,30}?)签订.*?合同",
            ],
            "from_group": 1,
            "to_group": 2,
            "prop_groups": {"amount": 3},
            "context_window": 300,
        })
        
        rules.append({
            "relation_type": RelationType.CONTRACT_WITH,
            "name": "合同关系",
            "patterns": [
                r"(.{2,30}?)与(.{2,30}?)签订.*?《(.{2,50}?)》",
                r"(.{2,30}?)和(.{2,30}?)签署.*?合同",
            ],
            "from_group": 1,
            "to_group": 2,
            "prop_groups": {"contract_name": 3},
            "context_window": 300,
        })
        
        rules.append({
            "relation_type": RelationType.BID_FOR,
            "name": "投标关系",
            "patterns": [
                r"(.{2,30}?)参与(.{2,50}?)投标",
                r"(.{2,30}?)对(.{2,50}?)进行投标",
                r"投标人[:：]\s*(.{2,30}?)",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 300,
        })
        
        rules.append({
            "relation_type": RelationType.WIN_BID,
            "name": "中标关系",
            "patterns": [
                r"(.{2,30}?)中标(.{2,50}?)",
                r"(.{2,30}?)为(.{2,50}?)中标人",
                r"(.{2,30}?)中标金额\s*([\d,\.]+)\s*万元",
            ],
            "from_group": 1,
            "to_group": 2,
            "prop_groups": {"win_amount": 3},
            "context_window": 300,
        })
        
        # ===== 人员关系规则 =====
        rules.append({
            "relation_type": RelationType.LEGAL_REP,
            "name": "法人关系",
            "patterns": [
                r"(.{2,4}?)为(.{2,30}?)法定代表人",
                r"(.{2,30}?)法定代表人[:：]\s*(.{2,4}?)",
                r"(.{2,4}?)担任(.{2,30}?)法人",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 200,
        })
        
        rules.append({
            "relation_type": RelationType.DIRECTOR,
            "name": "董事关系",
            "patterns": [
                r"(.{2,4}?)为(.{2,30}?)董事",
                r"(.{2,4}?)担任(.{2,30}?)董事",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 200,
        })
        
        rules.append({
            "relation_type": RelationType.EMPLOY,
            "name": "雇佣关系",
            "patterns": [
                r"(.{2,30}?)聘用(.{2,4}?)为",
                r"(.{2,4}?)系(.{2,30}?)员工",
                r"(.{2,30}?)员工[:：]\s*(.{2,4}?)",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 200,
        })
        
        rules.append({
            "relation_type": RelationType.MANAGE,
            "name": "管理关系",
            "patterns": [
                r"(.{2,4}?)负责(.{2,50}?)管理",
                r"(.{2,4}?)管理(.{2,50}?)",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 200,
        })
        
        # ===== 风险传导关系规则 =====
        rules.append({
            "relation_type": RelationType.CAUSE,
            "name": "因果关系",
            "patterns": [
                r"(.{2,50}?)导致(.{2,50}?)",
                r"(.{2,50}?)引发(.{2,50}?)",
                r"(.{2,50}?)造成(.{2,50}?)",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 300,
        })
        
        rules.append({
            "relation_type": RelationType.GUARANTEE,
            "name": "担保关系",
            "patterns": [
                r"(.{2,30}?)为(.{2,30}?)提供担保",
                r"(.{2,30}?)担保(.{2,30}?)",
            ],
            "from_group": 1,
            "to_group": 2,
            "context_window": 200,
        })
        
        return rules
    
    def extract_relations_from_text(self, text: str, entities: List[ExtractedEntity], 
                                    source: str = "") -> List[ExtractedRelation]:
        """从文本中抽取关系"""
        relations = []
        
        # 1. 基于规则抽取
        rule_relations = self._extract_by_rules(text, entities, source)
        relations.extend(rule_relations)
        
        # 2. 基于共现分析抽取
        cooccur_relations = self._extract_by_cooccurrence(text, entities, source)
        relations.extend(cooccur_relations)
        
        # 3. 基于同属性关联（同地址、同电话等）
        attr_relations = self._extract_by_shared_attributes(entities, source)
        relations.extend(attr_relations)
        
        # 去重
        relations = self._deduplicate_relations(relations)
        
        return relations
    
    def _extract_by_rules(self, text: str, entities: List[ExtractedEntity], 
                          source: str) -> List[ExtractedRelation]:
        """基于规则抽取关系"""
        relations = []
        
        # 构建实体名称到实体的映射
        entity_map = {}
        for entity in entities:
            entity_map[entity.name] = entity
            # 也添加短名称匹配
            if len(entity.name) > 4:
                entity_map[entity.name[:4]] = entity
        
        for rule in self.rules:
            for pattern in rule["patterns"]:
                matches = re.finditer(pattern, text)
                
                for match in matches:
                    try:
                        from_name = match.group(rule["from_group"]).strip()
                        to_name = match.group(rule["to_group"]).strip()
                        
                        # 查找对应的实体
                        from_entity = self._find_entity(from_name, entities)
                        to_entity = self._find_entity(to_name, entities)
                        
                        if from_entity and to_entity and from_entity != to_entity:
                            # 提取属性
                            props = {}
                            if "prop_groups" in rule:
                                for prop_name, group_idx in rule["prop_groups"].items():
                                    if group_idx <= match.lastindex:
                                        prop_value = match.group(group_idx)
                                        if prop_value:
                                            # 尝试转换为数值
                                            try:
                                                props[prop_name] = float(prop_value.replace(',', ''))
                                            except:
                                                props[prop_name] = prop_value
                            
                            # 获取证据文本
                            start = max(0, match.start() - 50)
                            end = min(len(text), match.end() + 50)
                            evidence = text[start:end]
                            
                            relations.append(ExtractedRelation(
                                relation_type=rule["relation_type"],
                                from_entity=from_entity,
                                to_entity=to_entity,
                                properties=props,
                                confidence=0.8,
                                source=source,
                                evidence=evidence
                            ))
                    except Exception as e:
                        logger.debug(f"规则匹配失败: {e}")
                        continue
        
        return relations
    
    def _extract_by_cooccurrence(self, text: str, entities: List[ExtractedEntity], 
                                 source: str) -> List[ExtractedRelation]:
        """基于共现分析抽取关系"""
        relations = []
        
        # 按句子分割
        sentences = re.split(r'[。；\n]', text)
        
        for sentence in sentences:
            # 找出句子中出现的实体
            sentence_entities = []
            for entity in entities:
                if entity.name in sentence:
                    sentence_entities.append(entity)
            
            # 如果同一句子中有多个实体，建立共现关系
            if len(sentence_entities) >= 2:
                for i in range(len(sentence_entities)):
                    for j in range(i + 1, len(sentence_entities)):
                        e1 = sentence_entities[i]
                        e2 = sentence_entities[j]
                        
                        # 根据实体类型确定关系类型
                        rel_type = self._infer_relation_type(e1, e2, sentence)
                        
                        if rel_type:
                            relations.append(ExtractedRelation(
                                relation_type=rel_type,
                                from_entity=e1,
                                to_entity=e2,
                                properties={},
                                confidence=0.6,  # 共现关系置信度较低
                                source=source,
                                evidence=sentence[:100]
                            ))
        
        return relations
    
    def _extract_by_shared_attributes(self, entities: List[ExtractedEntity], 
                                      source: str) -> List[ExtractedRelation]:
        """基于共享属性抽取关系（同地址、同电话等）"""
        relations = []
        
        # 按地址分组
        addr_groups = {}
        for entity in entities:
            if entity.entity_type in [EntityType.COMPANY, EntityType.PERSON]:
                addr = entity.properties.get("address")
                if addr:
                    if addr not in addr_groups:
                        addr_groups[addr] = []
                    addr_groups[addr].append(entity)
        
        # 同地址关系
        for addr, group in addr_groups.items():
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        relations.append(ExtractedRelation(
                            relation_type=RelationType.SAME_ADDR,
                            from_entity=group[i],
                            to_entity=group[j],
                            properties={"address": addr},
                            confidence=0.9,
                            source=source,
                            evidence=f"同地址: {addr}"
                        ))
        
        # 按电话分组
        phone_groups = {}
        for entity in entities:
            if entity.entity_type in [EntityType.COMPANY, EntityType.PERSON]:
                phone = entity.properties.get("phone")
                if phone:
                    if phone not in phone_groups:
                        phone_groups[phone] = []
                    phone_groups[phone].append(entity)
        
        # 同电话关系
        for phone, group in phone_groups.items():
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        relations.append(ExtractedRelation(
                            relation_type=RelationType.SAME_PHONE,
                            from_entity=group[i],
                            to_entity=group[j],
                            properties={"phone": phone},
                            confidence=0.9,
                            source=source,
                            evidence=f"同电话: {phone}"
                        ))
        
        return relations
    
    def _find_entity(self, name: str, entities: List[ExtractedEntity]) -> Optional[ExtractedEntity]:
        """根据名称查找实体"""
        # 精确匹配
        for entity in entities:
            if entity.name == name:
                return entity
        
        # 包含匹配
        for entity in entities:
            if name in entity.name or entity.name in name:
                return entity
        
        return None
    
    def _infer_relation_type(self, e1: ExtractedEntity, e2: ExtractedEntity, 
                             context: str) -> Optional[RelationType]:
        """根据实体类型和上下文推断关系类型"""
        
        # 公司-公司关系
        if e1.entity_type == EntityType.COMPANY and e2.entity_type == EntityType.COMPANY:
            if "投标" in context or "招标" in context:
                return RelationType.BID_FOR
            elif "合同" in context or "签订" in context:
                return RelationType.CONTRACT_WITH
            elif "交易" in context or "支付" in context:
                return RelationType.TRADE
            elif "担保" in context:
                return RelationType.GUARANTEE
        
        # 人员-公司关系
        if (e1.entity_type == EntityType.PERSON and e2.entity_type == EntityType.COMPANY) or \
           (e1.entity_type == EntityType.COMPANY and e2.entity_type == EntityType.PERSON):
            if "法人" in context:
                return RelationType.LEGAL_REP
            elif "董事" in context:
                return RelationType.DIRECTOR
            elif "监事" in context:
                return RelationType.SUPERVISOR
            elif "员工" in context or "工作" in context:
                return RelationType.EMPLOY
        
        # 人员-项目关系
        if e1.entity_type == EntityType.PERSON and e2.entity_type == EntityType.PROJECT:
            if "负责" in context or "管理" in context:
                return RelationType.MANAGE
        
        # 公司-项目关系
        if e1.entity_type == EntityType.COMPANY and e2.entity_type == EntityType.PROJECT:
            if "中标" in context:
                return RelationType.WIN_BID
            elif "投标" in context:
                return RelationType.BID_FOR
        
        # 风险-实体关系
        if e1.entity_type == EntityType.RISK:
            return RelationType.CAUSE
        
        return None
    
    def _deduplicate_relations(self, relations: List[ExtractedRelation]) -> List[ExtractedRelation]:
        """去重"""
        seen = set()
        unique = []
        
        for rel in relations:
            key = (rel.relation_type, rel.from_entity.name, rel.to_entity.name)
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        
        return unique
    
    def extract_from_file(self, file_path: str, entities: List[ExtractedEntity] = None) -> List[ExtractedRelation]:
        """从文件中抽取关系"""
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            return []
        
        # 读取文本
        text = ""
        try:
            text = path.read_text(encoding='utf-8')
        except:
            logger.warning(f"无法读取文件: {file_path}")
            return []
        
        # 如果没有提供实体，先抽取实体
        if entities is None:
            from entity_extractor import EntityExtractor
            extractor = EntityExtractor()
            entities = extractor.extract_from_text(text, source=str(path))
        
        return self.extract_relations_from_text(text, entities, source=str(path))
    
    def batch_extract(self, directory: str, pattern: str = "*") -> Dict[str, List[ExtractedRelation]]:
        """批量抽取目录下的文件"""
        results = {}
        path = Path(directory)
        
        for file_path in path.glob(pattern):
            if file_path.is_file():
                relations = self.extract_from_file(str(file_path))
                if relations:
                    results[str(file_path)] = relations
                    logger.info(f"从 {file_path.name} 抽取了 {len(relations)} 个关系")
        
        return results
    
    def export_to_json(self, relations: List[ExtractedRelation], output_path: str):
        """导出为JSON"""
        data = []
        for rel in relations:
            item = {
                "relation_type": rel.relation_type.value,
                "type_code": rel.relation_type.name,
                "from_entity": {
                    "type": rel.from_entity.entity_type.value,
                    "name": rel.from_entity.name,
                },
                "to_entity": {
                    "type": rel.to_entity.entity_type.value,
                    "name": rel.to_entity.name,
                },
                "properties": rel.properties,
                "confidence": rel.confidence,
                "source": rel.source,
                "evidence": rel.evidence[:100] if rel.evidence else "",
            }
            data.append(item)
        
        Path(output_path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        logger.info(f"已导出 {len(data)} 个关系到 {output_path}")


# ========== 测试 ==========
if __name__ == "__main__":
    from entity_extractor import EntityExtractor
    
    extractor = EntityExtractor()
    relation_extractor = RelationExtractor()
    
    # 测试文本
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
    
    三、审计建议
    建议加强关联交易管理，防范财务风险。
    """
    
    # 抽取实体
    entities = extractor.extract_from_text(test_text, source="测试文档")
    print(f"共抽取 {len(entities)} 个实体")
    
    # 抽取关系
    relations = relation_extractor.extract_relations_from_text(
        test_text, entities, source="测试文档"
    )
    
    print(f"\n共抽取 {len(relations)} 个关系:\n")
    for rel in relations:
        print(f"[{rel.relation_type.value}] {rel.from_entity.name} -> {rel.to_entity.name}")
        print(f"  属性: {rel.properties}")
        print(f"  置信度: {rel.confidence}")
        print(f"  证据: {rel.evidence[:50]}...")
        print()
    
    # 导出测试
    relation_extractor.export_to_json(relations, "test_relations.json")
