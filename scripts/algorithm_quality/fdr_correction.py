#!/usr/bin/env python3
"""
P0-2: 统计检验多重比较 FDR 校正
解决：6个统计算法同时跑 → 26.5%误报概率
方法：Benjamini-Hochberg FDR控制 → 控制到5%
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import json

@dataclass
class AnomalyResult:
    """单个统计检验的异常结果"""
    test_name: str           # 检验名称
    p_value: float           # 原始p值
    statistic: float         # 检验统计量
    is_significant: bool = False  # 是否显著
    adjusted_p_value: float = 0.0  # FDR校正后p值
    rank: int = 0            # p值排序
    fdr_significant: bool = False  # FDR校正后是否显著


class FDRCorrection:
    """
    Benjamini-Hochberg FDR 多重比较校正器
    
    使用：
    >>> corrector = FDRCorrection(alpha=0.05)
    >>> results = corrector.correct([
    ...     ('Benford', 0.001, 45.2),
    ...     ('Z-score', 0.04, 2.1),
    ...     ('Mann-Kendall', 0.15, 1.4),
    ... ])
    >>> for r in results:
    ...     print(f"{r.test_name}: p={r.p_value:.4f} adj_p={r.adjusted_p_value:.4f} sig={r.fdr_significant}")
    """

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def correct(self, test_results: List[Tuple[str, float, float]]) -> List[AnomalyResult]:
        """
        对多个统计检验结果进行BH校正
        
        Args:
            test_results: [(test_name, p_value, statistic), ...]
        
        Returns:
            List[AnomalyResult]: 校正后结果
        """
        if not test_results:
            return []

        # 按p值排序
        sorted_tests = sorted(test_results, key=lambda x: x[1])
        n = len(sorted_tests)
        results = []

        for i, (name, p_val, stat) in enumerate(sorted_tests, 1):
            result = AnomalyResult(
                test_name=name,
                p_value=p_val,
                statistic=stat,
                rank=i
            )
            # BH校正: adjusted_p = min(p * n / i, 1)
            adjusted = min(p_val * n / i, 1.0)
            result.adjusted_p_value = adjusted
            result.is_significant = p_val < self.alpha
            result.fdr_significant = adjusted < self.alpha
            results.append(result)

        return results

    def correct_dict(self, results_dict: Dict[str, float]) -> Dict[str, AnomalyResult]:
        """字典输入格式"""
        items = [(name, p_val, 0.0) for name, p_val in results_dict.items()]
        corrected = self.correct(items)
        return {r.test_name: r for r in corrected}

    def summary(self, results: List[AnomalyResult]) -> Dict:
        """输出校正摘要"""
        raw_sig = sum(1 for r in results if r.is_significant)
        fdr_sig = sum(1 for r in results if r.fdr_significant)
        filtered_out = raw_sig - fdr_sig
        
        return {
            'total_tests': len(results),
            'raw_significant': raw_sig,
            'fdr_significant': fdr_sig,
            'filtered_out': filtered_out,
            'false_positive_probability_before': 1 - (1 - self.alpha) ** len(results),
            'false_positive_probability_after': self.alpha,
            'alpha': self.alpha,
            'method': 'Benjamini-Hochberg',
            'significant_tests': [
                {
                    'name': r.test_name,
                    'p_value': round(r.p_value, 6),
                    'adjusted_p': round(r.adjusted_p_value, 6)
                }
                for r in results if r.fdr_significant
            ]
        }

    @staticmethod
    def bonferroni_correct(p_values: List[float]) -> List[float]:
        """Bonferroni校正（更保守，适合零容错场景）"""
        n = len(p_values)
        return [min(p * n, 1.0) for p in p_values]


# ===== 审计专用统计检验适配器 =====

class AuditStatisticsCorrector:
    """
    审计场景专用：自动收集6类统计检验p值 → FDR校正 → 输出分级结论
    """
    
    def __init__(self, alpha: float = 0.05):
        self.corrector = FDRCorrection(alpha)
        self.tests: Dict[str, float] = {}
        self.results: List[AnomalyResult] = []
    
    def add_benford(self, observed: List[int], n_digits: int = 1) -> float:
        """Benford定律检验"""
        if len(observed) < 3:
            return 1.0
        expected = [np.log10(1 + 1/d) * sum(observed) for d in range(1, 10)]
        chi2, p = stats.chisquare(f_obs=observed[:9], f_exp=expected[:9])
        self.tests['Benford'] = p
        return p

    def add_zscore(self, values: np.ndarray, threshold: float = 3.0) -> float:
        """Z-score检验：假设正态分布，计算尾概率"""
        if len(values) < 3:
            return 1.0
        z = (values - np.mean(values)) / (np.std(values) + 1e-10)
        n_extreme = np.sum(np.abs(z) > threshold)
        # 二项检验：极端值比例是否显著高于预期
        expected = len(values) * 2 * (1 - stats.norm.cdf(threshold))
        from scipy.stats import binomtest
        result = binomtest(n_extreme, len(values), p=expected/len(values), alternative='greater')
        self.tests['Z-score'] = result.pvalue
        return result.pvalue

    def add_mann_kendall(self, series: np.ndarray) -> float:
        """Mann-Kendall趋势检验"""
        if len(series) < 4:
            return 1.0
        from scipy.stats import kendalltau
        x = np.arange(len(series))
        tau, p = kendalltau(x, series)
        self.tests['Mann-Kendall'] = p
        return p

    def correct_all(self) -> Dict:
        """跑全部已收集检验 → FDR校正"""
        items = [(name, p, 0.0) for name, p in self.tests.items()]
        self.results = self.corrector.correct(items)
        return self.corrector.summary(self.results)

    def get_significant_findings(self) -> List[str]:
        """只输出FDR校正后依然显著的发现"""
        return [r.test_name for r in self.results if r.fdr_significant]


# ===== CLI =====
if __name__ == '__main__':
    # 模拟：6个检验同时跑
    print("=" * 60)
    print("  审计统计检验多重比较 FDR 校正演示")
    print("=" * 60)
    
    auditor = AuditStatisticsCorrector(alpha=0.05)
    
    # 模拟数据
    np.random.seed(42)
    normal_data = np.random.normal(1000, 200, 1000)
    trend_data = normal_data.copy()
    trend_data[500:] += np.linspace(0, 300, 500)  # 后500个逐步升高
    benford_obs = [305, 170, 125, 95, 80, 65, 55, 50, 45]  # ~Benford分布
    
    # 跑6个检验
    auditor.add_benford(benford_obs)
    auditor.add_zscore(normal_data)
    auditor.add_mann_kendall(trend_data)
    # 模拟更多p值
    auditor.tests['CUSUM'] = 0.03
    auditor.tests['Apriori'] = 0.08
    auditor.tests['PageRank'] = 0.12
    
    result = auditor.correct_all()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print(f"\n校正前误报概率: {result['false_positive_probability_before']:.1%}")
    print(f"校正后误报概率: {result['false_positive_probability_after']:.1%}")
    print(f"被过滤掉的假阳性: {result['filtered_out']} 个")
    print(f"FDR显著发现: {auditor.get_significant_findings()}")
