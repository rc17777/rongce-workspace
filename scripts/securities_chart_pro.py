# -*- coding: utf-8 -*-
"""
融策·专业研报图文模块生成器 v1.0
================================
生成更接近券商深度报告的信息饱和型高清图表：
- 300DPI高清输出
- 稳重深色系 + 铜金强调
- 图表自带结论标题、关键指标条、分析注释、资料来源
- 适合直接插入Word/PPT研报正文

用法：
    python -X utf8 scripts/securities_chart_pro.py demo --out output/charts_pro
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D

# 稳重研报色系：深海军蓝 + 石墨灰 + 铜金 + 冷青
COLORS = {
    'navy': '#061A33',
    'navy2': '#0A2A4A',
    'ink': '#1F2933',
    'gray': '#53616D',
    'muted': '#8793A0',
    'grid': '#D9DEE5',
    'paper': '#FFFFFF',
    'panel': '#F4F6F8',
    'gold': '#B88A44',
    'gold2': '#D6B071',
    'teal': '#1A6F78',
    'blue': '#2E6E9E',
    'red': '#B8403A',
    'green': '#2B7A55',
}

PALETTE = [COLORS['navy'], COLORS['gold'], COLORS['teal'], COLORS['blue'], COLORS['red'], COLORS['green']]


def setup():
    plt.rcParams.update({
        'font.family': ['Microsoft YaHei', 'SimHei', 'sans-serif'],
        'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
        'axes.unicode_minus': False,
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.12,
        'axes.linewidth': 0.8,
    })


def fmt_num(v):
    if abs(v) >= 10000:
        return f'{v/10000:.1f}万'
    if abs(v) >= 1000:
        return f'{v:,.0f}'
    if abs(v) >= 100:
        return f'{v:.0f}'
    return f'{v:.1f}'


def add_header(fig, title, subtitle='', tag='融策·审盾研究'):
    fig.patches.append(Rectangle((0.0, 0.92), 1.0, 0.08, transform=fig.transFigure,
                                 facecolor=COLORS['navy'], edgecolor='none', zorder=-1))
    fig.patches.append(Rectangle((0.0, 0.905), 1.0, 0.015, transform=fig.transFigure,
                                 facecolor=COLORS['gold'], edgecolor='none', zorder=-1))
    fig.text(0.035, 0.963, tag, ha='left', va='center', fontsize=9, color=COLORS['gold2'], fontweight='bold')
    fig.text(0.035, 0.936, title, ha='left', va='center', fontsize=17, color='white', fontweight='bold')
    if subtitle:
        fig.text(0.985, 0.936, subtitle, ha='right', va='center', fontsize=9, color='#C9D2DC')


def add_kpis(fig, kpis):
    if not kpis:
        return
    left, y, width, height = 0.035, 0.80, 0.93, 0.085
    n = len(kpis)
    gap = 0.012
    box_w = (width - gap * (n - 1)) / n
    for i, item in enumerate(kpis):
        x = left + i * (box_w + gap)
        fig.patches.append(FancyBboxPatch((x, y), box_w, height,
                          boxstyle='round,pad=0.006,rounding_size=0.006',
                          transform=fig.transFigure, facecolor=COLORS['panel'],
                          edgecolor='#D5DBE3', linewidth=0.8))
        fig.text(x + 0.012, y + 0.057, item.get('label', ''), ha='left', va='center',
                 fontsize=8, color=COLORS['gray'])
        fig.text(x + 0.012, y + 0.026, item.get('value', ''), ha='left', va='center',
                 fontsize=15, color=item.get('color', COLORS['navy']), fontweight='bold')


def add_note_panel(fig, notes, title='核心判断'):
    if not notes:
        return
    x, y, w, h = 0.66, 0.17, 0.305, 0.57
    fig.patches.append(FancyBboxPatch((x, y), w, h,
                      boxstyle='round,pad=0.008,rounding_size=0.006',
                      transform=fig.transFigure, facecolor='#FAFBFC',
                      edgecolor='#CDD5DF', linewidth=0.8))
    fig.patches.append(Rectangle((x, y + h - 0.045), w, 0.045, transform=fig.transFigure,
                                 facecolor=COLORS['navy2'], edgecolor='none'))
    fig.text(x + 0.018, y + h - 0.022, title, ha='left', va='center', fontsize=10,
             color='white', fontweight='bold')
    yy = y + h - 0.085
    for i, note in enumerate(notes, 1):
        fig.text(x + 0.018, yy, f'{i}.', ha='left', va='top', fontsize=9,
                 color=COLORS['gold'], fontweight='bold')
        fig.text(x + 0.045, yy, note, ha='left', va='top', fontsize=9,
                 color=COLORS['ink'], linespacing=1.45, wrap=True)
        yy -= 0.105


def style_axis(ax):
    ax.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#AEB7C2')
    ax.spines['bottom'].set_color('#AEB7C2')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.grid(axis='y', color=COLORS['grid'], linestyle='-', linewidth=0.7, alpha=0.85)
    ax.grid(axis='x', visible=False)
    ax.tick_params(axis='both', labelsize=9, colors=COLORS['gray'], length=0)


def add_source(fig, source, date='2026-07-21'):
    fig.text(0.035, 0.045, f'资料来源：{source}', ha='left', va='center', fontsize=7.5,
             color=COLORS['muted'])
    fig.text(0.965, 0.045, f'制图：融策AI审计中台 | {date}', ha='right', va='center', fontsize=7.5,
             color=COLORS['muted'])


def pro_line(data, out):
    setup()
    fig = plt.figure(figsize=(12.5, 7.2), facecolor='white')
    add_header(fig, data['title'], data.get('subtitle', ''))
    add_kpis(fig, data.get('kpis', []))
    add_note_panel(fig, data.get('notes', []))
    add_source(fig, data.get('source', '融策会计师事务所'))

    ax = fig.add_axes([0.07, 0.18, 0.55, 0.55])
    style_axis(ax)
    x = np.arange(len(data['x']))
    for i, s in enumerate(data['series']):
        color = s.get('color', PALETTE[i % len(PALETTE)])
        y = np.array(s['data'], dtype=float)
        ax.plot(x, y, color=color, linewidth=2.6, marker='o', markersize=6.5,
                markerfacecolor='white', markeredgewidth=2, label=s['name'], zorder=5)
        # 最后一个点标注
        ax.text(x[-1] + 0.08, y[-1], fmt_num(y[-1]), fontsize=9, color=color,
                fontweight='bold', va='center')
        # 极值点标注
        idx_max = int(np.argmax(y))
        ax.scatter([idx_max], [y[idx_max]], s=78, color=color, edgecolor='white', linewidth=1.2, zorder=6)
        ax.text(idx_max, y[idx_max] * 1.015, fmt_num(y[idx_max]), fontsize=8,
                color=color, ha='center', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(data['x'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_num(v)))
    ax.set_title(data.get('chart_title', ''), loc='left', fontsize=11, color=COLORS['ink'], fontweight='bold', pad=12)
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.02), frameon=False, fontsize=9, ncol=2)

    # 关键事件标注
    for ev in data.get('events', []):
        ax.axvline(ev['x'], color=COLORS['gold'], linewidth=1.2, linestyle='--', alpha=0.7)
        ax.text(ev['x'] + 0.04, ax.get_ylim()[1] * 0.92, ev['text'], fontsize=8,
                color=COLORS['gold'], ha='left', va='top')

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor='white')
    plt.close(fig)
    print(f'✅ 专业折线图已保存: {out}')


def pro_bar(data, out):
    setup()
    fig = plt.figure(figsize=(12.5, 7.2), facecolor='white')
    add_header(fig, data['title'], data.get('subtitle', ''))
    add_kpis(fig, data.get('kpis', []))
    add_note_panel(fig, data.get('notes', []))
    add_source(fig, data.get('source', '融策会计师事务所'))

    ax = fig.add_axes([0.07, 0.18, 0.55, 0.55])
    style_axis(ax)
    x = np.arange(len(data['x']))
    n = len(data['series'])
    width = min(0.28, 0.72 / n)
    offsets = np.linspace(-width * (n - 1) / 2, width * (n - 1) / 2, n)

    for i, s in enumerate(data['series']):
        color = s.get('color', PALETTE[i % len(PALETTE)])
        y = np.array(s['data'], dtype=float)
        bars = ax.bar(x + offsets[i], y, width=width * 0.92, color=color, alpha=0.92,
                      edgecolor='white', linewidth=0.8, label=s['name'], zorder=4)
        for b, v in zip(bars, y):
            ax.text(b.get_x() + b.get_width()/2, v + max(y)*0.015, fmt_num(v),
                    ha='center', va='bottom', fontsize=8, color=COLORS['ink'], fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(data['x'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_num(v)))
    ax.set_title(data.get('chart_title', ''), loc='left', fontsize=11, color=COLORS['ink'], fontweight='bold', pad=12)
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.02), frameon=False, fontsize=9, ncol=2)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor='white')
    plt.close(fig)
    print(f'✅ 专业柱状图已保存: {out}')


def pro_dual(data, out):
    setup()
    fig = plt.figure(figsize=(12.5, 7.2), facecolor='white')
    add_header(fig, data['title'], data.get('subtitle', ''))
    add_kpis(fig, data.get('kpis', []))
    add_note_panel(fig, data.get('notes', []))
    add_source(fig, data.get('source', '融策会计师事务所'))

    ax1 = fig.add_axes([0.07, 0.18, 0.55, 0.55])
    style_axis(ax1)
    x = np.arange(len(data['x']))
    left = data['left_axis']
    right = data['right_axis']
    y1 = np.array(left['data'], dtype=float)
    y2 = np.array(right['data'], dtype=float)

    ax1.bar(x, y1, width=0.55, color=left.get('color', COLORS['navy']), alpha=0.9,
            edgecolor='white', linewidth=0.8, label=left['name'], zorder=4)
    ax1.tick_params(axis='y', labelcolor=left.get('color', COLORS['navy']))
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_num(v)))
    for xi, yi in zip(x, y1):
        ax1.text(xi, yi + max(y1)*0.02, fmt_num(yi), ha='center', va='bottom', fontsize=8, color=COLORS['ink'])

    ax2 = ax1.twinx()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_color(right.get('color', COLORS['gold']))
    ax2.tick_params(axis='y', labelsize=9, colors=right.get('color', COLORS['gold']), length=0)
    ax2.plot(x, y2, color=right.get('color', COLORS['gold']), linewidth=2.8,
             marker='D', markersize=6, markerfacecolor='white', markeredgewidth=2,
             label=right['name'], zorder=6)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}%'))
    for xi, yi in zip(x, y2):
        ax2.text(xi, yi, f'{yi:.1f}%', ha='center', va='bottom' if yi >= 0 else 'top',
                 fontsize=8, color=right.get('color', COLORS['gold']), fontweight='bold')

    ax1.set_xticks(x)
    ax1.set_xticklabels(data['x'])
    ax1.set_title(data.get('chart_title', ''), loc='left', fontsize=11, color=COLORS['ink'], fontweight='bold', pad=12)
    handles = [Line2D([0], [0], color=left.get('color', COLORS['navy']), lw=8),
               Line2D([0], [0], color=right.get('color', COLORS['gold']), lw=2.8, marker='D', markerfacecolor='white')]
    ax1.legend(handles, [left['name'], right['name']], loc='upper left', bbox_to_anchor=(0, 1.02), frameon=False, fontsize=9, ncol=2)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor='white')
    plt.close(fig)
    print(f'✅ 专业双轴图已保存: {out}')


def pro_matrix(data, out):
    """信息饱和型矩阵图，适合审计方法/风险分布。"""
    setup()
    fig = plt.figure(figsize=(12.5, 7.2), facecolor='white')
    add_header(fig, data['title'], data.get('subtitle', ''))
    add_kpis(fig, data.get('kpis', []))
    add_note_panel(fig, data.get('notes', []))
    add_source(fig, data.get('source', '融策会计师事务所'))

    ax = fig.add_axes([0.07, 0.16, 0.55, 0.58])
    ax.set_facecolor('white')
    rows = data['rows']
    cols = data['cols']
    values = np.array(data['values'])
    im = ax.imshow(values, cmap='YlGnBu', aspect='auto')
    ax.set_xticks(np.arange(len(cols)))
    ax.set_xticklabels(cols, fontsize=9, color=COLORS['ink'])
    ax.set_yticks(np.arange(len(rows)))
    ax.set_yticklabels(rows, fontsize=9, color=COLORS['ink'])
    for i in range(len(rows)):
        for j in range(len(cols)):
            ax.text(j, i, f'{values[i, j]:.0f}', ha='center', va='center', fontsize=9,
                    color='white' if values[i, j] > values.max()*0.55 else COLORS['ink'], fontweight='bold')
    ax.set_title(data.get('chart_title', ''), loc='left', fontsize=11, color=COLORS['ink'], fontweight='bold', pad=12)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors=COLORS['gray'], length=0)
    cbar.outline.set_visible(False)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor='white')
    plt.close(fig)
    print(f'✅ 专业矩阵图已保存: {out}')


def demo(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pro_line({
        'title': '财政收入修复斜率放缓，税收收入弹性仍是关键变量',
        'subtitle': '宏观财政专题 | 年度趋势跟踪',
        'chart_title': '图1：全国一般公共预算收入与税收收入走势（亿元）',
        'source': '财政部，Wind，融策会计师事务所整理',
        'x': ['2020', '2021', '2022', '2023', '2024', '2025E'],
        'series': [
            {'name': '一般公共预算收入', 'data': [182895, 202539, 203703, 216784, 220000, 228000], 'color': COLORS['navy']},
            {'name': '税收收入', 'data': [154310, 172731, 166614, 181129, 182000, 190000], 'color': COLORS['gold']},
        ],
        'kpis': [
            {'label': '2025E预算收入', 'value': '22.8万亿', 'color': COLORS['navy']},
            {'label': '2024-2025E增量', 'value': '+0.8万亿', 'color': COLORS['gold']},
            {'label': '税收占比', 'value': '83.3%', 'color': COLORS['teal']},
        ],
        'notes': [
            '财政收入修复并非线性扩张，税基质量和房地产链条回暖仍决定后续弹性。',
            '税收收入占比维持高位，说明非税收入拉动空间有限，审计应重点关注税源真实性。',
            '若预算收入增速明显高于经济增速，应回查一次性收入、非税缴库和跨期调节。',
        ],
        'events': [{'x': 2, 'text': '留抵退税冲击'}]
    }, out_dir / '01_pro_line_fiscal.png')

    pro_bar({
        'title': '项目结构决定审计资源配置，绩效评价与工程决算是主战场',
        'subtitle': '融策业务结构分析 | 项目类型对比',
        'chart_title': '图2：2025年度审计咨询项目类型分布（个）',
        'source': '融策项目台账，行业访谈，融策AI审计中台',
        'x': ['绩效评价', '经责审计', '工程竣工\n决算', '专项审计', '资产清查', '预算执行'],
        'series': [
            {'name': '融策承接', 'data': [45, 32, 28, 25, 20, 18], 'color': COLORS['navy']},
            {'name': '行业均值', 'data': [38, 35, 22, 30, 25, 22], 'color': '#9AA6B2'},
        ],
        'kpis': [
            {'label': '项目总量', 'value': '168个', 'color': COLORS['navy']},
            {'label': '优势业务占比', 'value': '43.5%', 'color': COLORS['gold']},
            {'label': '可AI复核项目', 'value': '100+', 'color': COLORS['teal']},
        ],
        'notes': [
            '绩效评价和工程竣工决算是最适合作为审盾一期验证样板的业务线。',
            '项目结构越标准化，越适合沉淀复核清单、法规引用和图表模板。',
            '后续应按业务线建立“数据口径-指标体系-报告模板”三件套。',
        ]
    }, out_dir / '02_pro_bar_projects.png')

    pro_dual({
        'title': '财政收入规模抬升但波动加大，增速变化暴露预算执行压力',
        'subtitle': '区县财政画像 | 收入规模与增长质量',
        'chart_title': '图3：某区县财政收入及同比增速',
        'source': '财政决算报表，融策会计师事务所整理',
        'x': ['2019', '2020', '2021', '2022', '2023', '2024'],
        'left_axis': {'name': '财政收入（亿元）', 'data': [32.5, 28.3, 35.1, 33.8, 38.2, 42.1], 'color': COLORS['navy']},
        'right_axis': {'name': '同比增速（%）', 'data': [8.3, -12.9, 24.0, -3.7, 13.0, 10.2], 'color': COLORS['gold']},
        'kpis': [
            {'label': '2024收入规模', 'value': '42.1亿', 'color': COLORS['navy']},
            {'label': '2024同比', 'value': '+10.2%', 'color': COLORS['gold']},
            {'label': '6年复合增速', 'value': '+5.3%', 'color': COLORS['teal']},
        ],
        'notes': [
            '2021年高增长带有恢复性特征，不能简单外推为长期财政能力。',
            '2022年回落后再修复，需核查收入确认时点、非税缴库和土地相关收入。',
            '报告正文应同时解释“规模”和“增速”，避免只看收入增长得出乐观结论。',
        ]
    }, out_dir / '03_pro_dual_revenue.png')

    pro_matrix({
        'title': '五坐标穿透模型提升疑点识别密度，工程与招投标场景最受益',
        'subtitle': '审盾方法论 | 风险信号矩阵',
        'chart_title': '图4：不同业务线的风险信号覆盖强度（0-100）',
        'source': '融策AI审计中台规则库，历史项目复盘',
        'rows': ['绩效评价', '经责审计', '工程决算', '招投标审计', '专项资金'],
        'cols': ['时空', '物理', '关系', '行为', '序列'],
        'values': [
            [62, 45, 50, 78, 66],
            [70, 58, 82, 73, 68],
            [85, 92, 65, 80, 76],
            [76, 88, 95, 90, 82],
            [68, 55, 72, 74, 80],
        ],
        'kpis': [
            {'label': '最高风险域', 'value': '招投标', 'color': COLORS['red']},
            {'label': '最强信号', 'value': '关系95', 'color': COLORS['gold']},
            {'label': '覆盖维度', 'value': '5坐标', 'color': COLORS['teal']},
        ],
        'notes': [
            '招投标审计的关系、行为和物理信号密集，是最容易形成铁证链的方向。',
            '工程决算依赖物理坐标和时空坐标，应重点接入现场影像、进度资料和支付节点。',
            '绩效评价不是没有数据，而是指标口径分散，需先做指标标准化再谈AI复核。',
        ]
    }, out_dir / '04_pro_matrix_risk.png')


def main():
    parser = argparse.ArgumentParser(description='融策·专业研报图文模块生成器')
    sub = parser.add_subparsers(dest='cmd')
    p = sub.add_parser('demo')
    p.add_argument('--out', default='output/charts_pro')
    args = parser.parse_args()
    if args.cmd == 'demo':
        demo(args.out)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
