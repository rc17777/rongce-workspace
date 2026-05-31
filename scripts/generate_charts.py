#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Pillow 精确绘制图表，解决 matplotlib 中文排版错位问题
"""
import os
from PIL import Image, ImageDraw, ImageFont

SVG_DIR = r"D:\openclaw-workspace\svgs"
os.makedirs(SVG_DIR, exist_ok=True)

# 字体路径
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttf"   # 微软雅黑粗体
FONT_REGULAR = "C:/Windows/Fonts/msyh.ttc"   # 微软雅黑常规
FONT_SMALL = "C:/Windows/Fonts/msyh.ttc"

# 试试黑体作为备选
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = "C:/Windows/Fonts/simhei.ttf"
if not os.path.exists(FONT_REGULAR):
    FONT_REGULAR = "C:/Windows/Fonts/simsun.ttc"


def get_font(size, bold=False):
    try:
        path = FONT_BOLD if bold else FONT_REGULAR
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


class Canvas:
    def __init__(self, width, height, bg='#f8f9fa'):
        self.img = Image.new('RGB', (width, height), bg)
        self.draw = ImageDraw.Draw(self.img)
        self.w = width
        self.h = height

    def rounded_rect(self, x1, y1, x2, y2, radius, fill, outline=None, width=1):
        """绘制圆角矩形"""
        from PIL import ImageDraw as ID
        d = self.draw
        # 绘制主体矩形
        d.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

    def text_center(self, cx, cy, text, font_size=12, color='#2c3e50', bold=False):
        """在中心点绘制多行文字"""
        font = get_font(font_size, bold)
        lines = text.split('\n')
        line_heights = []
        for line in lines:
            bbox = self.draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])
        total_h = sum(line_heights)
        spacing = 2
        total_h += spacing * (len(lines) - 1)
        y_start = cy - total_h // 2
        for i, line in enumerate(lines):
            bbox = self.draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = cx - tw // 2
            y = y_start + sum(line_heights[:i]) + spacing * i
            self.draw.text((x, y), line, fill=color, font=font)

    def text_left(self, x, y, text, font_size=10, color='#2c3e50'):
        font = get_font(font_size, False)
        self.draw.text((x, y), text, fill=color, font=font)

    def arrow_right(self, x1, y, x2):
        """水平箭头"""
        self.draw.line([(x1, y), (x2, y)], fill='#2c3e50', width=2)
        # 箭头尖
        self.draw.polygon([(x2, y), (x2-8, y-4), (x2-8, y+4)], fill='#2c3e50')

    def arrow_down(self, x, y1, y2):
        """垂直箭头"""
        self.draw.line([(x, y1), (x, y2)], fill='#2c3e50', width=2)
        self.draw.polygon([(x, y2), (x-4, y2-8), (x+4, y2-8)], fill='#2c3e50')

    def save(self, path):
        self.img.save(path, 'PNG')
        return path


# ============================================================
def generate_flowchart():
    """审核工作流程图 - Pillow 精确版"""
    cv = Canvas(1200, 1700)

    # 标题
    cv.rounded_rect(60, 30, 1140, 80, 10, '#1a5276')
    cv.text_center(600, 70, '阿坝县工程竣工财务决算审核工作流程图', font_size=22, color='white', bold=True)

    stage_y = 140
    box_w, box_h = 220, 48
    arrow_gap = 20

    # ====== 阶段一 ======
    cv.rounded_rect(60, stage_y, 1140, stage_y + 175, 8, None, outline='#1a5276', width=2)
    cv.text_left(80, stage_y + 10, '阶段一：接受委托与前期准备', font_size=16, color='#1a5276')
    section_top = stage_y + 40

    def draw_three_boxes(top, labels, box_w=220, box_h=48):
        total_w = 3 * box_w + 2 * arrow_gap
        start_x = (1200 - total_w) // 2
        cy = top + box_h // 2
        for i, label in enumerate(labels):
            x = start_x + i * (box_w + arrow_gap)
            cv.rounded_rect(x, top, x + box_w, top + box_h, 6, '#ecf0f1', outline='#7f8c8d', width=2)
            cv.text_center(x + box_w // 2, top + box_h // 2, label, font_size=13)
            if i < 2:
                ax1 = x + box_w + 4
                ax2 = start_x + (i + 1) * (box_w + arrow_gap) - 4
                cv.arrow_right(ax1, cy, ax2)

    draw_three_boxes(section_top, ['签订委托协议', '组建审核工作组', '收集项目资料'])

    cv.arrow_down(600, stage_y + 175, stage_y + 215)
    stage_y += 240

    # ====== 阶段二 ======
    cv.rounded_rect(60, stage_y, 1140, stage_y + 155, 8, None, outline='#1a5276', width=2)
    cv.text_left(80, stage_y + 10, '阶段二：资料初审与现场核查', font_size=16, color='#1a5276')
    section_top = stage_y + 40
    draw_three_boxes(section_top, ['资料完整性审查', '现场实地踏勘核查', '编制资料清单'])

    cv.arrow_down(600, stage_y + 155, stage_y + 195)
    stage_y += 220

    # ====== 阶段三：实质性审核 ======
    cv.rounded_rect(60, stage_y, 1140, stage_y + 300, 8, None, outline='#1a5276', width=2)
    cv.text_left(80, stage_y + 10, '阶段三：实质性审核', font_size=16, color='#1a5276')

    # 第一行
    r1_labels = ['工程价款审核\n结算/变更/索赔', '资金来源审核\n拨付/配套/自筹',
                 '资金使用审核\n合规性/真实性', '资产交付审核\n分类/计价/手续']
    r1_w, r1_h = 215, 65
    r1_gap = 18
    r1_total = 4 * r1_w + 3 * r1_gap
    r1_start_x = (1200 - r1_total) // 2
    r1_top = stage_y + 42
    r1_cy = r1_top + r1_h // 2
    for i, label in enumerate(r1_labels):
        x = r1_start_x + i * (r1_w + r1_gap)
        cv.rounded_rect(x, r1_top, x + r1_w, r1_top + r1_h, 6, '#d6eaf8', outline='#2980b9', width=2)
        cv.text_center(x + r1_w // 2, r1_cy, label, font_size=11, color='#1a5276')
        if i < 3:
            cv.arrow_right(x + r1_w + 4, r1_cy, r1_start_x + (i + 1) * (r1_w + r1_gap) - 4)

    # 第二行
    r2_labels = ['待摊投资审核\n管理费/监理费等', '其他投资审核\n设备/工器具等', '尾工工程审核\n预留/未完工程']
    r2_w = 240
    r2_gap = 30
    r2_total = 3 * r2_w + 2 * r2_gap
    r2_start_x = (1200 - r2_total) // 2
    r2_top = stage_y + 42 + r1_h + 20
    r2_cy = r2_top + r1_h // 2
    for i, label in enumerate(r2_labels):
        x = r2_start_x + i * (r2_w + r2_gap)
        cv.rounded_rect(x, r2_top, x + r2_w, r2_top + r1_h, 6, '#d6eaf8', outline='#2980b9', width=2)
        cv.text_center(x + r2_w // 2, r2_cy, label, font_size=11, color='#1a5276')
        if i < 2:
            cv.arrow_right(x + r2_w + 4, r2_cy, r2_start_x + (i + 1) * (r2_w + r2_gap) - 4)

    cv.arrow_down(600, stage_y + 300, stage_y + 340)
    stage_y += 365

    # ====== 阶段四 ======
    cv.rounded_rect(60, stage_y, 1140, stage_y + 145, 8, None, outline='#1a5276', width=2)
    cv.text_left(80, stage_y + 10, '阶段四：三级复核与报告出具', font_size=16, color='#1a5276')

    r4_top = stage_y + 45
    r4_w, r4_h = 280, 65
    r4_gap = 30
    r4_total = 3 * r4_w + 2 * r4_gap
    r4_start_x = (1200 - r4_total) // 2
    r4_cy = r4_top + r4_h // 2
    r4_colors = [('#fdebd0', '#e67e22', '#a04000'), ('#d5f5e3', '#27ae60', '#1e8449'), ('#d6eaf8', '#2980b9', '#1a5276')]
    r4_labels = ['一级复核\n项目负责人', '二级复核\n部门负责人', '三级复核(终审)\n主任会计师']
    for i, (label, (fill, outline, text_col)) in enumerate(zip(r4_labels, r4_colors)):
        x = r4_start_x + i * (r4_w + r4_gap)
        cv.rounded_rect(x, r4_top, x + r4_w, r4_top + r4_h, 6, fill, outline=outline, width=2)
        cv.text_center(x + r4_w // 2, r4_cy, label, font_size=12, color=text_col)
        if i < 2:
            cv.arrow_right(x + r4_w + 4, r4_cy, r4_start_x + (i + 1) * (r4_w + r4_gap) - 4)

    cv.arrow_down(600, stage_y + 145, stage_y + 185)
    stage_y += 210

    # ====== 阶段五 ======
    cv.rounded_rect(60, stage_y, 1140, stage_y + 155, 8, None, outline='#1a5276', width=2)
    cv.text_left(80, stage_y + 10, '阶段五：成果交付与后续服务', font_size=16, color='#1a5276')

    r5_top = stage_y + 45
    r5_w, r5_h = 260, 72
    r5_gap = 30
    r5_total = 3 * r5_w + 2 * r5_gap
    r5_start_x = (1200 - r5_total) // 2
    r5_cy = r5_top + r5_h // 2
    r5_labels = ['出具审核报告\n征求意见→正式出具', '归档与备案\n电子+纸质归档', '跟踪回访\n整改落实情况']
    for i, label in enumerate(r5_labels):
        x = r5_start_x + i * (r5_w + r5_gap)
        cv.rounded_rect(x, r5_top, x + r5_w, r5_top + r5_h, 6, '#e8f8f5', outline='#1abc9c', width=2)
        cv.text_center(x + r5_w // 2, r5_cy, label, font_size=12, color='#0e6655')
        if i < 2:
            cv.arrow_right(x + r5_w + 4, r5_cy, r5_start_x + (i + 1) * (r5_w + r5_gap) - 4)

    # 底部注释
    cv.text_center(600, 1640, '注：各阶段均设置质量控制节点，确保审核质量符合《基本建设财务规则》及川发改价格〔2013〕901号要求',
                   font_size=11, color='#95a5a6')

    # 左侧时间轴
    cv.draw.line([(30, 170), (30, 1500)], fill='#bdc3c7', width=2)
    for y in [270, 490, 680, 930, 1310]:
        cv.draw.ellipse([(22, y-8), (38, y+8)], fill='#1a5276')

    return cv.save(os.path.join(SVG_DIR, "flowchart.png"))


def generate_org_chart():
    """项目组织架构图 - Pillow 精确版（修复重叠）"""
    cv = Canvas(1200, 780)

    # 标题
    cv.rounded_rect(100, 15, 1100, 50, 8, '#1a5276')
    cv.text_center(600, 40, '阿坝县竣工财务决算审核项目组织架构图', font_size=18, color='white', bold=True)

    # === 第一层：总负责人 ===
    l1_x1, l1_y1, l1_x2, l1_y2 = 350, 85, 850, 135
    cv.rounded_rect(l1_x1, l1_y1, l1_x2, l1_y2, 10, '#1a5276')
    cv.text_center(600, 100, '项目总负责人（主任会计师）', font_size=15, color='white', bold=True)
    cv.text_center(600, 120, '全面负责 · 三级复核终审', font_size=11, color='#d5dbdb')

    # 第一层→第二层 连接
    cv.arrow_down(600, l1_y2, 170)
    cv.draw.line([(200, 170), (1000, 170)], fill='#1a5276', width=2)
    for cx in [200, 600, 1000]:
        cv.arrow_down(cx, 170, 195)

    # === 第二层：三位负责人 ===
    l2_y1, l2_y2 = 200, 270
    l2_data = [
        (40, 360, '项目负责人', 'CPA+高级职称\n一级复核·现场统筹', '#d4efdf', '#27ae60', '#1e8449'),
        (420, 780, '质量复核负责人', '质控部门经理\n二级复核·质量监控', '#d6eaf8', '#2980b9', '#1a5276'),
        (840, 1160, '后勤保障负责人', '综合管理部\n档案·联络·交通', '#fdebd0', '#e67e22', '#a04000'),
    ]
    l2_centers = []
    for x1, x2, title, sub, fill, outline, tc in l2_data:
        cv.rounded_rect(x1, l2_y1, x2, l2_y2, 8, fill, outline=outline, width=2)
        cx = (x1 + x2) // 2
        l2_centers.append(cx)
        cv.text_center(cx, l2_y1 + 22, title, font_size=13, color=tc, bold=True)
        # 副标题分行绘制，避免超出
        sub_lines = sub.split('\n')
        for si, sline in enumerate(sub_lines):
            cv.text_center(cx, l2_y1 + 48 + si * 13, sline, font_size=10, color='#2c3e50')

    # === 第三层连接线 ===
    l3_y_connect = 305
    l3_y1, l3_y2 = 315, 395

    # 左列（项目负责人）下属3个框 → 水平线范围 40~360, 中心 200
    cv.arrow_down(l2_centers[0], l2_y2, l3_y_connect)
    cv.draw.line([(40, l3_y_connect), (360, l3_y_connect)], fill='#27ae60', width=2)
    # 3个子框中心: 95, 200, 305 (等分40~360)
    l3_left_cx = [95, 200, 305]
    for cx in l3_left_cx:
        cv.arrow_down(cx, l3_y_connect, l3_y1)

    # 中列（质量复核负责人）下属1个框 → 中心 600
    cv.arrow_down(l2_centers[1], l2_y2, l3_y1)

    # 右列（后勤保障负责人）无下属框
    # 不画线

    # === 第三层：具体岗位 ===
    # 左列3个框，各宽100，紧密排列在40~360区间
    l3_w = 100
    l3_boxes_left = [
        (50, 'CPA审核员', '工程财务审核'),
        (155, '高级审计员', '待摊/资金审核'),
        (260, '审计助理', '资料整理/底稿'),
    ]
    for x1, title, sub in l3_boxes_left:
        x2 = x1 + l3_w
        cv.rounded_rect(x1, l3_y1, x2, l3_y2, 6, 'white', outline='#27ae60', width=2)
        cv.text_center((x1 + x2) // 2, l3_y1 + 22, title, font_size=11, color='#1e8449', bold=True)
        cv.text_center((x1 + x2) // 2, l3_y1 + 52, sub, font_size=9, color='#2c3e50')

    # 中列1个框（质控复核组），宽160，居中于600
    l3_mid_x1, l3_mid_x2 = 520, 680
    cv.rounded_rect(l3_mid_x1, l3_y1, l3_mid_x2, l3_y2, 6, 'white', outline='#2980b9', width=2)
    cv.text_center(600, l3_y1 + 22, '质控复核组', font_size=11, color='#1a5276', bold=True)
    cv.text_center(600, l3_y1 + 52, '独立复核/底稿检查', font_size=9, color='#2c3e50')

    # 右列（后勤）下级：档案管理员
    cv.arrow_down(l2_centers[2], l2_y2, l3_y1)
    l3_right_x1, l3_right_x2 = 940, 1060
    cv.rounded_rect(l3_right_x1, l3_y1, l3_right_x2, l3_y2, 6, 'white', outline='#e67e22', width=2)
    cv.text_center((l3_right_x1 + l3_right_x2) // 2, l3_y1 + 22, '综合协调员', font_size=11, color='#a04000', bold=True)
    cv.text_center((l3_right_x1 + l3_right_x2) // 2, l3_y1 + 52, '档案/联络/出行', font_size=9, color='#2c3e50')

    # === 底部说明 ===
    cv.text_center(600, 460, '项目组实行组长负责制，各岗位职责明确、相互配合、相互制约', font_size=12, color='#7f8c8d')
    cv.text_center(600, 495, '人员变动需经采购人书面同意，接替人员资质不低于原人员', font_size=12, color='#7f8c8d')

    # 图例
    cv.rounded_rect(350, 540, 850, 580, 6, 'white', outline='#bdc3c7', width=1)
    legends = [('#27ae60', '审核执行线'), ('#2980b9', '质量复核线'), ('#e67e22', '后勤保障线')]
    for i, (color, label) in enumerate(legends):
        lx = 380 + i * 160
        cv.draw.line([(lx, 560), (lx + 30, 560)], fill=color, width=2)
        cv.text_left(lx + 35, 553, label, font_size=10, color='#2c3e50')

    return cv.save(os.path.join(SVG_DIR, "org_chart.png"))


def generate_quality_arch():
    """质量保证体系架构图 - Pillow 精确版"""
    cv = Canvas(1200, 1000)

    # 标题
    cv.rounded_rect(80, 15, 1120, 50, 8, '#1a5276')
    cv.text_center(600, 40, '竣工财务决算审核质量保证体系架构图', font_size=18, color='white', bold=True)

    # 顶层目标
    cv.rounded_rect(200, 85, 1000, 135, 20, '#1a5276')
    cv.text_center(600, 110, '质量管理目标：审核结论客观公正、数据准确无误', font_size=16, color='white', bold=True)

    # 连接线
    cv.arrow_down(600, 135, 170)
    cv.draw.line([(170, 170), (1030, 170)], fill='#1a5276', width=2)
    cv.arrow_down(170, 170, 195)
    cv.arrow_down(380, 170, 195)
    cv.arrow_down(600, 170, 195)
    cv.arrow_down(820, 170, 195)
    cv.arrow_down(1030, 170, 195)

    # 四大支柱
    pillars = [
        (50, 200, 310, 295, '制度保障', '执业质量控制制度 / 三级复核', '#d4efdf', '#27ae60', '#1e8449'),
        (320, 200, 580, 295, '人员保障', 'CPA持证团队 / 持续培训', '#d6eaf8', '#2980b9', '#1a5276'),
        (620, 200, 880, 295, '流程保障', '标准化底稿 / 节点控制', '#fdebd0', '#e67e22', '#a04000'),
        (890, 200, 1150, 295, '风险管控', '风险评估 / 廉洁保密', '#f5b7b1', '#c0392b', '#78281f'),
    ]
    for x1, y1, x2, y2, title, sub, fill, outline, tc in pillars:
        cv.rounded_rect(x1, y1, x2, y2, 8, fill, outline=outline, width=2)
        cv.text_center((x1+x2)//2, y1+35, title, font_size=14, color=tc, bold=True)
        cv.text_center((x1+x2)//2, y1+65, sub, font_size=11, color='#2c3e50')
        cv.arrow_down((x1+x2)//2, y2, y2+30)
        cv.arrow_down((x1+x2)//2, y2+30, y2+55)

    # 具体措施（四列）
    measures = [
        (20, 350, 300, 620, '制度保障措施',
         ['执业质量控制制度', '三级复核实施细则', '审计工作底稿规范', '档案管理制度',
          '廉政保密制度', '重大问题请示报告', '责任追究制度'], '#27ae60'),
        (310, 350, 590, 620, '人员保障措施',
         ['CPA持证成员不少于6人', '高级职称项目负责人', '工程+财务复合背景', '年度培训不少于40学时',
          '政府审计项目经验', '人员变更审批制度', '胜任能力动态评估'], '#2980b9'),
        (610, 350, 890, 620, '流程保障措施',
         ['标准化工作底稿模板', '关键节点质量检查表', '审核日志全程记录', '双人交叉复核机制',
          '时限预警提醒机制', '与采购人沟通反馈', '质量考核与奖惩'], '#e67e22'),
        (900, 350, 1180, 620, '风险管控措施',
         ['项目风险分级评估', '重大风险预警机制', '廉洁从业承诺书', '保密协议签署',
          '利益冲突申报', '重大事项报告', '质量事故应急预案'], '#c0392b'),
    ]
    for x1, y1, x2, y2, title, items, ec in measures:
        cv.rounded_rect(x1, y1, x2, y2, 8, 'white', outline=ec, width=2)
        cx = (x1 + x2) // 2
        cv.text_center(cx, y1 + 18, title, font_size=12, color=ec, bold=True)
        cv.draw.line([(x1+15, y1+32), (x2-15, y1+32)], fill=ec, width=1)
        for i, item in enumerate(items):
            cv.text_left(x1 + 15, y1 + 42 + i * 32, '• ' + item, font_size=11, color='#2c3e50')

    # 汇聚线
    for cx in [170, 450, 750, 1040]:
        cv.arrow_down(cx, 620, 670)
    cv.draw.line([(170, 670), (1040, 670)], fill='#1a5276', width=2)
    cv.arrow_down(600, 670, 710)

    # 底层持续改进
    cv.rounded_rect(150, 715, 1050, 830, 10, '#1a5276')
    cv.text_center(600, 740, '质量持续改进机制', font_size=16, color='#f9e79f', bold=True)
    cv.text_center(600, 770, '项目后评价 → 经验总结 → 制度修订 → 培训提升 → 质量考核 → 持续改进',
                   font_size=12, color='white')
    cv.text_center(600, 800, 'PDCA循环：Plan（策划）→ Do（实施）→ Check（检查）→ Act（改进）',
                   font_size=11, color='#d5dbdb')

    # 底部
    cv.text_center(600, 880, '遵循标准：中国注册会计师审计准则、基本建设财务规则、川发改价格〔2013〕901号',
                   font_size=11, color='#7f8c8d')
    cv.text_center(600, 915, '《会计师事务所质量管理准则第5101号——业务质量管理》（2024年修订）',
                   font_size=11, color='#7f8c8d')

    return cv.save(os.path.join(SVG_DIR, "quality_arch.png"))


def generate_risk_matrix():
    """风险矩阵图 - Pillow 精确版"""
    cv = Canvas(1000, 750)

    # 标题
    cv.text_center(500, 25, '竣工财务决算审核重点难点分析矩阵', font_size=18, color='#1a5276', bold=True)

    # 坐标轴
    ox, oy = 150, 600
    axis_w, axis_h = 700, 480
    cv.draw.line([(ox, oy), (ox + axis_w, oy)], fill='#2c3e50', width=2)
    cv.draw.line([(ox, oy), (ox, oy - axis_h)], fill='#2c3e50', width=2)
    cv.text_center(ox + axis_w // 2, oy + 35, '风险发生概率 →', font_size=13, color='#2c3e50')
    cv.text_center(30, oy - axis_h // 2, '影响程度 →', font_size=13, color='#2c3e50')

    # 象限分隔
    mid_x = ox + axis_w // 2
    mid_y = oy - axis_h // 2
    cv.draw.line([(mid_x, oy), (mid_x, oy - axis_h)], fill='#bdc3c7', width=1)
    cv.draw.line([(ox, mid_y), (ox + axis_w, mid_y)], fill='#bdc3c7', width=1)

    # 象限标签
    cv.text_center(ox + axis_w // 4, oy - axis_h * 3 // 4, '低概率—高影响\n（重点关注）', font_size=11, color='#27ae60')
    cv.text_center(ox + axis_w * 3 // 4, oy - axis_h * 3 // 4, '高概率—高影响\n（优先处置）', font_size=11, color='#c0392b', bold=True)
    cv.text_center(ox + axis_w // 4, oy - axis_h // 4, '低概率—低影响\n（常规管理）', font_size=11, color='#7f8c8d')
    cv.text_center(ox + axis_w * 3 // 4, oy - axis_h // 4, '高概率—低影响\n（持续监控）', font_size=11, color='#e67e22')

    # 气泡 - 坐标映射到轴内
    def map_xy(px, py, r):
        return (ox + int(px * axis_w / 100), oy - int(py * axis_h / 100), int(r * axis_w / 100))

    bubbles = [
        (82, 82, 8, '资金管理', '#e74c3c'),      # 高概率-高影响
        (72, 72, 7, '工程变更', '#e74c3c'),
        (65, 85, 6.5, '待摊投资', '#e67e22'),
        (35, 78, 7, '资产交付', '#2980b9'),      # 低概率-高影响
        (25, 68, 6, '尾工工程', '#2980b9'),
        (70, 30, 6, '资料完整性', '#27ae60'),     # 高概率-低影响
        (82, 40, 5.5, '时限压力', '#27ae60'),
        (22, 28, 5, '天气', '#95a5a6'),          # 低概率-低影响
        (38, 38, 5, '交通', '#95a5a6'),
    ]
    for px, py, r, label, color in bubbles:
        cx, cy, cr = map_xy(px, py, r)
        cv.draw.ellipse([(cx-cr, cy-cr), (cx+cr, cy+cr)], fill=color)
        # 白色半透明文字
        cv.text_center(cx, cy, label, font_size=10, color='white')

    # 图例
    legends = [('#e74c3c', '高风险'), ('#e67e22', '中高风险'), ('#2980b9', '中等风险'), ('#27ae60', '低风险')]
    cv.rounded_rect(180, 680, 820, 720, 6, 'white', outline='#bdc3c7', width=1)
    for i, (color, label) in enumerate(legends):
        cx = 230 + i * 160
        cv.draw.ellipse([(cx-8, 692), (cx+8, 708)], fill=color)
        cv.text_left(cx + 15, 695, label, font_size=11, color='#2c3e50')

    return cv.save(os.path.join(SVG_DIR, "risk_matrix.png"))


if __name__ == '__main__':
    print("Pillow 精确绘制图表...")
    for fn, name in [(generate_flowchart, '审核工作流程图'),
                      (generate_org_chart, '项目组织架构图'),
                      (generate_quality_arch, '质量保证体系架构图'),
                      (generate_risk_matrix, '重点难点分析矩阵')]:
        path = fn()
        print(f"  [OK] {name} -> {path}")
    print("完成！")
