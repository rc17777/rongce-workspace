# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import shutil

W, H = 1800, 1100
BLUE = (10, 31, 63)
TEAL = (26, 92, 110)
GOLD = (197, 149, 92)
BG = (245, 242, 236)
WHITE = (255, 255, 255)
TEXT = (31, 41, 51)

OUT = Path(r"C:\Users\scrccpa\.openclaw\workspace\output\openclaw-capability-maps-v2")
DESK = Path.home() / "Desktop" / "OpenClaw-capability-maps-v2"
OUT.mkdir(parents=True, exist_ok=True)
DESK.mkdir(parents=True, exist_ok=True)

FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size: int, bold: bool = False):
    path = FONT_BOLD if bold and Path(FONT_BOLD).exists() else FONT_REG
    return ImageFont.truetype(path, size)


def wrap_text(text: str, max_chars: int):
    lines = []
    for part in str(text).split("\n"):
        current = ""
        for ch in part:
            current += ch
            if len(current) >= max_chars:
                lines.append(current)
                current = ""
        if current:
            lines.append(current)
    return lines or [""]


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline=None, radius=18, width=3):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str):
    draw.rectangle((0, 0, W, H), fill=BG)
    draw.rectangle((50, 40, W - 50, 120), fill=BLUE)
    draw.text((80, 56), title, font=font(36, True), fill=WHITE)
    rounded(draw, (50, 140, W - 50, 208), WHITE, GOLD, 12, 3)
    draw.text((80, 160), subtitle, font=font(22), fill=TEXT)


def draw_box(draw, box, title, body, fill, outline, title_fill, body_fill, center=False, title_size=26, body_size=20):
    x1, y1, x2, y2 = box
    rounded(draw, box, fill, outline)
    if center:
        lines = wrap_text(title, 18) + wrap_text(body, 24)
        y = y1 + 26
        for i, line in enumerate(lines):
            f = font(title_size if i == 0 else body_size, i == 0)
            bbox = draw.textbbox((0, 0), line, font=f)
            tw = bbox[2] - bbox[0]
            x = x1 + ((x2 - x1) - tw) // 2
            draw.text((x, y), line, font=f, fill=title_fill if i == 0 else body_fill)
            y += 40
        return

    draw.text((x1 + 22, y1 + 18), title, font=font(title_size, True), fill=title_fill)
    y = y1 + 66
    for line in wrap_text(body, 20):
        draw.text((x1 + 22, y), line, font=font(body_size), fill=body_fill)
        y += 32


def draw_arrow(draw, start, end):
    draw.line((start, end), fill=GOLD, width=5)
    x1, y1 = start
    x2, y2 = end
    ang = math.atan2(y2 - y1, x2 - x1)
    pts = [
        (x2 - 24 * math.cos(ang + 2.55), y2 - 24 * math.sin(ang + 2.55)),
        (x2 - 24 * math.cos(ang - 2.55), y2 - 24 * math.sin(ang - 2.55)),
    ]
    draw.polygon([end] + pts, fill=GOLD)


def save_image(name: str, image: Image.Image):
    out_path = OUT / name
    image.save(out_path)
    shutil.copy2(out_path, DESK / name)


# 1 总览图
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
draw_header(d, "OpenClaw 四大能力版块总览", "一句话：不是聊天框，而是融策的审计业务 AI 作战中枢。")
draw_box(
    d,
    (610, 445, 1190, 610),
    "OpenClaw 融策AI统一中枢",
    "调度：LLM / Agent / Skills / Memory / RAG / 本地工具",
    GOLD,
    BLUE,
    BLUE,
    BLUE,
    center=True,
    title_size=30,
    body_size=21,
)
quadrants = [
    ((80, 255, 520, 430), "审计业务主战场", "报告复核、经责绩效、专项预算、串标采购、工程审计", BLUE, WHITE),
    ((1280, 255, 1720, 430), "知识与记忆底座", "Memory、Obsidian、RAG、法规案例、项目经验", TEAL, WHITE),
    ((80, 700, 520, 875), "文档图表产出", "Word、PPT、Excel、流程图、图表、标书、汇报材料", TEAL, WHITE),
    ((1280, 700, 1720, 875), "自动化与经营辅助", "浏览器、企业微信、定时巡检、多Agent、业务方案", BLUE, WHITE),
]
for box, title, body, fill, text_fill in quadrants:
    draw_box(d, box, title, body, fill, GOLD, text_fill, text_fill, title_size=25, body_size=19)
for start, end in [
    ((520, 345), (610, 492)),
    ((1280, 345), (1190, 492)),
    ((520, 785), (610, 563)),
    ((1280, 785), (1190, 563)),
]:
    draw_arrow(d, start, end)
save_image("01-openclaw-overview-v2.png", img)

# 2 工作流图
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
draw_header(d, "OpenClaw + LLM + RAG + Obsidian 工作流", "标准路线：Memory 定上下文，Skill 定流程，Knowledge 补资料，最后形成交付件。")
steps = [
    ("1. 接收任务", "报告、数据、流程图、标书、管理问题", "用户需求"),
    ("2. 查记忆", "偏好、历史项目、模板、禁忌", "Memory"),
    ("3. 选技能", "96 个技能按场景路由", "Skill"),
    ("4. 调知识库", "Obsidian、RAG、法规、案例、方法论", "Knowledge"),
    ("5. 产出交付", "图、表、文档、报告、底稿、方案", "交付件"),
]
step_x = 80
for idx, (title, body, tag) in enumerate(steps):
    fill = BG if idx in (0, 4) else WHITE
    draw_box(d, (step_x, 390, step_x + 290, 565), title, body, fill, BLUE, TEXT, TEXT, title_size=24, body_size=19)
    rounded(d, (step_x + 55, 650, step_x + 235, 724), GOLD if idx in (0, 4) else WHITE, GOLD, 12, 3)
    bbox = d.textbbox((0, 0), tag, font=font(22, True))
    tx = step_x + 145 - (bbox[2] - bbox[0]) // 2
    d.text((tx, 672), tag, font=font(22, True), fill=BLUE)
    if idx < len(steps) - 1:
        draw_arrow(d, (step_x + 290, 478), (step_x + 345, 478))
    step_x += 345
save_image("02-openclaw-workflow-v2.png", img)

# 3 矩阵图
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
draw_header(d, "OpenClaw 四大版块能力矩阵", "把“能做什么”翻译成“交付什么、什么时候用”。")
cols = [70, 310, 790, 1190]
widths = [220, 450, 370, 540]
headers = ["版块", "能做什么", "典型交付物", "最适合场景"]
y = 260
for x, w, header in zip(cols, widths, headers):
    d.rectangle((x, y, x + w, y + 72), fill=BLUE)
    d.text((x + 18, y + 20), header, font=font(24, True), fill=WHITE)
rows = [
    ("审计业务", "报告复核、经责绩效、串标采购、工程/专项/预算审计", "复核清单、疑点台账、审计底稿、风险画像", "拿到资料后快速找问题、定性、补证据"),
    ("知识底座", "Memory、RAG、Obsidian、法规案例、历史模板", "法规依据、案例素材、方法论引用、知识问答", "查依据、找案例、复用以前沉淀"),
    ("产出表达", "Word、PPT、Excel、流程图、架构图、图表、标书", "PPT、报告、图表、draw.io、标书章节", "汇报、投标、培训、内部管理"),
    ("自动化经营", "浏览器、企业微信、定时任务、多Agent、脚本工具", "自动采集、巡检提醒、任务拆解、项目看板", "重复活、长流程、多人协作式任务"),
]
y += 72
for ridx, row in enumerate(rows):
    row_fill = WHITE if ridx % 2 else (250, 248, 244)
    row_h = 138
    for cidx, (x, w, value) in enumerate(zip(cols, widths, row)):
        d.rectangle((x, y, x + w, y + row_h), fill=row_fill, outline=GOLD, width=3)
        max_chars = 9 if w < 250 else 18 if w < 400 else 24
        yy = y + 16
        for line in wrap_text(value, max_chars):
            d.text((x + 16, yy), line, font=font(21, cidx == 0), fill=TEXT)
            yy += 30
    y += row_h
save_image("03-openclaw-matrix-v2.png", img)

# 同步原 drawio 源文件，便于后续改图
src_drawio = Path(r"C:\Users\scrccpa\.openclaw\workspace\output\openclaw-capability-maps")
if src_drawio.exists():
    for path in src_drawio.glob("*.drawio"):
        shutil.copy2(path, DESK / path.name)

print(str(DESK))
