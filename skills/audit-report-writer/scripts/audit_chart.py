"""
审计数据可视化工具
使用语义色板生成审计图表，SVG可编辑输出
用法: 
  py audit_chart.py bar --data '{"高风险":5,"中风险":12,"低风险":8}' --title '审计发现分布'
  py audit_chart.py trend --data '{"2022":150,"2023":180,"2024":120}' --title '近三年采购金额趋势'
  py audit_chart.py fundflow --data '{"预算":500,"采购":320,"工程":120,"服务":60}' --title '资金流向'
"""
import json
import argparse
import sys
import os

# 确保matplotlib使用非交互后端
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.fonttype'] = 'none'

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 尝试设置中文字体
for font_name in ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']:
    try:
        fm.findfont(font_name, fallback_to_default=False)
        plt.rcParams['font.sans-serif'] = [font_name]
        plt.rcParams['axes.unicode_minus'] = False
        break
    except:
        continue

# === 语义色板 ===
RISK_COLORS = {
    '高风险': '#C0392B',
    '中风险': '#E67E22',
    '低风险': '#27AE60',
    '合规':   '#2980B9',
}

COMPARE_COLORS = ['#2C3E50', '#3498DB', '#27AE60', '#E67E22', '#8E44AD', '#C0392B']

FINANCE_COLORS = {
    '收入': '#27AE60',
    '支出': '#C0392B',
    '结余': '#2980B9',
    '预算': '#BDC3C7',
    '实际': '#2C3E50',
}


def auto_color(labels):
    """自动为标签分配颜色"""
    colors = []
    for i, label in enumerate(labels):
        if label in RISK_COLORS:
            colors.append(RISK_COLORS[label])
        elif label in FINANCE_COLORS:
            colors.append(FINANCE_COLORS[label])
        else:
            colors.append(COMPARE_COLORS[i % len(COMPARE_COLORS)])
    return colors


def chart_bar(data, title, output='audit_chart', fmt='svg'):
    """柱状图 - 审计发现分布等"""
    labels = list(data.keys())
    values = list(data.values())
    colors = auto_color(labels)

    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.5), 6))
    bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=0.5, width=0.6)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                f'{val}', ha='center', fontsize=11, fontweight='bold')

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('数量', fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    _save(fig, output, fmt)
    print(f'✅ 柱状图已保存: {output}.{fmt}')


def chart_trend(data, title, output='audit_chart', fmt='svg'):
    """趋势折线图"""
    labels = list(data.keys())
    values = list(data.values())

    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.2), 5))
    ax.plot(labels, values, color='#2980B9', marker='o', linewidth=2.5, markersize=8)
    ax.fill_between(labels, values, alpha=0.1, color='#2980B9')

    for i, (x, y) in enumerate(zip(labels, values)):
        ax.annotate(f'{y}', (x, y), textcoords="offset points", xytext=(0, 12),
                    ha='center', fontsize=10, fontweight='bold')

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    _save(fig, output, fmt)
    print(f'✅ 趋势图已保存: {output}.{fmt}')


def chart_fundflow(data, title, output='audit_chart', fmt='svg'):
    """资金流向水平柱状图"""
    labels = list(data.keys())
    values = list(data.values())
    colors = auto_color(labels)

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.8)))
    bars = ax.barh(labels, values, color=colors, edgecolor='white', linewidth=0.5, height=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                f'{val:.0f}万', va='center', fontsize=10)

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('金额（万元）', fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.invert_yaxis()

    plt.tight_layout()
    _save(fig, output, fmt)
    print(f'✅ 资金流向图已保存: {output}.{fmt}')


def chart_pie(data, title, output='audit_chart', fmt='svg'):
    """饼图 - 占比分析"""
    labels = list(data.keys())
    values = list(data.values())
    colors = auto_color(labels)

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors, autopct='%1.1f%%',
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(edgecolor='white', linewidth=1.5)
    )
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight('bold')

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

    plt.tight_layout()
    _save(fig, output, fmt)
    print(f'✅ 饼图已保存: {output}.{fmt}')


def _save(fig, output, fmt):
    if fmt == 'svg':
        fig.savefig(f'{output}.svg', format='svg', bbox_inches='tight')
    elif fmt == 'png':
        fig.savefig(f'{output}.png', dpi=300, bbox_inches='tight')
    elif fmt == 'both':
        fig.savefig(f'{output}.svg', format='svg', bbox_inches='tight')
        fig.savefig(f'{output}.png', dpi=300, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='审计数据可视化工具')
    parser.add_argument('chart_type', choices=['bar', 'trend', 'fundflow', 'pie'],
                        help='图表类型: bar=柱状图, trend=趋势图, fundflow=资金流向, pie=饼图')
    parser.add_argument('--data', default=None, help='JSON格式数据')
    parser.add_argument('--datafile', default=None, help='JSON数据文件路径（与--data二选一）')
    parser.add_argument('--title', default='审计数据图表', help='图表标题')
    parser.add_argument('--output', default='audit_chart', help='输出文件名（不含扩展名）')
    parser.add_argument('--format', default='svg', choices=['svg', 'png', 'both'], help='输出格式')
    args = parser.parse_args()

    if args.data:
        data = json.loads(args.data)
    elif args.datafile:
        with open(args.datafile, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    else:
        print('错误：需要 --data 或 --datafile 参数')
        sys.exit(1)

    chart_funcs = {
        'bar': chart_bar,
        'trend': chart_trend,
        'fundflow': chart_fundflow,
        'pie': chart_pie,
    }

    chart_funcs[args.chart_type](data, args.title, args.output, args.format)


if __name__ == '__main__':
    main()
