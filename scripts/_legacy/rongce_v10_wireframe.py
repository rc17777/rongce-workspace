# -*- coding: utf-8 -*-
"""四川融策宣传册 v10 —— 框架确认版（Wireframe）
每页只画布局框架：色块标分区、占位符标位置、不填具体文案。
用户确认布局后，再据此填内容。
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WK = Path("work/sichuan_rongce_brochure/v10_wireframe")
WK.mkdir(parents=True, exist_ok=True)

NW = "#1A365D"; TL = "#3A7B8A"; GD = "#D4A574"
MU = "#718096"; IK = "#2D3748"; WH = "#FFFFFF"; BG = "#FAF8F4"
W, H = 1653, 2339
M = 160  # page margin
COL_W = 620  # content column width

def rgb(s):
    h = s.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def rga(s, a=255): return (*rgb(s), a)

def font(size, bold=False):
    for p in [r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
              r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]:
        if Path(p).exists(): return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()

def wireframe_box(d, x, y, w, h, label, color, alpha=40):
    """Draw a wireframe zone: semi-transparent fill + border + label"""
    d.rounded_rectangle([x, y, x+w, y+h], radius=8, fill=rga(color, alpha), outline=rga(color, 80), width=2)
    # Label
    f = font(20)
    tw = d.textlength(label, font=f)
    d.text((x + (w-tw)//2, y + h//2 - 12), label, font=f, fill=rga(color, 140))

def label(d, x, y, text, size=24, color=IK):
    d.text((x, y), text, font=font(size, True), fill=rgb(color))

def left_bar(d):
    d.rectangle([0, 0, 6, H], fill=rga(NW, 40))
    d.rectangle([6, 0, 10, H], fill=rga(GD, 40))

# ===== PAGE 0: Layout Key (legend page) =====
def p0_legend():
    img = Image.new("RGB", (W, H), rgb(WH))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((M, 100), "LAYOUT LEGEND", font=font(48, True), fill=NW)
    d.text((M, 170), "框架图例说明", font=font(32), fill=MU)
    items = [
        ("深蓝", NW, "标题、页编号、重点强调"),
        ("青绿", TL, "副标题、辅助信息、装饰区"),
        ("铜金", GD, "分割线、小装饰、强调色"),
        ("暖白", BG, "页面底色"),
        ("浅灰", "#E8E0D4", "信息卡片底色"),
        ("灰色", MU, "说明文字"),
    ]
    for i, (name, clr, desc) in enumerate(items):
        y0 = 280 + i*80
        d.rounded_rectangle([M, y0, M+80, y0+60], radius=8, fill=rgb(clr), outline=rga(IK, 30), width=1)
        d.text((M+110, y0+5), name, font=font(24, True), fill=IK)
        d.text((M+110, y0+35), desc, font=font(20), fill=MU)
    # Structure
    d.text((M, 800), "10页结构", font=font(36, True), fill=NW)
    pages = [
        "01 封面 | 02 为什么融策 | 03 方法论 | 04 服务体系 | 05 政府审计",
        "06 预算绩效 | 07 工程咨询 | 08 数字化 | 09 代表经验 | 10 合作价值"
    ]
    for i, line in enumerate(pages):
        d.text((M, 860 + i*40), line, font=font(22), fill=MU)
    return img

# ===== WIREFRAME PAGE TEMPLATE =====
def wf_page(num, title, en, zones):
    """
    zones: list of (x, y, w, h, label, color)
    """
    img = Image.new("RGB", (W, H), rgb(BG))
    d = ImageDraw.Draw(img, "RGBA")
    left_bar(d)
    # Page header zone
    d.text((M, 80), f"P{num:02d} — {title}", font=font(48, True), fill=NW)
    d.text((M, 150), en, font=font(22), fill=rga(GD, 120))
    d.line([M, 185, M+500, 185], fill=rga(GD, 60), width=2)
    # Zone boxes
    for (x, y, w, h, label, color) in zones:
        wireframe_box(d, x, y, w, h, label, color)
    # Footer
    d.rectangle([0, H-50, W, H], fill=rga(NW, 30))
    d.text((M, H-38), "底部栏：公司理念/页码", font=font(18), fill=rga(IK, 60))
    # Page number
    d.text((W-120, 30), f"{num:02d}", font=font(80, True), fill=rga(NW, 25))
    return img

# ===== P1: Cover Wireframe =====
def wf_cover():
    img = Image.new("RGB", (W, H), rgb(NW))
    d = ImageDraw.Draw(img, "RGBA")
    # Top brand zone
    d.rectangle([0, 0, W, 320], fill=rga(NW))
    d.rectangle([0, 320, W, 326], fill=rga(GD, 80))
    d.text((M, 80), "[BRAND: SICHUAN RONGCE LOGO]", font=font(36, True), fill=rga(WH, 60))
    # Center statement zone
    wireframe_box(d, M, 420, 700, 260, "主标题 + 副标题 + 分割线", GD, 25)
    # Bottom info
    d.rectangle([0, H-80, W, H], fill=rga(NW))
    d.text((M, H-55), "[BOTTOM BAR: 业务标签 + 公司全称]", font=font(24), fill=rga(WH, 50))
    # Decorative zone
    wireframe_box(d, W-600, -50, 550, 500, "装饰区：几何图案/渐变", TL, 15)
    d.text((W-250, 30), "01", font=font(200, True), fill=rga(WH, 8))
    return img

# ===== P2: Why Rongce Wireframe =====
def wf_p2():
    zones = [
        (M, 230, COL_W, 30, "副标题: 核心问题(1行)", MU),
        (M, 270, COL_W, 80, "主问题: 两个追问(2行)", NW),
        (M, 370, COL_W, 40, "说明文字(1行)", MU),
        (M, 440, 320, 200, "卡片①: 不只查账", NW),
        (M+360, 440, 320, 200, "卡片②: 不只找问题", TL),
        (M+720, 440, 320, 200, "卡片③: 不只靠经验", NW),
        (M, 680, COL_W+720, 130, "公司简介(4行要点)", "#E8E0D4"),
    ]
    return wf_page(2, "为什么是融策？", "WHY RONGCE", zones)

# ===== P3: Method Wireframe =====
def wf_p3():
    zones = [
        (M, 230, 320, 250, "资金线: 两要点", NW),
        (M+360, 230, 320, 250, "项目线: 两要点", TL),
        (M+720, 230, 320, 250, "责任线: 两要点", NW),
        (M, 520, COL_W+720, 60, "五步流程: ①→②→③→④→⑤", TL),
        (M, 620, COL_W+720, 80, "核心声明(1行居中)", "#E8E0D4"),
    ]
    return wf_page(3, "我们怎么做？", "OUR METHODOLOGY", zones)

# ===== P4: Services Overview Wireframe =====
def wf_p4():
    zones = [
        (M, 230, COL_W, 30, "副标题: 服务理念(1行)", MU),
        (M, 280, 250, 200, "政府审计", NW),
        (M+280, 280, 250, 200, "预算绩效", TL),
        (M+560, 280, 250, 200, "工程咨询", NW),
        (M+840, 280, 250, 200, "采购审计", TL),
        (M+1120, 280, 250, 200, "管理咨询", NW),
        (M, 520, COL_W+720, 80, "协同说明(1-2行)", "#E8E0D4"),
        (M, 640, COL_W+720, 120, "详细列表: 每条业务线的具体服务", MU),
    ]
    return wf_page(4, "服务体系", "SERVICE SYSTEM", zones)

# ===== P5: Gov Audit Wireframe =====
def wf_p5():
    zones = [
        (M, 230, COL_W, 30, "副标题: 审计理念(1行)", MU),
        (M, 280, 350, 140, "有没有·合规性", NW),
        (M+380, 280, 350, 140, "对不对·准确性", TL),
        (M+760, 280, 350, 140, "值不值·绩效性", GD),
        (M, 460, COL_W+720, 180, "四项服务领域表格", "#E8E0D4"),
    ]
    return wf_page(5, "政府审计", "GOVERNMENT AUDIT", zones)

# ===== P6: Budget Performance Wireframe =====
def wf_p6():
    zones = [
        (M, 230, COL_W, 60, "副标题: 绩效理念(2行)", MU),
        (M+200, 340, 220, 100, "事前评估", NW),
        (M+480, 280, 220, 100, "目标审核", TL),
        (M+760, 340, 220, 100, "运行监控", NW),
        (M+480, 460, 220, 100, "重点评价", TL),
        (M+200, 520, 220, 100, "结果应用", NW),
        (M, 680, COL_W+720, 100, "全周期说明(2行)", "#E8E0D4"),
        (M, 820, COL_W+720, 60, "交付物说明(1行)", MU),
    ]
    return wf_page(6, "预算绩效管理", "BUDGET PERFORMANCE", zones)

# ===== P7: Engineering Wireframe =====
def wf_p7():
    zones = [
        (M, 230, COL_W, 30, "副标题: 工程理念(1行)", MU),
        (M, 290, 320, 140, "预算编制/财政评审", NW),
        (M+360, 290, 320, 140, "清单及招标控制价", TL),
        (M+720, 290, 320, 140, "结算审核", NW),
        (M+360, 470, 320, 140, "全过程工程咨询", TL),
        (M, 650, COL_W+720, 150, "核心能力列表(4项)", "#E8E0D4"),
    ]
    return wf_page(7, "工程咨询与财政评审", "ENGINEERING CONSULTING", zones)

# ===== P8: Digital Wireframe =====
def wf_p8():
    zones = [
        (M, 230, COL_W, 30, "副标题: 数字化理念(1行)", MU),
        (M, 290, COL_W+360, 140, "01 数据标准", NW),
        (M+360, 290, COL_W+360, 140, "02 规则模型", TL),
        (M, 470, COL_W+360, 140, "03 穿透核查", NW),
        (M+360, 470, COL_W+360, 140, "04 报告复核", TL),
        (M, 650, COL_W+720, 100, "数字化理念声明(1-2行)", "#E8E0D4"),
    ]
    return wf_page(8, "数字化审计能力", "DIGITAL AUDIT CAPABILITIES", zones)

# ===== P9: Experience Wireframe =====
def wf_p9():
    zones = [
        (M, 230, COL_W, 30, "副标题: 经验概述(1行)", MU),
        (940, 140, 500, 200, "服务版图: 4个地点", TL),
        (M, 300, 700, 100, "代表客户: 标题+标签列表(14家)", "#E8E0D4"),
        (M, 450, 700, 50, "覆盖领域(1行)", MU),
        (940, 380, 500, 60, "领域标签", "#E8E0D4"),
    ]
    return wf_page(9, "代表经验", "REPRESENTATIVE EXPERIENCE", zones)

# ===== P10: Contact Wireframe =====
def wf_p10():
    img = Image.new("RGB", (W, H), rgb(NW))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 280, W, 286], fill=rga(GD, 80))
    d.text((M, 80), "[P10] 合作价值 / VALUE PROPOSITION", font=font(48, True), fill=rga(WH, 60))
    d.text((M, 150), "[副标题]", font=font(24), fill=rga(WH, 30))
    d.line([M, 190, M+500, 190], fill=rga(GD, 50), width=3)
    d.text((M, 250), "[核心理念: 我们交付的不只是报告...]", font=font(30), fill=rga(WH, 50))
    wireframe_box(d, M, 340, 650, 280, "联系信息: 电话/邮箱/网址/地址", GD, 20)
    wireframe_box(d, 880, 340, 650, 280, "合作承诺: 4条原则", GD, 20)
    wireframe_box(d, W-400, H-400, 350, 200, "装饰区: 几何图案", TL, 10)
    d.rectangle([0, H-50, W, H], fill=rga(NW))
    return img

# ===== Generate all 11 pages (0 legend + 10 content) =====
makers = [
    p0_legend,
    wf_cover, wf_p2, wf_p3, wf_p4, wf_p5,
    wf_p6, wf_p7, wf_p8, wf_p9, wf_p10
]

for i, maker in enumerate(makers):
    out = WK / f"page_{i:02d}.png"
    print(f"Wireframe {i:02d}...", end=" ")
    img = maker()
    img.save(out, quality=80)
    print("OK")

print(f"\nDone. {len(makers)} wireframe pages in {WK}")
