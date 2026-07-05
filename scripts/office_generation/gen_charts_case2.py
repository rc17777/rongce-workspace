import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc
import numpy as np
import os

outdir = r'D:\openclaw-workspace\output\模拟案例二'
os.makedirs(outdir, exist_ok=True)

# ========== 统一品牌色 ==========
C1 = '#1C355E'  # 深蓝主色
C2 = '#2D5F9A'  # 中蓝
C3 = '#4A90D9'  # 浅蓝
C4 = '#E8F0FA'  # 极浅蓝
C5 = '#F5A623'  # 橘色强调
C6 = '#D0021B'  # 红色
C7 = '#27AE60'  # 绿色
C8 = '#333333'  # 深灰文字

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 图1: 绩效评价指标体系四维框架图 ====================
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

# 标题
ax.text(6, 7.5, '老旧小区改造专项绩效评价指标体系框架', fontsize=18, fontweight='bold',
        ha='center', va='center', color=C1)

# 四维金字塔 - 顶层
rect1 = FancyBboxPatch((4, 5.8), 4, 1.2, boxstyle="round,pad=0.1",
                        facecolor=C1, edgecolor='white', linewidth=2)
ax.add_patch(rect1)
ax.text(6, 6.4, '项目决策 (20%)', fontsize=14, fontweight='bold', ha='center', va='center', color='white')
ax.text(6, 6.1, '立项依据 | 绩效目标 | 资金投入', fontsize=9, ha='center', va='center', color='#CCD9F0')

# 第二层 - 三个模块
for i, (title, items, y) in enumerate([
    ('项目管理 (25%)', '资金管理 | 财务管理 | 采购管理', 4.2),
    ('过程管理 (25%)', '工程进度 | 质量管理 | 安全管理', 2.6),
    ('项目产出 (20%)', '数量完成 | 质量达标 | 时效合规', 1.0)
]):
    x = 4 if i == 0 else (1.5 if i == 1 else 6.5)
    w = 4 if i == 0 else 4
    rect = FancyBboxPatch((x, y), w, 1.0, boxstyle="round,pad=0.1",
                          facecolor=C2, edgecolor='white', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x+w/2, y+0.6, title, fontsize=12, fontweight='bold', ha='center', va='center', color='white')
    ax.text(x+w/2, y+0.25, items, fontsize=8, ha='center', va='center', color='#CCD9F0')

# 连接箭头
for (y_top, y_bot, x_mid) in [(5.8, 5.2, 6), (4.2, 3.5, 3.5), (4.2, 3.5, 8.5)]:
    ax.annotate('', xy=(x_mid, y_bot), xytext=(x_mid, y_top),
                arrowprops=dict(arrowstyle='->', color=C3, lw=2))

# 底层 - 项目效果
rect_base = FancyBboxPatch((1.5, -0.3), 9, 0.8, boxstyle="round,pad=0.1",
                           facecolor=C7, edgecolor='white', linewidth=2)
ax.add_patch(rect_base)
ax.text(6, 0.1, '项目效益 (10%)  社会效益 | 生态效益 | 可持续影响 | 满意度', fontsize=12,
        fontweight='bold', ha='center', va='center', color='white')

plt.tight_layout()
fig.savefig(os.path.join(outdir, '1_指标框架.png'), dpi=200, bbox_inches='tight', transparent=False, facecolor='white')
plt.close()

# ==================== 图2: 评价工作流程图 ====================
fig, ax = plt.subplots(1, 1, figsize=(12, 6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis('off')

ax.text(6, 5.6, '老旧小区改造专项绩效评价工作流程', fontsize=18, fontweight='bold',
        ha='center', va='center', color=C1)

stages = [
    ('准备阶段', '制定方案\n指标设计\n基础数据表', C1),
    ('实施阶段', '资料收集\n现场核查\n问卷调查', C2),
    ('分析阶段', '数据分析\n指标评分\n问题确认', C3),
    ('报告阶段', '撰写报告\n征求意见\n定稿归档', C2),
    ('整改跟踪', '问题整改\n“回头看”\n结果运用', C7),
]

for idx, (title, detail, color) in enumerate(stages):
    x = 1.0 + idx * 2.2
    y = 3.0
    rect = FancyBboxPatch((x, y-0.8), 1.8, 1.9, boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor='white', linewidth=2, alpha=0.9)
    ax.add_patch(rect)
    ax.text(x+0.9, y+0.75, title, fontsize=13, fontweight='bold', ha='center', va='center', color='white')
    for j, line in enumerate(detail.split('\n')):
        ax.text(x+0.9, y+0.2 - j*0.4, line, fontsize=8, ha='center', va='center', color='#E8F0FA')

    if idx < len(stages) - 1:
        ax.annotate('', xy=(x+1.8, y+0.2), xytext=(x+2.2, y+0.2),
                    arrowprops=dict(arrowstyle='->', color=C8, lw=2.5))

# 时间轴
ax.plot([1.0, 11.0], [0.5, 0.5], color=C8, linewidth=2)
for i in range(6):
    ax.plot(1.0 + i*2.0, 0.5, 'o', color=C5, markersize=10)
ax.text(1.0, 0.15, '第1-2周', ha='center', fontsize=8, color=C8)
ax.text(3.0, 0.15, '第3-5周', ha='center', fontsize=8, color=C8)
ax.text(5.0, 0.15, '第6-8周', ha='center', fontsize=8, color=C8)
ax.text(7.0, 0.15, '第9-11周', ha='center', fontsize=8, color=C8)
ax.text(9.0, 0.15, '第12-16周', ha='center', fontsize=8, color=C8)

plt.tight_layout()
fig.savefig(os.path.join(outdir, '2_评价流程.png'), dpi=200, bbox_inches='tight', transparent=False, facecolor='white')
plt.close()

# ==================== 图3: 评价团队组织架构 ====================
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

ax.text(5, 5.6, '评价团队组织架构', fontsize=16, fontweight='bold', ha='center', va='center', color=C1)

# 项目负责人
rect_lead = FancyBboxPatch((3.5, 4.8), 3, 0.6, boxstyle="round,pad=0.05",
                           facecolor=C1, edgecolor='white', linewidth=2)
ax.add_patch(rect_lead)
ax.text(5, 5.1, '项目负责人（1名）', fontsize=12, fontweight='bold', ha='center', va='center', color='white')

# 四个组
groups = [
    ('综合协调组', '统筹调度\n沟通对接\n进度管控', 2),
    ('技术评价组', '现场核查\n指标评分\n数据分析', 2),
    ('财务审计组', '资金审查\n预算执行\n合规审计', 2),
    ('报告质控组', '报告撰写\n质量审核\n档案管理', 2),
]

for idx, (name, detail, members) in enumerate(groups):
    x = 0.5 + idx * 2.4
    w = 2.0
    rect = FancyBboxPatch((x, 2.5), w, 1.8, boxstyle="round,pad=0.05",
                          facecolor=C2, edgecolor='white', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x+w/2, 3.8, name, fontsize=11, fontweight='bold', ha='center', va='center', color='white')
    ax.text(x+w/2, 3.3, f'（{members}名）', fontsize=9, ha='center', va='center', color='#CCD9F0')
    for j, line in enumerate(detail.split('\n')):
        ax.text(x+w/2, 2.9 - j*0.35, line, fontsize=7, ha='center', va='center', color='#E8F0FA')

    # 连接线
    ax.plot([5, x+w/2], [4.8, 4.3], color=C3, linewidth=1.5)

plt.tight_layout()
fig.savefig(os.path.join(outdir, '3_组织架构.png'), dpi=200, bbox_inches='tight', transparent=False, facecolor='white')
plt.close()

# ==================== 图4: 预算构成饼图 ====================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))

# 左图：改造费用构成
labels1 = ['基础设施改造', '配套设施完善', '环境整治提升', '便民服务优化', '管理费及预备费']
sizes1 = [42, 25, 15, 8, 10]
colors1 = [C1, C2, C3, '#7FB3E0', C5]
explode1 = (0.05, 0, 0, 0, 0)

wedges1, texts1, autotexts1 = ax1.pie(sizes1, explode=explode1, labels=labels1, colors=colors1,
                                       autopct='%1.1f%%', startangle=90, pctdistance=0.6)
for t in autotexts1:
    t.set_fontsize(10)
    t.set_fontweight('bold')
for t in texts1:
    t.set_fontsize(10)
ax1.set_title('改造费用构成', fontsize=14, fontweight='bold', color=C1, pad=15)

# 右图：评价费用预算
labels2 = ['人员费用', '差旅交通', '专家咨询', '资料印刷', '其他']
sizes2 = [45, 20, 18, 10, 7]
colors2 = [C1, C2, C3, '#7FB3E0', C5]

wedges2, texts2, autotexts2 = ax2.pie(sizes2, labels=labels2, colors=colors2,
                                       autopct='%1.1f%%', startangle=90, pctdistance=0.6)
for t in autotexts2:
    t.set_fontsize(10)
    t.set_fontweight('bold')
for t in texts2:
    t.set_fontsize(10)
ax2.set_title('绩效评价费用预算构成', fontsize=14, fontweight='bold', color=C1, pad=15)

plt.tight_layout()
fig.savefig(os.path.join(outdir, '4_预算构成.png'), dpi=200, bbox_inches='tight', transparent=False, facecolor='white')
plt.close()

# ==================== 图5: 问题风险雷达图 ====================
fig, ax = plt.subplots(1, 1, figsize=(8, 8), subplot_kw=dict(polar=True))

categories = ['立项决策', '资金管理', '工程进度', '工程质量', '安全管理',
              '采购合规', '竣工验收', '长效管护', '满意度', '档案管理']
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

values = [3, 4, 4, 5, 5, 4, 4, 5, 3, 3]
values += values[:1]

ax.plot(angles, values, 'o-', linewidth=2, color=C1, markersize=8)
ax.fill(angles, values, alpha=0.25, color=C2)

# 添加风险等级环
for r in [1, 2, 3, 4, 5]:
    ax.plot(np.linspace(0, 2*np.pi, 100), [r]*100, '--', color='gray', alpha=0.3, linewidth=0.5)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=11, fontweight='bold', color=C8)
ax.set_ylim(1, 5)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(['很低', '较低', '中等', '较高', '很高'], fontsize=9)
ax.set_title('老旧小区改造常见问题风险等级评估', fontsize=15, fontweight='bold', color=C1, pad=25)

plt.tight_layout()
fig.savefig(os.path.join(outdir, '5_风险雷达图.png'), dpi=200, bbox_inches='tight', transparent=False, facecolor='white')
plt.close()

# ==================== 图6: 指标评分分布 ====================
fig, ax = plt.subplots(figsize=(10, 5))

categories_bar = ['项目决策', '项目管理', '过程管理', '项目产出', '项目效益']
full_scores = [20, 25, 25, 20, 10]
# 模拟得分（后续实际填）
actual_scores = [16, 20, 18, 16, 7]

x = np.arange(len(categories_bar))
width = 0.3

bars1 = ax.bar(x - width/2, full_scores, width, label='满分值', color=C4, edgecolor=C2, linewidth=1.5)
bars2 = ax.bar(x + width/2, actual_scores, width, label='预计得分', color=C1, alpha=0.85)

# 数据标签
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
            f'{bar.get_height():.0f}', ha='center', fontsize=10, color=C2, fontweight='bold')
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
            f'{bar.get_height():.0f}', ha='center', fontsize=10, color=C1, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(categories_bar, fontsize=11)
ax.set_ylabel('分值', fontsize=11)
ax.set_title('绩效评价指标评分预估对比', fontsize=14, fontweight='bold', color=C1)
ax.legend(fontsize=10)
ax.set_ylim(0, 30)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
fig.savefig(os.path.join(outdir, '6_指标评分.png'), dpi=200, bbox_inches='tight', transparent=False, facecolor='white')
plt.close()

print(f'6个图表已生成到: {outdir}')
for f in os.listdir(outdir):
    print(f'  {f}')
