#!/usr/bin/env python3
"""
三步法 Step 1：算法雷达 — 持续扫描学术界/工业界新算法
"""

import json, os, re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class AlgorithmEntry:
    """算法条目"""
    name: str                    # 算法名称
    category: str                # 类别: 统计/NLP/图分析/时序/多模型/合规
    scenario: str                # 审计场景
    source: str                  # 来源: 论文/开源/工业
    year: int                    # 发表年份
    status: str = 'watching'     # watching/testing/adopted/rejected
    replace: str = ''            # 替代哪个现有算法
    chinese_support: bool = False
    local_deploy: bool = False   # 是否可本地部署
    complexity: str = 'low'      # low/medium/high
    roe_score: int = 0           # 投入产出比 1-5
    notes: str = ''
    test_date: str = ''
    test_result: str = ''
    adopted_version: str = ''


class AlgorithmRadar:
    """
    算法雷达：扫描、跟踪、评估
    
    使用：
    >>> radar = AlgorithmRadar()
    >>> radar.scan()  # 扫描默认来源
    >>> radar.report()  # 输出当前状态
    """
    
    def __init__(self, radar_file: str = ''):
        if not radar_file:
            radar_file = os.path.join(
                os.path.dirname(__file__), '..', '..', 
                'config', 'algorithm_quality', 'radar.json'
            )
        self.radar_file = radar_file
        self.entries: List[AlgorithmEntry] = []
        self.load()
    
    def load(self):
        """加载雷达数据库"""
        if os.path.exists(self.radar_file):
            with open(self.radar_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.entries = [AlgorithmEntry(**e) for e in data.get('entries', [])]
        else:
            self._seed_database()
    
    def save(self):
        """保存雷达数据库"""
        os.makedirs(os.path.dirname(self.radar_file), exist_ok=True)
        data = {
            'last_updated': datetime.now().isoformat(),
            'total_entries': len(self.entries),
            'entries': [asdict(e) for e in self.entries]
        }
        with open(self.radar_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _seed_database(self):
        """初始种子数据库"""
        seeds = [
            AlgorithmEntry('Isolation Forest', '统计', '财务异常检测', 'sklearn', 2008,
                          status='adopted', replace='Z-score(单独使用)', 
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=5, notes='多维无监督异常检测，零标签需求'),
            AlgorithmEntry('BGE-M3', 'NLP', '合同相似度', 'BAAI智源', 2024,
                          status='testing', replace='Sentence-BERT',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=5, notes='中文embedding SOTA, 支持8192 tokens'),
            AlgorithmEntry('FrauDAR', '图分析', '围标串标', 'CMU', 2016,
                          status='testing', replace='PageRank(围标检测)',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=5, notes='二部图稠密子图挖掘，直击围标串标'),
            AlgorithmEntry('UIE', 'NLP', '信息抽取', '百度PaddleNLP', 2022,
                          status='testing', replace='通用NER',
                          chinese_support=True, local_deploy=True, complexity='medium',
                          roe_score=4, notes='一prompt多实体抽取'),
            AlgorithmEntry('SimCSE-chinese', 'NLP', '文本相似度', 'HFL', 2021,
                          status='watching',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=3, notes='中文对比学习'),
            AlgorithmEntry('GraphSAGE', '图分析', '关联穿透', 'Stanford', 2017,
                          status='watching',
                          chinese_support=True, local_deploy=True, complexity='medium',
                          roe_score=3, notes='图神经网络归纳式学习'),
            AlgorithmEntry('Prophet', '时序', '预算预测', 'Meta', 2017,
                          status='watching',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=4, notes='时间序列自动分解预测'),
            AlgorithmEntry('LOF', '统计', '异常检测', 'sklearn', 2000,
                          status='adopted', replace='Z-score(密度异常场景)',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=4, notes='局部密度离群检测'),
            AlgorithmEntry('Benford二位数', '统计', '财务数据', '学术界', 1995,
                          status='adopted', replace='Benford单位数(补充)',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=3, notes='二位数Benford更灵敏'),
            AlgorithmEntry('STL分解', '时序', '趋势分析', 'statsmodels', 1990,
                          status='adopted', replace='Mann-Kendall(补充)',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=4, notes='季节趋势残差分解'),
            AlgorithmEntry('LayoutLMv3', 'NLP', '文档理解', 'Microsoft', 2022,
                          status='watching',
                          chinese_support=False, local_deploy=True, complexity='high',
                          roe_score=2, notes='需中文预训练，投入大'),
            AlgorithmEntry('Fraudar', '图分析', '串标', 'CMU', 2016,
                          status='testing', replace='PageRank(供应商围标)',
                          chinese_support=True, local_deploy=True, complexity='low',
                          roe_score=5, notes='稠密二部图，完美匹配围标场景'),
        ]
        
        # 去重
        seen = set()
        unique = []
        for s in seeds:
            if s.name not in seen:
                seen.add(s.name)
                unique.append(s)
        
        self.entries = unique
        self.save()
    
    def scan(self) -> Dict:
        """扫描最新趋势"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'sources_checked': [
                'arXiv (cs.AI, cs.CL, stat.ML)',
                'Papers with Code: NLP, Anomaly Detection',
                'HuggingFace trending models',
                'GitHub trending Python repos',
                'BAAI/Baidu/PaddleNLP releases',
            ],
            'alerts': [],
            'recommended_actions': []
        }
        
        # 检查本地模型状态
        adopted = [e for e in self.entries if e.status == 'adopted']
        testing = [e for e in self.entries if e.status == 'testing']
        watching = [e for e in self.entries if e.status == 'watching']
        
        report['pipeline'] = {
            'adopted': len(adopted),
            'testing': len(testing),
            'watching': len(watching),
            'adopted_names': [a.name for a in adopted],
            'testing_names': [t.name for t in testing],
        }
        
        # 高ROE未测试的 → 建议升级
        high_roe_watching = [e for e in watching if e.roe_score >= 4]
        if high_roe_watching:
            report['alerts'].append({
                'type': 'HIGH_ROE_UNTESTED',
                'message': f'{len(high_roe_watching)}个高ROE算法尚未测试',
                'items': [e.name for e in high_roe_watching]
            })
            report['recommended_actions'].append(
                f"优先测试: {', '.join([e.name for e in high_roe_watching])}"
            )
        
        # 长期未更新的 → 提醒
        last = self._get_last_update()
        days_since = (datetime.now() - datetime.fromisoformat(last)).days if last else 999
        if days_since > 30:
            report['alerts'].append({
                'type': 'STALE_RADAR',
                'message': f'雷达数据库{days_since}天未更新，建议刷新'
            })
        
        return report
    
    def _get_last_update(self) -> str:
        """获取雷达最后更新时间"""
        if os.path.exists(self.radar_file):
            with open(self.radar_file, 'r') as f:
                data = json.load(f)
                return data.get('last_updated', '')
        return ''
    
    def add_watch(self, entry: AlgorithmEntry):
        """添加观察"""
        entry.status = 'watching'
        for i, e in enumerate(self.entries):
            if e.name == entry.name and e.category == entry.category:
                self.entries[i] = entry
                return
        self.entries.append(entry)
    
    def promote(self, name: str, to_status: str):
        """状态升级"""
        for e in self.entries:
            if e.name == name:
                e.status = to_status
                if to_status == 'adopted':
                    e.adopted_version = f'v{datetime.now().strftime("%Y%m%d")}'
                break
    
    def report(self) -> str:
        """输出雷达报告"""
        lines = [
            "=" * 70,
            "  🔭 融策 · 算法雷达",
            f"  更新: {self._get_last_update() or '初始'}  |  收录: {len(self.entries)} 个算法",
            "=" * 70,
            ""
        ]
        
        for status in ['adopted', 'testing', 'watching', 'rejected']:
            items = [e for e in self.entries if e.status == status]
            if items:
                icon = {'adopted':'✅','testing':'🔬','watching':'👀','rejected':'❌'}[status]
                lines.append(f"  {icon} {status.upper()} ({len(items)})")
                for item in items:
                    replace_info = f" → 替代 {item.replace}" if item.replace else ""
                    lines.append(f"     {item.name}: {item.scenario}{replace_info} [ROE={item.roe_score}]")
                lines.append("")
        
        return '\n'.join(lines)


# ===== CLI =====
if __name__ == '__main__':
    radar = AlgorithmRadar()
    print(radar.report())
    
    scan = radar.scan()
    if scan['alerts']:
        print("\n⚠️ 告警:")
        for alert in scan['alerts']:
            print(f"  [{alert['type']}] {alert['message']}")
    if scan['recommended_actions']:
        print("\n📋 建议行动:")
        for action in scan['recommended_actions']:
            print(f"  → {action}")
