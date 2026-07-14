# -*- coding: utf-8 -*-
"""
BIM工程审计工具 - IFC模型解析与工程量比对
简化版：支持IFC文件解析、工程量提取、与结算书比对
"""
import json
import re
from typing import List, Dict, Optional
from collections import defaultdict

class BIMEngineeringAuditTool:
    """BIM工程审计工具"""
    
    def __init__(self):
        self.quantities = {}
        self.changes = []
    
    def parse_ifc_quantities(self, ifc_data: Dict) -> Dict:
        """解析IFC模型中的工程量"""
        if not ifc_data or 'elements' not in ifc_data:
            return {'error': '无效的IFC数据'}
        
        quantities = defaultdict(lambda: {'count': 0, 'volume': 0, 'area': 0, 'length': 0, 'weight': 0})
        
        for element in ifc_data['elements']:
            elem_type = element.get('type', 'Unknown')
            props = element.get('properties', {})
            
            quantities[elem_type]['count'] += 1
            quantities[elem_type]['volume'] += props.get('Volume', 0)
            quantities[elem_type]['area'] += props.get('Area', 0)
            quantities[elem_type]['length'] += props.get('Length', 0)
            quantities[elem_type]['weight'] += props.get('Weight', 0)
        
        result = {}
        for elem_type, data in quantities.items():
            result[elem_type] = dict(data)
        
        self.quantities = result
        return {
            'element_types': len(result),
            'total_elements': sum(d['count'] for d in result.values()),
            'quantities': result
        }
    
    def compare_with_settlement(self, bim_quantities: Dict, settlement_data: Dict) -> Dict:
        """比对BIM工程量与结算书工程量"""
        if not bim_quantities or not settlement_data:
            return {'error': '缺少比对数据'}
        
        differences = []
        
        for item in settlement_data.get('items', []):
            item_name = item.get('name', '')
            settlement_qty = item.get('quantity', 0)
            
            matched = False
            for elem_type, bim_data in bim_quantities.items():
                if self._match_item(item_name, elem_type):
                    bim_qty = bim_data.get('volume', bim_data.get('area', bim_data.get('length', 0)))
                    
                    if bim_qty > 0:
                        diff_rate = abs(bim_qty - settlement_qty) / bim_qty
                        
                        diff = {
                            'item_name': item_name,
                            'bim_quantity': bim_qty,
                            'settlement_quantity': settlement_qty,
                            'difference': bim_qty - settlement_qty,
                            'difference_rate': diff_rate,
                            'unit': item.get('unit', ''),
                            'unit_price': item.get('unit_price', 0),
                            'amount_difference': (bim_qty - settlement_qty) * item.get('unit_price', 0),
                            'status': self._classify_difference(diff_rate)
                        }
                        differences.append(diff)
                        matched = True
                        break
            
            if not matched:
                differences.append({
                    'item_name': item_name,
                    'bim_quantity': 0,
                    'settlement_quantity': settlement_qty,
                    'difference': -settlement_qty,
                    'difference_rate': 1.0,
                    'status': '未匹配'
                })
        
        total_items = len(differences)
        normal_items = sum(1 for d in differences if d['status'] == '正常')
        attention_items = sum(1 for d in differences if d['status'] == '关注')
        abnormal_items = sum(1 for d in differences if d['status'] == '异常')
        
        total_amount_diff = sum(d.get('amount_difference', 0) for d in differences)
        
        return {
            'total_items': total_items,
            'normal': normal_items,
            'attention': attention_items,
            'abnormal': abnormal_items,
            'total_amount_difference': total_amount_diff,
            'differences': differences
        }
    
    def _match_item(self, item_name: str, elem_type: str) -> bool:
        """匹配结算项目与BIM构件类型"""
        item_lower = item_name.lower()
        elem_lower = elem_type.lower()
        
        keywords = {
            'wall': ['墙', '砌体', '墙体'],
            'slab': ['板', '楼板', '地面'],
            'beam': ['梁', '横梁'],
            'column': ['柱', '立柱'],
            'foundation': ['基础', '地基', '桩'],
            'window': ['窗', '窗户'],
            'door': ['门', '户门'],
            'roof': ['屋面', '屋顶', '防水'],
            'stair': ['楼梯', '梯'],
            'rebar': ['钢筋', '钢筋工程'],
            'concrete': ['混凝土', '砼'],
        }
        
        for key, cn_names in keywords.items():
            if key in elem_lower:
                for cn in cn_names:
                    if cn in item_lower:
                        return True
        
        return False
    
    def _classify_difference(self, rate: float) -> str:
        """分类差异等级"""
        if rate < 0.03:
            return '正常'
        elif rate < 0.05:
            return '关注'
        else:
            return '异常'
    
    def analyze_change_orders(self, change_orders: List[Dict]) -> Dict:
        """分析变更单"""
        if not change_orders:
            return {'error': '无变更单数据'}
        
        type_counts = defaultdict(int)
        reason_counts = defaultdict(int)
        total_increase = 0
        total_decrease = 0
        
        for order in change_orders:
            change_type = order.get('type', '未知')
            type_counts[change_type] += 1
            
            reason = order.get('reason', '未知')
            reason_counts[reason] += 1
            
            amount = order.get('amount', 0)
            if amount > 0:
                total_increase += amount
            else:
                total_decrease += abs(amount)
        
        evaluations = []
        for order in change_orders:
            score = 50
            
            amount = abs(order.get('amount', 0))
            if amount < 10000:
                score += 10
            elif amount < 100000:
                score += 0
            else:
                score -= 10
            
            reason = order.get('reason', '')
            if '现场条件' in reason or '设计优化' in reason:
                score += 15
            elif '业主要求' in reason:
                score += 5
            elif '未明确' in reason or '其他' in reason:
                score -= 10
            
            before = order.get('before', '')
            after = order.get('after', '')
            if before and after and len(before) > 5 and len(after) > 5:
                score += 10
            
            score = max(0, min(100, score))
            
            if score >= 80:
                evaluation = '高度合理'
            elif score >= 60:
                evaluation = '基本合理'
            elif score >= 40:
                evaluation = '存疑'
            else:
                evaluation = '不合理'
            
            evaluations.append({
                'order_id': order.get('order_id', ''),
                'type': order.get('type', ''),
                'amount': order.get('amount', 0),
                'reason': reason,
                'score': score,
                'evaluation': evaluation
            })
        
        return {
            'total_changes': len(change_orders),
            'type_distribution': dict(type_counts),
            'reason_distribution': dict(reason_counts),
            'total_increase': total_increase,
            'total_decrease': total_decrease,
            'net_change': total_increase - total_decrease,
            'evaluations': evaluations,
            'high_risk_changes': sum(1 for e in evaluations if e['score'] < 40)
        }
    
    def generate_report(self, comparison: Dict, changes: Dict = None) -> str:
        """生成BIM工程审计报告"""
        report = f"# BIM工程审计报告\n\n## 一、工程量比对结果\n\n### 总体情况\n"
        report += f"- 比对项目数：{comparison.get('total_items', 0)} 项\n"
        report += f"- 正常（差异<3%）：{comparison.get('normal', 0)} 项\n"
        report += f"- 关注（3%-5%）：{comparison.get('attention', 0)} 项\n"
        report += f"- 异常（差异>5%）：{comparison.get('abnormal', 0)} 项\n"
        report += f"- 金额总差异：{comparison.get('total_amount_difference', 0):,.2f} 元\n\n"
        
        report += "### 差异明细\n"
        for diff in comparison.get('differences', []):
            status = diff.get('status', '')
            emoji = {'正常': 'OK', '关注': '!!', '异常': 'XX', '未匹配': '??'}.get(status, '')
            report += f"\n{emoji} **{diff['item_name']}**\n"
            report += f"- BIM工程量：{diff.get('bim_quantity', 0):,.2f}\n"
            report += f"- 结算工程量：{diff.get('settlement_quantity', 0):,.2f}\n"
            report += f"- 差异：{diff.get('difference', 0):,.2f}（{diff.get('difference_rate', 0)*100:.1f}%）\n"
            report += f"- 状态：{status}\n"
            if 'amount_difference' in diff:
                report += f"- 金额差异：{diff['amount_difference']:,.2f} 元\n"
        
        if changes:
            report += f"\n## 二、变更单分析\n"
            report += f"- 变更总数：{changes.get('total_changes', 0)} 项\n"
            report += f"- 增加金额：{changes.get('total_increase', 0):,.2f} 元\n"
            report += f"- 减少金额：{changes.get('total_decrease', 0):,.2f} 元\n"
            report += f"- 净变更：{changes.get('net_change', 0):,.2f} 元\n"
            report += f"- 高风险变更：{changes.get('high_risk_changes', 0)} 项\n"
            
            report += "\n### 变更合理性评估\n"
            for eva in changes.get('evaluations', []):
                emoji = {'高度合理': 'OK', '基本合理': 'ok', '存疑': '??', '不合理': 'XX'}.get(eva['evaluation'], '')
                report += f"{emoji} {eva['order_id']}：{eva['evaluation']}（{eva['score']}分）- 金额{eva['amount']:,.2f}元\n"
                report += f"  原因：{eva['reason']}\n"
        
        report += "\n## 三、审计建议\n"
        if comparison.get('abnormal', 0) > 0:
            report += f"\n重点关注：发现{comparison['abnormal']}项工程量异常差异，建议深入核查\n"
        
        if changes and changes.get('high_risk_changes', 0) > 0:
            report += f"\n变更风险：发现{changes['high_risk_changes']}项高风险变更，建议逐一核实\n"
        
        report += "\n1. 对异常差异项进行现场核查\n"
        report += "2. 核实变更单的合理性和合规性\n"
        report += "3. 检查隐蔽工程的影像资料\n"
        report += "4. 复核工程量计算过程\n"
        
        return report
