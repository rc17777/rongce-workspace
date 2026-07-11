"""
专项债券审计工具 - 四环节检查清单生成与风险分析
"""
import json
from typing import List, Dict
from datetime import datetime

class SpecialBondAuditTool:
    """专项债券审计工具"""
    
    # 四环节检查清单
    CHECKLISTS = {
        'issuance': {
            'name': '发行环节',
            'items': [
                {'id': 'I1', 'item': '新增限额分配是否合理', 'method': '核对限额分配文件与分配依据'},
                {'id': 'I2', 'item': '是否结合地区财力、债务风险等因素', 'method': '检查分配办法与标准'},
                {'id': 'I3', 'item': '项目是否属于支持范围', 'method': '对照七大领域+两新一重'},
                {'id': 'I4', 'item': '融资规模与项目收益是否平衡', 'method': '核查收益测算依据'},
                {'id': 'I5', 'item': '是否存在盲目扩大融资需求', 'method': '对比历史年度需求'},
                {'id': 'I6', 'item': '偿债责任是否明确', 'method': '检查偿债责任书'},
            ]
        },
        'usage': {
            'name': '使用环节',
            'items': [
                {'id': 'U1', 'item': '资金是否及时拨付', 'method': '核对拨付时间与凭证'},
                {'id': 'U2', 'item': '是否专款专用', 'method': '追踪资金流向与用途'},
                {'id': 'U3', 'item': '资金支付与项目进度是否匹配', 'method': '比对支付率与进度率'},
                {'id': 'U4', 'item': '是否存在资金挪用', 'method': '检查最终用途与合同'},
                {'id': 'U5', 'item': '是否存在资金闲置', 'method': '检查资金在账时间'},
                {'id': 'U6', 'item': '拨付程序是否合规', 'method': '核对审批流程'},
            ]
        },
        'management': {
            'name': '管理环节',
            'items': [
                {'id': 'M1', 'item': '绩效目标是否明确可考核', 'method': '检查绩效目标设置'},
                {'id': 'M2', 'item': '绩效指标是否量化', 'method': '检查指标量化程度'},
                {'id': 'M3', 'item': '信息公开是否完整及时', 'method': '检查政府网站公开情况'},
                {'id': 'M4', 'item': '项目收益是否真实实现', 'method': '核对收益实现凭证'},
                {'id': 'M5', 'item': '收益是否覆盖本息', 'method': '计算覆盖倍数'},
                {'id': 'M6', 'item': '收益归集是否及时', 'method': '检查归集时间与账户'},
            ]
        },
        'repayment': {
            'name': '偿还环节',
            'items': [
                {'id': 'R1', 'item': '是否制定偿债计划', 'method': '检查偿债计划文件'},
                {'id': 'R2', 'item': '偿债资金来源是否可靠', 'method': '核实资金来源'},
                {'id': 'R3', 'item': '是否建立偿债准备金', 'method': '检查准备金账户'},
                {'id': 'R4', 'item': '项目收益是否及时归集', 'method': '检查归集记录'},
                {'id': 'R5', 'item': '是否存在偿债风险', 'method': '计算债务率、偿债率'},
                {'id': 'R6', 'item': '风险预警机制是否有效', 'method': '检查预警指标与响应'},
            ]
        }
    }
    
    # 常见问题库
    COMMON_ISSUES = {
        'issuance': [
            {'issue': '限额分配科学性不高', 'evidence': '未结合实际情况制定办法，债务绩效评价标准不明确'},
            {'issue': '或有债务未动态监管', 'evidence': '仅将法定债务率作为衡量指标'},
            {'issue': '偿债责任不匹配', 'evidence': '市县依赖省级财政兜底'},
            {'issue': '为政绩盲目上马项目', 'evidence': '掩盖自身债务风险，放大融资需求'},
        ],
        'usage': [
            {'issue': '资金拨付滞后', 'evidence': '资金在财政账户闲置，未按时拨付到项目'},
            {'issue': '资金挪用', 'evidence': '用于非指定项目或日常支出'},
            {'issue': '进度不匹配', 'evidence': '资金支付率与项目进度率差异大'},
            {'issue': '拆分规避审批', 'evidence': '同一项目多次拆分支付'},
        ],
        'management': [
            {'issue': '绩效目标虚化', 'evidence': '绩效指标无法考核，未与收益挂钩'},
            {'issue': '信息公开不完整', 'evidence': '未按规定公开债券信息'},
            {'issue': '收益造假', 'evidence': '收益测算虚高，实际收益远低于预期'},
            {'issue': '收益未及时归集', 'evidence': '收益滞留项目单位，未归集偿债账户'},
        ],
        'repayment': [
            {'issue': '偿债计划缺失', 'evidence': '未制定偿债计划或计划不可行'},
            {'issue': '偿债资金不足', 'evidence': '项目收益无法覆盖本息'},
            {'issue': '风险预警失效', 'evidence': '未建立预警机制或预警指标不合理'},
            {'issue': '逾期风险', 'evidence': '债务率超过预警阈值'},
        ]
    }
    
    def generate_checklist(self, stages: List[str] = None) -> Dict:
        """生成检查清单
        
        Args:
            stages: 环节列表 ['issuance', 'usage', 'management', 'repayment']
        
        Returns:
            检查清单
        """
        if not stages:
            stages = ['issuance', 'usage', 'management', 'repayment']
        
        result = {}
        for stage in stages:
            if stage in self.CHECKLISTS:
                result[stage] = self.CHECKLISTS[stage]
        
        return result
    
    def analyze_bond(self, bond_data: Dict) -> Dict:
        """分析专项债券项目
        
        Args:
            bond_data: 债券项目数据
                {
                    'name': '债券名称',
                    'amount': 发行规模,
                    'term': 期限,
                    'project_type': '项目类型',
                    'budget': 预算,
                    'actual_cost': 实际成本,
                    'progress': 进度,
                    'revenue': 实际收益,
                    'expected_revenue': 预期收益,
                    'debt_ratio': 债务率,
                    'repayment_plan': True/False,
                }
        
        Returns:
            分析结果
        """
        issues = []
        
        # 1. 收益覆盖分析
        expected = bond_data.get('expected_revenue', 0)
        actual = bond_data.get('revenue', 0)
        amount = bond_data.get('amount', 0)
        
        if expected > 0:
            cover_ratio = actual / expected if expected else 0
            if cover_ratio < 1.0:
                issues.append({
                    'stage': 'management',
                    'severity': 'high',
                    'issue': '收益覆盖不足',
                    'description': f'实际收益{actual}仅为预期的{cover_ratio*100:.1f}%',
                    'expected': expected,
                    'actual': actual
                })
            elif cover_ratio < 1.2:
                issues.append({
                    'stage': 'management',
                    'severity': 'medium',
                    'issue': '收益覆盖勉强',
                    'description': f'覆盖倍数{cover_ratio:.2f}，接近警戒线',
                })
        
        # 2. 成本超支分析
        budget = bond_data.get('budget', 0)
        actual_cost = bond_data.get('actual_cost', 0)
        if budget > 0 and actual_cost > budget * 1.2:
            issues.append({
                'stage': 'usage',
                'severity': 'high',
                'issue': '成本严重超支',
                'description': f'实际成本{actual_cost}超预算{budget}的20%以上',
                'budget': budget,
                'actual': actual_cost
            })
        
        # 3. 进度滞后分析
        progress = bond_data.get('progress', 0)
        if progress < 0.5:
            issues.append({
                'stage': 'usage',
                'severity': 'medium',
                'issue': '项目进度严重滞后',
                'description': f'当前进度仅{progress*100:.1f}%',
                'progress': progress
            })
        
        # 4. 偿债风险分析
        debt_ratio = bond_data.get('debt_ratio', 0)
        if debt_ratio > 1.2:
            issues.append({
                'stage': 'repayment',
                'severity': 'high',
                'issue': '债务率过高',
                'description': f'债务率{debt_ratio*100:.1f}%超过警戒线120%',
                'debt_ratio': debt_ratio
            })
        
        # 5. 偿债计划分析
        if not bond_data.get('repayment_plan', False):
            issues.append({
                'stage': 'repayment',
                'severity': 'medium',
                'issue': '偿债计划缺失',
                'description': '未制定偿债计划或偿债计划不完整'
            })
        
        # 计算风险评分
        risk_score = 100
        for issue in issues:
            if issue['severity'] == 'high':
                risk_score -= 15
            elif issue['severity'] == 'medium':
                risk_score -= 8
            else:
                risk_score -= 3
        
        risk_score = max(0, risk_score)
        
        if risk_score >= 80:
            risk_level = '低风险'
        elif risk_score >= 60:
            risk_level = '中风险'
        elif risk_score >= 40:
            risk_level = '高风险'
        else:
            risk_level = '极高风险'
        
        return {
            'bond_name': bond_data.get('name', ''),
            'amount': amount,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'issues': issues,
            'issue_count': len(issues),
            'high_risk_count': sum(1 for i in issues if i['severity'] == 'high'),
            'checklist': self.generate_checklist()
        }
    
    def generate_report(self, result: Dict) -> str:
        """生成专项债券审计报告"""
        report = f"""# 专项债券审计报告

## 一、基本情况
- 债券名称：{result.get('bond_name', '未知')}
- 发行规模：{result.get('amount', 0):,.2f} 元
- 风险评分：{result.get('risk_score', 0)}/100
- 风险等级：{result.get('risk_level', '未知')}

## 二、问题发现（{result.get('issue_count', 0)} 项）
"""
        severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        
        stage_names = {'issuance': '发行环节', 'usage': '使用环节', 
                      'management': '管理环节', 'repayment': '偿还环节'}
        
        for i, issue in enumerate(result.get('issues', []), 1):
            sev = issue.get('severity', 'low')
            emoji = severity_emoji.get(sev, '⚪')
            stage = stage_names.get(issue.get('stage', ''), '未知')
            report += f"\n### {i}. {emoji} [{stage}] {issue.get('issue', '')}\n"
            report += f"- 风险等级：{sev.upper()}\n"
            report += f"- 问题描述：{issue.get('description', '')}\n"
        
        report += "\n## 三、四环节检查清单\n"
        for stage_key, stage_data in result.get('checklist', {}).items():
            report += f"\n### {stage_data['name']}\n"
            for item in stage_data['items']:
                report += f"- [ ] **{item['id']}** {item['item']}\n"
                report += f"  - 检查方法：{item['method']}\n"
        
        report += "\n## 四、审计建议\n"
        if result.get('high_risk_count', 0) > 0:
            report += f"\n⚠️ 发现 {result['high_risk_count']} 项高风险问题，建议立即深入调查。\n"
        else:
            report += "\n未发现高风险问题，建议按清单逐项核查。\n"
        
        report += "\n### 重点建议\n"
        report += "1. 对照检查清单逐项核实\n"
        report += "2. 重点关注收益实现和偿债安排\n"
        report += "3. 核实项目进度与资金支付匹配性\n"
        report += "4. 检查信息公开和绩效目标设置\n"
        
        return report

if __name__ == '__main__':
    tool = SpecialBondAuditTool()
    
    # 测试
    bond = {
        'name': 'XX市2024年专项债券',
        'amount': 50000000,
        'budget': 50000000,
        'actual_cost': 65000000,
        'progress': 0.3,
        'expected_revenue': 8000000,
        'revenue': 2000000,
        'debt_ratio': 1.5,
        'repayment_plan': False
    }
    
    result = tool.analyze_bond(bond)
    print(tool.generate_report(result))
