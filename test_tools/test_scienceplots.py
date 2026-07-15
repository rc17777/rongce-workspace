"""Test SciencePlots - create sample audit-style charts with journal themes."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import scienceplots

# Check available styles
print("Available SciencePlots styles:")
science_styles = [s for s in plt.style.available if any(k in s for k in ['science', 'nature', 'ieee', 'grid', 'no-latex', 'bright', 'vibrant', 'muted', 'high-vis', 'retro', 'std-colors'])]
for s in sorted(science_styles):
    print(f"  {s}")

# Create test data
categories = ['预算编制', '工程结算', '绩效评价', '经责审计', '资产清查', '专项债']
values = [125.3, 89.7, 156.2, 98.4, 67.1, 112.8]
# Simulate multi-year comparison
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
import os
os.makedirs(output_dir, exist_ok=True)

# Test 1: Bar chart with science style
print("\n=== Test 1: Science style bar chart ===")
with plt.style.context(['science', 'no-latex', 'grid']):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#0A1F3F', '#1A5C6E', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=0.5)
    ax.set_xlabel('业务类别')
    ax.set_ylabel('项目金额（万元）')
    ax.set_title('融策会计师事务所 - 各业务线项目金额分布')
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'science_bar.png'), dpi=200)
    print("Saved: science_bar.png")

# Test 2: IEEE style with multi-year comparison
print("\n=== Test 2: IEEE style grouped bar ===")
with plt.style.context(['ieee', 'no-latex', 'grid']):
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(categories))
    width = 0.25
    for i, year in enumerate(years):
        vals = [multi_data[cat][i] for cat in categories]
        ax.bar(x + i*width, vals, width, label=f'{year}年', edgecolor='black', linewidth=0.3)
    ax.set_xticks(x + width)
    ax.set_xticklabels(categories)
    ax.set_ylabel('项目金额（万元）')
    ax.set_title('各业务线三年趋势对比')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'ieee_grouped_bar.png'), dpi=200)
    print("Saved: ieee_grouped_bar.png")

# Test 3: Nature style
print("\n=== Test 3: Nature style ===")
with plt.style.context(['nature', 'no-latex']):
    fig, ax = plt.subplots(figsize=(10, 6))
    # Horizontal bar - cleaner for publication
    ax.barh(categories[::-1], values[::-1], 
            color=['#0A1F3F', '#1A5C6E', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D'][::-1])
    ax.set_xlabel('项目金额（万元）')
    ax.set_title('业务线项目金额分布')
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'nature_bar.png'), dpi=200)
    print("Saved: nature_bar.png")

# Test 4: High-vis for presentations
print("\n=== Test 4: High-vis style for slides ===")
with plt.style.context(['science', 'high-vis', 'no-latex']):
    fig, ax = plt.subplots(figsize=(10, 6))
    # Pie chart alternative - donut
    wedges, texts, autotexts = ax.pie(
        values, labels=categories, autopct='%1.1f%%',
        colors=['#0A1F3F', '#1A5C6E', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D'],
        startangle=90, pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='white')
    )
    for t in autotexts:
        t.set_fontsize(8)
    ax.set_title('业务线收入占比')
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'highvis_donut.png'), dpi=200)
    print("Saved: highvis_donut.png")

# Test 5: Scatter with retro style
print("\n=== Test 5: Retro style scatter ===")
np.random.seed(42)
with plt.style.context(['science', 'retro', 'no-latex']):
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.random.normal(100, 30, 50)
    y = np.random.normal(100, 30, 50)
    sizes = np.random.uniform(20, 200, 50)
    scatter = ax.scatter(x, y, s=sizes, c=sizes, cmap='YlOrRd', alpha=0.6, edgecolors='black', linewidth=0.3)
    ax.set_xlabel('预算偏差率（%）')
    ax.set_ylabel('结算偏差率（%）')
    ax.set_title('项目偏差率分布散点图')
    cbar = fig.colorbar(scatter)
    cbar.set_label('项目规模（万元）')
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'retro_scatter.png'), dpi=200)
    print("Saved: retro_scatter.png")

print("\nDone! All 5 charts saved to:", output_dir)
