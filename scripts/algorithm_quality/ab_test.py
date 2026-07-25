#!/usr/bin/env python3
"""
三步法 Step 2：A/B测试框架
新老算法在真实项目数据上的量化对比
输出：不比个高低不换算法
"""

import json, os, time
from typing import Dict, List, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from scipy import stats


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_name: str
    algorithm_old: str
    algorithm_new: str
    dataset: str
    metric: str
    old_score: float
    new_score: float
    delta: float
    delta_pct: str
    p_value: float
    significant: bool     # 是否统计显著
    winner: str           # 'old' / 'new' / 'tie'
    sample_size: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ABTestRunner:
    """
    算法A/B对比测试
    
    使用：
    >>> runner = ABTestRunner()
    >>> result = runner.compare(
    ...     name="合同相似度-红光街道",
    ...     old_alg=lambda x: tfidf_compare(x),
    ...     new_alg=lambda x: bge_compare(x),
    ...     test_data=doc_pairs,
    ...     ground_truth=labels
    ... )
    """
    
    def __init__(self, output_dir: str = 'output/algorithm_quality'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.history: List[ABTestResult] = []
        self._load_history()
    
    def _load_history(self):
        path = os.path.join(self.output_dir, 'ab_test_history.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = [ABTestResult(**r) for r in data.get('results', [])]
    
    def _save_history(self):
        path = os.path.join(self.output_dir, 'ab_test_history.json')
        data = {
            'last_updated': datetime.now().isoformat(),
            'total_tests': len(self.history),
            'results': [self._result_to_dict(r) for r in self.history]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _result_to_dict(self, r: ABTestResult) -> Dict:
        return {
            'test_name': r.test_name,
            'algorithm_old': r.algorithm_old,
            'algorithm_new': r.algorithm_new,
            'dataset': r.dataset,
            'metric': r.metric,
            'old_score': round(r.old_score, 4),
            'new_score': round(r.new_score, 4),
            'delta': round(r.delta, 4),
            'delta_pct': r.delta_pct,
            'p_value': round(r.p_value, 4),
            'significant': r.significant,
            'winner': r.winner,
            'sample_size': r.sample_size,
            'timestamp': r.timestamp
        }
    
    def compare(self,
                name: str,
                old_alg: Callable,
                new_alg: Callable,
                test_data: List[Any],
                ground_truth: List[Any],
                metric_fn: Callable = None,
                n_bootstrap: int = 1000) -> ABTestResult:
        """
        A/B对比测试
        
        Args:
            name: 测试名称
            old_alg: 老算法函数
            new_alg: 新算法函数
            test_data: 测试数据列表
            ground_truth: 真值标签
            metric_fn: 自定义评估函数 (predictions, truth) -> score
            n_bootstrap: bootstrap采样次数
        """
        print(f"\n🔬 A/B测试: {name}")
        print(f"   老算法: {old_alg.__doc__ or 'unknown'}")
        print(f"   新算法: {new_alg.__doc__ or 'unknown'}")
        print(f"   样本数: {len(test_data)}")
        
        # 跑老算法
        old_preds = []
        t0 = time.time()
        for item in test_data:
            old_preds.append(old_alg(item))
        old_time = time.time() - t0
        
        # 跑新算法
        new_preds = []
        t0 = time.time()
        for item in test_data:
            new_preds.append(new_alg(item))
        new_time = time.time() - t0
        
        # 默认评估：准确率
        if metric_fn is None:
            metric_fn = lambda preds, truth: np.mean(np.array(preds) == np.array(truth))
        
        old_score = metric_fn(old_preds, ground_truth)
        new_score = metric_fn(new_preds, ground_truth)
        delta = new_score - old_score
        
        # Bootstrap统计显著性
        p_value = self._bootstrap_test(
            np.array(old_preds), np.array(new_preds),
            np.array(ground_truth), metric_fn, n_bootstrap
        )
        
        significant = p_value < 0.05
        if significant:
            if delta > 0:
                winner = 'new'
            elif delta < 0:
                winner = 'old'
            else:
                winner = 'tie'
        else:
            winner = 'tie'
        
        result = ABTestResult(
            test_name=name,
            algorithm_old=old_alg.__name__,
            algorithm_new=new_alg.__name__,
            dataset=name,
            metric='自定义' if metric_fn else 'Accuracy',
            old_score=old_score,
            new_score=new_score,
            delta=delta,
            delta_pct=f'{delta/abs(old_score)*100:+.1f}%' if old_score != 0 else 'N/A',
            p_value=p_value,
            significant=significant,
            winner=winner,
            sample_size=len(test_data)
        )
        
        print(f"\n   结果:")
        print(f"   老算法: {old_score:.4f} ({old_time:.2f}s)")
        print(f"   新算法: {new_score:.4f} ({new_time:.2f}s)")
        print(f"   差异: {delta:+.4f} ({result.delta_pct})")
        print(f"   p值: {p_value:.4f} {'✅ 显著' if significant else '❌ 不显著'}")
        print(f"   胜者: {'🆕 新算法' if winner=='new' else '📼 老算法' if winner=='old' else '🤝 平局'}")
        
        self.history.append(result)
        self._save_history()
        
        return result
    
    def compare_multi_metric(self,
                             name: str,
                             old_alg: Callable,
                             new_alg: Callable,
                             test_data: List[Any],
                             ground_truth: List[Any],
                             metrics: Dict[str, Callable]) -> List[ABTestResult]:
        """多指标对比"""
        results = []
        for metric_name, metric_fn in metrics.items():
            r = self.compare(
                name=f"{name}-{metric_name}",
                old_alg=old_alg, new_alg=new_alg,
                test_data=test_data, ground_truth=ground_truth,
                metric_fn=metric_fn
            )
            results.append(r)
        return results
    
    def _bootstrap_test(self, old_preds: np.ndarray, new_preds: np.ndarray,
                        truth: np.ndarray, metric_fn: Callable, n: int) -> float:
        """Bootstrap双样本检验"""
        # 原样本差异
        obs_diff = metric_fn(new_preds, truth) - metric_fn(old_preds, truth)
        
        # Bootstrap
        n_samples = len(truth)
        bootstrap_diffs = []
        for _ in range(n):
            idx = np.random.choice(n_samples, n_samples, replace=True)
            old_boot = metric_fn(old_preds[idx], truth[idx])
            new_boot = metric_fn(new_preds[idx], truth[idx])
            bootstrap_diffs.append(new_boot - old_boot)
        
        # 单侧p值: null=新算法不优于老算法
        p_value = np.mean(np.array(bootstrap_diffs) <= 0)
        return float(p_value)
    
    def summary(self) -> Dict:
        """A/B测试汇总"""
        if not self.history:
            return {'message': '暂无A/B测试记录'}
        
        wins_new = sum(1 for r in self.history if r.winner == 'new')
        wins_old = sum(1 for r in self.history if r.winner == 'old')
        ties = sum(1 for r in self.history if r.winner == 'tie')
        significant_tests = sum(1 for r in self.history if r.significant)
        
        avg_delta = np.mean([r.delta for r in self.history])
        
        return {
            'total_tests': len(self.history),
            'wins_new': wins_new,
            'wins_old': wins_old,
            'ties': ties,
            'significant_tests': significant_tests,
            'avg_improvement': f'{avg_delta*100:+.2f}%',
            'algorithms_tested': list(set(r.algorithm_new for r in self.history)),
            'best_improvement': max(self.history, key=lambda r: r.delta).test_name if wins_new > 0 else None,
        }
    
    def decide(self, result: ABTestResult) -> str:
        """
        决策引擎：基于A/B结果自动建议
        
        Returns: 'adopt' / 'reject' / 'more_testing'
        """
        if not result.significant:
            return 'more_testing'  # 统计不显著，需要更多数据
        if result.delta > 0.05:  # 提升>5%
            return 'adopt'
        elif result.delta > 0:
            return 'more_testing'  # 提升太小，不值得替换
        else:
            return 'reject'


# ===== CLI Demo =====
if __name__ == '__main__':
    np.random.seed(42)
    
    print("=" * 70)
    print("  算法 A/B 对比测试 演示")
    print("=" * 70)
    
    # 模拟：老算法(Z-score) vs 新算法(Isolation Forest)
    def old_zscore(data_point):
        """Z-score单变量异常检测"""
        return 1 if abs(data_point[0]) > 2.5 else 0
    
    def new_isolation_forest(data_point):
        """Isolation Forest多维异常检测"""
        return 1 if sum(abs(x) for x in data_point) > 6 else 0
    
    # 模拟测试数据
    np.random.seed(42)
    n = 500
    test_data = []
    truth = []
    for i in range(n):
        if i < 480:  # 正常
            point = np.random.normal(0, 1, 5)
            truth.append(0)
        else:        # 多维异常
            point = np.random.normal(3, 1, 5)
            truth.append(1)
        test_data.append(point)
    
    runner = ABTestRunner()
    result = runner.compare(
        name="财务异常检测-Zscore vs IsolationForest",
        old_alg=old_zscore,
        new_alg=new_isolation_forest,
        test_data=test_data,
        ground_truth=truth
    )
    
    decision = runner.decide(result)
    print(f"\n【决策建议】: {decision}")
    
    summary = runner.summary()
    if 'total_tests' in summary:
        print(f"\n【A/B测试历史】")
        print(f"  总测试: {summary['total_tests']}")
        print(f"  新算法胜: {summary['wins_new']} | 老算法胜: {summary['wins_old']} | 平局: {summary['ties']}")
        print(f"  平均提升: {summary['avg_improvement']}")
