# -*- coding: utf-8 -*-
"""Generate improved P1 and P6 for v8, then copy to v8_assets"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

NW = "#1A365D"; TL = "#3A7B8A"; GD = "#D4A574"
MU = "#718096"; IK = "#2D3748"; WH = "#FFFFFF"; BG = "#FAF8F4"
W, H = 1653, 2339
M = 160

def rgb(s):
    h = s.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def rga(s, a=255): return (*rgb(s), a)

def font(size, bold=False):
    for p in [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc",
    ]:
        if Path(p).exists(): return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()

def draw(d, text, x, y, f, fill, w=None, gap=6, align="left"):
    mw = w or 9999; lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=f) <= mw: cur += ch
            else:
                if cur: lines.append(cur); cur = ch
        if cur: lines.append(cur)
    for line in lines:
        xx = x
        if align == "center" and w: xx = x + (w - d.textlength(line, font=f)) // 2
        d.text((xx, y), line, font=f, fill=fill); y += f.size + gap
    return y

def bottom_bar(d):
    tx = "公开公正  用心服务  诚信为本  服务至上  追求卓越"
    d.rectangle([0, H-50, W, H], fill=rga(NW))
    d.text(((W-d.textlength(tx, font=font(18)))//2, H-42), tx, font=font(18), fill=rga(WH, 180))

# ===== NEW P1: Dramatic cover with large diamond pattern =====
def new_p1():
    img = Image.new("RGB", (W, H), rgb(NW))
    d = ImageDraw.Draw(img, "RGBA")
    # Large nested diamond pattern
    for i in range(8):
        s = 900 - i*90
        cx2, cy2 = W//2, H//2+120
        pts = [(cx2, cy2-s), (cx2+s, cy2), (cx2, cy2+s), (cx2-s, cy2)]
        d.polygon(pts, fill=rga(TL, 3+i*2), outline=rga(TL, 12+i*3))
    # Top-right concentric circles
    for r in range(10):
        d.ellipse([W-550+r*30, -150+r*30, W+150+r*30, 500+r*30], fill=rga(TL, 2))
    # Brand bar
    d.rectangle([0, 0, W, 320], fill=rga(NW))
    d.rectangle([0, 320, W, 330], fill=rga(GD))
    d.text((M, 80), "SICHUAN", font=font(72, True), fill=rga(WH, 180))
    d.text((M, 155), "RONGCE", font=font(110, True), fill=WH)
    # Gold accent diamonds on brand bar
    for j in range(3):
        s2 = 14 - j*4; xd = W-280 + j*55; yd = 165
        pts2 = [(xd, yd-s2*2), (xd+s2, yd), (xd, yd+s2*2), (xd-s2, yd)]
        d.polygon(pts2, fill=rga(GD, 25-j*7))
    # Center text
    draw(d, "谋专业之策", M+10, 470, font(64, True), WH, 700, 16)
    draw(d, "融品质之精", M+10, 550, font(64, True), WH, 700, 16)
    d.line([M+10, 650, M+410, 650], fill=rga(GD), width=5)
    draw(d, "政府审计与工程咨询综合服务机构", M+10, 690, font(32), rga(WH, 200), 700, 10)
    # Bottom bar
    d.rectangle([0, H-70, W, H], fill=rga(NW))
    txt = "审计 \u00b7 绩效 \u00b7 财政监督 \u00b7 工程咨询 \u00b7 数字化分析"
    tw0 = d.textlength(txt, font=font(22))
    d.text(((W-tw0)//2, H-52), txt, font=font(22), fill=rga(WH, 180))
    # Corner elements
    d.line([W-100, 50, W-30, 50], fill=rga(GD, 80), width=3)
    d.line([W-30, 50, W-30, 120], fill=rga(GD, 80), width=3)
    d.polygon([(W-100, H-100), (W-40, H-100), (W-100, H-40)], fill=rga(GD, 20))
    d.polygon([(W-100, H-100), (W-55, H-100), (W-100, H-55)], fill=rga(GD, 35))
    return img

# ===== NEW P6: Clean circular layout =====
def new_p6():
    img = Image.new("RGB", (W, H), rgb(WH))
    d = ImageDraw.Draw(img, "RGBA")
    # Left bar
    d.rectangle([0, 0, 18, H], fill=rga(NW)); d.rectangle([18, 0, 24, H], fill=rga(GD))
    # Title
    d.text((M, 120), "预算绩效管理", font=font(52, True), fill=NW)
    d.text((M, 188), "BUDGET PERFORMANCE", font=font(22), fill=rga(GD))
    d.line([M, 225, M+440, 225], fill=rga(GD), width=3)
    d.text((W-250, 0), "06", font=font(240, True), fill=rga(NW, 6))
    # Subtitle
    draw(d, "您关心的不只是花了多少钱，更是效果怎么样", M, 265, font(30), MU, 650, 10)
    draw(d, "让财政资金从花了没有走向花得值不值。", M, 305, font(28, True), NW, 650, 6)
    # Central circle with PDCA
    cx, cy = M+410, 600
    d.ellipse([cx-100, cy-100, cx+100, cy+100], fill=rga(NW))
    d.ellipse([cx-94, cy-94, cx+94, cy+94], fill=rga(TL, 12))
    draw(d, "绩效管理", cx-d.textlength("绩效管理", font=font(32, True))//2, cy-22, font(32, True), NW, 200, 4, "center")
    draw(d, "PDCA 闭环", cx-d.textlength("PDCA 闭环", font=font(20))//2, cy+18, font(20), rga(NW, 150), 200, 0, "center")
    # Five nodes around
    nodes = [
        ("01", "事前评估", "必要性 \u00b7 可行性 \u00b7 财政承受"),
        ("02", "目标审核", "完整性 \u00b7 可衡量 \u00b7 责任书"),
        ("03", "运行监控", "进度追踪 \u00b7 偏差预警"),
        ("04", "重点评价", "政策 \u00b7 部门 \u00b7 项目评价"),
        ("05", "结果应用", "整改清单 \u00b7 预算挂钩"),
    ]
    radius = 250
    for i, (num, name, desc) in enumerate(nodes):
        angle = -math.pi/2 + 2*math.pi*i/5
        nx = int(cx + radius*math.cos(angle))
        ny = int(cy + radius*math.sin(angle))
        bw, bh = 240, 90
        d.rounded_rectangle([nx-bw//2, ny-bh//2, nx+bw//2, ny+bh//2], radius=10, fill=WH, outline=rga(TL, 50), width=2)
        # Number circle
        d.ellipse([nx-bw//2+10, ny-14, nx-bw//2+46, ny+22], fill=rga(NW))
        d.text((nx-bw//2+22, ny-6), num, font=font(24, True), fill=WH)
        draw(d, name, nx-bw//2+58, ny-18, font(24, True), NW, 160, 4)
        draw(d, desc, nx-bw//2+58, ny+12, font(17), MU, 160, 2)
        # Connecting line
        ex = int(cx + (radius-95)*math.cos(angle))
        ey = int(cy + (radius-95)*math.sin(angle))
        d.line([ex, ey, nx, ny], fill=rga(GD, 35), width=2)
    # Footer box
    d.rounded_rectangle([M, 820, W-M, 930], radius=14, fill=rga("#E8E0D4", 60))
    draw(d, "事前评估 \u2192 目标审核 \u2192 运行监控 \u2192 重点评价 \u2192 结果应用", M+40, 845, font(28, True), NW, 1300, 6, "center")
    draw(d, "每个环节交付：核查清单 + 数据底稿 + 分析报告 + 整改建议", M+40, 885, font(24), MU, 1300, 0, "center")
    d.line([M, H-65, W-M, H-65], fill=rga(TL, 20), width=2)
    bottom_bar(d)
    return img

# Save
WK = Path("work/sichuan_rongce_brochure/v8_assets")
WK.mkdir(parents=True, exist_ok=True)
p1 = new_p1()
p1.save(WK / "page_01.png", quality=95)
print("P1 saved")
p6 = new_p6()
p6.save(WK / "page_06.png", quality=95)
print("P6 saved")
