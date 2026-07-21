# -*- coding: utf-8 -*-
"""
融策·券商风图表渲染引擎 (Securities-Style Chart Engine)
======================================================
一键生成顶级券商研报风格的图表（折线图/柱状图/面积图/双轴图/表格）。
特色：极简坐标系、融策品牌配色、资料来源脚注、数据标签克制。

用法:
    python securities_chart.py line --data data.json --out chart.png
    python securities_chart.py bar --data data.json --out chart.png
    python securities_chart.py area --data data.json --out chart.png
    python securities_chart.py dual --data data.json --out chart.png
    python securities_chart.py table --data data.json --out table.png
    python securities_chart.py demo --out demo/   # 生成所有示例

数据格式 (JSON):
{
    "title": "图1：2020-2025年全国一般公共预算收入（亿元）",
    "source": "财政部，融策会计师事务所",
    "x": ["2020", "2021", "2022", "2023", "2024", "2025E"],
    "series": [
        {"name": "中央收入", "data": [...], "color": "#0A1F3F"},
        {"name": "地方收入", "data": [...], "color": "#1A5C6E"}
    ],
    "highlight": {"series": "地方收入", "points": [4], "label": "峰值"},
    "annotations": [{"x": 3, "y": 105000, "text": "疫情后反弹", "dx": 20, "dy": -15}]
}

Author: 融策右护卫 (OpenClaw AI)
Date: 2026-07-21
"""

import sys, os, json, argparse
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

# ============================================================
# 融策品牌色 & 券商风主题常量
# ============================================================

COLORS = {
    'deep_blue':   '#0A1F3F',   # 融策深蓝 — 主色
    'teal':        '#1A5C6E',   # 融策青绿 — 副色
    'copper_gold': '#C5955C',   # 融策铜金 — 强调色
    'warm_gray':   '#F5F2EC',   # 融策暖灰 — 底色
    'dark_gray':   '#4A4A4A',   # 深灰 — 正文
    'mid_gray':    '#9B9B9B',   # 中灰 — 网格线/轴线
    'light_gray':  '#E8E8E8',   # 浅灰 — 表头底纹
    'bg_white':    '#FFFFFF',   # 纯白 — 图表背景
    'red_accent':  '#C0392B',   # 红色强调（涨/正）
    'green_accent':'#27AE60',   # 绿色强调（跌/负）
}

# 券商研报经典色板（多系列自动配色）
PALETTE_SECURITIES = [
    '#0A1F3F',   # 深蓝
    '#C5955C',   # 铜金
    '#1A5C6E',   # 青绿
    '#E74C3C',   # 红
    '#3498DB',   # 亮蓝
    '#2ECC71',   # 绿
    '#9B59B6',   # 紫
    '#F39C12',   # 橙
    '#1ABC9C',   # 青
    '#E67E22',   # 深橙
]

# ============================================================
# 全局样式设置
# ============================================================

def setup_mpl():
    """设置matplotlib全局参数为券商研报风格"""
    plt.rcParams.update({
        'font.family': ['Microsoft YaHei', 'SimHei', 'sans-serif'],
        'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
        'axes.unicode_minus': False,
        'figure.dpi': 150,
        'savefig.dpi': 150,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.3,
        'axes.edgecolor': COLORS['mid_gray'],
        'axes.linewidth': 0.6,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.color': COLORS['mid_gray'],
        'grid.linestyle': '--',
        'grid.linewidth': 0.5,
        'xtick.color': COLORS['dark_gray'],
        'ytick.color': COLORS['dark_gray'],
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'axes.labelsize': 9,
        'axes.titlesize': 11,
        'legend.fontsize': 8,
        'legend.frameon': False,
    })


def apply_securities_style(ax):
    """对单个Axes应用券商风极简样式"""
    # 去掉顶部和右侧边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # 弱化左边和底部边框
    ax.spines['left'].set_color(COLORS['mid_gray'])
    ax.spines['left'].set_linewidth(0.6)
    ax.spines['bottom'].set_color(COLORS['mid_gray'])
    ax.spines['bottom'].set_linewidth(0.6)
    # 浅色背景
    ax.set_facecolor(COLORS['bg_white'])


def add_source_footer(fig, source_text, y_position=0.02):
    """在图表底部添加资料来源脚注（券商研报的灵魂）"""
    fig.text(
        0.12, y_position,
        f'资料来源：{source_text}',
        fontsize=7,
        color=COLORS['mid_gray'],
        ha='left', va='bottom',
        style='italic'
    )


# ============================================================
# 图表类型实现
# ============================================================

def chart_line(data, output_path, width=8, height=4.5):
    """折线图 — 券商最常用的趋势图"""
    setup_mpl()
    fig, ax = plt.subplots(figsize=(width, height))
    apply_securities_style(ax)

    x = data.get('x', [])
    x_pos = range(len(x))
    series_list = data.get('series', [])
    title = data.get('title', '')
    source = data.get('source', '')
    annotations = data.get('annotations', [])

    for i, s in enumerate(series_list):
        color = s.get('color', PALETTE_SECURITIES[i % len(PALETTE_SECURITIES)])
        values = s.get('data', [])
        name = s.get('name', f'Series {i+1}')

        line, = ax.plot(x_pos, values, color=color, linewidth=1.8,
                        marker='o', markersize=5, markerfacecolor='white',
                        markeredgewidth=1.5, markeredgecolor=color,
                        label=name, zorder=3)

    # X轴标签
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x, rotation=0, fontsize=8)
    ax.set_xlim(-0.5, len(x) - 0.5)

    # Y轴格式化
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f'{v:,.0f}' if v >= 1000 else f'{v:.1f}'
    ))

    # 标题
    ax.set_title(title, fontsize=11, fontweight='bold',
                 color=COLORS['deep_blue'], pad=12, loc='left')

    # 图例
    if len(series_list) > 1:
        ax.legend(loc='upper left', frameon=False, ncol=len(series_list))

    # 标注
    for ann in annotations:
        ax.annotate(ann.get('text', ''), xy=(ann['x'], ann['y']),
                    xytext=(ann.get('dx', 10), ann.get('dy', -10)),
                    textcoords='offset points', fontsize=7,
                    color=COLORS['copper_gold'],
                    arrowprops=dict(arrowstyle='->', color=COLORS['copper_gold'], lw=0.8))

    add_source_footer(fig, source)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(output_path, facecolor='white')
    plt.close(fig)
    print(f'✅ 折线图已保存: {output_path}')


def chart_bar(data, output_path, width=8, height=4.5):
    """柱状图 — 对比分析"""
    setup_mpl()
    fig, ax = plt.subplots(figsize=(width, height))
    apply_securities_style(ax)

    x = data.get('x', [])
    series_list = data.get('series', [])
    title = data.get('title', '')
    source = data.get('source', '')

    n_series = len(series_list)
    n_x = len(x)
    bar_width = 0.7 / n_series if n_series > 1 else 0.45
    x_pos = np.arange(n_x)
    x_offsets = np.linspace(-bar_width * (n_series - 1) / 2,
                            bar_width * (n_series - 1) / 2,
                            max(n_series, 1))

    for i, s in enumerate(series_list):
        color = s.get('color', PALETTE_SECURITIES[i % len(PALETTE_SECURITIES)])
        values = s.get('data', [])
        name = s.get('name', f'Series {i+1}')
        offset = x_offsets[i] if n_series > 1 else 0

        bars = ax.bar(x_pos + offset, values, bar_width * 0.9,
                      color=color, alpha=0.88, label=name, edgecolor='white',
                      linewidth=0.5, zorder=3)

        # 数据标签（仅标最大值和最小值）
        if len(values) > 3:
            vmax, vmin = max(values), min(values)
            for bar, v in zip(bars, values):
                if v == vmax or v == vmin:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            f'{v:,.0f}' if v >= 100 else f'{v:.1f}',
                            ha='center', va='bottom', fontsize=7,
                            color=COLORS['dark_gray'], fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x, rotation=0, fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f'{v:,.0f}' if v >= 1000 else f'{v:.1f}'
    ))
    ax.set_title(title, fontsize=11, fontweight='bold',
                 color=COLORS['deep_blue'], pad=12, loc='left')

    if n_series > 1:
        ax.legend(loc='upper right', frameon=False, ncol=n_series)

    add_source_footer(fig, source)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(output_path, facecolor='white')
    plt.close(fig)
    print(f'✅ 柱状图已保存: {output_path}')


def chart_area(data, output_path, width=8, height=4.5):
    """面积图 — 占比变化 / 时序累积"""
    setup_mpl()
    fig, ax = plt.subplots(figsize=(width, height))
    apply_securities_style(ax)

    x = data.get('x', [])
    x_pos = range(len(x))
    series_list = data.get('series', [])
    title = data.get('title', '')
    source = data.get('source', '')

    for i, s in enumerate(series_list):
        color = s.get('color', PALETTE_SECURITIES[i % len(PALETTE_SECURITIES)])
        values = s.get('data', [])
        name = s.get('name', f'Series {i+1}')
        stacked = data.get('stacked', False)

        alpha = 0.3 if not stacked else 0.5 + i * 0.1
        ax.fill_between(x_pos, values, alpha=alpha, color=color,
                        label=name, linewidth=0)
        ax.plot(x_pos, values, color=color, linewidth=1.5, markersize=0)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x, fontsize=8)
    ax.set_xlim(-0.2, len(x) - 0.8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f'{v:,.0f}' if v >= 1000 else f'{v:.1f}'
    ))
    ax.set_title(title, fontsize=11, fontweight='bold',
                 color=COLORS['deep_blue'], pad=12, loc='left')

    if len(series_list) > 1:
        ax.legend(loc='upper left', frameon=False, ncol=min(len(series_list), 3))

    add_source_footer(fig, source)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(output_path, facecolor='white')
    plt.close(fig)
    print(f'✅ 面积图已保存: {output_path}')


def chart_dual(data, output_path, width=8, height=4.5):
    """双轴图 — 两个不同量纲指标叠加（如收入+增速）"""
    setup_mpl()
    fig, ax1 = plt.subplots(figsize=(width, height))
    apply_securities_style(ax1)

    x = data.get('x', [])
    x_pos = range(len(x))
    title = data.get('title', '')
    source = data.get('source', '')

    # 左轴（柱状图/折线）
    left_series = data.get('left_axis', data.get('series', [{}])[0] if data.get('series') else {})
    left_data = left_series.get('data', [])
    left_name = left_series.get('name', '左轴')
    left_color = left_series.get('color', COLORS['deep_blue'])
    left_type = left_series.get('type', 'bar')

    if left_type == 'bar':
        ax1.bar(x_pos, left_data, color=left_color, alpha=0.85, width=0.55,
                label=left_name, zorder=3, edgecolor='white', linewidth=0.5)
    else:
        ax1.plot(x_pos, left_data, color=left_color, linewidth=1.8,
                 marker='o', markersize=5, markerfacecolor='white',
                 markeredgewidth=1.5, markeredgecolor=left_color,
                 label=left_name, zorder=3)

    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f'{v:,.0f}' if v >= 1000 else f'{v:.1f}'
    ))
    ax1.tick_params(axis='y', labelcolor=left_color)

    # 右轴（折线）
    ax2 = ax1.twinx()
    right_series = data.get('right_axis', data.get('series', [{}, {}])[1] if len(data.get('series', [])) > 1 else {})
    right_data = right_series.get('data', [])
    right_name = right_series.get('name', '右轴')
    right_color = right_series.get('color', COLORS['copper_gold'])

    ax2.plot(x_pos, right_data, color=right_color, linewidth=1.8,
             marker='s', markersize=4, markerfacecolor='white',
             markeredgewidth=1.3, markeredgecolor=right_color,
             label=right_name, zorder=3, linestyle='--')
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f'{v:.1f}%' if abs(v) < 100 else f'{v:,.0f}'
    ))
    ax2.tick_params(axis='y', labelcolor=right_color)
    ax2.spines['right'].set_color(right_color)
    ax2.spines['right'].set_linewidth(0.8)
    ax2.spines['top'].set_visible(False)

    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(x, fontsize=8)
    ax1.set_title(title, fontsize=11, fontweight='bold',
                  color=COLORS['deep_blue'], pad=12, loc='left')

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc='upper left', frameon=False, ncol=2)

    add_source_footer(fig, source)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(output_path, facecolor='white')
    plt.close(fig)
    print(f'✅ 双轴图已保存: {output_path}')


def chart_table(data, output_path, width=8, height=None):
    """三线表 — 券商经典数据表"""
    setup_mpl()

    headers = data.get('headers', [])
    rows = data.get('rows', [])
    title = data.get('title', '')
    source = data.get('source', '')
    col_widths = data.get('col_widths', None)

    n_rows = len(rows) + 1  # +1 for header
    n_cols = len(headers)

    if height is None:
        height = max(2.5, n_rows * 0.4 + 1.5)

    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis('off')

    # 表格
    cell_text = []
    for row in rows:
        cell_text.append([str(v) for v in row])

    table = ax.table(
        cellText=cell_text,
        colLabels=headers,
        cellLoc='center',
        loc='center',
        colWidths=col_widths,
        edges='horizontal'  # 只画水平线
    )

    # 样式设置
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.6)

    for key, cell in table.get_celld().items():
        cell.set_edgecolor(COLORS['mid_gray'])
        cell.set_linewidth(0.4)
        cell.set_facecolor('white')

        # 表头行
        if key[0] == 0:
            cell.set_facecolor(COLORS['deep_blue'])
            cell.set_text_props(color='white', fontweight='bold', fontsize=8.5)
            cell.set_edgecolor(COLORS['deep_blue'])
            cell.set_linewidth(1.2)
        else:
            cell.set_text_props(color=COLORS['dark_gray'], fontsize=8)
            # 交替行底色
            if key[0] % 2 == 0:
                cell.set_facecolor('#F8F9FA')

    # 顶线和底线加粗
    for key, cell in table.get_celld().items():
        if key[0] == 0 or key[0] == len(rows):
            cell.set_linewidth(1.2)

    # 标题
    ax.set_title(title, fontsize=11, fontweight='bold',
                 color=COLORS['deep_blue'], pad=20, loc='left')

    add_source_footer(fig, source, y_position=0.04)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(output_path, facecolor='white')
    plt.close(fig)
    print(f'✅ 三线表已保存: {output_path}')


# ============================================================
# 批量导入模式（从 Excel/CSV 直接生成图表）
# ============================================================

def from_csv(filepath, chart_type='line', output_path=None):
    """从CSV文件直接生成图表（第1列=X轴，其他列=数据系列）"""
    import csv
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    x = [r[0] for r in rows]
    series = []
    for i, h in enumerate(headers[1:], 1):
        values = [float(r[i]) if r[i] else 0 for r in rows]
        series.append({
            'name': h,
            'data': values,
            'color': PALETTE_SECURITIES[(i - 1) % len(PALETTE_SECURITIES)]
        })

    data = {
        'title': f'图：{Path(filepath).stem}',
        'source': '融策会计师事务所',
        'x': x,
        'series': series
    }

    if output_path is None:
        output_path = str(Path(filepath).with_suffix('.png'))

    chart_map = {'line': chart_line, 'bar': chart_bar, 'area': chart_area}
    chart_map.get(chart_type, chart_line)(data, output_path)
    return output_path


# ============================================================
# 演示数据
# ============================================================

DEMO_DIR = Path(__file__).parent.parent / 'output' / 'charts_demo'

def generate_demos(out_dir=None):
    """生成所有图表类型的券商风示例"""
    if out_dir is None:
        out_dir = DEMO_DIR
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- 1. 折线图：财政收入趋势 ----
    chart_line({
        'title': '图1：2020-2025年全国一般公共预算收入（亿元）',
        'source': '财政部，融策会计师事务所',
        'x': ['2020', '2021', '2022', '2023', '2024', '2025E'],
        'series': [
            {'name': '一般公共预算收入', 'data': [182895, 202539, 203703, 216784, 220000, 228000],
             'color': COLORS['deep_blue']},
            {'name': '其中：税收收入', 'data': [154310, 172731, 166614, 181129, 182000, 190000],
             'color': COLORS['copper_gold']},
        ],
        'annotations': [
            {'x': 2, 'y': 166614, 'text': '留抵退税政策影响', 'dx': 15, 'dy': -25},
        ]
    }, str(out_dir / '01_line_revenue.png'))

    # ---- 2. 柱状图：审计项目类型对比 ----
    chart_bar({
        'title': '图2：2025年度审计项目类型分布（个）',
        'source': '融策会计师事务所',
        'x': ['绩效评价', '经责审计', '工程竣工\n决算', '专项审计', '资产清查', '预算执行'],
        'series': [
            {'name': '融策承接', 'data': [45, 32, 28, 25, 20, 18],
             'color': COLORS['deep_blue']},
            {'name': '行业平均', 'data': [38, 35, 22, 30, 25, 22],
             'color': COLORS['mid_gray']},
        ]
    }, str(out_dir / '02_bar_projects.png'))

    # ---- 3. 面积图：专项债发行趋势 ----
    chart_area({
        'title': '图3：2020-2024年全国新增专项债券发行规模（亿元）',
        'source': '财政部，融策会计师事务所',
        'x': ['2020', '2021', '2022', '2023', '2024'],
        'series': [
            {'name': '新增专项债', 'data': [37500, 35800, 36500, 38000, 39000],
             'color': COLORS['deep_blue']},
        ]
    }, str(out_dir / '03_area_bonds.png'))

    # ---- 4. 双轴图：收入+增速 ----
    chart_dual({
        'title': '图4：某区县财政收入及同比增速',
        'source': '财政局决算报表，融策会计师事务所',
        'x': ['2019', '2020', '2021', '2022', '2023', '2024'],
        'left_axis': {
            'name': '财政收入（亿元）', 'type': 'bar',
            'data': [32.5, 28.3, 35.1, 33.8, 38.2, 42.1],
            'color': COLORS['deep_blue']
        },
        'right_axis': {
            'name': '同比增速（%）',
            'data': [8.3, -12.9, 24.0, -3.7, 13.0, 10.2],
            'color': COLORS['copper_gold']
        },
    }, str(out_dir / '04_dual_axis.png'))

    # ---- 5. 三线表：绩效评价得分 ----
    chart_table({
        'title': '表1：2024年度部门整体支出绩效评价得分汇总',
        'source': '融策会计师事务所',
        'headers': ['单位', '预算执行\n(30分)', '产出指标\n(30分)', '效益指标\n(25分)', '满意度\n(15分)', '总分'],
        'rows': [
            ['A局', '28.5', '27.2', '22.8', '13.5', '92.0'],
            ['B局', '26.8', '25.1', '21.3', '12.0', '85.2'],
            ['C局', '29.1', '28.0', '23.5', '14.2', '94.8'],
            ['D局', '24.3', '22.5', '19.8', '11.5', '78.1'],
            ['E局', '27.0', '26.8', '22.0', '13.8', '89.6'],
        ]
    }, str(out_dir / '05_table_scores.png'))

    print(f'\n🎉 全部示例已生成到: {out_dir}')
    return out_dir


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='融策·券商风图表渲染引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python securities_chart.py demo --out ./charts/
  python securities_chart.py line --data data.json --out chart.png
  python securities_chart.py from-csv --file data.csv --type bar
        '''
    )
    sub = parser.add_subparsers(dest='command')

    # demo
    p_demo = sub.add_parser('demo', help='生成全部示例图表')
    p_demo.add_argument('--out', default=str(DEMO_DIR), help='输出目录')

    # line
    p_line = sub.add_parser('line', help='折线图')
    p_line.add_argument('--data', required=True, help='JSON数据文件')
    p_line.add_argument('--out', required=True, help='输出PNG路径')

    # bar
    p_bar = sub.add_parser('bar', help='柱状图')
    p_bar.add_argument('--data', required=True, help='JSON数据文件')
    p_bar.add_argument('--out', required=True, help='输出PNG路径')

    # area
    p_area = sub.add_parser('area', help='面积图')
    p_area.add_argument('--data', required=True, help='JSON数据文件')
    p_area.add_argument('--out', required=True, help='输出PNG路径')

    # dual
    p_dual = sub.add_parser('dual', help='双轴图')
    p_dual.add_argument('--data', required=True, help='JSON数据文件')
    p_dual.add_argument('--out', required=True, help='输出PNG路径')

    # table
    p_tab = sub.add_parser('table', help='三线表')
    p_tab.add_argument('--data', required=True, help='JSON数据文件')
    p_tab.add_argument('--out', required=True, help='输出PNG路径')

    # from-csv
    p_csv = sub.add_parser('from-csv', help='从CSV生成图表')
    p_csv.add_argument('--file', required=True, help='CSV文件路径')
    p_csv.add_argument('--type', default='line', choices=['line', 'bar', 'area'])
    p_csv.add_argument('--out', default=None, help='输出路径')

    args = parser.parse_args()

    if args.command == 'demo':
        generate_demos(args.out)
    elif args.command == 'line':
        with open(args.data, 'r', encoding='utf-8') as f:
            chart_line(json.load(f), args.out)
    elif args.command == 'bar':
        with open(args.data, 'r', encoding='utf-8') as f:
            chart_bar(json.load(f), args.out)
    elif args.command == 'area':
        with open(args.data, 'r', encoding='utf-8') as f:
            chart_area(json.load(f), args.out)
    elif args.command == 'dual':
        with open(args.data, 'r', encoding='utf-8') as f:
            chart_dual(json.load(f), args.out)
    elif args.command == 'table':
        with open(args.data, 'r', encoding='utf-8') as f:
            chart_table(json.load(f), args.out)
    elif args.command == 'from-csv':
        from_csv(args.file, args.type, args.out)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
