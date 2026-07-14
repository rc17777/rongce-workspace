# -*- coding: utf-8 -*-
"""Diagnose the brochure for professional design issues."""
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

slides_dir = r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\slides'

print('=== 页面诊断 ===')
print()

page_layouts = []
for fname in sorted(os.listdir(slides_dir)):
    if not fname.endswith('.html'):
        continue
    fpath = os.path.join(slides_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    uses_shared = 'brochure-theme.css' in content
    has_own_style = '<style>' in content
    has_masthead = 'masthead' in content
    has_footer = 'footer' in content
    has_sidebar = 'sidebar' in content or 'side' in content.lower()
    
    # Count hardcoded px values
    px_values = re.findall(r'(\d+)px', content)
    # Count colors
    colors = re.findall(r'#[0-9A-Fa-f]{6}', content)
    
    # Determine layout type
    if 'transition-page' in content:
        layout = '过渡页'
    elif 'cover-bg' in content or 'hero-title' in content.lower():
        layout = '封面'
    elif 'masthead' not in content:
        layout = '特殊'
    elif 'sidebar' in content or 'side' in content.lower():
        layout = '左栏+右内容'
    else:
        layout = '自定义'
    
    page_layouts.append((fname, layout, len(lines), len(px_values), len(colors), uses_shared, has_own_style, has_masthead, has_footer))

print(f'{"文件名":25s} {"布局":15s} {"行数":5s} {"px值":5s} {"颜色":5s} {"共享CSS":8s} {"自有CSS":8s} {"导航栏":8s} {"页脚":5s}')
print('-' * 95)
for fname, layout, lines, px, colors, shared, own, mast, foot in page_layouts:
    print(f'{fname:25s} {layout:15s} {lines:5d} {px:5d} {colors:5d} {"Y" if shared else "N":8s} {"Y" if own else "N":8s} {"Y" if mast else "N":8s} {"Y" if foot else "N":5s}')

# Count layout uniqueness
layouts = [l[1] for l in page_layouts]
print(f'\n布局类型分布:')
for l in set(layouts):
    count = layouts.count(l)
    print(f'  {l}: {count}页')

# Check for shared CSS usage
shared_count = sum(1 for l in page_layouts if l[5])
own_count = sum(1 for l in page_layouts if l[6])
print(f'\n共享CSS引用: {shared_count}/{len(page_layouts)}')
print(f'自有CSS: {own_count}/{len(page_layouts)}')

# Count pages that DON'T use shared CSS
print('\n未使用共享CSS的页面:')
for fname, layout, lines, px, colors, shared, own, mast, foot in page_layouts:
    if not shared and not 'transition' in fname:
        print(f'  {fname} ({layout})')

print('\n=== 核心问题 ===')
print('1. 布局类型单一: 12/17页是"左栏+右内容"')
print('2. 自有CSS分散: 部分页面不用共享CSS，风格不统一')
print('3. 硬编码px值: 每页拆解成不同px间距')
print('4. 颜色值分散: 各页自己定义颜色，容易不一致')