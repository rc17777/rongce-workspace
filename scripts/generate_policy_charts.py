# -*- coding: utf-8 -*-
"""
融策公司37项制度体系 - 5张流程图生成脚本
使用 matplotlib + Pillow 绘制
"""
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties
import numpy as np

# 强制UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

# ===== 品牌配色 =====
DEEP_BLUE = '#0A1F3F'
TEAL = '#1A5C6E'
COPPER_GOLD = '#C5955C'
WARM_GRAY = '#F5F2EC'
WHITE = '#FFFFFF'

# ===== 字体设置 =====
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 字体属性
FONT_TITLE = FontProperties(family='Microsoft YaHei', weight='bold', size=28)
FONT_SUBTITLE = FontProperties(family='Microsoft YaHei', weight='bold', size=18)
FONT_CATEGORY = FontProperties(family='Microsoft YaHei', weight='bold', size=14)
FONT_ITEM = FontProperties(family='SimSun', size=11)
FONT_SMALL = FontProperties(family='SimSun', size=9)
FONT_FOOTER = FontProperties(family='Microsoft YaHei', size=10)

# 输出路径
OUTPUT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\output\新制度体系\charts'

# A4横向 300dpi
FIG_WIDTH = 3508 / 300  # inches
FIG_HEIGHT = 2480 / 300  # inches
DPI = 300


def add_footer(ax):
    """添加底部公司标注"""
    ax.text(0.5, 0.02, 
            '四川融策会计师事务所有限公司 | 四川融策工程咨询有限公司',
            transform=ax.transAxes,
            fontproperties=FONT_FOOTER,
            ha='center', va='bottom',
            color=TEAL, alpha=0.8)


def draw_rounded_box(ax, x, y, w, h, text, fontprop, 
                     facecolor=WHITE, edgecolor=TEAL, 
                     linewidth=1.5, textcolor=DEEP_BLUE, 
                     boxstyle='round,pad=0.1', alpha=1.0):
    """绘制圆角矩形并添加文字"""
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=boxstyle,
                         facecolor=facecolor,
                         edgecolor=edgecolor,
                         linewidth=linewidth,
                         alpha=alpha)
    ax.add_patch(box)
    ax.text(x, y, text, fontproperties=fontprop,
            ha='center', va='center', color=textcolor)
    return box


def draw_arrow(ax, x1, y1, x2, y2, color=COPPER_GOLD, linewidth=2, style='->'):
    """绘制箭头"""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style,
                            color=color,
                            linewidth=linewidth,
                            mutation_scale=15)
    ax.add_patch(arrow)


# ===== 第1张：制度体系总览图 =====
def generate_architecture_chart():
    """生成制度体系总览图"""
    print("正在生成第1张：制度体系总览图...")
    
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    fig.patch.set_facecolor(WARM_GRAY)
    ax.set_facecolor(WARM_GRAY)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis('off')
    
    # 顶部标题
    ax.text(50, 66, '四川融策公司制度体系', 
            fontproperties=FONT_TITLE,
            ha='center', va='center', color=DEEP_BLUE)
    
    # 中心节点
    center_y = 58
    draw_rounded_box(ax, 50, center_y, 18, 4, '制度体系\n(37项)', 
                     FONT_CATEGORY, facecolor=TEAL, edgecolor=DEEP_BLUE,
                     textcolor=WHITE, linewidth=2.5)
    
    # 7大类数据
    categories = [
        ('治理', 4, ['#09股东会议事规则', '#05制度发布与版本管理', '#26公司章程(事务所)', '#27公司章程(工程公司)']),
        ('人力', 7, ['#10招聘与入职', '#01薪酬管理', '#02绩效考核', '#12职级晋升', '#11培训与发展', '#36高管考核', '#03员工手册']),
        ('财务', 6, ['#06财务报销', '#14预算管理', '#15资金管理', '#16固定资产', '#13收入确认与回款', '#37可分配利润核算']),
        ('业务', 7, ['#20投标管理', '#17业务承接与合同', '#04项目管理', '#19业务分包', '#18客户关系', '#31业务拓展与创新', '#35跨部门协同']),
        ('质控', 4, ['#21三级复核', '#07审计质控', '#08造价咨询质控', '#22执业责任追究']),
        ('行政', 5, ['#28办公场所', '#29采购管理', '#25档案管理', '#24印章与证照', '#23信息安全与保密']),
        ('专项', 4, ['#32风险管理', '#30数智化建设', '#33党建工作', '#34项目独立核算与分润']),
    ]
    
    n_cats = len(categories)
    cat_width = 90 / n_cats
    start_x = 5
    
    for i, (cat_name, count, items) in enumerate(categories):
        cx = start_x + i * cat_width + cat_width / 2
        
        # 从中心连线到分类
        draw_arrow(ax, 50, center_y - 2, cx, 48, color=COPPER_GOLD, linewidth=2)
        
        # 分类标题框
        draw_rounded_box(ax, cx, 46, 10, 3.5, f'{cat_name}\n({count}项)', 
                         FONT_CATEGORY, facecolor=DEEP_BLUE, edgecolor=TEAL,
                         textcolor=WHITE, linewidth=2)
        
        # 列出具体制度
        item_y_start = 40
        item_spacing = 4.5
        for j, item in enumerate(items):
            iy = item_y_start - j * item_spacing
            draw_rounded_box(ax, cx, iy, 11, 3, item, 
                             FONT_SMALL, facecolor=WHITE, edgecolor=TEAL,
                             textcolor=DEEP_BLUE, linewidth=1)
            if j < len(items) - 1:
                # 小连线
                ax.plot([cx, cx], [iy - 1.5, iy - item_spacing + 1.5], 
                        color=COPPER_GOLD, linewidth=1, alpha=0.6)
    
    add_footer(ax)
    
    # 保存
    out_path = os.path.join(OUTPUT_DIR, '00-architecture.png')
    plt.tight_layout(pad=0.5)
    plt.savefig(out_path, dpi=DPI, facecolor=WARM_GRAY, bbox_inches='tight')
    plt.close()
    print(f"✓ 第1张已保存: {out_path}")
    return out_path


# ===== 第2张：人力资源管理流程图 =====
def generate_hr_flow_chart():
    """生成人力资源管理流程图"""
    print("正在生成第2张：人力资源管理流程图...")
    
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    fig.patch.set_facecolor(WARM_GRAY)
    ax.set_facecolor(WARM_GRAY)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis('off')
    
    # 标题
    ax.text(50, 65, '人力资源管理全流程', 
            fontproperties=FONT_TITLE,
            ha='center', va='center', color=DEEP_BLUE)
    ax.text(50, 61, 'HR全生命周期管理', 
            fontproperties=FONT_SUBTITLE,
            ha='center', va='center', color=TEAL)
    
    # HR流程节点
    hr_nodes = [
        ('招聘入职', '#10', '人才引进\n岗位匹配'),
        ('薪酬定级', '#01', '薪酬体系\n等级划分'),
        ('绩效考核', '#02', '目标设定\n绩效评估'),
        ('职级晋升', '#12', '晋升通道\n能力评定'),
        ('培训发展', '#11', '技能培训\n职业规划'),
        ('高管考核', '#36', '经营目标\n责任考核'),
        ('离职管理', '#03', '离职交接\n知识传承'),
    ]
    
    n = len(hr_nodes)
    x_positions = np.linspace(12, 88, n)
    y_main = 42
    
    for i, (name, num, desc) in enumerate(hr_nodes):
        x = x_positions[i]
        
        # 主节点
        draw_rounded_box(ax, x, y_main, 11, 5, name, 
                         FONT_CATEGORY, facecolor=TEAL, edgecolor=DEEP_BLUE,
                         textcolor=WHITE, linewidth=2)
        
        # 描述卡片
        draw_rounded_box(ax, x, y_main - 8, 10, 4, desc, 
                         FONT_SMALL, facecolor=WHITE, edgecolor=COPPER_GOLD,
                         textcolor=DEEP_BLUE, linewidth=1)
        
        # 制度编号标签
        ax.text(x, y_main + 4, num, 
                fontproperties=FONT_SMALL, ha='center', va='center',
                color=COPPER_GOLD, weight='bold')
        
        # 箭头连接
        if i < n - 1:
            draw_arrow(ax, x + 5.5, y_main, x_positions[i+1] - 5.5, y_main,
                      color=COPPER_GOLD, linewidth=2.5)
    
    # 底部制度清单卡片
    card_y = 15
    card_items = [
        '#10 招聘与入职管理制度',
        '#01 薪酬管理制度',
        '#02 绩效考核管理制度',
        '#12 职级晋升管理制度',
        '#11 培训与发展管理制度',
        '#36 高管经营目标责任与绩效考核办法',
        '#03 员工手册',
    ]
    
    # 大背景卡片
    card_box = FancyBboxPatch((8, card_y - 5), 84, 12,
                              boxstyle='round,pad=0.3',
                              facecolor=WHITE, edgecolor=TEAL,
                              linewidth=1.5, alpha=0.9)
    ax.add_patch(card_box)
    
    ax.text(50, card_y + 5, '对应制度清单', 
            fontproperties=FONT_CATEGORY, ha='center', va='center',
            color=DEEP_BLUE)
    
    # 分两列显示
    col1_x = 25
    col2_x = 65
    for i, item in enumerate(card_items):
        if i < 4:
            ax.text(col1_x, card_y + 1 - i * 2.2, item,
                    fontproperties=FONT_ITEM, ha='left', va='center',
                    color=TEAL)
        else:
            ax.text(col2_x, card_y + 1 - (i - 4) * 2.2, item,
                    fontproperties=FONT_ITEM, ha='left', va='center',
                    color=TEAL)
    
    add_footer(ax)
    
    out_path = os.path.join(OUTPUT_DIR, '01-hr-flow.png')
    plt.tight_layout(pad=0.5)
    plt.savefig(out_path, dpi=DPI, facecolor=WARM_GRAY, bbox_inches='tight')
    plt.close()
    print(f"✓ 第2张已保存: {out_path}")
    return out_path


# ===== 第3张：财务管理流程图 =====
def generate_finance_flow_chart():
    """生成财务管理流程图（环状）"""
    print("正在生成第3张：财务管理流程图...")
    
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    fig.patch.set_facecolor(WARM_GRAY)
    ax.set_facecolor(WARM_GRAY)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis('off')
    
    # 标题
    ax.text(50, 65, '财务管理闭环流程', 
            fontproperties=FONT_TITLE,
            ha='center', va='center', color=DEEP_BLUE)
    ax.text(50, 61, '从费用报销到利润分配的完整循环', 
            fontproperties=FONT_SUBTITLE,
            ha='center', va='center', color=TEAL)
    
    # 财务流程节点（环状布局）
    fin_nodes = [
        ('费用报销', '#06', '日常费用\n报销审批'),
        ('预算编制', '#14', '年度预算\n编制执行'),
        ('资金管理', '#15', '资金调度\n收支管理'),
        ('固定资产', '#16', '资产采购\n折旧管理'),
        ('收入确认\n与回款', '#13', '项目收入\n回款跟踪'),
        ('利润核算', '#37', '可分配利润\n核算分配'),
    ]
    
    n = len(fin_nodes)
    center_x, center_y = 50, 35
    radius = 18
    
    # 计算节点位置（环形）
    angles = np.linspace(90, 90 - 360, n, endpoint=False)
    positions = []
    
    for i, (name, num, desc) in enumerate(fin_nodes):
        angle_rad = np.radians(angles[i])
        x = center_x + radius * np.cos(angle_rad)
        y = center_y + radius * np.sin(angle_rad) * 0.7  # 椭圆
        positions.append((x, y))
        
        # 主节点
        draw_rounded_box(ax, x, y, 12, 5, name, 
                         FONT_CATEGORY, facecolor=TEAL, edgecolor=DEEP_BLUE,
                         textcolor=WHITE, linewidth=2)
        
        # 编号
        ax.text(x, y + 3.5, num, 
                fontproperties=FONT_SMALL, ha='center', va='center',
                color=COPPER_GOLD, weight='bold')
        
        # 描述
        draw_rounded_box(ax, x, y - 5, 10, 3, desc, 
                         FONT_SMALL, facecolor=WHITE, edgecolor=COPPER_GOLD,
                         textcolor=DEEP_BLUE, linewidth=1)
    
    # 绘制环形箭头
    for i in range(n):
        x1, y1 = positions[i]
        x2, y2 = positions[(i + 1) % n]
        
        # 计算箭头起点和终点（从边缘出发）
        dx = x2 - x1
        dy = y2 - y1
        dist = np.sqrt(dx**2 + dy**2)
        
        # 缩短箭头避免重叠
        offset = 6.5
        sx = x1 + dx / dist * offset
        sy = y1 + dy / dist * offset
        ex = x2 - dx / dist * offset
        ey = y2 - dy / dist * offset
        
        draw_arrow(ax, sx, sy, ex, ey, color=COPPER_GOLD, linewidth=2.5)
    
    # 中心强调框
    center_box = FancyBboxPatch((center_x - 8, center_y - 3), 16, 6,
                                boxstyle='round,pad=0.2',
                                facecolor=DEEP_BLUE, edgecolor=COPPER_GOLD,
                                linewidth=2.5, alpha=0.95)
    ax.add_patch(center_box)
    ax.text(center_x, center_y + 0.5, '财务闭环', 
            fontproperties=FONT_CATEGORY, ha='center', va='center',
            color=WHITE)
    ax.text(center_x, center_y - 1.5, '回款→利润→分润', 
            fontproperties=FONT_SMALL, ha='center', va='center',
            color=COPPER_GOLD)
    
    # 底部制度清单
    card_y = 8
    card_items = [
        '#06 财务报销管理制度',
        '#14 预算管理制度',
        '#15 资金管理制度',
        '#16 固定资产管理制度',
        '#13 项目收入确认与回款管理制度',
        '#37 可分配利润核算细则',
    ]
    
    card_box = FancyBboxPatch((10, card_y - 3), 80, 8,
                              boxstyle='round,pad=0.2',
                              facecolor=WHITE, edgecolor=TEAL,
                              linewidth=1.5, alpha=0.9)
    ax.add_patch(card_box)
    
    ax.text(50, card_y + 3.5, '对应制度', 
            fontproperties=FONT_CATEGORY, ha='center', va='center',
            color=DEEP_BLUE)
    
    for i, item in enumerate(card_items):
        col = i % 3
        row = i // 3
        ax.text(20 + col * 25, card_y + 0.5 - row * 2, item,
                fontproperties=FONT_SMALL, ha='left', va='center',
                color=TEAL)
    
    add_footer(ax)
    
    out_path = os.path.join(OUTPUT_DIR, '02-fin-flow.png')
    plt.tight_layout(pad=0.5)
    plt.savefig(out_path, dpi=DPI, facecolor=WARM_GRAY, bbox_inches='tight')
    plt.close()
    print(f"✓ 第3张已保存: {out_path}")
    return out_path


# ===== 第4张：业务运营与质控流程图 =====
def generate_biz_qc_flow_chart():
    """生成业务运营与质控流程图"""
    print("正在生成第4张：业务运营与质控流程图...")
    
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    fig.patch.set_facecolor(WARM_GRAY)
    ax.set_facecolor(WARM_GRAY)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis('off')
    
    # 标题
    ax.text(50, 65, '业务运营与质控全流程', 
            fontproperties=FONT_TITLE,
            ha='center', va='center', color=DEEP_BLUE)
    ax.text(50, 61, '从投标到分润的完整业务链', 
            fontproperties=FONT_SUBTITLE,
            ha='center', va='center', color=TEAL)
    
    # 业务流程节点
    biz_nodes = [
        ('投标管理', '#20', '项目投标\n标书编制'),
        ('业务承接', '#17', '合同签订\n风险评估'),
        ('项目管理', '#04', '项目立项\n资源配置'),
        ('执行交付', '#19', '项目执行\n分包管理'),
        ('三级复核', '#21', '项目组复核\n部门复核\n公司复核'),
        ('质控检查', '#07/#08', '审计质控\n造价质控'),
        ('客户满意度', '#18', '客户反馈\n关系维护'),
        ('分润核算', '#34', '项目核算\n利润分配'),
        ('跨部门协同', '#35', '交叉营销\n协同奖励'),
    ]
    
    n = len(biz_nodes)
    
    # 分两行排列
    row1_nodes = biz_nodes[:5]
    row2_nodes = biz_nodes[5:]
    
    # 第一行（从左到右）
    row1_y = 45
    row1_x = np.linspace(10, 90, len(row1_nodes))
    
    for i, (name, num, desc) in enumerate(row1_nodes):
        x = row1_x[i]
        
        # 主节点
        draw_rounded_box(ax, x, row1_y, 11, 4.5, name, 
                         FONT_CATEGORY, facecolor=TEAL, edgecolor=DEEP_BLUE,
                         textcolor=WHITE, linewidth=2)
        
        # 编号
        ax.text(x, row1_y + 3.5, num, 
                fontproperties=FONT_SMALL, ha='center', va='center',
                color=COPPER_GOLD, weight='bold')
        
        # 描述
        draw_rounded_box(ax, x, row1_y - 5, 10, 3.5, desc, 
                         FONT_SMALL, facecolor=WHITE, edgecolor=COPPER_GOLD,
                         textcolor=DEEP_BLUE, linewidth=1)
        
        # 箭头
        if i < len(row1_nodes) - 1:
            draw_arrow(ax, x + 5.5, row1_y, row1_x[i+1] - 5.5, row1_y,
                      color=COPPER_GOLD, linewidth=2.5)
    
    # 从第一行末尾到第二行（弯曲箭头）
    last_row1_x = row1_x[-1]
    row2_y = 24
    row2_x = np.linspace(90, 10, len(row2_nodes))
    
    # 转弯箭头
    ax.annotate('', xy=(row2_x[0], row2_y + 3), 
                xytext=(last_row1_x, row1_y - 8),
                arrowprops=dict(arrowstyle='->', color=COPPER_GOLD, 
                               linewidth=2.5, connectionstyle='arc3,rad=0.3'))
    
    # 第二行（从右到左）
    for i, (name, num, desc) in enumerate(row2_nodes):
        x = row2_x[i]
        
        # 主节点
        draw_rounded_box(ax, x, row2_y, 11, 4.5, name, 
                         FONT_CATEGORY, facecolor=DEEP_BLUE, edgecolor=TEAL,
                         textcolor=WHITE, linewidth=2)
        
        # 编号
        ax.text(x, row2_y + 3.5, num, 
                fontproperties=FONT_SMALL, ha='center', va='center',
                color=COPPER_GOLD, weight='bold')
        
        # 描述
        draw_rounded_box(ax, x, row2_y - 5, 10, 3.5, desc, 
                         FONT_SMALL, facecolor=WHITE, edgecolor=COPPER_GOLD,
                         textcolor=DEEP_BLUE, linewidth=1)
        
        # 箭头（从右到左）
        if i < len(row2_nodes) - 1:
            draw_arrow(ax, x - 5.5, row2_y, row2_x[i+1] + 5.5, row2_y,
                      color=COPPER_GOLD, linewidth=2.5)
    
    # 底部制度清单
    card_y = 11
    all_policies = [
        '#20 投标管理制度', '#17 业务承接与合同管理制度',
        '#04 项目管理规范', '#19 业务分包管理制度',
        '#21 三级复核实施细则', '#07 审计质量控制制度',
        '#08 造价咨询质量控制制度', '#18 客户关系管理制度',
        '#34 项目独立核算与分润制度', '#35 跨部门协同与交叉营销奖励办法',
        '#22 执业责任追究制度'
    ]
    
    card_box = FancyBboxPatch((5, card_y - 1), 90, 7,
                              boxstyle='round,pad=0.2',
                              facecolor=WHITE, edgecolor=TEAL,
                              linewidth=1.5, alpha=0.9)
    ax.add_patch(card_box)
    
    ax.text(50, card_y + 4.5, '对应制度（11项）', 
            fontproperties=FONT_CATEGORY, ha='center', va='center',
            color=DEEP_BLUE)
    
    for i, item in enumerate(all_policies):
        col = i % 4
        row = i // 4
        ax.text(10 + col * 22, card_y + 1.8 - row * 2.2, item,
                fontproperties=FONT_SMALL, ha='left', va='center',
                color=TEAL)
    
    add_footer(ax)
    
    out_path = os.path.join(OUTPUT_DIR, '03-biz-qc-flow.png')
    plt.tight_layout(pad=0.5)
    plt.savefig(out_path, dpi=DPI, facecolor=WARM_GRAY, bbox_inches='tight')
    plt.close()
    print(f"✓ 第4张已保存: {out_path}")
    return out_path


# ===== 第5张：行政综合支撑流程图 =====
def generate_admin_flow_chart():
    """生成行政综合支撑流程图（中心辐射式）"""
    print("正在生成第5张：行政综合支撑流程图...")
    
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    fig.patch.set_facecolor(WARM_GRAY)
    ax.set_facecolor(WARM_GRAY)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis('off')
    
    # 标题
    ax.text(50, 66, '行政综合支撑体系', 
            fontproperties=FONT_TITLE,
            ha='center', va='center', color=DEEP_BLUE)
    ax.text(50, 62, '中心辐射式管理架构', 
            fontproperties=FONT_SUBTITLE,
            ha='center', va='center', color=TEAL)
    
    # 行政模块（中心辐射）
    admin_modules = [
        ('制度发布\n管理', '#05'),
        ('办公管理', '#28'),
        ('采购管理', '#29'),
        ('档案管理', '#25'),
        ('印章证照', '#24'),
        ('信息安全', '#23'),
        ('企业章程', '#26/#27'),
        ('数智化\n建设', '#30'),
        ('业务创新', '#31'),
        ('风险管理', '#32'),
        ('党建工作', '#33'),
    ]
    
    n = len(admin_modules)
    center_x, center_y = 50, 36
    radius_x = 28
    radius_y = 20
    
    # 中心节点
    center_box = FancyBboxPatch((center_x - 9, center_y - 4), 18, 8,
                                boxstyle='round,pad=0.3',
                                facecolor=DEEP_BLUE, edgecolor=COPPER_GOLD,
                                linewidth=3, alpha=0.95)
    ax.add_patch(center_box)
    ax.text(center_x, center_y + 1, '行政综合', 
            fontproperties=FONT_SUBTITLE, ha='center', va='center',
            color=WHITE)
    ax.text(center_x, center_y - 2, '支撑体系', 
            fontproperties=FONT_CATEGORY, ha='center', va='center',
            color=COPPER_GOLD)
    
    # 计算角度（均匀分布）
    angles = np.linspace(90, 90 - 360, n, endpoint=False)
    
    for i, (name, num) in enumerate(admin_modules):
        angle_rad = np.radians(angles[i])
        x = center_x + radius_x * np.cos(angle_rad)
        y = center_y + radius_y * np.sin(angle_rad)
        
        # 从中心到模块的连线
        draw_arrow(ax, center_x + 9 * np.cos(angle_rad), 
                   center_y + 4 * np.sin(angle_rad),
                   x - 5 * np.cos(angle_rad), 
                   y - 2.5 * np.sin(angle_rad),
                   color=COPPER_GOLD, linewidth=2)
        
        # 模块节点
        draw_rounded_box(ax, x, y, 11, 4.5, name, 
                         FONT_CATEGORY, facecolor=TEAL, edgecolor=DEEP_BLUE,
                         textcolor=WHITE, linewidth=2)
        
        # 编号标签
        ax.text(x, y + 3.5, num, 
                fontproperties=FONT_SMALL, ha='center', va='center',
                color=COPPER_GOLD, weight='bold')
    
    # 底部说明
    note_y = 8
    note_box = FancyBboxPatch((15, note_y - 2), 70, 5,
                              boxstyle='round,pad=0.2',
                              facecolor=WHITE, edgecolor=TEAL,
                              linewidth=1.5, alpha=0.9)
    ax.add_patch(note_box)
    
    ax.text(50, note_y + 1.5, '行政综合支撑体系覆盖制度管理、日常运营、安全保障、创新发展等全方位', 
            fontproperties=FONT_ITEM, ha='center', va='center',
            color=DEEP_BLUE)
    ax.text(50, note_y - 0.5, '共11项制度，为公司治理和业务运营提供坚实保障', 
            fontproperties=FONT_SMALL, ha='center', va='center',
            color=TEAL)
    
    add_footer(ax)
    
    out_path = os.path.join(OUTPUT_DIR, '04-admin-flow.png')
    plt.tight_layout(pad=0.5)
    plt.savefig(out_path, dpi=DPI, facecolor=WARM_GRAY, bbox_inches='tight')
    plt.close()
    print(f"✓ 第5张已保存: {out_path}")
    return out_path


# ===== 主函数 =====
def main():
    print("=" * 60)
    print("融策公司37项制度体系 - 流程图生成")
    print("=" * 60)
    
    try:
        generate_architecture_chart()
        generate_hr_flow_chart()
        generate_finance_flow_chart()
        generate_biz_qc_flow_chart()
        generate_admin_flow_chart()
        
        print("\n" + "=" * 60)
        print("✓ 全部5张流程图生成完成！")
        print(f"输出目录: {OUTPUT_DIR}")
        print("=" * 60)
        
        # 列出生成的文件
        for f in sorted(os.listdir(OUTPUT_DIR)):
            if f.endswith('.png'):
                fpath = os.path.join(OUTPUT_DIR, f)
                size_mb = os.path.getsize(fpath) / (1024 * 1024)
                print(f"  {f} ({size_mb:.2f} MB)")
        
    except Exception as e:
        print(f"\n✗ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
