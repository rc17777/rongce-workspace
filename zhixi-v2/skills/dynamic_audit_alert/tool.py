"""
动态审计预警工具 - 规则引擎与预警模型
"""
import json
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class DynamicAuditAlertTool:
    """动态审计预警工具"""
    
    # 预警规则库
    ALERT_RULES = {
        'financial': [
            {
                'id': 'F001',
                'name': '单笔大额支出',
                'condition': 'amount > monthly_avg * 5',
                'level': 'orange',
                'message': '单笔支出超过月均5倍，需核查'
            },
            {
                'id': 'F002',
                'name': '频繁小额拆分',
                'condition': 'daily_split_count > 5',
                'level': 'orange',
                'message': '同一项目日拆分超过5次，疑似规避审批'
            },
            {
                'id': 'F003',
                'name': '资金流向异常',
                'condition': 'flow_to_related == True',
                'level': 'red',
                'message': '资金流向关联账户，需深入核查'
            },
            {
                'id': 'F004',
                'name': '资金长期闲置',
                'condition': 'idle_days > 90',
                'level': 'yellow',
                'message': '资金闲置超过90天，需关注使用效率'
            },
        ],
        'project': [
            {
                'id': 'P001',
                'name': '项目进度严重滞后',
                'condition': 'progress_rate < 0.5',
                'level': 'orange',
                'message': '项目进度严重滞后，需关注资金支付匹配性'
            },
            {
                'id': 'P002',
                'name': '频繁变更',
                'condition': 'monthly_changes > 3',
                'level': 'orange',
                'message': '项目月变更超过3次，需评估变更合理性'
            },
            {
                'id': 'P003',
                'name': '成本超支',
                'condition': 'cost_overrun_rate > 0.2',
                'level': 'red',
                'message': '项目成本超支20%以上，需深入分析原因'
            },
        ],
        'compliance': [
            {
                'id': 'C001',
                'name': '政策变动影响',
                'condition': 'new_policy_impact == True',
                'level': 'yellow',
                'message': '新政策可能影响项目，需评估影响'
            },
            {
                'id': 'C002',
                'name': '违规处罚',
                'condition': 'new_penalty == True',
                'level': 'red',
                'message': '新增行政处罚，需核查整改情况'
            },
        ],
        'external': [
            {
                'id': 'E001',
                'name': '负面舆情',
                'condition': 'negative_news_count > 0',
                'level': 'yellow',
                'message': '出现负面舆情，需关注影响'
            },
            {
                'id': 'E002',
                'name': '关联风险',
                'condition': 'related_party_risk == True',
                'level': 'orange',
                'message': '关联方出现重大风险，需评估传导影响'
            },
        ]
    }
    
    # 预警级别配置
    LEVEL_CONFIG = {
        'red': {'name': '红色预警', 'emoji': '🔴', 'response_time': '2小时', 'channels': ['系统', '邮件', '短信', '电话']},
        'orange': {'name': '橙色预警', 'emoji': '🟡', 'response_time': '24小时', 'channels': ['系统', '邮件', '短信']},
        'yellow': {'name': '黄色预警', 'emoji': '🟢', 'response_time': '7天', 'channels': ['系统', '日报']},
    }
    
    def __init__(self):
        self.alert_history = []
        self.rule_stats = defaultdict(int)
    
    def evaluate_rules(self, data: Dict) -> List[Dict]:
        """评估数据触发哪些预警规则
        
        Args:
            data: 监测数据
                {
                    'amount': 金额,
                    'monthly_avg': 月均金额,
                    'daily_split_count': 日拆分次数,
                    'flow_to_related': 是否流向关联账户,
                    'idle_days': 闲置天数,
                    'progress_rate': 进度率,
                    'monthly_changes': 月变更次数,
                    'cost_overrun_rate': 成本超支率,
                    'new_policy_impact': 政策变动影响,
                    'new_penalty': 新增处罚,
                    'negative_news_count': 负面新闻数,
                    'related_party_risk': 关联方风险,
                }
        
        Returns:
            触发的预警列表
        """
        alerts = []
        
        for category, rules in self.ALERT_RULES.items():
            for rule in rules:
                if self._check_condition(rule['condition'], data):
                    alert = {
                        'id': rule['id'],
                        'name': rule['name'],
                        'category': category,
                        'level': rule['level'],
                        'message': rule['message'],
                        'timestamp': datetime.now().isoformat(),
                        'data': data,
                        'status': 'new'
                    }
                    alerts.append(alert)
                    self.rule_stats[rule['id']] += 1
        
        self.alert_history.extend(alerts)
        return alerts
    
    def _check_condition(self, condition: str, data: Dict) -> bool:
        """检查条件是否满足"""
        try:
            # 简单条件解析
            if '>' in condition:
                left, right = condition.split('>', 1)
                left_val = self._get_value(left.strip(), data)
                right_val = self._get_value(right.strip(), data)
                if left_val is not None and right_val is not None:
                    return left_val > right_val
            elif '==' in condition:
                left, right = condition.split('==', 1)
                left_val = self._get_value(left.strip(), data)
                right_val = self._get_value(right.strip(), data)
                if left_val is not None and right_val is not None:
                    return left_val == right_val
            return False
        except:
            return False
    
    def _get_value(self, expr: str, data: Dict):
        """从数据中获取值"""
        expr = expr.strip()
        
        # 直接取字段
        if expr in data:
            return data[expr]
        
        # 数值常量
        try:
            return float(expr)
        except:
            pass
        
        # 布尔常量
        if expr.lower() == 'true':
            return True
        if expr.lower() == 'false':
            return False
        
        return None
    
    def generate_alert_report(self, alerts: List[Dict]) -> str:
        """生成预警报告"""
        if not alerts:
            return "✅ 未发现预警，系统运行正常"
        
        # 按级别分组
        grouped = {'red': [], 'orange': [], 'yellow': []}
        for alert in alerts:
            level = alert.get('level', 'yellow')
            grouped[level].append(alert)
        
        report = f"""# 动态审计预警报告

## 一、预警概览
- 预警总数：{len(alerts)} 项
- 🔴 红色预警：{len(grouped['red'])} 项
- 🟡 橙色预警：{len(grouped['orange'])} 项
- 🟢 黄色预警：{len(grouped['yellow'])} 项

## 二、预警详情
"""
        
        for level in ['red', 'orange', 'yellow']:
            level_alerts = grouped[level]
            if not level_alerts:
                continue
            
            config = self.LEVEL_CONFIG.get(level, {})
            report += f"\n### {config.get('emoji', '')} {config.get('name', level)}（{len(level_alerts)}项）\n"
            report += f"- 响应时限：{config.get('response_time', '未知')}\n"
            report += f"- 推送渠道：{', '.join(config.get('channels', []))}\n\n"
            
            for i, alert in enumerate(level_alerts, 1):
                report += f"{i}. **{alert['name']}**（{alert['id']}）\n"
                report += f"   - {alert['message']}\n"
                report += f"   - 触发时间：{alert['timestamp'][:19]}\n\n"
        
        report += "## 三、处置建议\n\n"
        if grouped['red']:
            report += "⚠️ **红色预警需立即响应**：\n"
            for alert in grouped['red']:
                report += f"- {alert['name']}：立即核查相关数据，必要时暂停相关业务\n"
        
        if grouped['orange']:
            report += "\n△ **橙色预警需24小时内响应**：\n"
            for alert in grouped['orange']:
                report += f"- {alert['name']}：安排专人核实，评估风险影响\n"
        
        if grouped['yellow']:
            report += "\n⚠️ **黄色预警纳入日常关注**：\n"
            for alert in grouped['yellow']:
                report += f"- {alert['name']}：在下次审计中重点关注\n"
        
        return report
    
    def analyze_trend(self, days: int = 30) -> Dict:
        """分析预警趋势
        
        Args:
            days: 分析天数
        
        Returns:
            趋势分析结果
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]
        
        # 按天统计
        daily_counts = defaultdict(lambda: {'red': 0, 'orange': 0, 'yellow': 0})
        for alert in recent_alerts:
            date = alert['timestamp'][:10]
            level = alert.get('level', 'yellow')
            daily_counts[date][level] += 1
        
        # 按规则统计
        rule_counts = defaultdict(int)
        for alert in recent_alerts:
            rule_counts[alert.get('name', '未知')] += 1
        
        return {
            'total_alerts': len(recent_alerts),
            'daily_trend': dict(daily_counts),
            'top_rules': sorted(rule_counts.items(), key=lambda x: -x[1])[:5],
            'trend_direction': '上升' if len(recent_alerts) > days * 0.5 else '平稳'
        }
    
    def get_rule_effectiveness(self) -> Dict:
        """获取规则有效性统计"""
        return {
            'rule_trigger_counts': dict(self.rule_stats),
            'most_triggered': sorted(self.rule_stats.items(), key=lambda x: -x[1])[:5] if self.rule_stats else []
        }

if __name__ == '__main__':
    tool = DynamicAuditAlertTool()
    
    # 测试
    test_data = {
        'amount': 500000,
        'monthly_avg': 50000,
        'daily_split_count': 6,
        'flow_to_related': True,
        'idle_days': 120,
        'progress_rate': 0.3,
        'monthly_changes': 4,
        'cost_overrun_rate': 0.25,
        'new_policy_impact': True,
        'new_penalty': False,
        'negative_news_count': 1,
        'related_party_risk': True,
    }
    
    alerts = tool.evaluate_rules(test_data)
    print(tool.generate_alert_report(alerts))
    
    print("\n规则有效性:")
    print(json.dumps(tool.get_rule_effectiveness(), ensure_ascii=False, indent=2))
