"""
串标围标检测扩展模块 v2.0
新增：L8工商关联分析（天眼查API）
"""
import os
import json
import re
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime

# 天眼查API配置（需要用户自行申请）
TIANYANCHA_API_KEY = os.environ.get('TIANYANCHA_API_KEY', '')
TIANYANCHA_API_URL = 'http://open.api.tianyancha.com/services/v4/open'

class BidCollusionExtendedDetector:
    """串标围标扩展检测器：在原11层基础上增加L8工商关联"""
    
    def __init__(self, tianyancha_key: str = None):
        self.tianyancha_key = tianyancha_key or TIANYANCHA_API_KEY
        self._company_cache = {}  # 企业信息缓存
    
    # ========== L8: 工商关联分析 ==========
    
    def extract_company_names(self, text: str) -> List[str]:
        """从文本中提取企业名称"""
        # 匹配常见企业名称模式
        patterns = [
            r'([\u4e00-\u9fff]{2,30}(?:有限公司|有限责任公司|股份有限公司|集团|合伙企业|中心|工作室))',
            r'([\u4e00-\u9fff]{2,20}(?:公司|企业|厂|店|部|社))',
        ]
        companies = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            companies.update(matches)
        return list(companies)
    
    def query_company_info(self, company_name: str) -> Optional[Dict]:
        """查询企业工商信息（天眼查API）"""
        if not self.tianyancha_key:
            return None
        
        # 检查缓存
        if company_name in self._company_cache:
            return self._company_cache[company_name]
        
        try:
            import requests
            url = f"{TIANYANCHA_API_URL}/baseinfoNormal"
            headers = {
                'Authorization': self.tianyancha_key,
                'Content-Type': 'application/json'
            }
            params = {'name': company_name}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('state') == 'ok':
                    result = data.get('data', {})
                    self._company_cache[company_name] = result
                    return result
        except Exception as e:
            print(f"[L8] 查询企业信息失败 {company_name}: {e}")
        
        return None
    
    def query_company_relation(self, company_a: str, company_b: str) -> Dict:
        """查询两家企业的关联关系"""
        if not self.tianyancha_key:
            return {'related': False, 'reason': '未配置天眼查API'}
        
        try:
            import requests
            url = f"{TIANYANCHA_API_URL}/findCompanyRelation"
            headers = {
                'Authorization': self.tianyancha_key,
                'Content-Type': 'application/json'
            }
            params = {'companyNameA': company_a, 'companyNameB': company_b}
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'related': data.get('data', {}).get('haveRelate', False),
                    'relation_type': data.get('data', {}).get('relationType', ''),
                    'detail': data.get('data', {})
                }
        except Exception as e:
            print(f"[L8] 查询关联关系失败 {company_a}-{company_b}: {e}")
        
        return {'related': False, 'reason': '查询失败'}
    
    def analyze_bidder_relations(self, bidder_names: List[str]) -> List[Dict]:
        """分析投标人之间的关联关系"""
        relations = []
        n = len(bidder_names)
        
        for i in range(n):
            for j in range(i + 1, n):
                a, b = bidder_names[i], bidder_names[j]
                rel = self.query_company_relation(a, b)
                if rel.get('related'):
                    relations.append({
                        'company_a': a,
                        'company_b': b,
                        'relation_type': rel.get('relation_type', '未知'),
                        'confidence': 'high' if self.tianyancha_key else 'low'
                    })
        
        return relations
    
    def check_same_controller(self, bidder_names: List[str]) -> List[Dict]:
        """检查是否存在同一实际控制人"""
        controllers = {}
        results = []
        
        for name in bidder_names:
            info = self.query_company_info(name)
            if info:
                # 提取法定代表人
                legal_person = info.get('legalPersonName', '')
                if legal_person:
                    if legal_person in controllers:
                        controllers[legal_person].append(name)
                    else:
                        controllers[legal_person] = [name]
        
        for person, companies in controllers.items():
            if len(companies) > 1:
                results.append({
                    'type': '同一法定代表人',
                    'person': person,
                    'companies': companies,
                    'risk_level': 'high'
                })
        
        return results
    
    def check_address_similarity(self, bidder_names: List[str]) -> List[Dict]:
        """检查注册地址相似性"""
        addresses = {}
        results = []
        
        for name in bidder_names:
            info = self.query_company_info(name)
            if info:
                addr = info.get('regLocation', '')
                if addr:
                    # 简化地址用于比对（省市区）
                    simple_addr = self._simplify_address(addr)
                    if simple_addr in addresses:
                        addresses[simple_addr].append(name)
                    else:
                        addresses[simple_addr] = [name]
        
        for addr, companies in addresses.items():
            if len(companies) > 1:
                results.append({
                    'type': '注册地址相同/相近',
                    'address': addr,
                    'companies': companies,
                    'risk_level': 'medium'
                })
        
        return results
    
    def _simplify_address(self, addr: str) -> str:
        """简化地址用于比对"""
        # 提取省市区
        match = re.match(r'(.*?省|.*?自治区|.*?市辖区|.*?区|.*?县)', addr)
        return match.group(1) if match else addr[:20]
    
    def l8_full_analysis(self, bidder_names: List[str]) -> Dict:
        """L8完整工商关联分析"""
        print(f"[L8] 开始工商关联分析，共 {len(bidder_names)} 家企业")
        
        # 1. 两两关联分析
        relations = self.analyze_bidder_relations(bidder_names)
        
        # 2. 同一控制人检查
        same_controller = self.check_same_controller(bidder_names)
        
        # 3. 地址相似性检查
        address_similar = self.check_address_similarity(bidder_names)
        
        # 综合评估
        risk_score = 0
        indicators = []
        
        if relations:
            risk_score += 30 * len(relations)
            indicators.append(f"发现{len(relations)}组关联企业")
        
        if same_controller:
            risk_score += 40 * len(same_controller)
            indicators.append(f"发现{len(same_controller)}组同一控制人")
        
        if address_similar:
            risk_score += 20 * len(address_similar)
            indicators.append(f"发现{len(address_similar)}组地址相近")
        
        risk_level = 'low'
        if risk_score >= 80:
            risk_level = 'high'
        elif risk_score >= 40:
            risk_level = 'medium'
        
        return {
            'layer': 'L8',
            'name': '工商关联分析',
            'bidders_analyzed': len(bidder_names),
            'api_available': bool(self.tianyancha_key),
            'relations_found': len(relations),
            'same_controller_found': len(same_controller),
            'address_similar_found': len(address_similar),
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'indicators': indicators,
            'details': {
                'relations': relations,
                'same_controller': same_controller,
                'address_similar': address_similar
            }
        }
    
    # ========== 本地替代方案（无API时） ==========
    
    def local_relation_check(self, bidder_docs: List[Dict]) -> Dict:
        """不依赖API的本地关联检测"""
        # 从投标文件文本中提取信息进行比对
        relations = []
        
        for i, doc_a in enumerate(bidder_docs):
            for j, doc_b in enumerate(bidder_docs[i+1:], i+1):
                similarities = []
                
                # 1. 联系人/电话相似
                contact_a = doc_a.get('contact', '')
                contact_b = doc_b.get('contact', '')
                if contact_a and contact_b and contact_a == contact_b:
                    similarities.append('相同联系人/电话')
                
                # 2. 邮箱相似
                email_a = doc_a.get('email', '')
                email_b = doc_b.get('email', '')
                if email_a and email_b:
                    # 检查邮箱域名是否相同
                    domain_a = email_a.split('@')[-1] if '@' in email_a else ''
                    domain_b = email_b.split('@')[-1] if '@' in email_b else ''
                    if domain_a == domain_b and domain_a:
                        similarities.append(f'相同邮箱域名: {domain_a}')
                
                # 3. IP地址相似（如有）
                ip_a = doc_a.get('ip_address', '')
                ip_b = doc_b.get('ip_address', '')
                if ip_a and ip_b and ip_a == ip_b:
                    similarities.append(f'相同IP地址: {ip_a}')
                
                if similarities:
                    relations.append({
                        'company_a': doc_a.get('name', f'投标人{i+1}'),
                        'company_b': doc_b.get('name', f'投标人{j+1}'),
                        'similarities': similarities,
                        'source': '本地文本分析'
                    })
        
        risk_level = 'high' if len(relations) >= 2 else 'medium' if relations else 'low'
        
        return {
            'layer': 'L8-local',
            'name': '本地关联检测（无API）',
            'relations_found': len(relations),
            'risk_level': risk_level,
            'details': relations
        }

# 全局实例
def get_bid_detector(tianyancha_key: str = None) -> BidCollusionExtendedDetector:
    return BidCollusionExtendedDetector(tianyancha_key)

if __name__ == '__main__':
    # 测试
    detector = get_bid_detector()
    
    # 模拟投标人
    bidders = ['四川融策会计师事务所', '四川某工程咨询公司', '成都某科技公司']
    
    # 本地检测测试
    docs = [
        {'name': '公司A', 'contact': '13800138000', 'email': 'a@test.com'},
        {'name': '公司B', 'contact': '13800138000', 'email': 'b@test.com'},
        {'name': '公司C', 'contact': '13900139000', 'email': 'c@other.com'},
    ]
    result = detector.local_relation_check(docs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
