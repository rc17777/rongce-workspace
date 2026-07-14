"""
风险画像工具 - 多维度评分模型与雷达图生成
"""
import json
import numpy as np
from typing import List, Dict

class AuditRiskPortraitTool:
    """审计风险画像工具"""
    
    # 风险维度定义
    DIMENSIONS = {
        'financial': {
            'name': '财务风险',
            'weight': 0.25,
            'indicators': [
                {'name': '资产负债率', 'formula': '负债/资产', 'threshold': 0.8},
                {'name': '流动比率', 'formula': '流动资产/流动负债', 'threshold': 1.0},
                {'name': '收支平衡率', 'formula': '收入/支出', 'threshold': 1.0},
            ]
        },
        'operation': {
            'name': '运营风险',
            'weight': 0.20,
            'indicators': [
                {'name': '项目完成率', 'formula': '完成项目/计划项目', 'threshold': 0.8},
                {'name': '预算执行率', 'formula': '实际支出/预算', 'threshold': 0.9},
            ]
        },
        'compliance': {
            'name': '合规风险',
            'weight': 0.25,
            'indicators': [
                {'name': '违规频率', 'formula': '违规次数/审计次数', 'threshold': 0.1},
                {'name': '整改完成率', 'formula': '完成整改/应整改', 'threshold': 0.9},
            ]
        },
        'external': {
            'name': '外部风险',
            'weight': 0.20,
            'indicators': [
                {'name': '舆情负面指数', 'formula': '负面报道/总报道', 'threshold': 0.2},
                {'name': '政策变动影响', 'formula': '政策变动次数', 'threshold': 2},
            ]
        },
        'history': {
            'name': '历史风险',
            'weight': 0.10,
            'indicators': [
                {'name': '历史问题数', 'formula': '累计发现问题数', 'threshold': 5},
                {'name': '整改质量', 'formula': '整改质量评分', 'threshold': 80},
            ]
        }
    }
    
    def calculate_dimension_score(self, dimension: str, data: Dict) -> float:
        """计算单维度得分
        
        Args:
            dimension: 维度key
            data: 指标数据
        
        Returns:
            维度得分 (0-100)
        """
        if dimension not in self.DIMENSIONS:
            return 50
        
        dim_info = self.DIMENSIONS[dimension]
        indicators = dim_info['indicators']
        
        scores = []
        for ind in indicators:
            name = ind['name']
            threshold = ind['threshold']
            
            if name in data:
                value = data[name]
                # 计算得分
                if threshold > 0:
                    if dimension == 'compliance' and name == '违规频率':
                        # 反向指标：违规频率越低越好
                        score = max(0, 100 - (value / threshold) * 100)
                    elif dimension == 'compliance' and name == '整改完成率':
                        # 正向指标
                        score = min(100, (value / threshold) * 100)
                    elif dimension == 'financial' and name == '资产负债率':
                        # 反向指标
                        score = max(0, 100 - (value / threshold) * 100 * 0.8)
                    elif dimension == 'external' and name == '舆情负面指数':
                        # 反向指标
                        score = max(0, 100 - (value / threshold) * 100)
                    else:
                        # 默认正向指标
                        score = min(100, (value / threshold) * 100)
                else:
                    score = 50
            else:
                score = 50  # 数据缺失默认中等
            
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 50
    
    def generate_portrait(self, client_data: Dict) -> Dict:
        """生成风险画像
        
        Args:
            client_data: 客户数据
                {
                    'name': '单位名称',
                    'type': '单位性质',
                    'industry': '行业',
                    'financial': {'资产负债率': 0.75, '流动比率': 1.2, '收支平衡率': 1.1},
                    'operation': {'项目完成率': 0.85, '预算执行率': 0.92},
                    'compliance': {'违规频率': 0.05, '整改完成率': 0.95},
                    'external': {'舆情负面指数': 0.1, '政策变动影响': 1},
                    'history': {'历史问题数': 3, '整改质量': 85},
                }
        
        Returns:
            画像结果
        """
        dimension_scores = {}
        
        for dim_key, dim_info in self.DIMENSIONS.items():
            dim_data = client_data.get(dim_key, {})
            score = self.calculate_dimension_score(dim_key, dim_data)
            dimension_scores[dim_key] = {
                'name': dim_info['name'],
                'weight': dim_info['weight'],
                'score': round(score, 2)
            }
        
        # 计算综合得分
        total_score = sum(
            d['score'] * d['weight'] 
            for d in dimension_scores.values()
        )
        
        # 风险等级
        if total_score >= 80:
            risk_level = '低风险'
            risk_color = 'green'
        elif total_score >= 60:
            risk_level = '中风险'
            risk_color = 'yellow'
        elif total_score >= 40:
            risk_level = '高风险'
            risk_color = 'orange'
        else:
            risk_level = '极高风险'
            risk_color = 'red'
        
        # 风险标签
        risk_tags = []
        for dim_key, dim_data in dimension_scores.items():
            if dim_data['score'] < 40:
                risk_tags.append(f"{dim_data['name']}-极高")
            elif dim_data['score'] < 60:
                risk_tags.append(f"{dim_data['name']}-较高")
        
        # 生成雷达图数据
        radar_data = {
            'dimensions': [d['name'] for d in dimension_scores.values()],
            'scores': [d['score'] for d in dimension_scores.values()],
            'weights': [d['weight'] for d in dimension_scores.values()]
        }
        
        return {
            'client_name': client_data.get('name', '未知'),
            'client_type': client_data.get('type', ''),
            'industry': client_data.get('industry', ''),
            'total_score': round(total_score, 2),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_tags': risk_tags,
            'dimension_scores': dimension_scores,
            'radar_data': radar_data,
            'audit_suggestions': self._generate_suggestions(dimension_scores)
        }
    
    def _generate_suggestions(self, dimension_scores: Dict) -> List[str]:
        """生成审计建议"""
        suggestions = []
        
        # 按得分排序
        sorted_dims = sorted(
            dimension_scores.items(),
            key=lambda x: x[1]['score']
        )
        
        # 对最低分项给出建议
        for dim_key, dim_data in sorted_dims[:2]:
            if dim_data['score'] < 60:
                suggestions.append(
                    f"重点关注{dim_data['name']}（得分{dim_data['score']}）：" +
                    f"建议深入核查该维度相关业务流程和内部控制"
                )
            elif dim_data['score'] < 80:
                suggestions.append(
                    f"关注{dim_data['name']}（得分{dim_data['score']}）：" +
                    f"建议抽样检查"
                )
        
        if not suggestions:
            suggestions.append("整体风险可控，建议按常规程序执行审计")
        
        return suggestions
    
    def generate_radar_chart_config(self, portrait: Dict) -> Dict:
        """生成雷达图配置（ECharts格式）"""
        radar_data = portrait.get('radar_data', {})
        
        return {
            'title': {
                'text': f"{portrait['client_name']} - 风险雷达图",
                'subtext': f"综合评分：{portrait['total_score']} | 风险等级：{portrait['risk_level']}"
            },
            'radar': {
                'indicator': [
                    {'name': d, 'max': 100}
                    for d in radar_data.get('dimensions', [])
                ]
            },
            'series': [{
                'type': 'radar',
                'data': [{
                    'value': radar_data.get('scores', []),
                    'name': '风险评分'
                }]
            }]
        }
    
    def generate_report(self, portrait: Dict) -> str:
        """生成画像报告"""
        report = f"""# 审计风险画像报告

## 一、基本信息
- 单位名称：{portrait.get('client_name', '未知')}
- 单位性质：{portrait.get('client_type', '未知')}
- 所属行业：{portrait.get('industry', '未知')}

## 二、综合评分
- **总分**：{portrait.get('total_score', 0)}/100
- **风险等级**：{portrait.get('risk_level', '未知')}

## 三、维度分析
"""
        for dim_key, dim_data in portrait.get('dimension_scores', {}).items():
            score = dim_data['score']
            bar = '█' * int(score / 5) + '░' * (20 - int(score / 5))
            report += f"\n### {dim_data['name']}（权重{int(dim_data['weight']*100)}%）\n"
            report += f"- 得分：{score} [{bar}]\n"
            if score < 40:
                report += "- 状态：⚠️ 极高风险\n"
            elif score < 60:
                report += "- 状态：△ 较高风险\n"
            elif score < 80:
                report += "- 状态：⚠️ 中等风险\n"
            else:
                report += "- 状态：✅ 风险可控\n"
        
        # 风险标签
        tags = portrait.get('risk_tags', [])
        if tags:
            report += f"\n## 四、风险标签\n"
            for tag in tags:
                report += f"- 🏷️ {tag}\n"
        
        # 审计建议
        suggestions = portrait.get('audit_suggestions', [])
        if suggestions:
            report += f"\n## 五、审计建议\n"
            for i, s in enumerate(suggestions, 1):
                report += f"{i}. {s}\n"
        
        return report

if __name__ == '__main__':
    tool = AuditRiskPortraitTool()
    
    # 测试
    client = {
        'name': 'XX市财政局',
        'type': '行政单位',
        'industry': '财政',
        'financial': {'资产负债率': 0.75, '流动比率': 1.2, '收支平衡率': 1.1},
        'operation': {'项目完成率': 0.85, '预算执行率': 0.92},
        'compliance': {'违规频率': 0.05, '整改完成率': 0.95},
        'external': {'舆情负面指数': 0.1, '政策变动影响': 1},
        'history': {'历史问题数': 3, '整改质量': 85},
    }
    
    portrait = tool.generate_portrait(client)
    print(tool.generate_report(portrait))
    print("\n雷达图配置:")
    print(json.dumps(tool.generate_radar_chart_config(portrait), ensure_ascii=False))
