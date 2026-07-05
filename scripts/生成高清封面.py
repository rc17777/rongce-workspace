#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用Pillow生成高清封面图 (像素级清晰)"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image, ImageDraw, ImageFont

# ===== 尺寸设置 =====
# A4 300dpi = 2480x3508 像素
W = 2480
H = 3508

img = Image.new('RGB', (W, H), (10, 31, 63))  # #0A1F3F
draw = ImageDraw.Draw(img)

# ===== 字体 =====
# 尝试多种字体路径
font_dirs = [
    r'C:\Windows\Fonts',
    r'C:\Windows\Fonts\微软雅黑',
]
font_paths = []

# 搜索微软雅黑
for root, dirs, files in os.walk(r'C:\Windows\Fonts'):
    for f in files:
        if '微软雅黑' in f or 'msyh' in f.lower():
            font_paths.append(os.path.join(root, f))
            if len(font_paths) >= 2:
                break
    if len(font_paths) >= 2:
        break

print(f"找到字体: {font_paths}")

# 如果没有，尝试其他中文字体
if not font_paths:
    for root, dirs, files in os.walk(r'C:\Windows\Fonts'):
        for f in files:
            if 'yahei' in f.lower() or 'msyh' in f.lower():
                font_paths.append(os.path.join(root, f))
                break
        if font_paths:
            break

# 用系统字体
try:
    font_big = ImageFont.truetype(font_paths[0], 120) if font_paths else ImageFont.load_default()
    font_mid = ImageFont.truetype(font_paths[0], 80) if font_paths else ImageFont.load_default()
    font_small = ImageFont.truetype(font_paths[0], 48) if font_paths else ImageFont.load_default()
    font_info = ImageFont.truetype(font_paths[0], 36) if font_paths else ImageFont.load_default()
    font_tiny = ImageFont.truetype(font_paths[0], 24) if font_paths else ImageFont.load_default()
except:
    font_big = font_mid = font_small = font_info = font_tiny = ImageFont.load_default()

# ===== 背景 =====
# 渐变色背景（深蓝渐变）
for y in range(H):
    ratio = y / H
    r = int(10 + ratio * 5)
    g = int(31 + ratio * 20)
    b = int(63 + ratio * 30)
    for x in range(W):
        img.putpixel((x, y), (r, g, b))

# ===== 左侧金色竖条 =====
gold = (197, 149, 92)
gold_light = (232, 213, 181)

# 主竖条
for y in range(200, 3300):
    for x in range(180, 188):
        img.putpixel((x, y), gold)

# 副竖条（淡金）
for y in range(200, 3300):
    for x in range(196, 200):
        img.putpixel((x, y), gold_light)

# ===== 顶部金色横线 =====
for y in range(200, 204):
    for x in range(180, 600):
        img.putpixel((x, y), gold)

# ===== 底部金色横线 =====
for y in range(3296, 3300):
    for x in range(180, 600):
        img.putpixel((x, y), gold)

# ===== 右上几何装饰（半透明圆） =====
from PIL import ImageDraw
draw_shape = ImageDraw.Draw(img)
for i in range(3):
    cx = 2100 + i * 150
    cy = 400 + i * 80
    r = 300 - i * 60
    alpha = 40 - i * 10
    color = (197, 149, 92, alpha)
    # Pillow不支持直接RGBA绘制，用半透明覆盖
    overlay = Image.new('RGBA', (W, H), (0,0,0,0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(197, 149, 92, alpha))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

# ===== 底部几何装饰 =====
overlay = Image.new('RGBA', (W, H), (0,0,0,0))
overlay_draw = ImageDraw.Draw(overlay)
# 大圆
overlay_draw.ellipse([1800, 2800, 2300, 3300], fill=(21, 45, 74, 180))
overlay_draw.ellipse([2000, 2600, 2200, 2800], fill=(26, 50, 84, 150))
# 小圆
overlay_draw.ellipse([2100, 2900, 2200, 3000], fill=(197, 149, 92, 80))
img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
draw = ImageDraw.Draw(img)

# ===== 文字绘制 =====
# 公司名称
draw.text((230, 400), "四川融策会计师事务所", fill=gold, font=font_mid)

# 主标题 "投标文件"
draw.text((230, 520), "投  标  文  件", fill=(255, 255, 255), font=font_big)

# 英文副标题
draw.text((232, 680), "TECHNICAL PROPOSAL · BID DOCUMENT", fill=(107, 123, 141), font=font_tiny)

# 分隔线（正文前面）
draw.text((230, 740), "━" * 20, fill=gold, font=font_tiny)

# 项目信息
info_y = 820
info_color = (139, 157, 175)
info_items = [
    "项 目 名 称：________________________",
    "招 标 编 号：________________________",
    "投 标 单 位：四川融策会计师事务所",
    "日        期：____年____月____日",
]
for item in info_items:
    draw.text((230, info_y), item, fill=info_color, font=font_info)
    info_y += 80

# ===== 底边装饰文字 =====
draw.text((230, 3200), "诚信为本 · 专业立身", fill=(60, 85, 120), font=font_tiny)

# ===== 保存 =====
output = r'D:\openclaw-workspace\bid_aba\封面-投标文件_高清.png'
img.save(output, 'PNG')
print(f"✅ 高清封面已生成: {output}")
print(f"   尺寸: {img.size[0]}x{img.size[1]} ({img.size[0]//21*2.54:.0f} DPI)")
print(f"   文件: {os.path.getsize(output)//1024}KB")
