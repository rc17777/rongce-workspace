# Patch v7 -> v8: replace cover + P6
from pathlib import Path
v7 = Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v7.py')
text = v7.read_text('utf-8')

# Update paths
text = text.replace('/v7_assets', '/v8_assets')
text = text.replace('_v7_', '_v8_')

# New P1: much more visual cover
new_p1 = '''def p1_cover():
    img = Image.new("RGB", (W, H), rgb(NW))
    d = ImageDraw.Draw(img, "RGBA")
    # Large diamond geometric pattern
    for i in range(6):
        s = 800 - i*100
        cx, cy = W//2, H//2+100
        pts = [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)]
        d.polygon(pts, fill=rga(TL, 4+i*2), outline=rga(TL, 15+i*3))
    # Concentric decorative circles top-right
    for r in range(8):
        d.ellipse([W-600+r*35, -200+r*35, W+200+r*35, 550+r*35], fill=rga(TL, 2))
        d.ellipse([W-500+r*30, 300+r*30, W+100+r*30, 900+r*30], fill=rga(TL, 2))
    # Brand stripe at top
    d.rectangle([0, 0, W, 320], fill=rga(NW))
    d.rectangle([0, 320, W, 330], fill=rga(GD))
    d.text((M, 80), "SICHUAN", font=font(72, True), fill=rga(WH, 180))
    d.text((M, 155), "RONGCE", font=font(110, True), fill=WH)
    # Gold accent diamonds on brand bar
    for j in range(3):
        s2 = 15 - j*4; xd = W-300 + j*60; yd = 165
        pts2 = [(xd, yd-s2*2), (xd+s2, yd), (xd, yd+s2*2), (xd-s2, yd)]
        d.polygon(pts2, fill=rga(GD, 30-j*8))
    # Center statement
    draw(d, "谋专业之策", M+10, 460, font(64, True), WH, 700, 16)
    draw(d, "融品质之精", M+10, 540, font(64, True), WH, 700, 16)
    d.line([M+10, 640, M+410, 640], fill=rga(GD), width=5)
    draw(d, "政府审计与工程咨询综合服务机构", M+10, 680, font(32), rga(WH, 200), 700, 10)
    # Bottom bar
    d.rectangle([0, H-70, W, H], fill=rga(NW))
    tw0 = d.textlength("审计 \u00b7 绩效 \u00b7 财政监督 \u00b7 工程咨询 \u00b7 数字化分析", font=font(22))
    d.text(((W-tw0)//2, H-52), "审计 \u00b7 绩效 \u00b7 财政监督 \u00b7 工程咨询 \u00b7 数字化分析", font=font(22), fill=rga(WH, 180))
    # Corner accents
    d.line([W-100, 50, W-30, 50], fill=rga(GD, 80), width=3)
    d.line([W-30, 50, W-30, 120], fill=rga(GD, 80), width=3)
    d.polygon([(W-100, H-100), (W-40, H-100), (W-100, H-40)], fill=rga(GD, 20))
    d.polygon([(W-100, H-100), (W-55, H-100), (W-100, H-55)], fill=rga(GD, 35))
    return img'''

p1_start = text.find('def p1_cover():')
p2_start = text.find('\ndef p2_about():')
text = text[:p1_start] + new_p1 + text[p2_start:]

# New P6: cleaner cycle layout for budget performance
new_p6 = '''def p6_perf():
    img = Image.new("RGB", (W, H), rgb(WH))
    d = ImageDraw.Draw(img, "RGBA")
    left_bar(d)
    page_title(d, "预算绩效管理", "BUDGET PERFORMANCE")
    d.text((W-250, 0), "06", font=font(240, True), fill=rga(NW, 6))
    draw(d, "您关心的不只是"花了多少钱"，更是"效果怎么样"——让财政资金从"花了没有"走向"花得值不值"。", M, 240, font(30), MU, 650, 10)
    # Central circle
    cx, cy = M+380, 550
    d.ellipse([cx-90, cy-90, cx+90, cy+90], fill=rga(NW))
    d.ellipse([cx-85, cy-85, cx+85, cy+85], fill=rga(TL, 10))
    draw(d, "绩效管理", cx-d.textlength("绩效管理", font=font(32, True))//2, cy-20, font(32, True), NW, 200, 4, "center")
    draw(d, "PDCA闭环", cx-d.textlength("PDCA闭环", font=font(20))//2, cy+20, font(20), rga(NW, 150), 200, 0, "center")
    # Five nodes around
    import math
    nodes = [
        ("01", "事前评估", "必要性\u00b7可行性\n财政承受能力"),
        ("02", "目标审核", "完整性\u00b7可衡量\n绩效责任书"),
        ("03", "运行监控", "进度追踪\u00b7偏差预警\n资金支付监控"),
        ("04", "重点评价", "政策\u00b7部门\u00b7项目\n专项资金评价"),
        ("05", "结果应用", "整改清单\u00b7预算挂钩\n制度优化"),
    ]
    radius = 240
    for i, (num, name, desc) in enumerate(nodes):
        angle = -math.pi/2 + 2*math.pi*i/5
        nx = int(cx + radius*math.cos(angle))
        ny = int(cy + radius*math.sin(angle))
        bw, bh = 240, 90
        d.rounded_rectangle([nx-bw//2, ny-bh//2, nx+bw//2, ny+bh//2], radius=10, fill=WH, outline=rga(TL, 50), width=2)
        # Number circle
        d.ellipse([nx-bw//2+8, ny-14, nx-bw//2+44, ny+22], fill=rga(NW))
        d.text((nx-bw//2+20, ny-6), num, font=font(24, True), fill=WH)
        draw(d, name, nx-bw//2+56, ny-18, font(24, True), NW, 160, 4)
        draw(d, desc, nx-bw//2+56, ny+12, font(17), MU, 160, 2)
        # Line from center to node
        ex = int(cx + (radius-90)*math.cos(angle))
        ey = int(cy + (radius-90)*math.sin(angle))
        d.line([ex, ey, nx-int(bw//2*math.cos(angle)*0.6), ny-int(bh//2*math.sin(angle)*0.6)], fill=rga(GD, 40), width=2)
    # Description box
    d.rounded_rectangle([M, 820, W-M, 930], radius=14, fill=rga("#E8E0D4", 60))
    draw(d, "事前评估 → 目标审核 → 运行监控 → 重点评价 → 结果应用，每个环节交付核查清单+数据底稿+分析报告+整改建议。", M+40, 855, font(26), IK, 1300, 8, "center")
    d.line([M, H-65, W-M, H-65], fill=rga(TL, 20), width=2)
    bottom_bar(d)
    return img'''

p6_start = text.find('\ndef p6_perf():')
p7_start = text.find('\ndef p7_eng():')
text = text[:p6_start] + new_p6 + text[p7_start:]

Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v8.py').write_text(text, 'utf-8')
import py_compile
try:
    py_compile.compile(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v8.py', doraise=True)
    print('Syntax OK')
except Exception as e:
    print('FAIL:', e)
