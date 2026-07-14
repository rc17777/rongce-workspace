# -*- coding: utf-8 -*-
"""生成文档配图"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

output_dir = r'D:\openclaw-workspace\output\charts'
os.makedirs(output_dir, exist_ok=True)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 图1：五阶段工作流程图
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(14, 6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 6)
ax.axis('off')
ax.set_facecolor('#FAFBFC')

# 阶段数据
stages = [
    {'name': '第一阶段\n前置辅导', 'desc': '政策解读培训\n职能梳理\n历史数据分析\n资料清单交付', 'color': '#1C355E', 'x': 1},
    {'name': '第二阶段\n初步编制', 'desc': '管理效率指标编制\n履职效能指标编制\n指标值设定\n权重分配', 'color': '#2B579A', 'x': 3.4},
    {'name': '第三阶段\n专业审核', 'desc': '完整性审核\n科学性审核\n合理性审核\n可操作性审核', 'color': '#3A7BD5', 'x': 5.8},
    {'name': '第四阶段\n反馈修改', 'desc': '书面反馈\n沟通会议\n修订辅导\n争议处理', 'color': '#5B9BD5', 'x': 8.2},
    {'name': '第五阶段\n复核确认', 'desc': '逐项复核\n逻辑一致性检查\n准确性核实\n出具工作报告', 'color': '#8DB9E8', 'x': 10.6},
]

for i, s in enumerate(stages):
    # 主框
    rect = FancyBboxPatch((s['x'], 2.5), 2.2, 2.8, boxstyle="round,pad=0.15",
                           facecolor=s['color'], edgecolor='white', linewidth=2, alpha=0.9)
    ax.add_patch(rect)
    # 阶段名称
    ax.text(s['x'] + 1.1, 4.8, s['name'], ha='center', va='center',
            fontsize=12, fontweight='bold', color='white')
    # 描述
    ax.text(s['x'] + 1.1, 2.9, s['desc'], ha='center', va='center',
            fontsize=8, color='white', alpha=0.9)
    # 箭头
    if i < len(stages) - 1:
        ax.annotate('', xy=(s['x'] + 2.3, 3.9), xytext=(stages[i+1]['x'] - 0.1, 3.9),
                    arrowprops=dict(arrowstyle='->', color='#1C355E', lw=2.5))

# 图例/说明
ax.text(0.5, 1.6, '图1：绩效目标编制辅导与审核"五阶段闭环"工作流程', fontsize=14,
        fontweight='bold', color='#1C355E')
ax.text(0.5, 1.0, '该流程遵循"辅导先行→编制为主→审核把关→反馈闭环→复核兜底"的逻辑，确保全过程可控、可追溯。',
        fontsize=10, color='#666666')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'workflow.png'), dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('图1已生成：workflow.png')

# ============================================================
# 图2：绩效指标体系结构饼图
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 左图：管理效率 vs 履职效能 占比
labels1 = ['管理效率\n(4项指标, 18.2%)', '履职效能\n(18项指标, 81.8%)']
sizes1 = [18.2, 81.8]
colors1 = ['#E74C3C', '#3498DB']
explode1 = (0.05, 0)

wedges1, texts1, autotexts1 = ax1.pie(sizes1, explode=explode1, labels=labels1,
                                       colors=colors1, autopct='', startangle=90,
                                       textprops={'fontsize': 12, 'fontweight': 'bold'})
# 手动添加百分比
ax1.text(-1.15, 0.02, '18.2%', fontsize=18, fontweight='bold', color='white', ha='center')
ax1.text(0.95, -0.05, '81.8%', fontsize=18, fontweight='bold', color='white', ha='center')
ax1.set_title('现有指标体系结构', fontsize=14, fontweight='bold', color='#1C355E', pad=20)

# 右图：建议优化后的结构
labels2 = ['管理效率\n(建议增至12项)', '履职效能-产出\n(10项)', '履职效能-效益\n(8项)', '履职效能-满意度\n(3项)']
sizes2 = [36.4, 30.3, 24.2, 9.1]
colors2 = ['#E74C3C', '#2ECC71', '#F39C12', '#9B59B6']
explode2 = (0.05, 0, 0, 0)

wedges2, texts2 = ax2.pie(sizes2, explode=explode2, labels=labels2,
                             colors=colors2, startangle=90,
                             textprops={'fontsize': 11, 'fontweight': 'bold'})
ax2.set_title('建议优化后的指标体系结构', fontsize=14, fontweight='bold', color='#1C355E', pad=20)

fig.suptitle('图2：绩效指标体系结构对比分析', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'structure_pie.png'), dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('图2已生成：structure_pie.png')

# ============================================================
# 图3：绩效指标分类分布柱状图
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

categories = ['现有指标数', '建议指标数']
current = [4, 10, 8, 0, 0, 0, 0]  # 管理效率, 产出-时效, 产出-数量, 产出-质量, 效益, 满意度, 成本
proposed = [-4, -3, -3, -2, -4, -3, -2]  # 建议增加的数量
keep = [4, 3, 3, 2, 4, 0, 0]
add = [0, 0, 2, 0, 4, 3, 2]
labels = ['管理效率', '产出-时效', '产出-数量', '产出-质量', '效益指标', '满意度', '成本指标']
existing_colors = ['#E74C3C', '#2ECC71', '#2ECC71', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C']

x = np.arange(len(labels))
width = 0.35

# 现有指标
bars1 = ax.bar(x - width/2, current, width, label='现有指标',
               color=existing_colors, edgecolor='white', linewidth=1.5)

# 建议增补指标
bars2 = ax.bar(x + width/2, [c + a for c, a in zip(current, add)], width,
               label='建议指标总数', color=[c for c in existing_colors], alpha=0.4,
               edgecolor='white', linewidth=1.5, hatch='///')

# 在建议柱上标注新增数
for i, (c, a) in enumerate(zip(current, add)):
    if a > 0:
        ax.annotate(f'+{a}', (x[i] + width/2, c + a), textcoords="offset points",
                    xytext=(0, 8), ha='center', fontsize=11, fontweight='bold', color='#E74C3C')

# 在现有柱上标注数量
for i, v in enumerate(current):
    if v > 0:
        ax.text(x[i] - width/2, v + 0.5, str(v), ha='center', fontsize=11, fontweight='bold')

for i, (c, a) in enumerate(zip(current, add)):
    if c + a > 0:
        ax.text(x[i] + width/2, c + a + 0.5, str(c + a), ha='center', fontsize=11, fontweight='bold')

ax.set_ylabel('指标数量（项）', fontsize=12)
ax.set_title('图3：绩效指标分类分布对比——现有 vs 建议', fontsize=15, fontweight='bold', color='#1C355E')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.legend(fontsize=11, loc='upper right')
ax.set_ylim(0, max(current) + max(add) + 5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'indicator_distribution.png'), dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('图3已生成：indicator_distribution.png')

# ============================================================
# 图4：问题雷达图
# ============================================================
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

categories_radar = ['分类科学性', '指标量化度', '管理效率\n完整性', '指标值\n明确性',
                     '数量质量\n边界', '满意度\n指标', '成本指标\n维度']
N = len(categories_radar)
values = [3, 2, 2, 1, 3, 0, 1]  # 评分（1-5，越高越好）
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]
values += values[:1]

ax.plot(angles, values, 'o-', linewidth=2, color='#E74C3C', markersize=8)
ax.fill(angles, values, alpha=0.25, color='#E74C3C')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories_radar, fontsize=11, fontweight='bold')
ax.set_ylim(0, 5)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(['严重\n不足', '不足', '一般', '良好', '优秀'], fontsize=9)
ax.set_title('图4：现行绩效指标体系七维雷达诊断', fontsize=15, fontweight='bold',
             color='#1C355E', pad=25)

# 添加评分说明
ax.text(np.pi/2, -1.5, '（评分标准：5=优秀 4=良好 3=一般 2=不足 1=严重不足）',
        ha='center', fontsize=10, color='#999999')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'radar_diagnosis.png'), dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('图4已生成：radar_diagnosis.png')

# ============================================================
# 图5：三级复核质量控制图
# ============================================================
fig, ax = plt.subplots(figsize=(12, 5))
ax.set_xlim(0, 12)
ax.set_ylim(0, 5)
ax.axis('off')

# 三级复核金字塔
levels = [
    {'name': '三级复核\n总负责人', 'y': 3.8, 'h': 1.3, 'w': 2.5, 'x': 4.75,
     'color': '#1C355E', 'desc': '整体逻辑自洽\n重大问题判断\n报告严谨性'},
    {'name': '二级复核\n组长复核', 'y': 2.3, 'h': 1.3, 'w': 5.5, 'x': 3.25,
     'color': '#3A7BD5', 'desc': '审核结论准确性\n修改建议合理性\n底稿规范性'},
    {'name': '一级复核\n执行人员自查', 'y': 0.8, 'h': 1.3, 'w': 9, 'x': 1.5,
     'color': '#8DB9E8', 'desc': '审核程序执行到位\n审核发现完整记录\n数据准确性'},
]

for lvl in levels:
    rect = FancyBboxPatch((lvl['x'], lvl['y']), lvl['w'], lvl['h'],
                           boxstyle="round,pad=0.1", facecolor=lvl['color'],
                           edgecolor='white', linewidth=2, alpha=0.9)
    ax.add_patch(rect)
    ax.text(lvl['x'] + lvl['w']/2, lvl['y'] + lvl['h'] - 0.35, lvl['name'],
            ha='center', va='top', fontsize=13, fontweight='bold', color='white')
    ax.text(lvl['x'] + lvl['w']/2, lvl['y'] + 0.2, lvl['desc'],
            ha='center', va='bottom', fontsize=9, color='white', alpha=0.9)

ax.text(6, 5.4, '图5：三级复核质量控制金字塔', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
ax.text(6, 0.2, '自下而上，层层把关，确保交付成果零缺陷', fontsize=10, color='#666666', ha='center')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'quality_control.png'), dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('图5已生成：quality_control.png')

print('\n全部图表生成完毕！')
