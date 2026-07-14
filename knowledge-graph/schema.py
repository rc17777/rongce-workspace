# -*- coding: utf-8 -*-
"""
融策审计知识图谱 - Schema定义模块
定义三类核心实体（组织/业务/风险）和四类关系（股权/交易/人员/风险传导）
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum

# ========== 实体类型枚举 ==========
class EntityType(Enum):
    """三类核心实体"""
    # 组织类
    COMPANY = "公司/企业"
    GOV_DEPT = "政府部门"
    INSTITUTION = "事业单位"
    PROJECT_TEAM = "项目组"
    
    # 业务类
    PROJECT = "审计项目"
    CONTRACT = "合同"
    BID = "招投标"
    BUDGET = "预算"
    ASSET = "资产"
    FUND = "资金/专项债"
    
    # 风险类
    RISK = "风险点"
    ISSUE = "审计问题"
    FINDING = "发现事项"
    PERSON = "人员"
    
    # 辅助类
    ADDRESS = "地址"
    PHONE = "电话"
    BANK_ACCOUNT = "银行账户"

class RelationType(Enum):
    """四类核心关系"""
    # 股权关系
    HOLD = "控股"
    INVEST = "投资"
    CONTROL = "实际控制"
    
    # 交易关系
    TRADE = "交易"
    CONTRACT_WITH = "签约"
    BID_FOR = "投标于"
    WIN_BID = "中标"
    PAY = "支付"
    RECEIVE = "收款"
    
    # 人员关系
    LEGAL_REP = "担任法人"
    DIRECTOR = "担任董事"
    SUPERVISOR = "担任监事"
    EMPLOY = "雇佣"
    MANAGE = "管理"
    SUPERVISE = "监督"
    
    # 风险传导关系
    CAUSE = "导致"
    ASSOCIATE = "关联"
    SAME_ADDR = "同地址"
    SAME_PHONE = "同电话"
    SAME_BANK = "同账户"
    GUARANTEE = "担保"
    FAMILY = "亲属"

# ========== Schema定义 ==========
@dataclass
class EntitySchema:
    """实体Schema定义"""
    entity_type: EntityType
    label: str  # Neo4j标签
    properties: Dict[str, str]  # 属性名: 数据类型
    required_props: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.required_props:
            self.required_props = ["name"]

@dataclass
class RelationSchema:
    """关系Schema定义"""
    relation_type: RelationType
    type_name: str  # Neo4j关系类型
    from_types: List[EntityType]  # 允许的起点实体类型
    to_types: List[EntityType]  # 允许的终点实体类型
    properties: Dict[str, str] = field(default_factory=dict)
    required_props: List[str] = field(default_factory=list)

# ========== 完整Schema定义 ==========

# 组织类实体
ORGANIZATION_ENTITIES = {
    EntityType.COMPANY: EntitySchema(
        entity_type=EntityType.COMPANY,
        label="Company",
        properties={
            "name": "string",
            "reg_no": "string",  # 统一社会信用代码
            "reg_capital": "float",
            "established_date": "date",
            "industry": "string",
            "status": "string",  # 存续/注销/吊销
            "source": "string",  # 数据来源
        },
        required_props=["name"],
        indexes=["name", "reg_no"]
    ),
    
    EntityType.GOV_DEPT: EntitySchema(
        entity_type=EntityType.GOV_DEPT,
        label="GovDept",
        properties={
            "name": "string",
            "dept_code": "string",
            "level": "string",  # 中央/省/市/县
            "parent_dept": "string",
            "source": "string",
        },
        required_props=["name"],
        indexes=["name", "dept_code"]
    ),
    
    EntityType.INSTITUTION: EntitySchema(
        entity_type=EntityType.INSTITUTION,
        label="Institution",
        properties={
            "name": "string",
            "reg_no": "string",
            "institution_type": "string",  # 医院/学校/科研机构
            "source": "string",
        },
        required_props=["name"],
        indexes=["name"]
    ),
    
    EntityType.PROJECT_TEAM: EntitySchema(
        entity_type=EntityType.PROJECT_TEAM,
        label="ProjectTeam",
        properties={
            "name": "string",
            "team_id": "string",
            "leader": "string",
            "members": "list",
            "source": "string",
        },
        required_props=["name"],
        indexes=["team_id"]
    ),
}

# 业务类实体
BUSINESS_ENTITIES = {
    EntityType.PROJECT: EntitySchema(
        entity_type=EntityType.PROJECT,
        label="AuditProject",
        properties={
            "name": "string",
            "project_id": "string",
            "project_type": "string",  # 绩效评价/资产清查/专项债/监督检查
            "audit_scope": "string",
            "audit_period": "string",
            "budget_amount": "float",
            "actual_amount": "float",
            "status": "string",  # 进行中/已完成
            "source": "string",
        },
        required_props=["name", "project_type"],
        indexes=["project_id", "project_type"]
    ),
    
    EntityType.CONTRACT: EntitySchema(
        entity_type=EntityType.CONTRACT,
        label="Contract",
        properties={
            "name": "string",
            "contract_no": "string",
            "contract_type": "string",
            "amount": "float",
            "sign_date": "date",
            "start_date": "date",
            "end_date": "date",
            "status": "string",
            "source": "string",
        },
        required_props=["name"],
        indexes=["contract_no"]
    ),
    
    EntityType.BID: EntitySchema(
        entity_type=EntityType.BID,
        label="Bid",
        properties={
            "name": "string",
            "bid_no": "string",
            "bid_type": "string",  # 公开招标/邀请招标/竞争性谈判
            "bid_amount": "float",
            "bid_date": "date",
            "bid_status": "string",  # 招标中/已开标/已中标
            "source": "string",
        },
        required_props=["name"],
        indexes=["bid_no"]
    ),
    
    EntityType.BUDGET: EntitySchema(
        entity_type=EntityType.BUDGET,
        label="Budget",
        properties={
            "name": "string",
            "budget_id": "string",
            "budget_type": "string",  # 年度预算/项目预算
            "total_amount": "float",
            "fiscal_year": "string",
            "source": "string",
        },
        required_props=["name"],
        indexes=["budget_id"]
    ),
    
    EntityType.ASSET: EntitySchema(
        entity_type=EntityType.ASSET,
        label="Asset",
        properties={
            "name": "string",
            "asset_id": "string",
            "asset_type": "string",  # 固定资产/无形资产/流动资产
            "category": "string",
            "value": "float",
            "acquisition_date": "date",
            "location": "string",
            "source": "string",
        },
        required_props=["name"],
        indexes=["asset_id"]
    ),
    
    EntityType.FUND: EntitySchema(
        entity_type=EntityType.FUND,
        label="Fund",
        properties={
            "name": "string",
            "fund_id": "string",
            "fund_type": "string",  # 专项债/财政资金/自筹资金
            "amount": "float",
            "issue_date": "date",
            "maturity_date": "date",
            "interest_rate": "float",
            "source": "string",
        },
        required_props=["name"],
        indexes=["fund_id"]
    ),
}

# 风险类实体
RISK_ENTITIES = {
    EntityType.RISK: EntitySchema(
        entity_type=EntityType.RISK,
        label="Risk",
        properties={
            "name": "string",
            "risk_id": "string",
            "risk_type": "string",  # 合规风险/财务风险/操作风险
            "severity": "string",  # 高/中/低
            "probability": "string",  # 高/中/低
            "description": "string",
            "source": "string",
        },
        required_props=["name"],
        indexes=["risk_id"]
    ),
    
    EntityType.ISSUE: EntitySchema(
        entity_type=EntityType.ISSUE,
        label="Issue",
        properties={
            "name": "string",
            "issue_id": "string",
            "issue_type": "string",  # 违规/损失/管理缺陷
            "severity": "string",
            "amount": "float",
            "description": "string",
            "status": "string",  # 已整改/未整改/整改中
            "source": "string",
        },
        required_props=["name"],
        indexes=["issue_id"]
    ),
    
    EntityType.FINDING: EntitySchema(
        entity_type=EntityType.FINDING,
        label="Finding",
        properties={
            "name": "string",
            "finding_id": "string",
            "finding_type": "string",
            "category": "string",
            "description": "string",
            "evidence": "string",
            "source": "string",
        },
        required_props=["name"],
        indexes=["finding_id"]
    ),
    
    EntityType.PERSON: EntitySchema(
        entity_type=EntityType.PERSON,
        label="Person",
        properties={
            "name": "string",
            "id_card": "string",
            "phone": "string",
            "email": "string",
            "title": "string",  # 职务
            "department": "string",
            "source": "string",
        },
        required_props=["name"],
        indexes=["name", "id_card"]
    ),
    
    EntityType.ADDRESS: EntitySchema(
        entity_type=EntityType.ADDRESS,
        label="Address",
        properties={
            "address": "string",
            "province": "string",
            "city": "string",
            "district": "string",
            "source": "string",
        },
        required_props=["address"],
        indexes=["address"]
    ),
    
    EntityType.PHONE: EntitySchema(
        entity_type=EntityType.PHONE,
        label="Phone",
        properties={
            "phone": "string",
            "source": "string",
        },
        required_props=["phone"],
        indexes=["phone"]
    ),
    
    EntityType.BANK_ACCOUNT: EntitySchema(
        entity_type=EntityType.BANK_ACCOUNT,
        label="BankAccount",
        properties={
            "account_no": "string",
            "bank_name": "string",
            "account_name": "string",
            "source": "string",
        },
        required_props=["account_no"],
        indexes=["account_no"]
    ),
}

# 合并所有实体
ALL_ENTITIES = {**ORGANIZATION_ENTITIES, **BUSINESS_ENTITIES, **RISK_ENTITIES}

# ========== 关系Schema定义 ==========

RELATION_SCHEMAS = {
    # ===== 股权关系 =====
    RelationType.HOLD: RelationSchema(
        relation_type=RelationType.HOLD,
        type_name="HOLD",
        from_types=[EntityType.COMPANY, EntityType.GOV_DEPT, EntityType.INSTITUTION],
        to_types=[EntityType.COMPANY, EntityType.INSTITUTION],
        properties={"ratio": "float", "method": "string"},
        required_props=["ratio"]
    ),
    
    RelationType.INVEST: RelationSchema(
        relation_type=RelationType.INVEST,
        type_name="INVEST",
        from_types=[EntityType.COMPANY, EntityType.PERSON],
        to_types=[EntityType.COMPANY],
        properties={"amount": "float", "ratio": "float"},
    ),
    
    RelationType.CONTROL: RelationSchema(
        relation_type=RelationType.CONTROL,
        type_name="CONTROL",
        from_types=[EntityType.PERSON, EntityType.COMPANY],
        to_types=[EntityType.COMPANY],
        properties={"control_type": "string", "control_chain": "string"},
    ),
    
    # ===== 交易关系 =====
    RelationType.TRADE: RelationSchema(
        relation_type=RelationType.TRADE,
        type_name="TRADE",
        from_types=[EntityType.COMPANY, EntityType.GOV_DEPT, EntityType.INSTITUTION],
        to_types=[EntityType.COMPANY, EntityType.GOV_DEPT, EntityType.INSTITUTION],
        properties={
            "amount": "float",
            "trade_date": "date",
            "trade_type": "string",
            "contract_no": "string",
            "description": "string",
        },
    ),
    
    RelationType.CONTRACT_WITH: RelationSchema(
        relation_type=RelationType.CONTRACT_WITH,
        type_name="CONTRACT_WITH",
        from_types=[EntityType.COMPANY, EntityType.GOV_DEPT, EntityType.INSTITUTION],
        to_types=[EntityType.COMPANY, EntityType.GOV_DEPT, EntityType.INSTITUTION],
        properties={
            "contract_no": "string",
            "contract_amount": "float",
            "sign_date": "date",
        },
    ),
    
    RelationType.BID_FOR: RelationSchema(
        relation_type=RelationType.BID_FOR,
        type_name="BID_FOR",
        from_types=[EntityType.COMPANY],
        to_types=[EntityType.BID, EntityType.PROJECT],
        properties={
            "bid_amount": "float",
            "bid_date": "date",
            "bid_rank": "integer",
        },
    ),
    
    RelationType.WIN_BID: RelationSchema(
        relation_type=RelationType.WIN_BID,
        type_name="WIN_BID",
        from_types=[EntityType.COMPANY],
        to_types=[EntityType.BID, EntityType.PROJECT],
        properties={
            "win_amount": "float",
            "win_date": "date",
            "contract_no": "string",
        },
    ),
    
    RelationType.PAY: RelationSchema(
        relation_type=RelationType.PAY,
        type_name="PAY",
        from_types=[EntityType.COMPANY, EntityType.GOV_DEPT],
        to_types=[EntityType.COMPANY, EntityType.BANK_ACCOUNT],
        properties={
            "amount": "float",
            "pay_date": "date",
            "purpose": "string",
            "voucher_no": "string",
        },
    ),
    
    RelationType.RECEIVE: RelationSchema(
        relation_type=RelationType.RECEIVE,
        type_name="RECEIVE",
        from_types=[EntityType.COMPANY, EntityType.BANK_ACCOUNT],
        to_types=[EntityType.COMPANY, EntityType.GOV_DEPT],
        properties={
            "amount": "float",
            "receive_date": "date",
            "purpose": "string",
        },
    ),
    
    # ===== 人员关系 =====
    RelationType.LEGAL_REP: RelationSchema(
        relation_type=RelationType.LEGAL_REP,
        type_name="LEGAL_REP",
        from_types=[EntityType.PERSON],
        to_types=[EntityType.COMPANY, EntityType.INSTITUTION],
        properties={
            "start_date": "date",
            "end_date": "date",
            "is_current": "boolean",
        },
    ),
    
    RelationType.DIRECTOR: RelationSchema(
        relation_type=RelationType.DIRECTOR,
        type_name="DIRECTOR",
        from_types=[EntityType.PERSON],
        to_types=[EntityType.COMPANY, EntityType.INSTITUTION],
        properties={
            "position": "string",
            "start_date": "date",
            "end_date": "date",
        },
    ),
    
    RelationType.SUPERVISOR: RelationSchema(
        relation_type=RelationType.SUPERVISOR,
        type_name="SUPERVISOR",
        from_types=[EntityType.PERSON],
        to_types=[EntityType.COMPANY, EntityType.INSTITUTION],
        properties={
            "start_date": "date",
            "end_date": "date",
        },
    ),
    
    RelationType.EMPLOY: RelationSchema(
        relation_type=RelationType.EMPLOY,
        type_name="EMPLOY",
        from_types=[EntityType.COMPANY, EntityType.GOV_DEPT, EntityType.INSTITUTION],
        to_types=[EntityType.PERSON],
        properties={
            "position": "string",
            "department": "string",
            "start_date": "date",
            "end_date": "date",
        },
    ),
    
    RelationType.MANAGE: RelationSchema(
        relation_type=RelationType.MANAGE,
        type_name="MANAGE",
        from_types=[EntityType.PERSON],
        to_types=[EntityType.PROJECT, EntityType.ASSET, EntityType.FUND],
        properties={
            "role": "string",
            "start_date": "date",
            "end_date": "date",
        },
    ),
    
    RelationType.SUPERVISE: RelationSchema(
        relation_type=RelationType.SUPERVISE,
        type_name="SUPERVISE",
        from_types=[EntityType.GOV_DEPT, EntityType.PERSON],
        to_types=[EntityType.PROJECT, EntityType.COMPANY, EntityType.INSTITUTION],
        properties={
            "supervise_type": "string",
            "start_date": "date",
        },
    ),
    
    # ===== 风险传导关系 =====
    RelationType.CAUSE: RelationSchema(
        relation_type=RelationType.CAUSE,
        type_name="CAUSE",
        from_types=[EntityType.RISK, EntityType.ISSUE, EntityType.FINDING],
        to_types=[EntityType.RISK, EntityType.ISSUE, EntityType.FINDING, EntityType.COMPANY, EntityType.PROJECT],
        properties={
            "cause_type": "string",
            "confidence": "float",
            "description": "string",
        },
    ),
    
    RelationType.ASSOCIATE: RelationSchema(
        relation_type=RelationType.ASSOCIATE,
        type_name="ASSOCIATE",
        from_types=[EntityType.COMPANY, EntityType.PERSON],
        to_types=[EntityType.COMPANY, EntityType.PERSON],
        properties={
            "associate_type": "string",
            "confidence": "float",
        },
    ),
    
    RelationType.SAME_ADDR: RelationSchema(
        relation_type=RelationType.SAME_ADDR,
        type_name="SAME_ADDR",
        from_types=[EntityType.COMPANY, EntityType.PERSON],
        to_types=[EntityType.ADDRESS],
        properties={"addr_type": "string"},
    ),
    
    RelationType.SAME_PHONE: RelationSchema(
        relation_type=RelationType.SAME_PHONE,
        type_name="SAME_PHONE",
        from_types=[EntityType.COMPANY, EntityType.PERSON],
        to_types=[EntityType.PHONE],
        properties={"phone_type": "string"},
    ),
    
    RelationType.SAME_BANK: RelationSchema(
        relation_type=RelationType.SAME_BANK,
        type_name="SAME_BANK",
        from_types=[EntityType.COMPANY, EntityType.PERSON],
        to_types=[EntityType.BANK_ACCOUNT],
        properties={"account_type": "string"},
    ),
    
    RelationType.GUARANTEE: RelationSchema(
        relation_type=RelationType.GUARANTEE,
        type_name="GUARANTEE",
        from_types=[EntityType.COMPANY],
        to_types=[EntityType.COMPANY],
        properties={
            "guarantee_amount": "float",
            "guarantee_type": "string",
            "start_date": "date",
            "end_date": "date",
        },
    ),
    
    RelationType.FAMILY: RelationSchema(
        relation_type=RelationType.FAMILY,
        type_name="FAMILY",
        from_types=[EntityType.PERSON],
        to_types=[EntityType.PERSON],
        properties={
            "relation": "string",  # 父子/夫妻/兄弟等
            "confidence": "float",
        },
    ),
}

# ========== Schema管理类 ==========
class KnowledgeGraphSchema:
    """知识图谱Schema管理器"""
    
    def __init__(self):
        self.entities = ALL_ENTITIES
        self.relations = RELATION_SCHEMAS
    
    def get_entity_schema(self, entity_type: EntityType) -> Optional[EntitySchema]:
        """获取实体Schema"""
        return self.entities.get(entity_type)
    
    def get_relation_schema(self, relation_type: RelationType) -> Optional[RelationSchema]:
        """获取关系Schema"""
        return self.relations.get(relation_type)
    
    def get_entities_by_category(self, category: str) -> Dict[EntityType, EntitySchema]:
        """按类别获取实体"""
        if category == "organization":
            return ORGANIZATION_ENTITIES
        elif category == "business":
            return BUSINESS_ENTITIES
        elif category == "risk":
            return RISK_ENTITIES
        return {}
    
    def get_relations_by_category(self, category: str) -> Dict[RelationType, RelationSchema]:
        """按类别获取关系"""
        categories = {
            "equity": [RelationType.HOLD, RelationType.INVEST, RelationType.CONTROL],
            "trade": [RelationType.TRADE, RelationType.CONTRACT_WITH, RelationType.BID_FOR, 
                     RelationType.WIN_BID, RelationType.PAY, RelationType.RECEIVE],
            "personnel": [RelationType.LEGAL_REP, RelationType.DIRECTOR, RelationType.SUPERVISOR,
                         RelationType.EMPLOY, RelationType.MANAGE, RelationType.SUPERVISE],
            "risk": [RelationType.CAUSE, RelationType.ASSOCIATE, RelationType.SAME_ADDR,
                    RelationType.SAME_PHONE, RelationType.SAME_BANK, RelationType.GUARANTEE, RelationType.FAMILY],
        }
        rel_types = categories.get(category, [])
        return {rt: self.relations[rt] for rt in rel_types if rt in self.relations}
    
    def validate_entity(self, entity_type: EntityType, properties: Dict) -> (bool, List[str]):
        """验证实体属性"""
        schema = self.get_entity_schema(entity_type)
        if not schema:
            return False, [f"Unknown entity type: {entity_type}"]
        
        errors = []
        for prop in schema.required_props:
            if prop not in properties or properties[prop] is None:
                errors.append(f"Missing required property: {prop}")
        
        return len(errors) == 0, errors
    
    def validate_relation(self, relation_type: RelationType, from_type: EntityType, 
                         to_type: EntityType, properties: Dict) -> (bool, List[str]):
        """验证关系"""
        schema = self.get_relation_schema(relation_type)
        if not schema:
            return False, [f"Unknown relation type: {relation_type}"]
        
        errors = []
        if from_type not in schema.from_types:
            errors.append(f"Invalid from_type: {from_type}")
        if to_type not in schema.to_types:
            errors.append(f"Invalid to_type: {to_type}")
        
        for prop in schema.required_props:
            if prop not in properties or properties[prop] is None:
                errors.append(f"Missing required property: {prop}")
        
        return len(errors) == 0, errors
    
    def to_cypher_create_node(self, entity_type: EntityType, properties: Dict) -> str:
        """生成Cypher创建节点语句"""
        schema = self.get_entity_schema(entity_type)
        if not schema:
            return ""
        
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        return f"CREATE (n:{schema.label} {{{props_str}}})"
    
    def to_cypher_create_relation(self, relation_type: RelationType, 
                                  from_label: str, to_label: str, 
                                  from_props: Dict, to_props: Dict, 
                                  rel_props: Dict) -> str:
        """生成Cypher创建关系语句"""
        schema = self.get_relation_schema(relation_type)
        if not schema:
            return ""
        
        from_match = " AND ".join([f"a.{k} = ${k}_from" for k in from_props.keys()])
        to_match = " AND ".join([f"b.{k} = ${k}_to" for k in to_props.keys()])
        rel_props_str = ""
        if rel_props:
            rel_props_str = " { " + ", ".join([f"{k}: ${k}_rel" for k in rel_props.keys()]) + " }"
        
        return f"""
        MATCH (a:{from_label}), (b:{to_label})
        WHERE {from_match} AND {to_match}
        CREATE (a)-[:{schema.type_name}{rel_props_str}]->(b)
        """
    
    def print_schema_summary(self):
        """打印Schema摘要"""
        print("=" * 60)
        print("融策审计知识图谱 - Schema定义")
        print("=" * 60)
        print(f"\n【实体定义】共 {len(self.entities)} 种")
        print(f"  - 组织类: {len(ORGANIZATION_ENTITIES)} 种")
        print(f"  - 业务类: {len(BUSINESS_ENTITIES)} 种")
        print(f"  - 风险类: {len(RISK_ENTITIES)} 种")
        
        print(f"\n【关系定义】共 {len(self.relations)} 种")
        print(f"  - 股权关系: 3 种")
        print(f"  - 交易关系: 6 种")
        print(f"  - 人员关系: 6 种")
        print(f"  - 风险传导: 7 种")
        
        print("\n【核心实体】")
        for et, schema in self.entities.items():
            print(f"  {et.value} ({schema.label})")
        
        print("\n【核心关系】")
        for rt, schema in self.relations.items():
            print(f"  {rt.value} ({schema.type_name})")
        
        print("=" * 60)


# ========== 测试 ==========
if __name__ == "__main__":
    schema = KnowledgeGraphSchema()
    schema.print_schema_summary()
    
    # 测试验证
    valid, errors = schema.validate_entity(EntityType.COMPANY, {"name": "测试公司"})
    print(f"\n验证实体: {valid}, {errors}")
    
    valid, errors = schema.validate_entity(EntityType.COMPANY, {})
    print(f"验证实体(缺少name): {valid}, {errors}")
