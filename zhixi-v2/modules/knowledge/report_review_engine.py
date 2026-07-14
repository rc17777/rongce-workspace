"""
AI报告复核引擎 v2.0
基于15维检查法 + LLM生成修改建议
"""
import re
import json
from typing import List, Dict, Tuple, Optional

# Zhipu API 配置
ZHIPU_API = '6fd63d70ad8944e597ab5c2d3609fbf1.U41vqcRuzi8V8EBH'
ZHIPU_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
ZHIPU_MODEL = 'glm-4-plus'

class ReportReviewEngine:
    """AI报告复核引擎"""
    
    # 15维检查维度
    REVIEW_DIMENSIONS = [
        {"id": "d1", "name": "报告格式合规性", "desc": "是否符合GB/T9704公文格式、页边距、字体字号、行距等"},
        {"id": "d2", "name": "标题层级规范性", "desc": "标题层级是否清晰、编号是否连续、逻辑是否递进"},
        {"id": "d3", "name": "数据勾稽关系", "desc": "报告正文数据与附表数据是否一致、汇总是否正确"},
        {"id": "d4", "name": "金额计算准确性", "desc": "金额汇总、占比、增减幅度计算是否正确"},
        {"id": "d5", "name": "政策法规引用", "desc": "引用的政策法规是否准确、文号是否正确、是否现行有效"},
        {"id": "d6", "name": "术语一致性", "desc": "专业术语使用是否一致、规范，无错别字"},
        {"id": "d7", "name": "逻辑连贯性", "desc": "段落间逻辑是否连贯，结论是否有充分依据"},
        {"id": "d8", "name": "问题定性准确性", "desc": "审计发现问题定性是否准确，法规适用是否正确"},
        {"id": "d9", "name": "取证单↔报告一致性", "desc": "取证单记录的问题是否在报告中完整反映"},
        {"id": "d10", "name": "整改建议可行性", "desc": "整改建议是否具体、可操作、有针对性"},
        {"id": "d11", "name": "附表完整性", "desc": "附表是否齐全、表头是否正确、数据是否完整"},
        {"id": "d12", "name": "时间表述准确性", "desc": "审计期间、时间节点、截止日期表述是否准确"},
        {"id": "d13", "name": "单位名称一致性", "desc": "被审计单位名称、简称、代码是否全文一致"},
        {"id": "d14", "name": "附件清单完整性", "desc": "附件清单是否与实际附件对应、编号是否连续"},
        {"id": "d15", "name": "全文金额追踪", "desc": "关键金额在全文各处的表述是否一致、无矛盾"},
    ]
    
    def __init__(self):
        self.dimensions = self.REVIEW_DIMENSIONS
    
    def rule_based_check(self, report_text: str) -> List[Dict]:
        """基于规则的快速检查"""
        issues = []
        
        # d3: 金额勾稽检查 - 提取所有金额
        amounts = re.findall(r'([\d,]+\.\d{2})', report_text)
        if len(amounts) > 10:
            # 简单检查：是否有重复金额但上下文不同
            pass  # 复杂勾稽需要附表数据
        
        # d6: 术语一致性 - 常见错别字
        typo_patterns = [
            (r'审记', '审计'),
            (r'帐', '账'),
            (r'其它', '其他'),
            (r'做业', '作业'),
            (r'即然', '既然'),
        ]
        for pattern, correct in typo_patterns:
            matches = list(re.finditer(pattern, report_text))
            for m in matches:
                issues.append({
                    'dimension': 'd6',
                    'severity': 'warning',
                    'position': m.start(),
                    'original': m.group(),
                    'suggestion': correct,
                    'message': f"疑似错别字：'{m.group()}' 建议改为 '{correct}'"
                })
        
        # d13: 单位名称一致性
        # 提取可能的单位名称（简单规则）
        unit_patterns = re.findall(r'([\u4e00-\u9fff]{2,20}(?:局|厅|委|办|中心|公司|集团))', report_text)
        if unit_patterns:
            unique_units = set(unit_patterns)
            if len(unique_units) > 3:  # 可能有不一致
                issues.append({
                    'dimension': 'd13',
                    'severity': 'info',
                    'message': f"检测到 {len(unique_units)} 个不同单位名称/简称，请检查是否全文一致"
                })
        
        # d12: 时间表述
        date_patterns = re.findall(r'(\d{4})\s*年\s*(\d{1,2})\s*月', report_text)
        if date_patterns:
            years = set([d[0] for d in date_patterns])
            if len(years) > 1:
                issues.append({
                    'dimension': 'd12',
                    'severity': 'warning',
                    'message': f"检测到多个年份：{', '.join(sorted(years))}，请确认审计期间表述一致"
                })
        
        return issues
    
    def llm_review(self, report_text: str, max_chars: int = 8000) -> Dict:
        """LLM深度复核"""
        # 截断长文本
        truncated = report_text[:max_chars]
        
        prompt = f"""你是一位资深审计报告复核专家。请对以下审计报告进行复核，从15个维度检查问题。

## 15维检查清单
1. 报告格式合规性：是否符合公文格式要求
2. 标题层级规范性：标题层级是否清晰
3. 数据勾稽关系：数据是否一致
4. 金额计算准确性：计算是否正确
5. 政策法规引用：引用是否准确有效
6. 术语一致性：术语是否规范一致
7. 逻辑连贯性：逻辑是否通顺
8. 问题定性准确性：定性是否准确
9. 取证单↔报告一致性：是否闭环
10. 整改建议可行性：建议是否可操作
11. 附表完整性：附表是否齐全
12. 时间表述准确性：时间是否一致
13. 单位名称一致性：名称是否统一
14. 附件清单完整性：附件是否对应
15. 全文金额追踪：金额是否一致

## 审计报告内容
{truncated}

## 输出要求
请以JSON格式输出检查结果：
{{
  "overall_score": 85,
  "risk_level": "低",
  "dimensions": [
    {{
      "id": "d1",
      "name": "报告格式合规性",
      "score": 90,
      "issues": ["问题描述"],
      "suggestions": ["修改建议"]
    }}
  ],
  "critical_issues": ["致命问题列表"],
  "summary": "总体评价"
}}

注意：
- 只输出JSON，不要其他文字
- 如某维度无问题，issues为空数组
- critical_issues只列必须立即修改的问题"""
        
        try:
            import requests
            resp = requests.post(
                ZHIPU_URL,
                headers={
                    'Authorization': f'Bearer {ZHIPU_API}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': ZHIPU_MODEL,
                    'messages': [
                        {'role': 'system', 'content': '你是审计报告复核专家，输出严格JSON格式'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.2,
                    'max_tokens': 3000
                },
                timeout=120
            )
            
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                # 提取JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return {
                'overall_score': 0,
                'risk_level': '未知',
                'dimensions': [],
                'critical_issues': [f'LLM调用失败: {resp.status_code}'],
                'summary': '复核失败'
            }
        except Exception as e:
            return {
                'overall_score': 0,
                'risk_level': '未知',
                'dimensions': [],
                'critical_issues': [f'复核异常: {e}'],
                'summary': '复核失败'
            }
    
    def comprehensive_review(self, report_text: str) -> Dict:
        """综合复核：规则检查 + LLM深度分析"""
        # 规则检查
        rule_issues = self.rule_based_check(report_text)
        
        # LLM深度检查
        llm_result = self.llm_review(report_text)
        
        # 合并结果
        if 'critical_issues' not in llm_result:
            llm_result['critical_issues'] = []
        
        # 将规则检查发现的问题加入
        for issue in rule_issues:
            dim_name = next((d['name'] for d in self.dimensions if d['id'] == issue['dimension']), issue['dimension'])
            msg = issue['message']
            if issue['severity'] == 'warning' and msg not in llm_result['critical_issues']:
                llm_result['critical_issues'].append(msg)
        
        return {
            'overall_score': llm_result.get('overall_score', 0),
            'risk_level': llm_result.get('risk_level', '未知'),
            'dimensions': llm_result.get('dimensions', []),
            'critical_issues': llm_result.get('critical_issues', []),
            'rule_issues': rule_issues,
            'summary': llm_result.get('summary', ''),
            'report_length': len(report_text)
        }
    
    def generate_fix_suggestions(self, report_text: str, issues: List[str]) -> str:
        """基于问题列表生成修改建议"""
        prompt = f"""你是审计报告修改专家。请针对以下问题，给出具体的修改建议。

## 审计报告（部分）
{report_text[:3000]}

## 发现的问题
{chr(10).join(['- ' + i for i in issues])}

## 要求
1. 对每个问题给出具体修改建议
2. 如可能，给出修改后的示例文本
3. 标注修改优先级（高/中/低）
4. 保持审计报告的专业性和严谨性

请输出修改建议："""
        
        try:
            import requests
            resp = requests.post(
                ZHIPU_URL,
                headers={
                    'Authorization': f'Bearer {ZHIPU_API}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': ZHIPU_MODEL,
                    'messages': [
                        {'role': 'system', 'content': '你是审计报告修改专家'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 2500
                },
                timeout=120
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
            return f"修改建议生成失败: {resp.status_code}"
        except Exception as e:
            return f"修改建议生成异常: {e}"

# 全局实例
_review_engine = None

def get_review_engine() -> ReportReviewEngine:
    global _review_engine
    if _review_engine is None:
        _review_engine = ReportReviewEngine()
    return _review_engine
