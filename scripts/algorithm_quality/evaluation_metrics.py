#!/usr/bin/env python3
"""
P0-4: 审计算法评估指标体系
放弃Accuracy → 改用 AUC-PR / Precision@K / Recall@Budget / Expected Cost
适合低发生率场景（舞弊<1%）、类别不平衡
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from sklearn.metrics import (
    precision_recall_curve, auc, roc_auc_score,
    precision_score, recall_score, f1_score,
    confusion_matrix, average_precision_score
)
import json


@dataclass
class AuditEvalResult:
    """审计专用评估结果"""
    # 基础
    total_cases: int = 0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    # 核心指标
    auc_pr: float = 0.0            # 主指标
    precision_at_k: Dict[int, float] = field(default_factory=dict)  # Precision@5/10/20/50
    recall_at_budget: Dict[float, float] = field(default_factory=dict)  # 给定工时下的召回
    expected_cost: float = 0.0     # 总期望成本
    
    # 传统指标（参考）
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    accuracy: float = 0.0  # 仅供参考
    
    # 审计质量
    fraud_detection_rate: float = 0.0  # 舞弊检出率
    false_alarm_rate: float = 0.0      # 虚警率
    investigation_efficiency: float = 0.0  # 调查效率


class AuditMetrics:
    """
    审计专用评估器
    
    使用：
    >>> y_true = [0, 0, 1, 1, 0, 1]  # 0=正常 1=异常
    >>> y_score = [0.1, 0.05, 0.9, 0.7, 0.2, 0.85]
    >>> m = AuditMetrics(cost_fp=500, cost_fn=50000)  # 误报¥500, 漏报¥50000
    >>> result = m.evaluate(y_true, y_score)
    >>> print(f"AUC-PR: {result.auc_pr:.3f}, Precision@10: {result.precision_at_k.get(10, 0):.3f}")
    """

    def __init__(self, 
                 cost_fp: float = 500,      # 单次误报调查成本(元)
                 cost_fn: float = 50000,    # 单次漏报损失(元)
                 hourly_rate: float = 300,  # 审计师时薪
                 hours_per_case: float = 2  # 每个疑点平均调查工时
    ):
        self.cost_fp = cost_fp
        self.cost_fn = cost_fn
        self.hourly_rate = hourly_rate
        self.hours_per_case = hours_per_case

    def evaluate(self, 
                 y_true: np.ndarray, 
                 y_score: np.ndarray,
                 k_values: List[int] = [5, 10, 20, 50]) -> AuditEvalResult:
        """
        全量评估
        
        Args:
            y_true: 真实标签 (0=正常, 1=异常)
            y_score: 算法输出的风险分数 (越高越可疑)
            k_values: Precision@K 的 K 值
        """
        result = AuditEvalResult()
        result.total_cases = len(y_true)
        
        if result.total_cases == 0:
            return result
        
        # ===== 1. AUC-PR（主指标） =====
        try:
            result.auc_pr = average_precision_score(y_true, y_score)
        except:
            result.auc_pr = 0.0
        
        # ===== 2. Precision@K =====
        # 按分数降序排列，取前K个
        order = np.argsort(y_score)[::-1]
        for k in k_values:
            if k > len(order):
                continue
            top_k = order[:k]
            tp_at_k = np.sum(y_true[top_k] == 1)
            result.precision_at_k[k] = tp_at_k / k if k > 0 else 0
        
        # ===== 3. Recall@Budget =====
        # 给定调查预算（工时），能覆盖多少真实问题
        budgets = [10, 20, 50, 100, 200]  # 调查工时
        for budget in budgets:
            max_cases = int(budget / self.hours_per_case)
            if max_cases > len(order):
                max_cases = len(order)
            top_n = order[:max_cases]
            found = np.sum(y_true[top_n] == 1)
            total_fraud = np.sum(y_true == 1)
            result.recall_at_budget[budget] = found / total_fraud if total_fraud > 0 else 0
        
        # ===== 4. 二分类指标（用0.5阈值）=====
        y_pred = (y_score >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        result.true_positives = tp
        result.false_positives = fp
        result.true_negatives = tn
        result.false_negatives = fn
        
        result.precision = precision_score(y_true, y_pred, zero_division=0)
        result.recall = recall_score(y_true, y_pred, zero_division=0)
        result.f1 = f1_score(y_true, y_pred, zero_division=0)
        result.accuracy = (tp + tn) / (tp + tn + fp + fn)
        
        # ===== 5. Expected Cost =====
        result.expected_cost = (fp * self.cost_fp + fn * self.cost_fn)
        
        # ===== 6. 审计质量 =====
        total_fraud = np.sum(y_true == 1)
        result.fraud_detection_rate = tp / total_fraud if total_fraud > 0 else 0
        result.false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0
        result.investigation_efficiency = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        return result

    def compare(self, 
                old_scores: np.ndarray, 
                new_scores: np.ndarray, 
                y_true: np.ndarray) -> Dict:
        """新旧算法对比"""
        old_result = self.evaluate(y_true, old_scores)
        new_result = self.evaluate(y_true, new_scores)
        
        return {
            'old': self._result_to_dict(old_result),
            'new': self._result_to_dict(new_result),
            'delta': {
                'auc_pr': new_result.auc_pr - old_result.auc_pr,
                'precision_at_10': new_result.precision_at_k.get(10, 0) - old_result.precision_at_k.get(10, 0),
                'recall_at_budget_50': new_result.recall_at_budget.get(50, 0) - old_result.recall_at_budget.get(50, 0),
                'expected_cost_delta': new_result.expected_cost - old_result.expected_cost,
                'passed': (new_result.auc_pr >= old_result.auc_pr and 
                          new_result.expected_cost <= old_result.expected_cost)
            }
        }

    def _result_to_dict(self, r: AuditEvalResult) -> Dict:
        return {
            'auc_pr': round(r.auc_pr, 4),
            'precision_at_10': round(r.precision_at_k.get(10, 0), 4),
            'recall_at_budget_50': round(r.recall_at_budget.get(50, 0), 4),
            'expected_cost': round(r.expected_cost, 2),
            'fraud_detection_rate': round(r.fraud_detection_rate, 3),
            'false_alarm_rate': round(r.false_alarm_rate, 3),
            'investigation_efficiency': round(r.investigation_efficiency, 3),
            'f1': round(r.f1, 4)
        }


class CohenKappa:
    """Cohen's Kappa 标注一致性计算"""
    
    @staticmethod
    def pairwise(annotator1: List[int], annotator2: List[int]) -> float:
        """两个标注者的一致性"""
        from sklearn.metrics import cohen_kappa_score
        return cohen_kappa_score(annotator1, annotator2)

    @staticmethod
    def fleiss_kappa(ratings: np.ndarray) -> float:
        """
        Fleiss' Kappa: 多个标注者的一致性
        
        Args:
            ratings: N×M 矩阵, N=案例数, M=标注者数
        """
        n, m = ratings.shape
        # 简化实现（完整版需要statsmodels）
        from collections import Counter
        
        # 每个案例的标注分布
        n_categories = len(set(ratings.flatten()))
        category_counts = np.zeros((n, n_categories))
        for i in range(n):
            for cat in range(n_categories):
                category_counts[i, cat] = np.sum(ratings[i] == cat)
        
        # P_i: 每个案例的标注者间一致性
        P_i = np.sum(category_counts * (category_counts - 1), axis=1) / (m * (m - 1))
        P_bar = np.mean(P_i)
        
        # P_e: 期望一致性
        p_j = np.sum(category_counts, axis=0) / (n * m)
        P_e = np.sum(p_j ** 2)
        
        if P_e >= 1.0:
            return 1.0
        
        return (P_bar - P_e) / (1 - P_e)


# ===== CLI Demo =====
if __name__ == '__main__':
    np.random.seed(42)
    n = 1000
    
    # 模拟低发生率场景（审计异常~2%）
    y_true = np.random.binomial(1, 0.02, n)
    
    # 模拟算法分数：异常样本分数偏高
    y_score = np.random.beta(1, 3, n) * 0.5
    y_score[y_true == 1] = np.random.beta(3, 1, sum(y_true)) * 0.5 + 0.5
    
    # 旧版本（较差）
    y_score_old = np.random.beta(1, 2, n) * 0.5
    y_score_old[y_true == 1] = np.random.beta(2, 1.5, sum(y_true)) * 0.5 + 0.4
    
    print("=" * 60)
    print("  审计算法评估指标演示 (舞弊率~2%)")
    print("=" * 60)
    
    m = AuditMetrics(cost_fp=500, cost_fn=50000)
    
    # 单版本评估
    r = m.evaluate(y_true, y_score)
    print(f"\n【当前版本】")
    print(f"  AUC-PR (主指标):       {r.auc_pr:.4f}")
    print(f"  Precision@10:           {r.precision_at_k.get(10,0):.3f}")
    print(f"  Precision@50:           {r.precision_at_k.get(50,0):.3f}")
    print(f"  Recall@Budget(50工时):  {r.recall_at_budget.get(50,0):.3f}")
    print(f"  Expected Cost:          ¥{r.expected_cost:,.0f}")
    print(f"  Accuracy (仅供参考):     {r.accuracy:.3f}")
    print(f"  ——")
    print(f"  TP={r.true_positives}  FP={r.false_positives}")
    print(f"  FN={r.false_negatives}  TN={r.true_negatives}")
    
    # 新旧对比
    comp = m.compare(y_score_old, y_score, y_true)
    print(f"\n【新旧对比】")
    print(f"  ΔAUC-PR:  {comp['delta']['auc_pr']:+.4f}")
    print(f"  ΔPrec@10: {comp['delta']['precision_at_10']:+.4f}")
    print(f"  ΔCost:    ¥{comp['delta']['expected_cost_delta']:+,.0f}")
    print(f"  通过?     {'✅' if comp['delta']['passed'] else '❌'}")
    
    # Cohen's Kappa demo
    annotator_a = [0,0,1,1,0,1,0,1,1,0]
    annotator_b = [0,0,1,1,0,0,0,1,1,0]
    kappa = CohenKappa.pairwise(annotator_a, annotator_b)
    print(f"\n【Cohen's Kappa 标注一致性】: {kappa:.3f}")
    print(f"  0.81-1.00: 几乎完美  0.61-0.80: 较高")
    print(f"  0.41-0.60: 中等      0.21-0.40: 一般")
    print(f"  0.00-0.20: 极低      <0: 不如随机")
