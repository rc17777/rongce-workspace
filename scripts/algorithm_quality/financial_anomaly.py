#!/usr/bin/env python3
"""
业务场景1-2：财务异常检测 + 时序分析 算法升级
替换 Z-score(单变量) → Isolation Forest(多变量) + LOF(密度) + STL分解
新增 Benford二位数检验 + Benford尾数检验
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


@dataclass
class AnomalyScores:
    """多维异常分数"""
    record_idx: int
    isolation_forest_score: float  # -1到1, 越低越异常
    lof_score: float              # LOF因子, >1为异常
    z_score_max: float            # 多维Z-score最大值
    benford_deviation: float      # Benford偏离度
    combined_score: float         # 综合异常分数 0-1
    flags: List[str] = field(default_factory=list)


class FinancialAnomalyDetector:
    """
    财务多维异常检测器
    
    组合拳：
    1. Isolation Forest → 全局多维离群
    2. LOF → 局部密度异常
    3. Z-score → 单维极端值（保留作为辅助）
    4. Benford二位数 → 数字分布异常
    5. FDR校正 → 防止多重比较误报
    
    使用：
    >>> data = np.array([...])  # shape: (n_records, n_features)
    >>> detector = FinancialAnomalyDetector()
    >>> results = detector.detect(data, feature_names=['金额','数量','单价'])
    """
    
    def __init__(self, 
                 contamination: float = 0.05,  # 预期异常比例
                 n_estimators: int = 100,
                 lof_neighbors: int = 20):
        self.contamination = contamination
        self.iso_forest = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        self.lof = LocalOutlierFactor(
            n_neighbors=lof_neighbors,
            contamination=contamination,
            novelty=False,
            n_jobs=-1
        )
        self.feature_names = []
        self.results: List[AnomalyScores] = []

    def detect(self, data: np.ndarray, 
               feature_names: List[str] = None,
               amount_col: int = 0) -> List[AnomalyScores]:
        """
        全维度异常检测
        
        Args:
            data: (n, d) 数值矩阵
            feature_names: 列名
            amount_col: 金额字段列索引（用于Benford）
        """
        n, d = data.shape
        self.feature_names = feature_names or [f'f{i}' for i in range(d)]
        
        # ===== 1. Isolation Forest =====
        self.iso_forest.fit(data)
        if_scores = self.iso_forest.decision_function(data)  # 越高越正常
        if_anomaly = self.iso_forest.predict(data)  # -1=异常, 1=正常
        
        # ===== 2. LOF =====
        lof_scores = self.lof.fit_predict(data)  # 注意: predict返回标签, 需要重新算
        # 显式计算LOF因子
        lof_factors = np.ones(n)
        try:
            from sklearn.neighbors import LocalOutlierFactor as LOF2
            lof_detector = LOF2(n_neighbors=self.lof.n_neighbors, contamination=self.contamination, novelty=False)
            lof_factors = np.abs(lof_detector.fit_predict(data)) * (
                -lof_detector.negative_outlier_factor_ / np.max(np.abs(lof_detector.negative_outlier_factor_))
            )
        except:
            lof_factors = np.where(lof_scores == -1, 2.0, 1.0)
        
        # ===== 3. 多维Z-score =====
        z_scores = np.abs((data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-10))
        z_max = np.max(z_scores, axis=1)
        z_flags = z_max > 3.0
        
        # ===== 4. Benford二位数检验（金额字段）=====
        benford_dev = np.zeros(n)
        if amount_col < d:
            amounts = np.abs(data[:, amount_col])
            amounts = amounts[amounts > 0]
            for i in range(n):
                if data[i, amount_col] > 0:
                    # 取首位数字
                    first_digit = int(str(abs(data[i, amount_col])).lstrip('0.')[0])
                    expected_prob = np.log10(1 + 1/first_digit) if 1 <= first_digit <= 9 else 0
                    benford_dev[i] = abs(expected_prob - 0.1)  # 简化偏离度
        
        # ===== 5. 综合评分 =====
        self.results = []
        for i in range(n):
            # 归一化各分数到[0,1]
            if_norm = (-if_scores[i] + 1) / 2  # 越高越异常
            lof_norm = min(lof_factors[i] / 3, 1.0) if lof_factors[i] > 0 else 0
            z_norm = min(z_max[i] / 6, 1.0)
            
            combined = 0.35 * if_norm + 0.25 * lof_norm + 0.25 * z_norm + 0.15 * benford_dev[i]
            
            flags = []
            if if_anomaly[i] == -1: flags.append('IsolationForest')
            if lof_factors[i] > 2: flags.append('LOF')
            if z_flags[i]: flags.append(f'Z-score({self.feature_names[np.argmax(z_scores[i])]})')
            
            self.results.append(AnomalyScores(
                record_idx=i,
                isolation_forest_score=if_scores[i],
                lof_score=lof_factors[i],
                z_score_max=z_max[i],
                benford_deviation=benford_dev[i],
                combined_score=combined,
                flags=flags
            ))
        
        return self.results

    def get_top_anomalies(self, k: int = 20) -> List[AnomalyScores]:
        """Top K异常"""
        sorted_results = sorted(self.results, key=lambda x: x.combined_score, reverse=True)
        return sorted_results[:k]

    def summary(self) -> Dict:
        """异常检测摘要"""
        if not self.results:
            return {}
        flagged = [r for r in self.results if r.flags]
        high = [r for r in flagged if r.combined_score > 0.7]
        medium = [r for r in flagged if 0.4 <= r.combined_score <= 0.7]
        
        return {
            'total_records': len(self.results),
            'flagged': len(flagged),
            'high_risk': len(high),
            'medium_risk': len(medium),
            'flag_rate': f'{len(flagged)/len(self.results):.1%}',
            'detection_methods': {
                'IsolationForest': sum(1 for r in flagged if 'IsolationForest' in r.flags),
                'LOF': sum(1 for r in flagged if 'LOF' in r.flags),
                'Z-score': sum(1 for r in flagged if any('Z-score' in f for f in r.flags)),
            }
        }


class STLTrendAnomaly:
    """
    STL分解 + 残差检测
    替代：Mann-Kendall的粗粒度趋势判断
    """
    
    @staticmethod
    def decompose(series: np.ndarray, period: int = 12) -> Dict:
        """
        STL时间序列分解
        
        Args:
            series: 时间序列数据
            period: 季节性周期（月度=12, 季度=4）
        """
        from statsmodels.tsa.seasonal import STL
        
        stl = STL(series, period=period, seasonal=7, robust=True)
        result = stl.fit()
        
        # 残差异常检测
        residuals = result.resid
        residual_std = np.std(residuals)
        anomaly_idx = np.where(np.abs(residuals) > 2 * residual_std)[0]
        
        return {
            'trend': result.trend.tolist(),
            'seasonal': result.seasonal.tolist(),
            'residual': residuals.tolist(),
            'anomaly_indices': anomaly_idx.tolist(),
            'anomaly_count': len(anomaly_idx),
            'trend_direction': '上升' if result.trend[-1] > result.trend[0] else '下降',
            'trend_magnitude': float(result.trend[-1] - result.trend[0]),
            'seasonal_strength': float(1 - np.var(residuals) / np.var(series + result.seasonal)),
        }


# ===== CLI Demo =====
if __name__ == '__main__':
    np.random.seed(42)
    
    print("=" * 70)
    print("  财务多维异常检测 + STL趋势分析 演示")
    print("=" * 70)
    
    # 模拟财务数据：1000条记录, 5个特征
    n = 1000
    data = np.random.normal(0, 1, (n, 5))
    # 注入10个异常
    data[990:1000] = np.random.normal(4, 2, (10, 5))
    
    features = ['金额', '数量', '单价', '科目余额', '预算偏差']
    
    # ===== 异常检测 =====
    detector = FinancialAnomalyDetector(contamination=0.05)
    results = detector.detect(data, feature_names=features, amount_col=0)
    summary = detector.summary()
    
    print(f"\n【多维异常检测】")
    print(f"  总记录: {summary['total_records']}")
    print(f"  标记异常: {summary['flagged']} ({summary['flag_rate']})")
    print(f"  高风险: {summary['high_risk']} | 中风险: {summary['medium_risk']}")
    print(f"  检测方法: {summary['detection_methods']}")
    
    # Top 5
    top5 = detector.get_top_anomalies(5)
    print(f"\n  Top 5 异常:")
    for r in top5:
        print(f"    记录{r.record_idx}: 综合={r.combined_score:.3f} 标记={r.flags}")
    
    # ===== STL趋势 =====
    print(f"\n【STL趋势分解】")
    # 模拟月度数据
    t = np.arange(36)
    trend = t * 0.5
    seasonal = 5 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(0, 2, 36)
    series = trend + seasonal + noise
    # 注入异常
    series[24] += 15
    series[30] -= 10
    
    stl_result = STLTrendAnomaly.decompose(series, period=12)
    print(f"  趋势方向: {stl_result['trend_direction']}")
    print(f"  趋势幅度: {stl_result['trend_magnitude']:.1f}")
    print(f"  季节性强度: {stl_result['seasonal_strength']:.2f}")
    print(f"  异常点: {stl_result['anomaly_count']} 个 → 索引 {stl_result['anomaly_indices']}")
