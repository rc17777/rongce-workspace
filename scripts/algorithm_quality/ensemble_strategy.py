#!/usr/bin/env python3
"""
三步法 Step 3：算法组合策略
单个算法各有所短，组合起来相互补位
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import Counter
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


@dataclass
class EnsembleVote:
    """组合投票结果"""
    record_idx: int
    algorithms_voted: List[str]   # 哪些算法投了"有问题"
    algorithms_cleared: List[str] # 哪些算法投了"没问题"
    agreement: float              # 一致性 0-1
    consensus_type: str           # 'unanimous'(全票) / 'majority'(多数) / 'split'(分歧)
    risk_level: str               # 'HIGH'/'MEDIUM'/'LOW'/'NORMAL'
    details: Dict = field(default_factory=dict)


class AlgorithmEnsemble:
    """
    算法组合引擎
    
    三种组合策略：
    1. 交集策略（高置信）→ 多算法都报才算
    2. 并集策略（高召回）→ 任一算法报就算
    3. 加权投票 → 按风险等级加权
    
    使用：
    >>> ensemble = AlgorithmEnsemble(mode='weighted')
    >>> results = ensemble.combine({
    ...     'IsolationForest': if_results,
    ...     'LOF': lof_results,
    ...     'Z-score': zscore_results,
    ... })
    """
    
    def __init__(self, mode: str = 'weighted', 
                 min_agreement: float = 0.5,
                 fdr_alpha: float = 0.05):
        """
        Args:
            mode: 'intersection' | 'union' | 'weighted'
            min_agreement: 最小一致性阈值
            fdr_alpha: FDR校正alpha
        """
        self.mode = mode
        self.min_agreement = min_agreement
        self.fdr_alpha = fdr_alpha
        self.last_results: List[EnsembleVote] = []
    
    def combine(self,
                algorithm_outputs: Dict[str, np.ndarray],
                weights: Dict[str, float] = None,
                ground_truth: np.ndarray = None) -> List[EnsembleVote]:
        """
        多算法组合投票
        
        Args:
            algorithm_outputs: {算法名: bool数组(True=异常)}
            weights: 算法权重（默认均等）
        """
        algo_names = list(algorithm_outputs.keys())
        n_algo = len(algo_names)
        n_records = len(algorithm_outputs[algo_names[0]])
        
        if weights is None:
            weights = {name: 1.0 for name in algo_names}
        
        results = []
        
        for i in range(n_records):
            votes = {}
            for name in algo_names:
                votes[name] = bool(algorithm_outputs[name][i])
            
            voted = [name for name, v in votes.items() if v]
            cleared = [name for name, v in votes.items() if not v]
            
            # 加权一致性
            total_weight = sum(weights.values())
            anomaly_weight = sum(weights[n] for n in voted) / total_weight
            agreement = max(anomaly_weight, 1 - anomaly_weight)
            
            # 共识类型
            if len(voted) == n_algo:
                consensus = 'unanimous'
            elif len(voted) > n_algo / 2:
                consensus = 'majority'
            else:
                consensus = 'split'
            
            # 风险等级
            if consensus == 'unanimous':
                risk = 'HIGH'
            elif consensus == 'majority' and agreement > 0.7:
                risk = 'MEDIUM'
            elif consensus == 'split':
                risk = 'LOW'
            else:
                risk = 'NORMAL'
            
            # 模式决策
            if self.mode == 'intersection':
                final = len(voted) == n_algo  # 全部同意才算
            elif self.mode == 'union':
                final = len(voted) > 0  # 任一同意就算
            else:  # weighted
                final = anomaly_weight >= self.min_agreement
            
            results.append(EnsembleVote(
                record_idx=i,
                algorithms_voted=voted,
                algorithms_cleared=cleared,
                agreement=agreement,
                consensus_type=consensus,
                risk_level=risk,
                details={'weighted_score': anomaly_weight, 'final_flag': final}
            ))
        
        self.last_results = results
        return results
    
    def summary(self) -> Dict:
        """组合投票摘要"""
        if not self.last_results:
            return {}
        
        n = len(self.last_results)
        unanimous = sum(1 for r in self.last_results if r.consensus_type == 'unanimous')
        majority = sum(1 for r in self.last_results if r.consensus_type == 'majority')
        split = sum(1 for r in self.last_results if r.consensus_type == 'split')
        flagged = sum(1 for r in self.last_results if r.details.get('final_flag'))
        
        return {
            'mode': self.mode,
            'total_records': n,
            'flagged': flagged,
            'flag_rate': f'{flagged/n:.1%}' if n > 0 else '0%',
            'consensus': {
                'unanimous': unanimous,
                'majority': majority,
                'split': split,
            },
            'risk_distribution': {
                'HIGH': sum(1 for r in self.last_results if r.risk_level == 'HIGH'),
                'MEDIUM': sum(1 for r in self.last_results if r.risk_level == 'MEDIUM'),
                'LOW': sum(1 for r in self.last_results if r.risk_level == 'LOW'),
                'NORMAL': sum(1 for r in self.last_results if r.risk_level == 'NORMAL'),
            }
        }

    def get_high_confidence_flags(self) -> List[int]:
        """只返回全票通过的高置信异常"""
        return [r.record_idx for r in self.last_results if r.consensus_type == 'unanimous']

    def get_disagreements(self) -> List[EnsembleVote]:
        """返回算法间有分歧的案例 → 值得人工审查"""
        return [r for r in self.last_results if r.consensus_type == 'split']


class ScenarioEnsemble:
    """
    按业务场景定制的算法组合
    
    三套预设组合：
    - 财务异常：Isolation Forest + LOF + Z-score + Benford
    - 合同分析：BGE-M3 + TF-IDF + 关键词重叠
    - 关联穿透：Fraudar + PageRank + Louvain + 环路检测
    """
    
    PRESETS = {
        'financial_anomaly': {
            'name': '财务异常检测组合',
            'algorithms': ['IsolationForest', 'LOF', 'Z-score', 'Benford'],
            'mode': 'weighted',
            'weights': {'IsolationForest': 1.5, 'LOF': 1.0, 'Z-score': 0.8, 'Benford': 0.7},
            'min_agreement': 0.4,
            'description': '全票通过=95%+可信, 多数通过=需复核, 单独报告=参考'
        },
        'contract_similarity': {
            'name': '合同相似度组合',
            'algorithms': ['BGE-M3', 'TF-IDF', 'Keywords'],
            'mode': 'intersection',
            'weights': None,  # 等权
            'min_agreement': 0.66,  # 至少2/3同意
            'description': '三算法同报→铁证(L3层), 二算法→强信号, 一算法→参考'
        },
        'supplier_collusion': {
            'name': '供应商围标组合',
            'algorithms': ['Fraudar', 'PageRank', 'Louvain', 'CycleDetect'],
            'mode': 'weighted',
            'weights': {'Fraudar': 2.0, 'PageRank': 0.8, 'Louvain': 1.0, 'CycleDetect': 1.2},
            'min_agreement': 0.4,
            'description': 'Fraudar为主(权重2x), 其余辅助判断'
        }
    }
    
    @classmethod
    def get_preset(cls, scenario: str) -> Dict:
        """获取场景预设组合"""
        return cls.PRESETS.get(scenario, cls.PRESETS['financial_anomaly'])
    
    @classmethod
    def run_scenario(cls, scenario: str, 
                     algorithm_outputs: Dict[str, np.ndarray]) -> Dict:
        """运行场景组合"""
        preset = cls.get_preset(scenario)
        
        ensemble = AlgorithmEnsemble(
            mode=preset['mode'],
            min_agreement=preset['min_agreement']
        )
        
        results = ensemble.combine(
            algorithm_outputs=algorithm_outputs,
            weights=preset.get('weights')
        )
        
        summary = ensemble.summary()
        summary['scenario'] = scenario
        summary['preset'] = preset['name']
        summary['description'] = preset['description']
        
        high_conf = ensemble.get_high_confidence_flags()
        disagreements = ensemble.get_disagreements()
        
        return {
            'summary': summary,
            'high_confidence_flags': high_conf[:20],
            'disagreements': [(d.record_idx, d.algorithms_voted, d.algorithms_cleared) 
                            for d in disagreements[:10]],
            'recommendation': cls._generate_recommendation(summary)
        }
    
    @classmethod
    def _generate_recommendation(cls, summary: Dict) -> str:
        """基于结果生成审计建议"""
        risk = summary.get('risk_distribution', {})
        high = risk.get('HIGH', 0)
        
        if high > 10:
            return f"⚠️ 发现{high}个高置信异常项，建议优先排查，其中全票通过项误报概率极低"
        elif high > 0:
            return f"发现{high}个高置信异常项，建议逐项核实并形成取证单"
        else:
            return "未发现高置信异常，建议扩大检测范围或检查算法参数"


# ===== CLI Demo =====
if __name__ == '__main__':
    np.random.seed(42)
    
    print("=" * 70)
    print("  算法组合策略 演示")
    print("=" * 70)
    
    # 模拟3个算法的输出
    n = 1000
    algo1 = np.random.binomial(1, 0.05, n)  # IsolationForest
    algo2 = np.random.binomial(1, 0.04, n)  # LOF
    algo3 = np.random.binomial(1, 0.03, n)  # Z-score
    # 注入重叠的异常
    algo1[995:1000] = 1
    algo2[995:1000] = 1
    algo3[995:1000] = 1
    
    outputs = {'IsolationForest': algo1, 'LOF': algo2, 'Z-score': algo3}
    
    # 三种策略对比
    for mode in ['intersection', 'union', 'weighted']:
        ensemble = AlgorithmEnsemble(mode=mode)
        ensemble.combine(outputs)
        s = ensemble.summary()
        print(f"\n【{mode}】")
        print(f"  标记: {s['flagged']}/{s['total_records']} ({s['flag_rate']})")
        print(f"  全票: {s['consensus']['unanimous']} | 多数: {s['consensus']['majority']} | 分歧: {s['consensus']['split']}")
    
    # 场景预设
    print(f"\n{'='*70}")
    print(f"  场景预设组合")
    print(f"{'='*70}")
    
    for scenario in ['financial_anomaly', 'contract_similarity', 'supplier_collusion']:
        preset = ScenarioEnsemble.get_preset(scenario)
        print(f"\n【{preset['name']}】")
        print(f"  算法: {', '.join(preset['algorithms'])}")
        print(f"  模式: {preset['mode']} | 最小一致: {preset['min_agreement']}")
        print(f"  {preset['description']}")
