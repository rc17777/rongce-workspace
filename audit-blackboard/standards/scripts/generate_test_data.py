# -*- coding: utf-8 -*-
"""
评标专家偏离度检测 — 生成测试数据

用于验证 expert_bias_detection.py 的准确性
生成模拟评标数据，包含各种异常模式：
- 专家A：正常打分（基准）
- 专家B：对某投标人持续打高分（人情分）
- 专家C：对某投标人持续打低分（打压）
- 专家D：打分集中在狭窄区间（压线操作）
- 专家E：打分波动极大（标准差异常）
- 专家F：所有投标人打分一样（完全一致）
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

np.random.seed(42)

experts = ['张伟', '李娜', '王强', '刘洋', '陈静', '赵刚']
bidders = ['四川锦城建设', '成都远景工程', '四川华建集团', '成都新世纪建设', '四川天成建筑']

# 基础评分矩阵（专家×投标人）
# 满分100，正常分布：均值75-85，标准差5-8
base_scores = {
    '张伟':   [82, 78, 85, 80, 76],   # 正常
    '李娜':   [83, 79, 84, 81, 77],   # 正常
    '王强':   [95, 90, 88, 85, 80],   # 对前两个投标人打高分（人情分）
    '刘洋':   [70, 72, 65, 68, 75],   # 对第三个投标人打低分（打压）
    '陈静':   [80, 81, 79, 82, 80],   # 打分集中在狭窄区间（压线80-82）
    '赵刚':   [85, 85, 85, 85, 85],   # 所有一样（完全一致）
}

# 生成多维度评分（技术分、商务分、价格分）
dimensions = ['技术分', '商务分', '价格分']
weight = {'技术分': 0.4, '商务分': 0.3, '价格分': 0.3}

records = []
for expert in experts:
    for i, bidder in enumerate(bidders):
        # 总分
        total = base_scores[expert][i]
        # 按权重分配各维度（加随机扰动）
        tech = total * 0.4 + np.random.normal(0, 2)
        business = total * 0.3 + np.random.normal(0, 1.5)
        price = total * 0.3 + np.random.normal(0, 1.5)
        # 确保各维度在合理范围
        tech = np.clip(tech, 30, 100)
        business = np.clip(business, 30, 100)
        price = np.clip(price, 30, 100)

        records.append({
            '专家姓名': expert,
            '投标人名称': bidder,
            '技术分': round(tech, 2),
            '商务分': round(business, 2),
            '价格分': round(price, 2),
            '总分': round(tech + business + price, 2)
        })

df = pd.DataFrame(records)

# 保存测试数据
output_dir = Path(__file__).parent / 'test_data'
output_dir.mkdir(exist_ok=True)
output_path = output_dir / '评标打分测试数据.xlsx'
df.to_excel(output_path, index=False)

print(f"✅ 测试数据已生成: {output_path}")
print(f"\n📊 数据概要:")
print(f"   专家: {df['专家姓名'].nunique()} 人")
print(f"   投标人: {df['投标人名称'].nunique()} 家")
print(f"   评分记录: {len(df)} 条")
print(f"\n🔍 预设异常模式:")
print(f"   王强 → 对前两家投标人持续打高分（人情分）")
print(f"   刘洋 → 对第三家投标人打低分（打压）")
print(f"   陈静 → 打分集中在狭窄区间（压线）")
print(f"   赵刚 → 所有投标人打分完全一致")
print(f"\n运行检测:")
print(f"   python expert_bias_detection.py -i \"{output_path}\" -o \"偏离度分析报告.xlsx\"")
