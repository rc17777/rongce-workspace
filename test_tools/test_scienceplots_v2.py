"""Fix Chinese fonts for SciencePlots and regenerate charts with proper CJK support."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import scienceplots
import os

# Find Chinese fonts on the system
print("Available Chinese fonts:")
for f in fm.fontManager.ttflist:
    if any(k in f.name.lower() for k in ['hei', 'yahei', 'song', 'kai', 'ming', 'fang', 'chinese', 'cjk', 'simsun', 'noto sans']):
        print(f"  {f.name} -> {f.fname}")

# Use SimHei or Microsoft YaHei
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

categories = ['预算编制', '工程结算', '绩效评价', '经责审计', '资产清查', '专项债']
values = [125.3, 89.7, 156.2, 98.4, 67.1, 112.8]
years = ['2023', '2024', '2025']
multi_data = {
    '预算编制': [98.2, 112.5, 125.3],
    '工程结算': [75.4, 82.1, 89.7],
    '绩效评价': [120.5, 138.6, 156.2],
    '经责审计': [85.3, 92.1, 98.4],
    '资产清查': [55.2, 60.8, 67.1],
    '专项债': [90.1, 101.3, 112.8],
}

output_dir = r'D:\openclaw-workspace\test_tools\output'
os.makedirs(output_dir, exist_ok=True)

# Chart 1: Science style - clean bar chart
print("\n--- Chart 1: Science style bar ---")
with plt.style.context(['science', 'no-latex', 'grid']):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#0A1F3F', '#1A5C6E', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=0.5)
    ax.set_xlabel('业务类别', fontsize=11)
    ax.set_ylabel('项目金额（万元）', fontsize=11)
    ax.set_title('融策会计师事务所 — 各业务线项目金额分布', fontsize=13, fontweight='bold')
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1.5,
                f'{val:.1f}', ha='center', va='bottom', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, '01_science_bar.png'), dpi=200, bbox_inches='tight')
    print("Saved: 01_science_bar.png")

# Chart 2: IEEE style - multi-year grouped bar
print("--- Chart 2: IEEE style grouped bar ---")
with plt.style.context(['ieee', 'no-latex', 'grid']):
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(categories))
    width = 0.25
    year_colors = ['#0A1F3F', '#1A5C6E', '#C5955C']
    for i, year in enumerate(years):
        vals = [multi_data[cat][i] for cat in categories]
        ax.bar(x + i*width, vals, width, label=f'{year}年', color=year_colors[i], edgecolor='white', linewidth=0.3)
    ax.set_xticks(x + width)
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylabel('项目金额（万元）', fontsize=11)
    ax.set_title('各业务线三年趋势对比', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, '02_ieee_grouped.png'), dpi=200, bbox_inches='tight')
    print("Saved: 02_ieee_grouped.png")

# Chart 3: Nature style - horizontal bar
print("--- Chart 3: Nature style horizontal bar ---")
with plt.style.context(['nature', 'no-latex']):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(categories[::-1], values[::-1], 
            color=['#0A1F3F', '#1A5C6E', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D'][::-1],
            height=0.6)
    ax.set_xlabel('项目金额（万元）', fontsize=11)
    ax.set_title('业务线项目金额分布', fontsize=13, fontweight='bold')
    for i, v in enumerate(values[::-1]):
        ax.text(v + 1, i, f'{v:.1f}', va='center', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, '03_nature_hbar.png'), dpi=200, bbox_inches='tight')
    print("Saved: 03_nature_hbar.png")

# Chart 4: High-vis donut for presentations
print("--- Chart 4: High-vis donut ---")
with plt.style.context(['science', 'high-vis', 'no-latex']):
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, autotexts = ax.pie(
        values, labels=categories, autopct='%1.1f%%',
        colors=['#0A1F3F', '#1A5C6E', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D'],
        startangle=90, pctdistance=0.82,
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=1),
        textprops={'fontsize': 11}
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight('bold')
    ax.set_title('业务线收入占比', fontsize=14, fontweight='bold', pad=20)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, '04_highvis_donut.png'), dpi=200, bbox_inches='tight')
    print("Saved: 04_highvis_donut.png")

# Chart 5: Retro style scatter
print("--- Chart 5: Retro scatter ---")
np.random.seed(42)
with plt.style.context(['science', 'retro', 'no-latex']):
    fig, ax = plt.subplots(figsize=(9, 7))
    x = np.random.normal(100, 30, 50)
    y = np.random.normal(100, 30, 50)
    sizes = np.random.uniform(30, 250, 50)
    scatter = ax.scatter(x, y, s=sizes, c=sizes, cmap='YlOrRd', alpha=0.65, edgecolors='#333', linewidth=0.3)
    ax.set_xlabel('预算偏差率（%）', fontsize=11)
    ax.set_ylabel('结算偏差率（%）', fontsize=11)
    ax.set_title('项目偏差率分布散点图', fontsize=13, fontweight='bold')
    cbar = fig.colorbar(scatter, shrink=0.85)
    cbar.set_label('项目规模（万元）', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, '05_retro_scatter.png'), dpi=200, bbox_inches='tight')
    print("Saved: 05_retro_scatter.png")

# Chart 6: vibrant style comparison - budget vs settlement
print("--- Chart 6: Vibrant style radar-like horizontal comparison ---")
with plt.style.context(['science', 'vibrant', 'no-latex']):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    # Subplot 1: Budget
    ax1.bar(categories, values, color=['#0A1F3F', '#1A5C6E', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
    ax1.set_title('项目金额分布', fontsize=12, fontweight='bold')
    ax1.set_ylabel('万元')
    ax1.tick_params(axis='x', rotation=30)
    # Subplot 2: Growth rate line
    growth = [27.6, 19.0, 29.6, 15.4, 21.5, 25.2]
    ax2.plot(categories, growth, 'o-', color='#C5955C', linewidth=2, markersize=8, markerfacecolor='#0A1F3F')
    ax2.fill_between(range(len(categories)), growth, alpha=0.15, color='#1A5C6E')
    ax2.set_title('三年复合增长率', fontsize=12, fontweight='bold')
    ax2.set_ylabel('%')
    ax2.tick_params(axis='x', rotation=30)
    ax2.axhline(y=np.mean(growth), color='#A23B72', linestyle='--', alpha=0.5, label=f'均值 {np.mean(growth):.1f}%')
    ax2.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, '06_vibrant_comparison.png'), dpi=200, bbox_inches='tight')
    print("Saved: 06_vibrant_comparison.png")

print("\nAll 6 charts regenerated with Chinese font support!")
