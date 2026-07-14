# -*- coding: utf-8 -*-
"""生成补充配图（第二批）"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

output_dir = r'D:\openclaw-workspace\output\charts'
os.makedirs(output_dir, exist_ok=True)
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 图6：组织架构图
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))
ax.set_xlim(0, 12)
ax.set_ylim(0, 7)
ax.axis('off')

# 总负责人
rect = FancyBboxPatch((4, 5.5), 4, 1.0, boxstyle="round,pad=0.1",
                       facecolor='#1C355E', edgecolor='white', linewidth=2)
ax.add_patch(rect)
ax.text(6, 6.0, '项目总负责人（1人）', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
ax.text(6, 5.65, '注册会计师 | 10年以上经验 | 统筹决策', ha='center', va='center', fontsize=9, color='#CCCCCC')

# 连线
for x in [4, 8]:
    ax.plot([x+1, x+1], [5.5, 4.7], 'k-', lw=2, color='#1C355E')

# 管理层
mgrs = [('审核组长\n（1人）', '注册会计师 | 5年以上绩效评价\n组织实施 | 质量把控 | 报告撰写'),
        ('辅导组长\n（1人）', '中级以上职称 | 3年以上绩效管理\n培训辅导 | 答疑组织 | 沟通协调')]
for i, (name, desc) in enumerate(mgrs):
    x = 2 + i * 5
    rect = FancyBboxPatch((x, 3.5), 3.8, 1.2, boxstyle="round,pad=0.1",
                           facecolor='#3A7BD5', edgecolor='white', linewidth=2)
    ax.add_patch(rect)
    ax.text(x + 1.9, 4.3, name, ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(x + 1.9, 3.7, desc, ha='center', va='center', fontsize=8, color='#E0E0E0')
    # 下属连线
    for sx in [x + 0.95, x + 2.85]:
        ax.plot([sx, sx], [3.5, 2.7], '-', lw=1.5, color='#3A7BD5')

# 执行层
execs = [('审计助理\n（财务方向）', '2人\n管理效率审核\n预算数据比对'),
         ('审计助理\n（绩效方向）', '2人\n履职效能审核\n指标逻辑分析'),
         ('交通工程\n顾问', '1人(兼职)\n业务指标审核\n行业标准提供'),
         ('行政助理', '1人\n资料管理\n后勤保障')]
for i, (name, desc) in enumerate(execs):
    x = 0.5 + i * 2.9
    rect = FancyBboxPatch((x, 1.2), 2.5, 1.5, boxstyle="round,pad=0.08",
                           facecolor='#8DB9E8', edgecolor='white', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + 1.25, 2.35, name, ha='center', va='center', fontsize=10, fontweight='bold', color='#1C355E')
    ax.text(x + 1.25, 1.5, desc, ha='center', va='center', fontsize=8, color='#333333')

ax.text(6, 6.8, '图6：项目团队组织架构', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'org_chart.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图6已生成：org_chart.png')

# ============================================================
# 图7：四维审核方法体系图
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis('off')

# 中心
center = plt.Circle((6, 3), 1.2, facecolor='#1C355E', edgecolor='white', linewidth=3)
ax.add_patch(center)
ax.text(6, 3, '四维审核\n方法体系', ha='center', va='center', fontsize=13, fontweight='bold', color='white')

# 四维
dims = [
    ('查阅法', '基础方法', 9, 4.5, '#E74C3C',
     '政策文件\n三定方案\n预算批复\n决算报告'),
    ('比较分析法', '核心方法', 9, 1.5, '#3498DB',
     '横向比较\n同级别区县\n纵向比较\n近3年历史'),
    ('逻辑分析法', '诊断方法', 3, 1.5, '#2ECC71',
     '归属关系\n层级逻辑\n交叉重复\n逻辑矛盾'),
    ('数据验证法', '实证方法', 3, 4.5, '#F39C12',
     '数据回溯\n实际值vs参考值\n合理性判断\n趋势分析'),
]

for name, sub, cx, cy, color, desc in dims:
    rect = FancyBboxPatch((cx-1.2, cy-0.8), 2.4, 1.6, boxstyle="round,pad=0.1",
                           facecolor=color, edgecolor='white', linewidth=2, alpha=0.9)
    ax.add_patch(rect)
    ax.text(cx, cy+0.5, name, ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(cx, cy+0.05, sub, ha='center', va='center', fontsize=9, color='#EEEEEE')
    ax.text(cx, cy-0.4, desc, ha='center', va='center', fontsize=7.5, color='white', alpha=0.9)
    # 连线到中心
    ax.annotate('', xy=(cx-1.3 if cx>6 else cx+1.3, cy), xytext=(6+1.1 if cx>6 else 6-1.1, 3),
                arrowprops=dict(arrowstyle='->', color=color, lw=2))

ax.text(6, 5.8, '图7：四维审核方法体系', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'audit_methods.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图7已生成：audit_methods.png')

# ============================================================
# 图8：SMART原则指标设计图
# ============================================================
fig, ax = plt.subplots(figsize=(11, 7))
ax.set_xlim(0, 11)
ax.set_ylim(0, 7)
ax.axis('off')

smart_items = [
    ('S', 'Specific\n具体的', '#E74C3C', '指标指向明确\n不产生歧义\n具体到某一项工作'),
    ('M', 'Measurable\n可衡量的', '#3498DB', '可量化或可分级\n有明确数据来源\n可采集可验证'),
    ('A', 'Achievable\n可实现的', '#2ECC71', '目标值切合实际\n基于历史数据\n具有可达性'),
    ('R', 'Relevant\n相关的', '#F39C12', '与部门职能相关\n与预算匹配\n体现工作重点'),
    ('T', 'Time-bound\n有时限的', '#9B59B6', '有明确时间节点\n有完成期限\n可考核时间进度'),
]

for i, (letter, name, color, desc) in enumerate(smart_items):
    cx = 1.5 + i * 2.0
    # 圆
    circle = plt.Circle((cx, 3.8), 0.7, facecolor=color, edgecolor='white', linewidth=2.5)
    ax.add_patch(circle)
    ax.text(cx, 3.8, letter, ha='center', va='center', fontsize=24, fontweight='bold', color='white')
    # 名称
    ax.text(cx, 2.6, name, ha='center', va='center', fontsize=10, fontweight='bold', color=color)
    # 描述
    ax.text(cx, 1.2, desc, ha='center', va='center', fontsize=8.5, color='#555555')
    # 连线
    if i < 4:
        ax.annotate('', xy=(cx+1.3, 3.8), xytext=(cx+1.3-0.45, 3.8),
                    arrowprops=dict(arrowstyle='->', color='#AAAAAA', lw=1.5))

ax.text(5.5, 6.5, '图8：SMART原则——绩效指标设计五要素', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
ax.text(5.5, 0.3, '所有绩效指标均需满足SMART五要素，定性指标也应有明确的等级评价标准', fontsize=10, color='#999999', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'smart_principles.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图8已生成：smart_principles.png')

# ============================================================
# 图9：政策法规依据层级图
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))
ax.set_xlim(0, 12)
ax.set_ylim(0, 7)
ax.axis('off')

levels = [
    {'name': '《预算法》及实施条例', 'y': 5.8, 'color': '#1C355E', 'w': 7},
    {'name': '中发〔2018〕34号  全面实施预算绩效管理', 'y': 4.6, 'color': '#2B579A', 'w': 8.5},
    {'name': '财预〔2020〕10号  项目支出绩效评价管理办法', 'y': 3.4, 'color': '#3A7BD5', 'w': 9},
    {'name': '财预〔2015〕88号  中央部门预算绩效目标管理办法', 'y': 2.2, 'color': '#5B9BD5', 'w': 9.5},
    {'name': '财预〔2021〕6号  委托第三方参与绩效管理指导意见', 'y': 1.0, 'color': '#8DB9E8', 'w': 10},
]

for lvl in levels:
    x = (12 - lvl['w']) / 2
    rect = FancyBboxPatch((x, lvl['y']), lvl['w'], 0.9, boxstyle="round,pad=0.1",
                           facecolor=lvl['color'], edgecolor='white', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(6, lvl['y']+0.45, lvl['name'], ha='center', va='center', fontsize=11 if lvl['w']>8 else 10.5,
            fontweight='bold', color='white')

ax.text(6, 6.6, '图9：政策法规依据层级', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
ax.text(6, 0.3, '法律→中央意见→财政管理办法→操作指引  自上而下逐级细化', fontsize=10, color='#999999', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'policy_hierarchy.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图9已生成：policy_hierarchy.png')

# ============================================================
# 图10：问题诊断→修改建议 映射流程图
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')

# 左侧：7个问题
problems = [
    ('问题一\n分类归属错位', '#E74C3C'),
    ('问题二\n指标不可量化', '#E74C3C'),
    ('问题三\n管理效率单薄', '#E74C3C'),
    ('问题四\n指标值未填写', '#E74C3C'),
    ('问题五\n数量质量混淆', '#E74C3C'),
    ('问题六\n缺满意度指标', '#E74C3C'),
    ('问题七\n成本维度空洞', '#E74C3C'),
]

# 右侧：修改建议
solutions = [
    ('重新归类\n修正名称', '#2ECC71'),
    ('替代/分解/\n等级评价量化', '#2ECC71'),
    ('增设12项\n管理效率指标', '#2ECC71'),
    ('补全历史数据\n设定合理值', '#2ECC71'),
    ('区分数量质量\n明确口径', '#2ECC71'),
    ('增设3项\n满意度指标', '#2ECC71'),
    ('重组成本指标\n增效率指标', '#2ECC71'),
]

for i, ((pn, pc), (sn, sc)) in enumerate(zip(problems, solutions)):
    y = 7.2 - i * 1.0
    # 问题框
    rect = FancyBboxPatch((0.5, y-0.35), 3.0, 0.7, boxstyle="round,pad=0.05",
                           facecolor=pc, edgecolor='white', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(2.0, y, pn, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')
    # 箭头
    ax.annotate('', xy=(5.5, y), xytext=(3.7, y),
                arrowprops=dict(arrowstyle='->', color='#1C355E', lw=2))
    # 修改框
    rect = FancyBboxPatch((5.7, y-0.35), 3.5, 0.7, boxstyle="round,pad=0.05",
                           facecolor=sc, edgecolor='white', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(7.45, y, sn, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')

    # 右侧箭头→汇总
    ax.annotate('', xy=(10.5, y), xytext=(9.4, y),
                arrowprops=dict(arrowstyle='->', color='#AAAAAA', lw=1.5))

# 汇总框
rect = FancyBboxPatch((10.7, 1.5), 2.8, 5.8, boxstyle="round,pad=0.15",
                       facecolor='#1C355E', edgecolor='white', linewidth=2.5)
ax.add_patch(rect)
ax.text(12.1, 5.5, '汇总输出', ha='center', va='center', fontsize=13, fontweight='bold', color='white')
ax.text(12.1, 3.5, '三张汇总表\n①分类调整\n②量化改造\n③指标补充', ha='center', va='center', fontsize=10, color='#CCCCCC')
ax.text(12.1, 2.2, '→定稿绩效目标\n→审核工作报告', ha='center', va='center', fontsize=9, color='#8DB9E8')

ax.text(7, 7.8, '图10：问题诊断→修改建议 映射关系图', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'problem_solution_map.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图10已生成：problem_solution_map.png')

# ============================================================
# 图11：沟通协调机制图
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6))
ax.set_xlim(0, 11)
ax.set_ylim(0, 6)
ax.axis('off')

# 三角沟通
# 审计团队
rect = FancyBboxPatch((0.5, 1.5), 2.8, 2.5, boxstyle="round,pad=0.1",
                       facecolor='#1C355E', edgecolor='white', linewidth=2)
ax.add_patch(rect)
ax.text(1.9, 3.5, '四川融策\n会计师事务所', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax.text(1.9, 2.2, '审核+辅导\n双轨并行', ha='center', va='center', fontsize=9, color='#CCCCCC')

# 交通局
rect = FancyBboxPatch((4.1, 1.5), 2.8, 2.5, boxstyle="round,pad=0.1",
                       facecolor='#3A7BD5', edgecolor='white', linewidth=2)
ax.add_patch(rect)
ax.text(5.5, 3.5, '区交通运输局', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax.text(5.5, 2.2, '绩效目标编制\n反馈修改', ha='center', va='center', fontsize=9, color='#CCCCCC')

# 财政局
rect = FancyBboxPatch((7.7, 1.5), 2.8, 2.5, boxstyle="round,pad=0.1",
                       facecolor='#5B9BD5', edgecolor='white', linewidth=2)
ax.add_patch(rect)
ax.text(9.1, 3.5, '区财政局', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax.text(9.1, 2.2, '政策指导\n争议裁决', ha='center', va='center', fontsize=9, color='#CCCCCC')

# 连线标签
ax.annotate('辅导&审核', xy=(4.0, 3.5), xytext=(3.0, 3.5),
            arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=2))
ax.text(3.5, 3.8, '辅导&审核', ha='center', fontsize=9, color='#E74C3C', fontweight='bold')

ax.annotate('请示&汇报', xy=(7.6, 3.0), xytext=(7.0, 3.0),
            arrowprops=dict(arrowstyle='<->', color='#F39C12', lw=2))
ax.text(7.3, 3.3, '请示&汇报', ha='center', fontsize=9, color='#F39C12', fontweight='bold')

ax.annotate('政策解读\n争议裁决', xy=(7.6, 2.2), xytext=(7.0, 2.2),
            arrowprops=dict(arrowstyle='<->', color='#2ECC71', lw=2))
ax.text(7.3, 1.9, '政策解读', ha='center', fontsize=9, color='#2ECC71', fontweight='bold')

# 关键节点
ax.text(5.5, 1.0, '关键沟通节点：项目启动 → 审核发现沟通 → 修改稿确认 → 终稿交付',
        ha='center', fontsize=10, color='#666666', style='italic')

ax.text(5.5, 5.5, '图11：三方沟通协调机制', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'communication.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图11已生成：communication.png')

# ============================================================
# 图12：绩效目标"管理效率-履职效能"二维框架图
# ============================================================
fig, ax = plt.subplots(figsize=(13, 7))
ax.set_xlim(0, 13)
ax.set_ylim(0, 7)
ax.axis('off')

# 管理效率维度
rect = FancyBboxPatch((0.5, 3.5), 5.5, 3.0, boxstyle="round,pad=0.15",
                       facecolor='#E8EDF5', edgecolor='#1C355E', linewidth=2)
ax.add_patch(rect)
ax.text(3.25, 6.0, '管理效率维度', ha='center', fontsize=14, fontweight='bold', color='#1C355E')

# 管理效率子项
me_items = [
    ('预算管理', '预算偏离度 | 执行进度\n结余率 | 三公经费控制'),
    ('财务管理', '内控执行 | 资产规范\n采购合规 | 结转消化'),
    ('人员管理', '在编率 | 编外控制\n人均服务效能'),
    ('资产管理', '公路优良路率\n桥梁检测覆盖率'),
]
for i, (title, detail) in enumerate(me_items):
    x = 0.8 + i * 1.35
    rect = FancyBboxPatch((x, 4.8), 1.2, 1.3, boxstyle="round,pad=0.05",
                           facecolor='white', edgecolor='#3A7BD5', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x+0.6, 5.75, title, ha='center', fontsize=9, fontweight='bold', color='#1C355E')
    ax.text(x+0.6, 4.9, detail, ha='center', fontsize=6.5, color='#666666')

# 履职效能维度
rect = FancyBboxPatch((6.5, 3.5), 6.0, 3.0, boxstyle="round,pad=0.15",
                       facecolor='#FFF3E0', edgecolor='#E74C3C', linewidth=2)
ax.add_patch(rect)
ax.text(9.5, 6.0, '履职效能维度', ha='center', fontsize=14, fontweight='bold', color='#E74C3C')

pe_items = [
    ('产出指标', '数量 | 质量\n时效 | 成本'),
    ('效益指标', '经济 | 社会\n生态 | 可持续'),
    ('满意度指标', '居民 | 道路使用者\n实施单位'),
]
for i, (title, detail) in enumerate(pe_items):
    x = 6.8 + i * 2.0
    rect = FancyBboxPatch((x, 4.8), 1.7, 1.4, boxstyle="round,pad=0.05",
                           facecolor='white', edgecolor='#E74C3C', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x+0.85, 5.8, title, ha='center', fontsize=10, fontweight='bold', color='#E74C3C')
    ax.text(x+0.85, 4.9, detail, ha='center', fontsize=7.5, color='#666666')

# 底部说明
ax.text(6.25, 3.0, '建议权重：管理效率 30%-40%  |  履职效能 60%-70%',
        ha='center', fontsize=11, color='#1C355E', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5F5F5', edgecolor='#CCCCCC'))

ax.text(0.5, 1.5, '绩效目标的"两翼"：', fontsize=12, fontweight='bold', color='#1C355E')
body_texts = [
    '• 管理效率 = "花得规范" → 回答：部门资源配置是否高效、管理是否规范？',
    '• 履职效能 = "花得值" → 回答：财政资金投入产生了多少有效产出和实际效益？',
    '• 二者共同构成"全方位、全过程、全覆盖"的部门整体绩效画像'
]
for i, t in enumerate(body_texts):
    ax.text(0.8, 1.0 - i*0.5, t, fontsize=9.5, color='#555555')

ax.text(6.25, 6.8, '图12：部门整体绩效目标"管理效率-履职效能"二维框架', fontsize=14, fontweight='bold', color='#1C355E', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'framework_2d.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图12已生成：framework_2d.png')

# ============================================================
# 图13：指标修改前后对比（Before/After）
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

# Before
categories = ['管理\n效率', '产出\n时效', '产出\n数量', '产出\n质量', '效益\n指标', '满意\n度', '成本\n指标']
before_values = [4, 3, 3, 2, 8, 0, 0]
colors_before = ['#E74C3C']*7
bars1 = ax1.barh(range(len(categories)), before_values, color=colors_before, edgecolor='white', height=0.6)
for i, v in enumerate(before_values):
    if v > 0:
        ax1.text(v+0.2, i, str(v), va='center', fontsize=12, fontweight='bold', color='#E74C3C')
    else:
        ax1.text(0.5, i, '缺失!', va='center', fontsize=10, fontweight='bold', color='#E74C3C', style='italic')
ax1.set_yticks(range(len(categories)))
ax1.set_yticklabels(categories, fontsize=11)
ax1.set_title('修改前：22项指标', fontsize=14, fontweight='bold', color='#E74C3C')
ax1.set_xlim(0, 12)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.invert_yaxis()

# After
after_values = [12, 3, 5, 3, 8, 3, 2]
colors_after = ['#2ECC71']*7
bars2 = ax2.barh(range(len(categories)), after_values, color=colors_after, edgecolor='white', height=0.6)
for i, (b, a) in enumerate(zip(before_values, after_values)):
    ax2.text(a+0.2, i, str(a), va='center', fontsize=12, fontweight='bold', color='#2ECC71')
    if a > b:
        ax2.text(a/2, i-0.3, f'+{a-b}', va='center', fontsize=9, fontweight='bold', color='white')
ax2.set_yticks(range(len(categories)))
ax2.set_yticklabels(categories, fontsize=11)
ax2.set_title('修改后：36项指标', fontsize=14, fontweight='bold', color='#2ECC71')
ax2.set_xlim(0, 14)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.invert_yaxis()

fig.suptitle('图13：指标修改前后对比（Before → After）', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'before_after.png'), dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print('图13已生成：before_after.png')

print('\n全部补充图表生成完毕！共8张（图6-图13）')
