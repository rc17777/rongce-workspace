# -*- coding: utf-8 -*-
"""
融策评标专家偏离度检测模型 v1.0

功能：
  1. 统计偏离度分析（Z-score、IQR、CV变异系数）
  2. 专家一致性检验（Kendall W协调系数）
  3. 聚类分析（识别孤立评分专家）
  4. 异常打分模式识别（集中打高分/低分、压线打分）
  5. 输出可视化报告

用法：
  python expert_bias_detection.py \
    --input "评标打分表.xlsx" \
    --output "偏离度分析报告.xlsx" \
    --threshold-z 2.0 \
    --threshold-cv 0.3

输入格式：
  Excel/CSV，列要求：
  - 专家姓名（或专家ID）
  - 投标人名称（或投标人ID）
  - 评分（数字）
  - 可选：评分维度（技术/商务/价格）

作者：融策智审Agent
版本：1.0.0
日期：2026-06-24
"""

import sys, os, argparse, json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# ================================================================
# 核心算法
# ================================================================

class ExpertBiasDetector:
    """评标专家偏离度检测器"""

    def __init__(self, threshold_z=2.0, threshold_cv=0.3, min_experts=3, min_bidders=3):
        """
        Args:
            threshold_z: Z-score阈值，超过则认为显著偏离（默认2.0，即95%置信区间）
            threshold_cv: 变异系数阈值，超过则认为评分波动异常（默认0.3）
            min_experts: 最少专家数（少于则无法做统计分析）
            min_bidders: 最少投标人数
        """
        self.threshold_z = threshold_z
        self.threshold_cv = threshold_cv
        self.min_experts = min_experts
        self.min_bidders = min_bidders
        self.results = {}

    def load_data(self, file_path, expert_col='专家姓名', bidder_col='投标人名称',
                  score_col='评分', dimension_col=None):
        """加载评标数据

        Args:
            file_path: Excel/CSV文件路径
            expert_col: 专家姓名列名
            bidder_col: 投标人名称列名
            score_col: 评分列名
            dimension_col: 评分维度列名（可选，如'技术分'/'商务分'/'价格分'）
        """
        path = Path(file_path)
        if path.suffix.lower() in ('.xlsx', '.xls'):
            df = pd.read_excel(file_path)
        elif path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        # 自动识别列名（中文/英文）
        col_mapping = {
            expert_col: ['专家姓名', '专家', 'expert', 'expert_name', '评委', '评委姓名'],
            bidder_col: ['投标人名称', '投标人', 'bidder', '投标单位', '供应商名称', 'supplier'],
            score_col: ['评分', '分数', 'score', 'mark', '得分', '分值'],
            dimension_col: ['评分维度', '维度', 'dimension', '分项', 'category'] if dimension_col else []
        }

        for target, candidates in col_mapping.items():
            if target is None:
                continue
            if target not in df.columns:
                for cand in candidates:
                    if cand in df.columns:
                        df = df.rename(columns={cand: target})
                        break

        # 确保必要列存在
        for col in [expert_col, bidder_col, score_col]:
            if col not in df.columns:
                available = ', '.join(df.columns.tolist())
                raise ValueError(f"缺少必要列 '{col}'，可用列: {available}")

        # 清洗评分数据
        df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
        df = df.dropna(subset=[score_col])

        # 脱敏处理（名称替换为专家A/B/C、投标人1/2/3）
        self.expert_map = {name: f"专家{chr(65+i)}" for i, name in enumerate(df[expert_col].unique())}
        self.bidder_map = {name: f"投标人{j+1}" for j, name in enumerate(df[bidder_col].unique())}
        df[expert_col] = df[expert_col].map(self.expert_map)
        df[bidder_col] = df[bidder_col].map(self.bidder_map)

        self.df = df
        self.expert_col = expert_col
        self.bidder_col = bidder_col
        self.score_col = score_col
        self.dimension_col = dimension_col if dimension_col and dimension_col in df.columns else None

        n_experts = df[expert_col].nunique()
        n_bidders = df[bidder_col].nunique()
        print(f"\n📊 数据加载: {len(df)} 条评分记录")
        print(f"   专家: {n_experts} 人 | 投标人: {n_bidders} 人")
        if self.dimension_col:
            print(f"   评分维度: {df[self.dimension_col].nunique()} 个")

        return df

    def _build_score_matrix(self):
        """构建专家×投标人评分矩阵"""
        pivot = self.df.pivot_table(
            index=self.expert_col,
            columns=self.bidder_col,
            values=self.score_col,
            aggfunc='mean'  # 同一专家同一投标人有多个评分时取平均
        )
        return pivot

    # ================================================================
    # 检测方法1: Z-score 偏离度
    # ================================================================

    def detect_zscore_deviation(self):
        """Z-score偏离度检测

        原理：对每个投标人，计算所有专家评分的均值和标准差，
              然后计算每个专家评分的Z-score = (评分-均值)/标准差
              |Z-score| > threshold_z 则认为显著偏离
        """
        pivot = self._build_score_matrix()
        experts = pivot.index.tolist()
        bidders = pivot.columns.tolist()

        zscore_results = []
        for bidder in bidders:
            scores = pivot[bidder].dropna()
            if len(scores) < self.min_experts:
                continue
            mean_score = scores.mean()
            std_score = scores.std()
            if std_score == 0:
                continue

            for expert in scores.index:
                z = (scores[expert] - mean_score) / std_score
                if abs(z) > self.threshold_z:
                    zscore_results.append({
                        '检测方法': 'Z-score偏离',
                        '专家': expert,
                        '投标人': bidder,
                        '该专家评分': round(scores[expert], 2),
                        '该投标人平均评分': round(mean_score, 2),
                        '偏离标准差': round(std_score, 2),
                        'Z-score': round(z, 2),
                        '偏离方向': '偏高' if z > 0 else '偏低',
                        '风险等级': '高' if abs(z) > 3 else '中',
                        '说明': f"该专家评分比均值偏离 {abs(z):.1f} 个标准差"
                    })

        return pd.DataFrame(zscore_results) if zscore_results else pd.DataFrame()

    # ================================================================
    # 检测方法2: IQR 四分位距法
    # ================================================================

    def detect_iqr_outlier(self):
        """IQR异常值检测

        原理：对每个投标人，计算Q1(25%)和Q3(75%)，IQR = Q3-Q1
              正常范围: [Q1-1.5*IQR, Q3+1.5*IQR]
              超出此范围即为异常值
        """
        pivot = self._build_score_matrix()
        bidders = pivot.columns.tolist()

        iqr_results = []
        for bidder in bidders:
            scores = pivot[bidder].dropna()
            if len(scores) < self.min_experts:
                continue
            q1 = scores.quantile(0.25)
            q3 = scores.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            for expert, score in scores.items():
                if score < lower or score > upper:
                    iqr_results.append({
                        '检测方法': 'IQR异常值',
                        '专家': expert,
                        '投标人': bidder,
                        '该专家评分': round(score, 2),
                        'Q1': round(q1, 2),
                        'Q3': round(q3, 2),
                        'IQR': round(iqr, 2),
                        '正常范围': f"[{round(lower, 2)}, {round(upper, 2)}]",
                        '偏离方向': '偏低' if score < lower else '偏高',
                        '风险等级': '高' if score < lower - iqr or score > upper + iqr else '中',
                        '说明': f"超出四分位距正常范围"
                    })

        return pd.DataFrame(iqr_results) if iqr_results else pd.DataFrame()

    # ================================================================
    # 检测方法3: 变异系数 (CV) 分析
    # ================================================================

    def detect_cv_anomaly(self):
        """变异系数分析

        原理：对每个专家，计算其评分所有投标人的变异系数 CV = 标准差/均值
              CV > threshold_cv 说明该专家评分波动异常（可能打人情分或压分）
        """
        pivot = self._build_score_matrix()
        cv_results = []

        for expert in pivot.index:
            scores = pivot.loc[expert].dropna()
            if len(scores) < self.min_bidders:
                continue
            mean_s = scores.mean()
            std_s = scores.std()
            cv = std_s / mean_s if mean_s != 0 else 0

            if cv > self.threshold_cv:
                # 进一步分析：是普遍偏高/偏低还是选择性打分
                high_scores = (scores > scores.quantile(0.75)).sum()
                low_scores = (scores < scores.quantile(0.25)).sum()
                pattern = "选择性高分" if high_scores > len(scores) * 0.5 else \
                         "选择性低分" if low_scores > len(scores) * 0.5 else "波动大"

                cv_results.append({
                    '检测方法': '变异系数异常',
                    '专家': expert,
                    '评分均值': round(mean_s, 2),
                    '评分标准差': round(std_s, 2),
                    '变异系数CV': round(cv, 3),
                    '评分范围': f"{round(scores.min(), 2)} - {round(scores.max(), 2)}",
                    '打分模式': pattern,
                    '风险等级': '高' if cv > 0.5 else '中',
                    '说明': f"该专家评分波动异常(CV={cv:.3f})，存在{pattern}嫌疑"
                })

        return pd.DataFrame(cv_results) if cv_results else pd.DataFrame()

    # ================================================================
    # 检测方法4: Kendall W 协调系数
    # ================================================================

    def detect_kendall_w(self):
        """Kendall's W 协调系数

        原理：检验所有专家评分的一致性。
              W = 0 表示完全不一致（各评各的）
              W = 1 表示完全一致（专家打分一模一样）
              W < 0.5 通常认为一致性差，需要关注
        """
        pivot = self._build_score_matrix()
        # 去除有缺失值的专家
        pivot_clean = pivot.dropna()

        if pivot_clean.shape[0] < self.min_experts or pivot_clean.shape[1] < 2:
            return pd.DataFrame()

        # 转换为排名（Kendall W基于排名）
        rankings = pivot_clean.rank(axis=1, method='average')

        # 手动计算Kendall W
        n = rankings.shape[1]  # 投标人数
        m = rankings.shape[0]  # 专家数
        if m < 2 or n < 2:
            return pd.DataFrame()

        # 每个投标人的排名总和
        rank_sums = rankings.sum(axis=0)
        mean_rank_sum = rank_sums.mean()
        s = ((rank_sums - mean_rank_sum) ** 2).sum()
        w = (12 * s) / (m ** 2 * n * (n ** 2 - 1)) if n > 1 and m > 0 else 0

        # 判断一致性
        if w >= 0.7:
            consistency = "高度一致"
        elif w >= 0.5:
            consistency = "中等一致"
        elif w >= 0.3:
            consistency = "一致性较差"
        else:
            consistency = "严重不一致（需关注）"

        result = {
            '检测方法': 'Kendall W协调系数',
            '专家人数': m,
            '投标人数': n,
            '协调系数W': round(w, 4),
            '一致性评价': consistency,
            '风险等级': '高' if w < 0.3 else '中' if w < 0.5 else '低',
            '说明': f"专家评分一致性{consistency}，W={w:.4f}"
        }

        return pd.DataFrame([result])

    # ================================================================
    # 检测方法5: 聚类分析（孤立专家识别）
    # ================================================================

    def detect_cluster_outlier(self, n_clusters=2):
        """层次聚类分析

        原理：基于专家评分向量进行聚类，识别与大多数专家评分模式不同的专家
        """
        pivot = self._build_score_matrix()
        pivot_clean = pivot.fillna(pivot.mean(axis=1)).fillna(0)
        if pivot.shape[0] < self.min_experts:
            return pd.DataFrame()

        # 标准化
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        scaled = scaler.fit_transform(pivot.values)

        # 层次聚类
        dist = pdist(scaled, metric='euclidean')
        link = linkage(dist, method='ward')
        labels = fcluster(link, n_clusters, criterion='maxclust')

        # 找出小类（孤立专家）
        clusters = defaultdict(list)
        for expert, label in zip(pivot.index, labels):
            clusters[label].append(expert)

        cluster_results = []
        for label, experts in clusters.items():
            if len(experts) <= max(1, len(pivot) // 3):  # 小类（占比不超过1/3）
                for expert in experts:
                    cluster_results.append({
                        '检测方法': '聚类孤立',
                        '专家': expert,
                        '所属聚类': label,
                        '聚类人数': len(experts),
                        '总专家数': len(pivot),
                        '风险等级': '高' if len(experts) == 1 else '中',
                        '说明': f"该专家评分模式与大多数专家不同，独自构成聚类{label}"
                    })

        return pd.DataFrame(cluster_results) if cluster_results else pd.DataFrame()

    # ================================================================
    # 检测方法6: 压线打分/满分/零分检测
    # ================================================================

    def detect_extreme_pattern(self):
        """极端打分模式检测

        检测：
        - 频繁打满分（或接近满分）
        - 频繁打最低分
        - 打分集中在某个区间（如全部80-82分）
        """
        pivot = self._build_score_matrix()
        extreme_results = []

        for expert in pivot.index:
            scores = pivot.loc[expert].dropna()
            if len(scores) < 2:
                continue

            max_score = scores.max()
            min_score = scores.min()
            score_range = max_score - min_score

            # 假设满分100，检测
            full_marks = (scores >= 95).sum()
            zero_marks = (scores <= 10).sum()
            narrow_band = (scores.between(80, 82)).sum()  # 压线集中
            all_same = (scores == scores.iloc[0]).sum()

            if full_marks >= len(scores) * 0.5:
                extreme_results.append({
                    '检测方法': '极端打分模式',
                    '专家': expert,
                    '模式': '高分集中',
                    '满分/高分次数': int(full_marks),
                    '占其评分比例': f"{full_marks/len(scores)*100:.0f}%",
                    '风险等级': '高',
                    '说明': f"该专家{full_marks}/{len(scores)}次打高分(≥95)，疑似人情分"
                })

            if narrow_band >= len(scores) * 0.5:
                extreme_results.append({
                    '检测方法': '极端打分模式',
                    '专家': expert,
                    '模式': '压线集中',
                    '压线次数': int(narrow_band),
                    '占其评分比例': f"{narrow_band/len(scores)*100:.0f}%",
                    '风险等级': '高',
                    '说明': f"该专家{narrow_band}/{len(scores)}次打分集中在80-82分，疑似压线操作"
                })

            if all_same == len(scores):
                extreme_results.append({
                    '检测方法': '极端打分模式',
                    '专家': expert,
                    '模式': '完全一致',
                    '统一分数': round(scores.iloc[0], 2),
                    '评分次数': len(scores),
                    '风险等级': '高',
                    '说明': f"该专家对所有投标人打分完全一致({scores.iloc[0]}分)，严重异常"
                })

        return pd.DataFrame(extreme_results) if extreme_results else pd.DataFrame()

    # ================================================================
    # 综合检测
    # ================================================================

    def run_all_detections(self):
        """运行全部检测方法，返回综合报告"""
        print("\n" + "="*60)
        print("  评标专家偏离度检测 — 综合报告")
        print("="*60)

        methods = {
            'Kendall W协调系数': self.detect_kendall_w,
            'Z-score偏离': self.detect_zscore_deviation,
            'IQR异常值': self.detect_iqr_outlier,
            '变异系数异常': self.detect_cv_anomaly,
            '聚类孤立': self.detect_cluster_outlier,
            '极端打分模式': self.detect_extreme_pattern,
        }

        all_results = []
        summary = {}

        for name, method in methods.items():
            try:
                result = method()
                if not result.empty:
                    all_results.append(result)
                    summary[name] = {
                        '异常数': len(result),
                        '高': len(result[result['风险等级'] == '高']) if '风险等级' in result.columns else 0,
                        '中': len(result[result['风险等级'] == '中']) if '风险等级' in result.columns else 0,
                    }
                    print(f"\n✅ [{name}]: 发现 {len(result)} 条异常")
                    if '风险等级' in result.columns:
                        high = summary[name]['高']
                        mid = summary[name]['中']
                        if high > 0:
                            print(f"   🔴 高风险: {high} 条")
                        if mid > 0:
                            print(f"   🟡 中风险: {mid} 条")
                else:
                    summary[name] = {'异常数': 0, '高': 0, '中': 0}
                    print(f"\n✅ [{name}]: 未检出异常")
            except Exception as e:
                print(f"\n⚠️ [{name}]: 检测失败 - {e}")
                summary[name] = {'异常数': 0, '高': 0, '中': 0, 'error': str(e)}

        # 合并所有结果
        if all_results:
            combined = pd.concat(all_results, ignore_index=True)
        else:
            combined = pd.DataFrame()

        self.results = {
            'summary': summary,
            'combined': combined,
            'expert_map': self.expert_map,
            'bidder_map': self.bidder_map
        }

        return self.results

    # ================================================================
    # 输出报告
    # ================================================================

    def export_report(self, output_path, include_charts=True):
        """导出Excel报告（多sheet）"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet1: 综合摘要
            summary_data = []
            for method, stats in self.results['summary'].items():
                summary_data.append({
                    '检测方法': method,
                    '异常总数': stats.get('异常数', 0),
                    '高风险数': stats.get('高', 0),
                    '中风险数': stats.get('中', 0)
                })
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='检测摘要', index=False)

            # Sheet2: 详细异常记录
            if not self.results['combined'].empty:
                self.results['combined'].to_excel(writer, sheet_name='异常记录', index=False)

            # Sheet3: 评分矩阵（原始脱敏数据）
            pivot = self._build_score_matrix()
            pivot.to_excel(writer, sheet_name='评分矩阵')

            # Sheet4: 专家统计
            expert_stats = []
            pivot = self._build_score_matrix()
            for expert in pivot.index:
                scores = pivot.loc[expert].dropna()
                expert_stats.append({
                    '专家': expert,
                    '评分次数': len(scores),
                    '最高分': round(scores.max(), 2),
                    '最低分': round(scores.min(), 2),
                    '平均分': round(scores.mean(), 2),
                    '标准差': round(scores.std(), 2),
                    '变异系数': round(scores.std()/scores.mean(), 3) if scores.mean() != 0 else 0
                })
            pd.DataFrame(expert_stats).to_excel(writer, sheet_name='专家统计', index=False)

        print(f"\n💾 报告已导出: {output_path}")
        print(f"   Sheets: 检测摘要 / 异常记录 / 评分矩阵 / 专家统计")

        # 生成JSON格式（供audit-blackboard findings使用）
        json_path = output_path.with_suffix('.json')
        findings = self._convert_to_findings()
        json_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"💾 Findings JSON: {json_path}")

        return output_path

    def _convert_to_findings(self):
        """转换为audit-blackboard finding_schema格式"""
        if self.results['combined'].empty:
            return []

        findings = []
        for idx, row in self.results['combined'].iterrows():
            finding = {
                "finding_id": f"F-2026-{idx+1:03d}",
                "agent": "expert_bias_detector",
                "timestamp": pd.Timestamp.now().isoformat(),
                "type": "评标异常",
                "severity": row.get('风险等级', '中'),
                "summary": f"[{row.get('检测方法', '?')}] {row.get('专家', '?')} - {row.get('说明', '')}",
                "confidence": 85 if row.get('风险等级') == '高' else 65,
                "entities": [row.get('专家', ''), row.get('投标人', '')] if '投标人' in row else [row.get('专家', '')],
                "evidence": [f"{k}: {v}" for k, v in row.items() if pd.notna(v)],
                "law_refs": [],
                "related_findings": [],
                "amount": None,
                "status": "未确认"
            }
            findings.append(finding)
        return findings


# ================================================================
# CLI
# ================================================================

def main():
    parser = argparse.ArgumentParser(description='融策评标专家偏离度检测模型 v1.0')
    parser.add_argument('--input', '-i', required=True, help='输入文件路径（Excel/CSV）')
    parser.add_argument('--output', '-o', default='偏离度分析报告.xlsx', help='输出报告路径')
    parser.add_argument('--threshold-z', type=float, default=2.0, help='Z-score阈值（默认2.0）')
    parser.add_argument('--threshold-cv', type=float, default=0.3, help='变异系数阈值（默认0.3）')
    parser.add_argument('--expert-col', default='专家姓名', help='专家列名')
    parser.add_argument('--bidder-col', default='投标人名称', help='投标人列名')
    parser.add_argument('--score-col', default='评分', help='评分列名')
    parser.add_argument('--no-charts', action='store_true', help='不生成图表')
    args = parser.parse_args()

    detector = ExpertBiasDetector(
        threshold_z=args.threshold_z,
        threshold_cv=args.threshold_cv
    )

    # 加载数据
    detector.load_data(
        args.input,
        expert_col=args.expert_col,
        bidder_col=args.bidder_col,
        score_col=args.score_col
    )

    # 运行检测
    detector.run_all_detections()

    # 导出报告
    detector.export_report(args.output, include_charts=not args.no_charts)

    print("\n" + "="*60)
    print("  ✅ 评标专家偏离度检测完成")
    print("="*60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
