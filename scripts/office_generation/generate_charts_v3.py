# -*- coding: utf-8 -*-
"""补充最后一批图表，拉高视觉占比到50%"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np, os

output_dir = r'D:\openclaw-workspace\output\charts'
os.makedirs(output_dir, exist_ok=True)
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 图14：修改前后指标结构对比桑基图风格示意
fig, ax = plt.subplots(figsize=(13, 6))
ax.set_xlim(0, 13); ax.set_ylim(0, 6); ax.axis('off')

# Before 列
ax.text(1.5, 5.7, '修改前', ha='center', fontsize=16, fontweight='bold', color='#E74C3C')
before_items = [
    ('管理效率 4项', '#E74C3C'), ('产出-时效 3项', '#3498DB'), ('产出-数量 5项', '#2ECC71'),
    ('产出-质量 2项', '#9B59B6'), ('效益指标 8项', '#F39C12'), ('满意度 0项', '#E67E22'),
    ('成本效率 0项', '#1ABC9C')
]
for i, (name, color) in enumerate(before_items):
    y = 4.8 - i*0.65
    rect = FancyBboxPatch((0.2, y-0.25), 2.6, 0.5, boxstyle="round,pad=0.05",
                           facecolor=color, edgecolor='white', linewidth=1, alpha=0.85)
    ax.add_patch(rect)
    ax.text(1.5, y, name, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')

# After 列
ax.text(11.5, 5.7, '修改后', ha='center', fontsize=16, fontweight='bold', color='#2ECC71')
after_items = [
    ('管理效率 12项 (+8)', '#E74C3C'), ('产出-时效 3项', '#3498DB'), ('产出-数量 5项', '#2ECC71'),
    ('产出-质量 3项 (+1)', '#9B59B6'), ('效益指标 8项', '#F39C12'), ('满意度 3项 (+3)', '#E67E22'),
    ('成本效率 2项 (+2)', '#1ABC9C')
]
for i, (name, color) in enumerate(after_items):
    y = 4.8 - i*0.65
    rect = FancyBboxPatch((10.2, y-0.25), 2.6, 0.5, boxstyle="round,pad=0.05",
                           facecolor=color, edgecolor='white', linewidth=1, alpha=0.85)
    ax.add_patch(rect)
    ax.text(11.5, y, name, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')

# 箭头区域
for i in range(7):
    y = 4.8 - i*0.65
    ax.annotate('', xy=(10.0, y), xytext=(3.0, y),
                arrowprops=dict(arrowstyle='->', color='#1C355E', lw=1.5))

# 中间说明
ax.text(6.5, 5.7, '修改方向', ha='center', fontsize=13, fontweight='bold', color='#1C355E')
rect = FancyBboxPatch((4.5, 0.3), 4.0, 1.2, boxstyle="round,pad=0.1",
                       facecolor='#E8EDF5', edgecolor='#1C355E', linewidth=1.5)
ax.add_patch(rect)
ax.text(6.5, 1.1, '小计：22项', ha='center', fontsize=11, fontweight='bold', color='#E74C3C')
ax.text(6.5, 0.8, '新增14项，重构后36项', ha='center', fontsize=11, color='#2ECC71', fontweight='bold')
ax.text(6.5, 0.5, '管理效率占比: 18% -> 33%', ha='center', fontsize=9, color='#666666')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'side_by_side.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图14: side_by_side.png')

# 图15：指标值设定原则（3C原则）
fig, ax = plt.subplots(figsize=(11, 6))
ax.set_xlim(0, 11); ax.set_ylim(0, 6); ax.axis('off')

principles = [
    ('Challenging\n挑战性', 2.0, '#E74C3C', '目标值应略高于\n历史平均水平\n激励持续改进'),
    ('Comparable\n可比较', 5.5, '#3498DB', '目标值可横向\n（同级区县）和纵向\n（历史年度）比较'),
    ('Credible\n可信赖', 9.0, '#2ECC71', '目标值有历史数据\n或行业标准支撑\n经得起验证'),
]
for name, cx, color, desc in principles:
    circle = plt.Circle((cx, 3.5), 1.0, facecolor=color, edgecolor='white', linewidth=3, alpha=0.9)
    ax.add_patch(circle)
    ax.text(cx, 3.5, name, ha='center', va='center', fontsize=13, fontweight='bold', color='white')
    ax.text(cx, 1.5, desc, ha='center', va='center', fontsize=9.5, color='#555555')

ax.text(5.5, 5.5, '图15：指标值设定 3C 原则', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
ax.text(5.5, 0.5, '好的指标值 = 跳一跳够得着 + 看得懂可比 + 有数据撑得住', fontsize=10, color='#999999', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, '3c_principle.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图15: 3c_principle.png')

# 图16：绩效目标管理闭环
fig, ax = plt.subplots(figsize=(11, 6))
ax.set_xlim(0, 11); ax.set_ylim(0, 6); ax.axis('off')

cycle_items = [
    ('绩效目标\n编制', 1.8, 4.5, '#1C355E'),
    ('绩效监控\n（季度）', 5.5, 4.5, '#3A7BD5'),
    ('绩效评价\n（年度）', 9.2, 4.5, '#5B9BD5'),
    ('结果应用\n（反馈+整改）', 5.5, 1.5, '#8DB9E8'),
]
for name, cx, cy, color in cycle_items:
    rect = FancyBboxPatch((cx-1.5, cy-0.7), 3.0, 1.4, boxstyle="round,pad=0.1",
                           facecolor=color, edgecolor='white', linewidth=2)
    ax.add_patch(rect)
    ax.text(cx, cy, name, ha='center', va='center', fontsize=12, fontweight='bold', color='white')

# 循环箭头
for i in range(4):
    nxt = (i+1)%4
    x1, y1 = cycle_items[i][1], cycle_items[i][2]
    x2, y2 = cycle_items[nxt][1], cycle_items[nxt][2]
    midx, midy = (x1+x2)/2, (y1+y2)/2
    # 偏移让箭头走圆弧
    ax.annotate('', xy=(x2-0.8 if x2>x1 else x2+0.8, y2-0.8 if y2<y1 else y2+0.8),
                xytext=(x1+0.8 if x2>x1 else x1-0.8, y1-0.8 if y1>y2 else y1+0.8),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3', color='#1C355E', lw=2.5))

ax.text(5.5, 5.7, '图16：预算绩效管理闭环——本次辅导与审核服务的是第一步', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'performance_cycle.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图16: performance_cycle.png')

print('Done - 3 additional charts')
