import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from difflib import unified_diff

out = r"D:\openclaw-workspace\教科院内控分析"

files_meta = [
    ("内控制度2024.6.14-11.18.md", "V1", "2024.06.14-11.18"),
    ("内控制度2024.11.8-3.17.md", "V2", "2024.11.08-2025.03.17"),
    ("内控制度2025.3.17-4.11 - 副本.md", "V3", "2025.03.17-04.11"),
    ("内控制度2025.4.11-5.27.md", "V4", "2025.04.11-05.27"),
    ("内控制度2025.5.27-7.11.md", "V5", "2025.05.27-07.11"),
    ("内控制度2025.7.11-10.13 - 副本.md", "V6", "2025.07.11-10.13"),
    ("内控制度2025.10.13-11.5.md", "V7", "2025.10.13-11.05"),
    ("2025.11.5-1.23.md", "V8", "2025.11.05-2026.01.23"),
    ("2026.1.23—3.13 副本(1).md", "V9", "2026.01.23-03.13"),
    ("2026.3.13至今.md", "V10", "2026.03.13-至今"),
]

def extract_section(filepath, section_name):
    """Extract a section by ## heading"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    capturing = False
    content = []
    for line in lines:
        stripped = line.strip()
        if stripped == f'## {section_name}':
            capturing = True
            content.append(line)
            continue
        if capturing:
            if stripped.startswith('## ') and stripped != f'## {section_name}':
                break
            content.append(line)
    return ''.join(content) if content else None

def extract_chapter_names(filepath, section_name):
    """Extract all ### level chapter names from a section"""
    content = extract_section(filepath, section_name)
    if not content:
        return []
    chapters = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('### '):
            chapters.append(stripped.replace('### ', ''))
    return chapters

def get_section_stats(content):
    """Get line count and char count"""
    if not content:
        return 0, 0
    lines = content.splitlines()
    chars = sum(len(l.strip()) for l in lines if l.strip())
    return len(lines), chars

# Extract 政府采购管理制度 from all versions
procurement_data = {}
general_procurement_data = {}

for fname, ver, period in files_meta:
    fpath = os.path.join(out, fname)
    if not os.path.exists(fpath):
        continue
    
    # 政府采购管理制度
    proc = extract_section(fpath, '政府采购管理制度')
    chapters = extract_chapter_names(fpath, '政府采购管理制度')
    lines, chars = get_section_stats(proc)
    
    procurement_data[ver] = {
        'period': period,
        'exists': proc is not None,
        'chapters': chapters,
        'lines': lines,
        'chars': chars,
        'content': proc,
    }
    
    # 一般采购管理制度
    gen_proc = extract_section(fpath, '一般采购管理制度')
    gen_lines, gen_chars = get_section_stats(gen_proc)
    general_procurement_data[ver] = {
        'exists': gen_proc is not None,
        'lines': gen_lines,
        'chars': gen_chars,
    }

# ════════════════ Generate Report ════════════════
rpt = []
rpt.append('# 政府采购管理制度 — 10版本差异性分析\n')
rpt.append('## 一、存续状态总览\n\n')
rpt.append('| 版本 | 时间范围 | 政府采购管理制度 | 行数 | 字符数 | 一般采购管理制度 |')
rpt.append('|------|----------|:---:|-----:|-----:|:---:|')
for fname, ver, period in files_meta:
    p = procurement_data.get(ver, {})
    g = general_procurement_data.get(ver, {})
    status1 = '✅' if p.get('exists') else '❌已删除'
    status2 = f"{g.get('lines',0)}行" if g.get('exists') else '❌'
    rpt.append(f"| {ver} | {period} | {status1} | {p.get('lines',0)} | {p.get('chars',0)} | {status2} |")

rpt.append('\n\n## 二、章节结构对比（V1-V8）\n\n')

# Collect all unique chapter names
all_chapters = set()
for ver in ['V1','V2','V3','V4','V5','V6','V7','V8']:
    if procurement_data[ver]['exists']:
        for ch in procurement_data[ver]['chapters']:
            all_chapters.add(ch)

# Sort chapters by first appearance order
chapter_order = []
for ch in all_chapters:
    for ver in ['V1','V2','V3','V4','V5','V6','V7','V8']:
        if ch in procurement_data[ver]['chapters']:
            chapter_order.append(ch)
            break

rpt.append('| 章节 | V1 | V2 | V3 | V4 | V5 | V6 | V7 | V8 | 说明 |')
rpt.append('|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|------|')
for ch in chapter_order:
    row = f'| {ch} |'
    for ver in ['V1','V2','V3','V4','V5','V6','V7','V8']:
        if procurement_data[ver]['exists']:
            row += ' ✅ |' if ch in procurement_data[ver]['chapters'] else ' — |'
        else:
            row += ' ❌ |'
    # Detect changes
    first_ver = None
    for ver in ['V1','V2','V3','V4','V5','V6','V7','V8']:
        if procurement_data[ver]['exists'] and ch in procurement_data[ver]['chapters']:
            first_ver = ver
            break
    note = f'自{first_ver}起存在' if first_ver else ''
    row += f' {note} |'
    rpt.append(row)

rpt.append('\n\n## 三、逐版本差异详情\n\n')

# Compare adjacent versions
for idx in range(len(files_meta) - 1):
    v1_name, v1_ver, v1_period = files_meta[idx]
    v2_name, v2_ver, v2_period = files_meta[idx+1]
    
    p1 = procurement_data[v1_ver]
    p2 = procurement_data[v2_ver]
    
    rpt.append(f'### {v1_ver} → {v2_ver}\n')
    
    if not p1['exists'] and not p2['exists']:
        rpt.append('*两个版本均不存在政府采购管理制度*\n\n')
        continue
    
    if not p1['exists']:
        rpt.append(f'**{v1_ver}中不存在，{v2_ver}新增**\n\n')
        continue
    
    if not p2['exists']:
        rpt.append(f'**⚠️ {v1_ver}中存在（{p1["lines"]}行），{v2_ver}中已删除！**\n')
        rpt.append(f'- V1行数: {p1["lines"]}\n')
        rpt.append(f'- V1字符数: {p1["chars"]}\n')
        rpt.append(f'- 删除的制度章节: {p1["chapters"]}\n\n')
        
        # Check if general procurement expanded
        g1 = general_procurement_data[v1_ver]
        g2 = general_procurement_data[v2_ver]
        gen_diff = g2['lines'] - g1['lines']
        rpt.append(f'- 同时期一般采购管理制度变化: {g2["lines"]}行 ({"+" if gen_diff > 0 else ""}{gen_diff}行)\n\n')
        continue
    
    # Both exist - compare
    chapters_added = set(p2['chapters']) - set(p1['chapters'])
    chapters_removed = set(p1['chapters']) - set(p2['chapters'])
    lines_diff = p2['lines'] - p1['lines']
    chars_diff = p2['chars'] - p1['chars']
    
    if lines_diff == 0 and not chapters_added and not chapters_removed:
        rpt.append(f'*无变化* ({p1["lines"]}行, {p1["chars"]}字符)\n\n')
        continue
    
    rpt.append(f'- **行数变化:** {p1["lines"]} → {p2["lines"]} ({lines_diff:+d})\n')
    rpt.append(f'- **字符数变化:** {p1["chars"]} → {p2["chars"]} ({chars_diff:+d})\n')
    
    if chapters_added:
        rpt.append(f'- **➕ 新增章节:** {", ".join(sorted(chapters_added))}\n')
    if chapters_removed:
        rpt.append(f'- **➖ 删除章节:** {", ".join(sorted(chapters_removed))}\n')
    
    # Show actual diff
    if lines_diff != 0:
        diff = list(unified_diff(
            p1['content'].splitlines(keepends=True),
            p2['content'].splitlines(keepends=True),
            fromfile=v1_ver, tofile=v2_ver, lineterm=''
        ))
        # Only show first 30 diff lines
        if diff:
            rpt.append('\n<details>\n<summary>内容差异（展开查看）</summary>\n\n```diff\n')
            for line in diff[:60]:
                rpt.append(line.rstrip() + '\n')
            if len(diff) > 60:
                rpt.append(f'\n... (共{len(diff)}行差异，仅显示前60行)\n')
            rpt.append('```\n</details>\n')
    
    rpt.append('\n')

# ════════════════ V9-V10: What happened after deletion ════════════════
rpt.append('\n## 四、V9-V10：政府采购制度删除后分析\n\n')

for ver in ['V9', 'V10']:
    g = general_procurement_data[ver]
    rpt.append(f'### {ver}（{procurement_data[ver]["period"]}）\n\n')
    rpt.append(f'- 政府采购管理制度：**❌ 已删除**\n')
    rpt.append(f'- 一般采购管理制度：{g["lines"]}行\n\n')

# Compare V8 general procurement vs V9 general procurement
g8 = general_procurement_data['V8']
g9 = general_procurement_data['V9']
g10 = general_procurement_data['V10']

rpt.append('### 一般采购管理制度是否吸收了政府采购内容？\n\n')
rpt.append(f'| 版本 | 一般采购管理制度行数 | 变化 |\n')
rpt.append('|------|-----:|------|\n')
rpt.append(f'| V8（采购制度删除前） | {g8["lines"]} | — |\n')
rpt.append(f'| V9（删除政府采购） | {g9["lines"]} | {g9["lines"] - g8["lines"]:+d} |\n')
rpt.append(f'| V10（当前） | {g10["lines"]} | {g10["lines"] - g8["lines"]:+d} |\n')

if g9['lines'] > g8['lines']:
    rpt.append('\n**结论：** 一般采购管理制度在V9中行数增加，可能存在政府采购内容的吸收整合。\n\n')
else:
    rpt.append('\n**结论：** 一般采购管理制度未显著扩容，政府采购制度删除后可能依赖上级统一采购平台或外部制度承接。\n')

rpt.append('\n### V8政府采购管理制度内容概要（被删除前最后一版）\n\n')
p8 = procurement_data['V8']
if p8['content']:
    rpt.append(f'- 总行数：{p8["lines"]}行\n')
    rpt.append(f'- 总字符数：{p8["chars"]}字符\n')
    rpt.append(f'- 章节结构：\n')
    for ch in p8['chapters']:
        rpt.append(f'  - {ch}\n')

# ════════════════ V1 vs V8: first vs last before deletion ════════════════
rpt.append('\n\n## 五、V1 → V8 全程内容变化摘要\n\n')

p1 = procurement_data['V1']
p8 = procurement_data['V8']

rpt.append(f'### V1（初始版）→ V8（最终版）\n\n')
rpt.append(f'| 维度 | V1 | V8 | 变化 |\n')
rpt.append(f'|------|----|----|------|\n')
rpt.append(f'| 行数 | {p1["lines"]} | {p8["lines"]} | {p8["lines"] - p1["lines"]:+d} |\n')
rpt.append(f'| 字符数 | {p1["chars"]} | {p8["chars"]} | {p8["chars"] - p1["chars"]:+d} |\n')
rpt.append(f'| 章节数 | {len(p1["chapters"])} | {len(p8["chapters"])} | {len(p8["chapters"]) - len(p1["chapters"]):+d} |\n\n')

# Show chapters side by side
rpt.append('### 章节清单对比\n\n')
rpt.append('| V1章节 | V8章节 |\n')
rpt.append('|--------|--------|\n')
max_len = max(len(p1['chapters']), len(p8['chapters']))
for i in range(max_len):
    v1c = p1['chapters'][i] if i < len(p1['chapters']) else ''
    v8c = p8['chapters'][i] if i < len(p8['chapters']) else ''
    rpt.append(f'| {v1c} | {v8c} |\n')

# Write report
report_path = os.path.join(out, '政府采购差异性分析.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(rpt))

print(f"Report written to: {report_path}")
print("Done!")
