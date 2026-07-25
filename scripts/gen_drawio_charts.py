#!/usr/bin/env python3
"""
Generate 5 professional draw.io diagrams for Rongce policy system.
Uses mxGraphModel XML format with premium styling.
"""
import os, math

OUT_DIR = r"C:\Users\scrccpa\.openclaw\workspace\output\新制度体系\charts"
os.makedirs(OUT_DIR, exist_ok=True)

# Brand colors
BLUE = "#0A1F3F"
TEAL = "#1A5C6E"
COPPER = "#C5955C"
WARM = "#F5F2EC"
WHITE = "#FFFFFF"
LIGHT_BLUE = "#E8EDF2"
DARK = "#2D2D2D"

def mxCell(id, value="", style="", parent="1", **attrs):
    """Generate mxCell XML element."""
    vertex_val = attrs.pop("vertex", "0")
    attr_str = f'id="{id}" value="{_escape(value)}" style="{style}" vertex="{vertex_val}" parent="{parent}"'
    for k, v in attrs.items():
        attr_str += f' {k}="{v}"'
    geo = ""
    if vertex_val == "1":
        x = attrs.get("x", 0)
        y = attrs.get("y", 0)
        w = attrs.get("w", 80)
        h = attrs.get("h", 30)
        geo = f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
    elif "source" in attrs:
        geo = '<mxGeometry relative="1" as="geometry"/>'
    return f'<mxCell {attr_str}>{geo}</mxCell>'

def _escape(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("\n", "&#xa;")

def box_style(fill, stroke=BLUE, font_color=WHITE, rounded="1", size="14", font_style="1"):
    return f"rounded={rounded};whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontColor={font_color};fontSize={size};fontStyle={font_style};arcSize=10;"

def header_bg(h):
    """Draw header background shape."""
    return mxCell(
        "bg", "", box_style(BLUE, BLUE, WHITE, "0", "1", "0"),
        "1", vertex="1", x=0, y=0, w=1920, h=str(h)
    )

def title_text(x, y, w, text, size="28"):
    return mxCell(
        f"t{text[:8]}", text, box_style("none", "none", WHITE, "0", size, "1"),
        "1", vertex="1", x=x, y=y, w=w, h=50
    )

def subtitle_text(x, y, w, text):
    return mxCell(
        f"s{text[:8]}", text, box_style("none", "none", COPPER, "0", "14", "0"),
        "1", vertex="1", x=x, y=y, w=w, h=30
    )

def footer_text(x, y, w, text):
    return mxCell(
        f"f{text[:8]}", text, box_style("none", "none", TEAL, "0", "11", "0"),
        "1", vertex="1", x=x, y=y, w=w, h=25
    )

def node(id, x, y, w, h, text, fill=TEAL, font_color=WHITE, size="12"):
    return mxCell(id, text, box_style(fill, fill, font_color, "1", size),
                  "1", vertex="1", x=x, y=y, w=w, h=h)

def sub_node(id, x, y, w, h, text, size="10"):
    return mxCell(id, text, box_style(LIGHT_BLUE, TEAL, DARK, "1", size),
                  "1", vertex="1", x=x, y=y, w=w, h=h)

def arrow_style(color=COPPER):
    return f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor={color};strokeWidth=2;endArrow=block;endFill=1;"

def arrow(id, src, tgt, label="", color=COPPER):
    s = arrow_style(color)
    if label:
        s += f"fontColor={color};fontSize=10;"
    return mxCell(id, label, s, parent="1", vertex="0", source=src, target=tgt, edge="1")


# ═══════════════ DIAGRAM 1: ARCHITECTURE OVERVIEW ═══════════════
def diagram_architecture():
    W, H = 1920, 1150
    cells = []
    
    # Background
    cells.append(mxCell("bg", "", box_style(WARM, WARM, DARK, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=H))
    
    # Header bar
    cells.append(mxCell("hdr", "", box_style(BLUE, BLUE, WHITE, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=100))
    
    # Title
    cells.append(title_text(60, 20, 1800, "四川融策公司制度体系", "32"))
    cells.append(subtitle_text(60, 65, 1800, "37项制度 · 7大类别 · 2026年7月22日发布"))
    
    # Root node
    rx, ry, rw, rh = 860, 130, 200, 50
    cells.append(node("root", rx, ry, rw, rh, "制度体系", BLUE, WHITE, "16"))
    
    # 7 categories
    cat_names = ["治理层", "人力资源", "财务管理", "业务运营", "质量控制", "行政综合", "专项管理"]
    cat_counts = ["4项", "7项", "6项", "7项", "4项", "5项", "4项"]
    cat_ids = ["RC-GOV", "RC-HR", "RC-FIN", "RC-BIZ", "RC-QC", "RC-ADM", "RC-SPL"]
    cat_colors = [BLUE, TEAL, "#2E7D32", "#E65100", "#6A1B9A", "#0277BD", "#C62828"]
    
    cat_w = 200
    start_x = 80
    gap = (W - start_x*2 - 7*cat_w) // 6
    cat_y = 240
    
    for i, (name, count, cid, color) in enumerate(zip(cat_names, cat_counts, cat_ids, cat_colors)):
        cx = start_x + i * (cat_w + gap)
        cells.append(node(f"cat{i}", cx, cat_y, cat_w, 45, f"{name}\n{count}", color, WHITE, "13"))
        cells.append(arrow(f"a{i}", "root", f"cat{i}", "", COPPER))
    
    # Sub-items under each category (policy names)
    policy_data = {
        0: [("公司章程", "#01,#02"), ("制度管理", "#05"), ("股东会", "#09")],
        1: [("薪酬制度", "#01"), ("绩效考核", "#02"), ("员工手册", "#03"), 
            ("招聘入职", "#04"), ("培训发展", "#05"), ("职级晋升", "#06"), ("高管考核", "#07")],
        2: [("财务报销", "#01"), ("收入回款", "#02"), ("预算管理", "#03"),
            ("资金管理", "#04"), ("固定资产", "#05"), ("利润核算", "#06")],
        3: [("项目管理", "#04"), ("业务承接", "#17"), ("客户关系", "#18"),
            ("分包管理", "#19"), ("投标管理", "#20"), ("项目分润", "#34"), ("跨部门协同", "#35")],
        4: [("审计质控", "#07"), ("造价质控", "#08"), ("三级复核", "#21"), ("责任追究", "#22")],
        5: [("信息安全", "#23"), ("印章证照", "#24"), ("档案管理", "#25"),
            ("办公管理", "#28"), ("采购管理", "#29")],
        6: [("数智化", "#30"), ("业务创新", "#31"), ("风险管理", "#32"), ("党建", "#33")],
    }
    
    sub_y = 310
    sub_h = 22
    sub_w = 170
    
    for cat_i, items in policy_data.items():
        cx = start_x + cat_i * (cat_w + gap) + (cat_w - sub_w) // 2
        for j, (name, num) in enumerate(items):
            sy = sub_y + j * (sub_h + 4)
            cells.append(sub_node(f"cat{cat_i}_s{j}", cx, sy, sub_w, sub_h, f"{name} {num}", "9"))
    
    # Footer
    cells.append(footer_text(60, H-35, 1800, "四川融策会计师事务所有限公司  |  四川融策工程咨询有限公司"))
    
    return cells


# ═══════════════ DIAGRAM 2: HR LIFECYCLE ═══════════════
def diagram_hr():
    W, H = 1920, 1000
    cells = []
    cells.append(mxCell("bg", "", box_style(WARM, WARM, DARK, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=H))
    cells.append(mxCell("hdr", "", box_style(BLUE, BLUE, WHITE, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=85))
    cells.append(title_text(60, 12, 1800, "人力资源管理全流程", "28"))
    cells.append(subtitle_text(60, 52, 1800, "从招聘到离职 · 8项制度覆盖全生命周期"))
    
    # Horizontal flow
    stages = [
        ("招聘入职", "RC-HR-004", TEAL),
        ("薪酬定级", "RC-HR-001", "#2E7D32"),
        ("绩效考核", "RC-HR-002", "#6A1B9A"),
        ("职级晋升", "RC-HR-006", "#E65100"),
        ("高管考核", "RC-HR-007", "#C62828"),
        ("培训发展", "RC-HR-005", "#0277BD"),
        ("离职管理", "RC-HR-003", "#455A64"),
    ]
    
    node_w, node_h = 200, 65
    total_w = len(stages) * node_w + (len(stages)-1) * 50
    start_x = (W - total_w) // 2
    center_y = 280
    
    for i, (name, code, color) in enumerate(stages):
        nx = start_x + i * (node_w + 50)
        cells.append(node(f"hr{i}", nx, center_y, node_w, node_h, f"{name}\n{code}", color, WHITE, "13"))
        if i > 0:
            cells.append(arrow(f"ah{i}", f"hr{i-1}", f"hr{i}", "", COPPER))
    
    # Sub-items below each stage
    sub_details = [
        ("发布→面试→入职", "RC-HR-004"),
        ("基本+岗位+绩效", "RC-HR-001"),
        ("月度预发·季度清算", "RC-HR-002"),
        ("能力评审→答辩→晋级", "RC-HR-006"),
        ("经营40·协同30·管理30", "RC-HR-007"),
        ("继续教育·内部分享", "RC-HR-005"),
        ("交接→结算→证明", "RC-HR-003"),
    ]
    
    for i, (detail, _) in enumerate(sub_details):
        nx = start_x + i * (node_w + 50)
        cells.append(sub_node(f"hr_s{i}", nx, center_y + 80, node_w, 30, detail, "9"))
    
    # Key metrics bar
    metrics = [
        "📋 试用期2-6月", "💰 保底2100元/月", "📊 A/B/C/D四档", "🏆 半年度评审",
        "🎯 系数0.5-1.5", "📚 继续教育100%", "✋ 提前30天通知"
    ]
    bar_y = 480
    bw = 220
    total_bw = len(metrics) * bw + (len(metrics)-1) * 15
    bx = (W - total_bw) // 2
    for i, m in enumerate(metrics):
        cells.append(sub_node(f"metric{i}", bx + i*(bw+15), bar_y, bw, 35, m, "10"))
    
    cells.append(footer_text(60, H-35, 1800, "四川融策会计师事务所有限公司  |  四川融策工程咨询有限公司"))
    return cells


# ═══════════════ DIAGRAM 3: FINANCE CYCLE ═══════════════
def diagram_finance():
    W, H = 1920, 950
    cells = []
    cells.append(mxCell("bg", "", box_style(WARM, WARM, DARK, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=H))
    cells.append(mxCell("hdr", "", box_style(BLUE, BLUE, WHITE, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=85))
    cells.append(title_text(60, 12, 1800, "财务管理闭环流程", "28"))
    cells.append(subtitle_text(60, 52, 1800, "6项制度 · 从预算到分润的完整资金链路"))
    
    # Circular flow
    cx, cy = 960, 430
    radius = 280
    stages = [
        ("费用报销", "RC-FIN-001", "#2E7D32"),
        ("预算管理", "RC-FIN-003", "#0277BD"),
        ("资金管理", "RC-FIN-004", "#6A1B9A"),
        ("固定资产", "RC-FIN-005", "#E65100"),
        ("收入回款", "RC-FIN-002", TEAL),
        ("利润核算", "RC-FIN-006", "#C62828"),
    ]
    
    n = len(stages)
    nw, nh = 180, 55
    for i, (name, code, color) in enumerate(stages):
        angle = -math.pi/2 + i * 2*math.pi/n
        nx = cx + radius * math.cos(angle) - nw/2
        ny = cy + radius * math.sin(angle) - nh/2
        cells.append(node(f"fin{i}", int(nx), int(ny), nw, nh, f"{name}\n{code}", color, WHITE, "12"))
    
    # Connecting arrows
    for i in range(n):
        ni = (i + 1) % n
        cells.append(arrow(f"fa{i}", f"fin{i}", f"fin{ni}", "", COPPER))
    
    # Center node (闭环强调)
    cells.append(mxCell("center", "", box_style(BLUE, BLUE, WHITE, "1", "1", "0"),
                        "1", vertex="1", x=cx-70, y=cy-35, w=140, h=70))
    cells.append(node("clabel", cx-55, cy-20, 110, 40, "资金闭环", BLUE, WHITE, "14"))
    
    # Bottom: key principles
    principles = [
        "审计公摊8% · 工程公摊12%",
        "里程碑预发40-50% · 回款后清算",
        "利润核算细则为统一计算基础"
    ]
    py = cy + radius + 60
    for i, p in enumerate(principles):
        cells.append(sub_node(f"princ{i}", 400, py + i*32, 1120, 28, p, "10"))
    
    cells.append(footer_text(60, H-35, 1800, "四川融策会计师事务所有限公司  |  四川融策工程咨询有限公司"))
    return cells


# ═══════════════ DIAGRAM 4: BUSINESS OPERATIONS ═══════════════
def diagram_business():
    W, H = 1920, 1000
    cells = []
    cells.append(mxCell("bg", "", box_style(WARM, WARM, DARK, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=H))
    cells.append(mxCell("hdr", "", box_style(BLUE, BLUE, WHITE, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=85))
    cells.append(title_text(60, 12, 1800, "业务运营与质量控制全流程", "28"))
    cells.append(subtitle_text(60, 52, 1800, "11项制度 · 从投标到回款到分润的业务全链路"))
    
    # Two-row flow
    row1 = [
        ("投标管理", "RC-BIZ-005", "#0277BD"),
        ("业务承接", "RC-BIZ-002", TEAL),
        ("合同管理", "RC-BIZ-002", "#2E7D32"),
        ("项目执行", "RC-BIZ-001", "#E65100"),
    ]
    row2 = [
        ("三级复核", "RC-QC-003", "#6A1B9A"),
        ("质控检查", "RC-QC-001", "#C62828"),
        ("客户评价", "RC-BIZ-003", "#455A64"),
        ("回款分润", "RC-BIZ-006", COPPER),
    ]
    
    r1_y = 160
    nw, nh = 210, 55
    gap = 30
    total_r1 = len(row1) * nw + (len(row1)-1) * gap
    start_x1 = (W - total_r1) // 2
    
    r2_y = 340
    total_r2 = len(row2) * nw + (len(row2)-1) * gap
    start_x2 = (W - total_r2) // 2
    
    for i, (name, code, color) in enumerate(row1):
        nx = start_x1 + i * (nw + gap)
        cells.append(node(f"biz1_{i}", nx, r1_y, nw, nh, f"{name}\n{code}", color, WHITE, "12"))
        if i > 0:
            cells.append(arrow(f"ab1_{i}", f"biz1_{i-1}", f"biz1_{i}", "", COPPER))
    
    for i, (name, code, color) in enumerate(row2):
        nx = start_x2 + i * (nw + gap)
        cells.append(node(f"biz2_{i}", nx, r2_y, nw, nh, f"{name}\n{code}", color, WHITE, "12"))
        if i > 0:
            cells.append(arrow(f"ab2_{i}", f"biz2_{i-1}", f"biz2_{i}", "", COPPER))
    
    # Connect row1→row2
    cells.append(arrow("r1r2", "biz1_3", "biz2_0", "交付复核", TEAL))
    
    # Support layer
    support = [
        ("客户关系管理", "RC-BIZ-003"),
        ("分包管理", "RC-BIZ-004"),
        ("跨部门协同", "RC-BIZ-007"),
        ("责任追究", "RC-QC-004"),
    ]
    sy = 490
    sw = 200
    total_sw = len(support) * sw + (len(support)-1) * 20
    sx = (W - total_sw) // 2
    for i, (name, code) in enumerate(support):
        cells.append(sub_node(f"sup{i}", sx + i*(sw+20), sy, sw, 32, f"{name} {code}", "10"))
    
    cells.append(footer_text(60, H-35, 1800, "四川融策会计师事务所有限公司  |  四川融策工程咨询有限公司"))
    return cells


# ═══════════════ DIAGRAM 5: ADMIN SUPPORT ═══════════════
def diagram_admin():
    W, H = 1920, 980
    cells = []
    cells.append(mxCell("bg", "", box_style(WARM, WARM, DARK, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=H))
    cells.append(mxCell("hdr", "", box_style(BLUE, BLUE, WHITE, "0", "1", "0"),
                        "1", vertex="1", x=0, y=0, w=W, h=85))
    cells.append(title_text(60, 12, 1800, "行政综合支撑体系", "28"))
    cells.append(subtitle_text(60, 52, 1800, "12项制度 · 保障公司日常运营与管理规范"))
    
    # Center node
    cx, cy = 960, 520
    cells.append(node("admin_c", cx-80, cy-35, 160, 70, "行政综合\n管理体系", BLUE, WHITE, "14"))
    
    # Surrounding nodes in two rings
    ring1 = [
        ("制度发布管理", "RC-GOV-001"),
        ("信息安全", "RC-ADM-001"),
        ("印章证照", "RC-ADM-002"),
        ("档案管理", "RC-ADM-003"),
    ]
    ring2 = [
        ("公司章程", "RC-GOV-002/003"),
        ("办公管理", "RC-ADM-004"),
        ("采购管理", "RC-ADM-005"),
        ("数智化建设", "RC-SPL-001"),
        ("业务创新", "RC-SPL-002"),
        ("风险管理", "RC-SPL-003"),
        ("党建工作", "RC-SPL-004"),
    ]
    
    r1, r2 = 200, 380
    nw1, nh1 = 170, 50
    n = len(ring1)
    for i, (name, code) in enumerate(ring1):
        angle = -math.pi/2 + i * 2*math.pi/n
        nx = cx + r1 * math.cos(angle) - nw1/2
        ny = cy + r1 * math.sin(angle) - nh1/2
        cells.append(node(f"a1_{i}", int(nx), int(ny), nw1, nh1, f"{name}\n{code}", TEAL, WHITE, "11"))
        cells.append(arrow(f"aa1_{i}", "admin_c", f"a1_{i}", "", COPPER))
    
    nw2, nh2 = 170, 45
    n2 = len(ring2)
    for i, (name, code) in enumerate(ring2):
        angle = -math.pi/2 + i * 2*math.pi/n2
        nx = cx + r2 * math.cos(angle) - nw2/2
        ny = cy + r2 * math.sin(angle) - nh2/2
        cells.append(node(f"a2_{i}", int(nx), int(ny), nw2, nh2, f"{name}\n{code}", LIGHT_BLUE.replace("#",""), DARK, "10"))
        cells.append(arrow(f"aa2_{i}", "admin_c", f"a2_{i}", "", COPPER))
    
    cells.append(footer_text(60, H-35, 1800, "四川融策会计师事务所有限公司  |  四川融策工程咨询有限公司"))
    return cells


# ─── Build XML ───
def build_xml(diagram_name, cells):
    """Wrap cells in mxGraphModel XML."""
    cell_lines = "\n".join(cells)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1920" dy="1150" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1920" pageHeight="1150" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    {cell_lines}
  </root>
</mxGraphModel>'''

diagrams = [
    ("00-architecture", diagram_architecture()),
    ("01-hr-flow", diagram_hr()),
    ("02-fin-flow", diagram_finance()),
    ("03-biz-qc-flow", diagram_business()),
    ("04-admin-flow", diagram_admin()),
]

for name, cells in diagrams:
    xml = build_xml(name, cells)
    fpath = os.path.join(OUT_DIR, name + ".drawio")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  → {name}.drawio")

print(f"\n5 draw.io files written to {OUT_DIR}")
