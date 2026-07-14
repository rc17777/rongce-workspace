# -*- coding: utf-8 -*-
"""
融策审计知识图谱 - 实体抽取模块
从审计报告、合同、招投标文件中抽取实体
支持：PDF、Word、Excel、文本文件
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

# 导入Schema
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import EntityType, KnowledgeGraphSchema


@dataclass
class ExtractedEntity:
    """抽取的实体"""
    entity_type: EntityType
    name: str
    properties: Dict[str, Any]
    confidence: float = 1.0
    source: str = ""  # 来源文档
    position: Tuple[int, int] = (0, 0)  # 在文档中的位置


class EntityExtractor:
    """实体抽取器 - 基于规则+词典"""
    
    def __init__(self):
        self.schema = KnowledgeGraphSchema()
        
        # 预定义词典
        self.company_suffixes = [
            "有限公司", "有限责任公司", "股份有限公司", "集团公司",
            "合伙企业", "事务所", "中心", "研究院", "设计院", "工程公司",
            "咨询公司", "会计师事务所", "审计事务所", "建筑公司", "科技公司"
        ]
        
        self.gov_dept_keywords = [
            "财政局", "审计局", "发改委", "住建局", "交通局", "水利局",
            "教育局", "卫健委", "自然资源局", "生态环境局", "农业农村局",
            "人民政府", "街道办事处", "开发区管委会", "产业园区"
        ]
        
        self.institution_keywords = [
            "医院", "学校", "大学", "学院", "研究所", "研究院", "博物馆",
            "图书馆", "文化馆", "体育馆", "疾控中心", "卫生院"
        ]
        
        self.project_type_keywords = {
            "绩效评价": ["绩效评价", "绩效评估", "绩效审计", "项目绩效"],
            "资产清查": ["资产清查", "资产盘点", "资产核实", "清产核资"],
            "专项债": ["专项债券", "专项债", "政府债券", "债券资金"],
            "监督检查": ["监督检查", "专项检查", "督查", "巡查", "检查"],
            "预算编制": ["预算编制", "预算评审", "预算审核", "预算审查"],
            "工程结算": ["工程结算", "竣工结算", "结算审核", "结算审计"],
            "全过程咨询": ["全过程咨询", "全过程工程咨询", "项目管理"],
            "财政评审": ["财政评审", "财政投资评审", "投资评审"],
        }
        
        self.risk_keywords = [
            "风险", "问题", "缺陷", "违规", "损失", "浪费", "低效",
            "舞弊", "腐败", "关联交易", "利益输送", "围标", "串标"
        ]
        
        # 正则模式
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """编译正则表达式"""
        patterns = {}
        
        # 公司名称匹配
        company_pattern = r"([^，。；\n\r]{2,30}(?:" + "|".join(self.company_suffixes) + "))"
        patterns['company'] = re.compile(company_pattern)
        
        # 政府部门匹配
        gov_pattern = r"([^，。；\n\r]{2,30}(?:" + "|".join(self.gov_dept_keywords) + "))"
        patterns['gov_dept'] = re.compile(gov_pattern)
        
        # 机构匹配
        inst_pattern = r"([^，。；\n\r]{2,30}(?:" + "|".join(self.institution_keywords) + "))"
        patterns['institution'] = re.compile(inst_pattern)
        
        # 统一社会信用代码
        patterns['reg_no'] = re.compile(r'[0-9A-Z]{18}')
        
        # 金额匹配（万元/元）
        patterns['amount'] = re.compile(
            r'(?:金额|资金|投资|预算|合同额|中标价|成交价)[\s：:]*([\d,\.]+)\s*(?:万元|元|亿元)'
        )
        
        # 日期匹配
        patterns['date'] = re.compile(
            r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2})'
        )
        
        # 项目名称匹配（常见前缀）
        patterns['project'] = re.compile(
            r'(?:项目名称|工程名称|标段名称|采购项目)[\s：:]*([^\n\r]{2,50})'
        )
        
        # 合同编号
        patterns['contract_no'] = re.compile(
            r'(?:合同编号|合同号|编号)[\s：:]*([A-Za-z0-9\-]{5,30})'
        )
        
        # 招标编号
        patterns['bid_no'] = re.compile(
            r'(?:招标编号|项目编号|采购编号|标段编号)[\s：:]*([A-Za-z0-9\-]{5,30})'
        )
        
        # 人员姓名（中文姓名）
        patterns['person'] = re.compile(
            r'(?:法定代表人|法人|负责人|项目经理|总监|联系人|经办人|审计人员)[\s：:]*([\u4e00-\u9fa5]{2,4})'
        )
        
        # 电话号码
        patterns['phone'] = re.compile(
            r'(?:电话|联系方式|手机|传真)[\s：:]*([\d\-]{7,15})'
        )
        
        # 地址
        patterns['address'] = re.compile(
            r'(?:地址|注册地址|办公地址|项目地点)[\s：:]*([^\n\r]{5,100})'
        )
        
        # 银行账户
        patterns['bank_account'] = re.compile(
            r'(?:账号|银行账户|开户账号)[\s：:]*([\d\s]{10,25})'
        )
        
        # 身份证号码
        patterns['id_card'] = re.compile(
            r'(?:身份证号|身份证)[\s：:]*([\dX]{15,18})'
        )
        
        return patterns
    
    def extract_from_text(self, text: str, source: str = "") -> List[ExtractedEntity]:
        """从文本中抽取实体"""
        entities = []
        
        # 1. 抽取公司
        entities.extend(self._extract_companies(text, source))
        
        # 2. 抽取政府部门
        entities.extend(self._extract_gov_depts(text, source))
        
        # 3. 抽取事业单位
        entities.extend(self._extract_institutions(text, source))
        
        # 4. 抽取项目
        entities.extend(self._extract_projects(text, source))
        
        # 5. 抽取合同
        entities.extend(self._extract_contracts(text, source))
        
        # 6. 抽取招投标
        entities.extend(self._extract_bids(text, source))
        
        # 7. 抽取人员
        entities.extend(self._extract_persons(text, source))
        
        # 8. 抽取地址
        entities.extend(self._extract_addresses(text, source))
        
        # 9. 抽取电话
        entities.extend(self._extract_phones(text, source))
        
        # 10. 抽取银行账户
        entities.extend(self._extract_bank_accounts(text, source))
        
        # 11. 抽取风险/问题
        entities.extend(self._extract_risks(text, source))
        
        # 去重
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    def _extract_companies(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取公司实体"""
        entities = []
        matches = self.patterns['company'].finditer(text)
        
        for match in matches:
            name = match.group(1).strip()
            if len(name) < 4 or len(name) > 50:
                continue
            
            # 提取注册资本
            reg_capital = None
            capital_match = re.search(
                rf'{re.escape(name)}.*?注册资本[\s：:]*([\d,\.]+)\s*万元',
                text[max(0, match.start()-200):match.start()+200]
            )
            if capital_match:
                reg_capital = float(capital_match.group(1).replace(',', ''))
            
            # 提取统一社会信用代码
            reg_no = None
            reg_no_match = self.patterns['reg_no'].search(
                text[max(0, match.start()-100):match.start()+100]
            )
            if reg_no_match:
                reg_no = reg_no_match.group(0)
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.COMPANY,
                name=name,
                properties={
                    "name": name,
                    "reg_capital": reg_capital,
                    "reg_no": reg_no,
                },
                confidence=0.9,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_gov_depts(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取政府部门"""
        entities = []
        matches = self.patterns['gov_dept'].finditer(text)
        
        for match in matches:
            name = match.group(1).strip()
            if len(name) < 4 or len(name) > 50:
                continue
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.GOV_DEPT,
                name=name,
                properties={"name": name},
                confidence=0.85,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_institutions(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取事业单位"""
        entities = []
        matches = self.patterns['institution'].finditer(text)
        
        for match in matches:
            name = match.group(1).strip()
            if len(name) < 4 or len(name) > 50:
                continue
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.INSTITUTION,
                name=name,
                properties={"name": name},
                confidence=0.8,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_projects(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取审计项目"""
        entities = []
        
        # 匹配项目名称
        matches = self.patterns['project'].finditer(text)
        for match in matches:
            name = match.group(1).strip()
            
            # 识别项目类型
            project_type = "其他"
            for ptype, keywords in self.project_type_keywords.items():
                if any(kw in text[max(0, match.start()-500):match.start()+100] for kw in keywords):
                    project_type = ptype
                    break
            
            # 提取金额
            budget_amount = None
            amount_match = self.patterns['amount'].search(
                text[max(0, match.start()-300):match.start()+300]
            )
            if amount_match:
                budget_amount = float(amount_match.group(1).replace(',', ''))
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.PROJECT,
                name=name,
                properties={
                    "name": name,
                    "project_type": project_type,
                    "budget_amount": budget_amount,
                },
                confidence=0.85,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_contracts(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取合同"""
        entities = []
        
        # 匹配合同编号
        matches = self.patterns['contract_no'].finditer(text)
        for match in matches:
            contract_no = match.group(1).strip()
            
            # 提取合同名称（前后文）
            name = "合同"
            name_match = re.search(
                r'《([^》]{2,50}?)》.*?合同',
                text[max(0, match.start()-200):match.start()+200]
            )
            if name_match:
                name = name_match.group(1) + "合同"
            
            # 提取金额
            amount = None
            amount_match = self.patterns['amount'].search(
                text[max(0, match.start()-200):match.start()+200]
            )
            if amount_match:
                amount = float(amount_match.group(1).replace(',', ''))
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.CONTRACT,
                name=name,
                properties={
                    "name": name,
                    "contract_no": contract_no,
                    "amount": amount,
                },
                confidence=0.8,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_bids(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取招投标"""
        entities = []
        
        # 匹配招标编号
        matches = self.patterns['bid_no'].finditer(text)
        for match in matches:
            bid_no = match.group(1).strip()
            
            # 提取项目名称
            name = "招标项目"
            name_match = re.search(
                r'(?:项目名称|工程名称)[\s：:]*([^\n\r]{2,50})',
                text[max(0, match.start()-200):match.start()+200]
            )
            if name_match:
                name = name_match.group(1).strip()
            
            # 提取金额
            bid_amount = None
            amount_match = self.patterns['amount'].search(
                text[max(0, match.start()-200):match.start()+200]
            )
            if amount_match:
                bid_amount = float(amount_match.group(1).replace(',', ''))
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.BID,
                name=name,
                properties={
                    "name": name,
                    "bid_no": bid_no,
                    "bid_amount": bid_amount,
                },
                confidence=0.8,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_persons(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取人员"""
        entities = []
        
        # 匹配人员姓名+职务
        matches = self.patterns['person'].finditer(text)
        for match in matches:
            name = match.group(1).strip()
            
            # 确定职务
            title = ""
            context = text[max(0, match.start()-20):match.start()]
            if "法定代表人" in context or "法人" in context:
                title = "法定代表人"
            elif "负责人" in context:
                title = "负责人"
            elif "项目经理" in context:
                title = "项目经理"
            elif "总监" in context:
                title = "总监"
            elif "联系人" in context:
                title = "联系人"
            elif "经办人" in context:
                title = "经办人"
            elif "审计" in context:
                title = "审计人员"
            
            # 提取身份证号
            id_card = None
            id_match = self.patterns['id_card'].search(
                text[max(0, match.start()-50):match.start()+50]
            )
            if id_match:
                id_card = id_match.group(1)
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.PERSON,
                name=name,
                properties={
                    "name": name,
                    "title": title,
                    "id_card": id_card,
                },
                confidence=0.75,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_addresses(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取地址"""
        entities = []
        matches = self.patterns['address'].finditer(text)
        
        for match in matches:
            address = match.group(1).strip()
            
            # 提取省市信息
            province = ""
            city = ""
            
            province_match = re.match(r'([^省]+省)?([^市]+市)?', address)
            if province_match:
                province = province_match.group(1) or ""
                city = province_match.group(2) or ""
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.ADDRESS,
                name=address,
                properties={
                    "address": address,
                    "province": province,
                    "city": city,
                },
                confidence=0.8,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_phones(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取电话"""
        entities = []
        matches = self.patterns['phone'].finditer(text)
        
        for match in matches:
            phone = match.group(1).strip()
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.PHONE,
                name=phone,
                properties={"phone": phone},
                confidence=0.85,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_bank_accounts(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取银行账户"""
        entities = []
        matches = self.patterns['bank_account'].finditer(text)
        
        for match in matches:
            account_no = match.group(1).strip().replace(" ", "")
            
            # 提取银行名称
            bank_name = ""
            bank_match = re.search(
                r'(?:开户行|开户银行)[\s：:]*([^\n\r]{2,30})',
                text[max(0, match.start()-100):match.start()+100]
            )
            if bank_match:
                bank_name = bank_match.group(1).strip()
            
            entities.append(ExtractedEntity(
                entity_type=EntityType.BANK_ACCOUNT,
                name=account_no,
                properties={
                    "account_no": account_no,
                    "bank_name": bank_name,
                },
                confidence=0.85,
                source=source,
                position=(match.start(), match.end())
            ))
        
        return entities
    
    def _extract_risks(self, text: str, source: str) -> List[ExtractedEntity]:
        """抽取风险/问题"""
        entities = []
        
        # 基于关键词和上下文抽取
        for keyword in self.risk_keywords:
            pattern = re.compile(rf'([^。；\n\r]{{5,80}}?{keyword}[^。；\n\r]{{0,50}}?)')
            matches = pattern.finditer(text)
            
            for match in matches:
                description = match.group(1).strip()
                
                # 确定风险类型
                risk_type = "其他"
                if "合规" in description or "违规" in description:
                    risk_type = "合规风险"
                elif "财务" in description or "资金" in description:
                    risk_type = "财务风险"
                elif "操作" in description or "管理" in description:
                    risk_type = "操作风险"
                elif "舞弊" in description or "腐败" in description:
                    risk_type = "舞弊风险"
                
                entities.append(ExtractedEntity(
                    entity_type=EntityType.RISK,
                    name=description[:30] + "..." if len(description) > 30 else description,
                    properties={
                        "name": description[:50],
                        "risk_type": risk_type,
                        "description": description,
                    },
                    confidence=0.7,
                    source=source,
                    position=(match.start(), match.end())
                ))
        
        return entities
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """去重"""
        seen = set()
        unique = []
        
        for entity in entities:
            key = (entity.entity_type, entity.name)
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        
        return unique
    
    def extract_from_file(self, file_path: str) -> List[ExtractedEntity]:
        """从文件中抽取实体"""
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            return []
        
        # 根据文件类型读取内容
        text = ""
        suffix = path.suffix.lower()
        
        if suffix == '.txt':
            text = path.read_text(encoding='utf-8')
        elif suffix == '.json':
            data = json.loads(path.read_text(encoding='utf-8'))
            text = json.dumps(data, ensure_ascii=False)
        else:
            # 对于其他格式，尝试读取文本
            try:
                text = path.read_text(encoding='utf-8')
            except:
                logger.warning(f"无法读取文件: {file_path}")
                return []
        
        return self.extract_from_text(text, source=str(path))
    
    def batch_extract(self, directory: str, pattern: str = "*") -> Dict[str, List[ExtractedEntity]]:
        """批量抽取目录下的文件"""
        results = {}
        path = Path(directory)
        
        for file_path in path.glob(pattern):
            if file_path.is_file():
                entities = self.extract_from_file(str(file_path))
                if entities:
                    results[str(file_path)] = entities
                    logger.info(f"从 {file_path.name} 抽取了 {len(entities)} 个实体")
        
        return results
    
    def export_to_json(self, entities: List[ExtractedEntity], output_path: str):
        """导出为JSON"""
        data = []
        for entity in entities:
            item = {
                "entity_type": entity.entity_type.value,
                "type_code": entity.entity_type.name,
                "name": entity.name,
                "properties": entity.properties,
                "confidence": entity.confidence,
                "source": entity.source,
            }
            data.append(item)
        
        Path(output_path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        logger.info(f"已导出 {len(data)} 个实体到 {output_path}")


# ========== 测试 ==========
if __name__ == "__main__":
    extractor = EntityExtractor()
    
    # 测试文本
    test_text = """
    关于XX市2023年度预算执行绩效评价项目的审计报告
    
    被审计单位：XX市财政局
    审计项目：2023年度预算执行绩效评价
    审计期间：2023年1月1日至2023年12月31日
    
    一、基本情况
    XX市财政局（统一社会信用代码：123456789012345678）负责全市财政预算管理。
    本次审计涉及XX市城市建设投资有限公司（注册资本：50000万元）、
    XX市交通发展集团有限公司（注册资本：30000万元）等5家单位。
    
    二、审计发现
    1. 预算编制不规范，部分项目预算金额（1200万元）与实际执行偏差较大；
    2. XX市城市建设投资有限公司存在关联交易风险，涉及金额约500万元；
    3. 项目"XX市2023年道路改造工程"（合同编号：HT-2023-001）
       中标单位：XX建筑工程有限公司，中标金额：8500万元；
    4. 法定代表人：张三，身份证号：510101199001011234；
    5. 联系电话：028-12345678，地址：XX市XX区XX路123号。
    
    三、审计建议
    建议加强预算管理，防范财务风险。
    """
    
    entities = extractor.extract_from_text(test_text, source="测试文档")
    
    print(f"\n共抽取 {len(entities)} 个实体:\n")
    for entity in entities:
        print(f"[{entity.entity_type.value}] {entity.name}")
        print(f"  属性: {entity.properties}")
        print(f"  置信度: {entity.confidence}")
        print()
    
    # 导出测试
    extractor.export_to_json(entities, "test_entities.json")
