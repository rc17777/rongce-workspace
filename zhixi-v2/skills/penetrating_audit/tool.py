"""
穿透式审计工具 - 数据追踪与路径分析
支持资金穿透、项目穿透、供应链穿透
"""
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

class PenetratingAuditTool:
    """穿透式审计工具"""
    
    def __init__(self):
        self.penetration_types = {
            'fund': '资金穿透',
            'project': '项目穿透',
            'supply_chain': '供应链穿透'
        }
    
    def fund_penetration(self, transactions: List[Dict]) -> Dict:
        """资金穿透分析
        
        Args:
            transactions: 交易记录列表
                [{date, from_account, to_account, amount, purpose, project_id}]
        
        Returns:
            穿透分析结果
        """
        if not transactions:
            return {'error': '无交易数据'}
        
        # 构建资金流向图
        flow_graph = {}
        for t in transactions:
            from_acc = t.get('from_account', '')
            to_acc = t.get('to_account', '')
            amount = t.get('amount', 0)
            
            if from_acc not in flow_graph:
                flow_graph[from_acc] = {'out': [], 'in': [], 'balance': 0}
            if to_acc not in flow_graph:
                flow_graph[to_acc] = {'out': [], 'in': [], 'balance': 0}
            
            flow_graph[from_acc]['out'].append({
                'to': to_acc, 'amount': amount, 'date': t.get('date', '')
            })
            flow_graph[to_acc]['in'].append({
                'from': from_acc, 'amount': amount, 'date': t.get('date', '')
            })
            flow_graph[from_acc]['balance'] -= amount
            flow_graph[to_acc]['balance'] += amount
        
        # 识别异常模式
        anomalies = []
        
        # 1. 资金闭环检测（多步回流）
        for account, data in flow_graph.items():
            for out_tx in data['out']:
                target = out_tx['to']
                if target in flow_graph:
                    target_data = flow_graph[target]
                    for target_out in target_data['out']:
                        if target_out['to'] == account:
                            anomalies.append({
                                'type': '资金闭环',
                                'severity': 'high',
                                'description': f'{account} → {target}({out_tx["amount"]}) → 回流到{account}',
                                'accounts': [account, target]
                            })
        
        # 2. 大额异常检测
        amounts = [t.get('amount', 0) for t in transactions]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        
        for t in transactions:
            if t.get('amount', 0) > avg_amount * 5:
                anomalies.append({
                    'type': '大额异常',
                    'severity': 'medium',
                    'description': f'单笔金额{t["amount"]}远超均值{avg_amount:.2f}',
                    'transaction': t
                })
        
        # 3. 频繁拆分检测
        from collections import Counter
        purposes = [t.get('purpose', '') for t in transactions]
        purpose_counts = Counter(purposes)
        
        for purpose, count in purpose_counts.items():
            if count > 5:
                anomalies.append({
                    'type': '频繁拆分',
                    'severity': 'medium',
                    'description': f'同一用途"{purpose}"出现{count}次，疑似拆分',
                    'purpose': purpose,
                    'count': count
                })
        
        return {
            'type': '资金穿透',
            'total_transactions': len(transactions),
            'total_amount': sum(t.get('amount', 0) for t in transactions),
            'accounts_involved': len(flow_graph),
            'flow_graph': flow_graph,
            'anomalies': anomalies,
            'anomaly_count': len(anomalies)
        }
    
    def project_penetration(self, projects: List[Dict]) -> Dict:
        """项目穿透分析
        
        Args:
            projects: 项目记录列表
                [{project_id, name, budget, actual_cost, status, start_date, end_date, changes}]
        
        Returns:
            穿透分析结果
        """
        if not projects:
            return {'error': '无项目数据'}
        
        anomalies = []
        
        for p in projects:
            # 1. 成本超支检测
            budget = p.get('budget', 0)
            actual = p.get('actual_cost', 0)
            if budget > 0 and actual > budget * 1.2:
                anomalies.append({
                    'type': '成本超支',
                    'severity': 'high',
                    'project': p.get('name', ''),
                    'description': f'实际成本{actual}超预算{budget}的20%以上',
                    'budget': budget,
                    'actual': actual,
                    'over_rate': (actual - budget) / budget
                })
            
            # 2. 频繁变更检测
            changes = p.get('changes', [])
            if len(changes) > 3:
                anomalies.append({
                    'type': '频繁变更',
                    'severity': 'medium',
                    'project': p.get('name', ''),
                    'description': f'项目变更{len(changes)}次',
                    'change_count': len(changes)
                })
            
            # 3. 进度滞后检测
            status = p.get('status', '')
            end_date = p.get('end_date', '')
            if status == '进行中' and end_date:
                try:
                    from datetime import datetime
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    if datetime.now() > end:
                        anomalies.append({
                            'type': '进度滞后',
                            'severity': 'medium',
                            'project': p.get('name', ''),
                            'description': f'项目超期未完成，计划完成{end_date}'
                        })
                except:
                    pass
        
        return {
            'type': '项目穿透',
            'total_projects': len(projects),
            'total_budget': sum(p.get('budget', 0) for p in projects),
            'total_actual': sum(p.get('actual_cost', 0) for p in projects),
            'anomalies': anomalies,
            'anomaly_count': len(anomalies)
        }
    
    def supply_chain_penetration(self, suppliers: List[Dict], contracts: List[Dict]) -> Dict:
        """供应链穿透分析
        
        Args:
            suppliers: 供应商列表 [{name, contact, address, legal_person}]
            contracts: 合同列表 [{contract_id, supplier, amount, date, items}]
        
        Returns:
            穿透分析结果
        """
        if not suppliers or not contracts:
            return {'error': '缺少供应商或合同数据'}
        
        anomalies = []
        
        # 1. 同一联系人检测
        contacts = {}
        for s in suppliers:
            contact = s.get('contact', '')
            if contact:
                if contact not in contacts:
                    contacts[contact] = []
                contacts[contact].append(s.get('name', ''))
        
        for contact, names in contacts.items():
            if len(names) > 1:
                anomalies.append({
                    'type': '同一联系人',
                    'severity': 'high',
                    'description': f'多家供应商使用同一联系人{contact}',
                    'suppliers': names
                })
        
        # 2. 同一法人检测
        legals = {}
        for s in suppliers:
            lp = s.get('legal_person', '')
            if lp:
                if lp not in legals:
                    legals[lp] = []
                legals[lp].append(s.get('name', ''))
        
        for lp, names in legals.items():
            if len(names) > 1:
                anomalies.append({
                    'type': '同一法人',
                    'severity': 'high',
                    'description': f'多家供应商同一法定代表人{lp}',
                    'suppliers': names
                })
        
        # 3. 地址相似检测
        addresses = {}
        for s in suppliers:
            addr = s.get('address', '')[:20]  # 简化地址
            if addr:
                if addr not in addresses:
                    addresses[addr] = []
                addresses[addr].append(s.get('name', ''))
        
        for addr, names in addresses.items():
            if len(names) > 1:
                anomalies.append({
                    'type': '地址相同',
                    'severity': 'medium',
                    'description': f'多家供应商注册地址相同',
                    'suppliers': names
                })
        
        # 4. 价格异常检测
        from collections import defaultdict
        item_prices = defaultdict(list)
        
        for c in contracts:
            items = c.get('items', [])
            for item in items:
                name = item.get('name', '')
                price = item.get('unit_price', 0)
                if name and price:
                    item_prices[name].append(price)
        
        for item_name, prices in item_prices.items():
            if len(prices) > 2:
                avg_price = sum(prices) / len(prices)
                for price in prices:
                    if price > avg_price * 1.5 or price < avg_price * 0.5:
                        anomalies.append({
                            'type': '价格异常',
                            'severity': 'medium',
                            'description': f'商品"{item_name}"价格{price}偏离均价{avg_price:.2f}',
                            'item': item_name,
                            'price': price,
                            'avg_price': avg_price
                        })
        
        return {
            'type': '供应链穿透',
            'supplier_count': len(suppliers),
            'contract_count': len(contracts),
            'total_amount': sum(c.get('amount', 0) for c in contracts),
            'anomalies': anomalies,
            'anomaly_count': len(anomalies)
        }
    
    def generate_report(self, result: Dict) -> str:
        """生成穿透式审计报告"""
        report = f"""# 穿透式审计分析报告

## 一、审计类型：{result.get('type', '未知')}

## 二、基本情况
"""
        if 'total_transactions' in result:
            report += f"- 交易笔数：{result['total_transactions']}\n"
            report += f"- 涉及金额：{result['total_amount']:,.2f} 元\n"
            report += f"- 涉及账户：{result['accounts_involved']} 个\n"
        
        if 'total_projects' in result:
            report += f"- 项目数量：{result['total_projects']}\n"
            report += f"- 预算总额：{result['total_budget']:,.2f} 元\n"
            report += f"- 实际成本：{result['total_actual']:,.2f} 元\n"
        
        if 'supplier_count' in result:
            report += f"- 供应商数量：{result['supplier_count']}\n"
            report += f"- 合同数量：{result['contract_count']}\n"
            report += f"- 合同金额：{result['total_amount']:,.2f} 元\n"
        
        report += f"\n## 三、异常发现（{result.get('anomaly_count', 0)} 项）\n\n"
        
        severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        
        for i, anomaly in enumerate(result.get('anomalies', []), 1):
            sev = anomaly.get('severity', 'low')
            emoji = severity_emoji.get(sev, '⚪')
            report += f"### {i}. {emoji} {anomaly.get('type', '未知')}\n"
            report += f"- 风险等级：{sev.upper()}\n"
            report += f"- 问题描述：{anomaly.get('description', '')}\n"
            
            if 'accounts' in anomaly:
                report += f"- 涉及账户：{', '.join(anomaly['accounts'])}\n"
            if 'project' in anomaly:
                report += f"- 涉及项目：{anomaly['project']}\n"
            if 'suppliers' in anomaly:
                report += f"- 涉及供应商：{', '.join(anomaly['suppliers'])}\n"
            
            report += "\n"
        
        report += "## 四、审计建议\n\n"
        
        if result.get('anomaly_count', 0) > 0:
            high_risks = [a for a in result.get('anomalies', []) if a.get('severity') == 'high']
            if high_risks:
                report += "⚠️ **重点关注**：发现高风险异常，建议立即深入调查\n\n"
            else:
                report += "△ **一般关注**：发现中等风险异常，建议核实确认\n\n"
        else:
            report += "✅ **正常**：未发现明显异常\n\n"
        
        return report

if __name__ == '__main__':
    # 测试
    tool = PenetratingAuditTool()
    
    # 测试资金穿透
    transactions = [
        {'date': '2024-01-01', 'from_account': '财政专户', 'to_account': '项目A', 'amount': 1000000, 'purpose': '工程款'},
        {'date': '2024-01-02', 'from_account': '项目A', 'to_account': '供应商甲', 'amount': 500000, 'purpose': '材料款'},
        {'date': '2024-01-03', 'from_account': '供应商甲', 'to_account': '财政专户', 'amount': 500000, 'purpose': '退款'},
        {'date': '2024-01-04', 'from_account': '项目A', 'to_account': '供应商甲', 'amount': 500000, 'purpose': '材料款'},
        {'date': '2024-01-05', 'from_account': '项目A', 'to_account': '供应商甲', 'amount': 500000, 'purpose': '材料款'},
    ]
    result = tool.fund_penetration(transactions)
    print(tool.generate_report(result))
