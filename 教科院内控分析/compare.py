import os, re, difflib
from datetime import datetime

out = r"D:\openclaw-workspace\教科院内控分析"

# File timeline mapping (from filename dates)
files_meta = [
    ("内控制度2024.6.14-11.18.md", "2024-06-14", "2024-11-18"),
    ("内控制度2024.11.8-3.17.md", "2024-11-08", "2025-03-17"),
    ("内控制度2025.3.17-4.11 - 副本.md", "2025-03-17", "2025-04-11"),
    ("内控制度2025.4.11-5.27.md", "2025-04-11", "2025-05-27"),
    ("内控制度2025.5.27-7.11.md", "2025-05-27", "2025-07-11"),
    ("内控制度2025.7.11-10.13 - 副本.md", "2025-07-11", "2025-10-13"),
    ("内控制度2025.10.13-11.5.md", "2025-10-13", "2025-11-05"),
    ("2025.11.5-1.23.md", "2025-11-05", "2026-01-23"),
    ("2026.1.23—3.13 副本(1).md", "2026-01-23", "2026-03-13"),
    ("2026.3.13至今.md", "2026-03-13", "至今"),
]

def extract_toc(filepath):
    """Extract table of contents lines from a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_toc = False
    toc = []
    for line in lines:
        stripped = line.strip()
        if stripped == '目 录':
            in_toc = True
            continue
        if in_toc:
            if stripped.startswith('# ') or stripped.startswith('## '):
                break
            if stripped:
                toc.append(stripped)
    return toc

def extract_sections(filepath):
    """Extract all section headings with their hierarchical structure"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    sections = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            # Part (第一部分 etc.)
            sections.append(('part', stripped.replace('# ', '')))
        elif stripped.startswith('## ') and not stripped.startswith('### '):
            sections.append(('chapter', stripped.replace('## ', '')))
        elif stripped.startswith('### '):
            sections.append(('section', stripped.replace('### ', '')))
    return sections

def compare_tocs(all_tocs):
    """Compare TOCs across all versions"""
    report = []
    report.append("# 教科院内控制度 - 差异性分析报告\n")
    report.append(f"**分析时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    report.append(f"**文件数量:** {len(files_meta)}个版本\n")
    report.append(f"**覆盖周期:** 2024年6月 → 至今\n")
    report.append("---\n")
    
    # 1. TOC comparison - What sections exist in each version?
    report.append("## 一、目录结构演变（篇章级差异）\n")
    
    all_section_names = set()
    for fname, _, _ in files_meta:
        fpath = os.path.join(out, fname)
        if os.path.exists(fpath):
            sections = extract_sections(fpath)
            for stype, sname in sections:
                if stype == 'part':
                    all_section_names.add(('PART', sname))
                elif stype == 'chapter':
                    all_section_names.add(('CHAPTER', sname))
    
    # Build comparison matrix
    sorted_sections = sorted(all_section_names, key=lambda x: x[1])
    
    # Part-level comparison
    parts = [s for s in sorted_sections if s[0] == 'PART']
    report.append("### 1.1 篇章结构变化\n")
    report.append("| 篇章 | " + " | ".join([f"V{i+1}" for i in range(len(files_meta))]) + " |")
    report.append("|------|" + "|".join(["------" for _ in files_meta]) + "|")
    
    for _, pname in parts:
        row = f"| {pname} |"
        for fname, _, _ in files_meta:
            fpath = os.path.join(out, fname)
            if os.path.exists(fpath):
                sections = extract_sections(fpath)
                part_names = [s[1] for s in sections if s[0] == 'part']
                row += " ✅ |" if pname in part_names else " ❌ |"
            else:
                row += " - |"
        report.append(row)
    
    # Chapter-level comparison
    chapters = [s for s in sorted_sections if s[0] == 'CHAPTER']
    report.append("\n### 1.2 制度章节变化\n")
    report.append("| 制度名称 | " + " | ".join([f"V{i+1}" for i in range(len(files_meta))]) + " |")
    report.append("|------|" + "|".join(["------" for _ in files_meta]) + "|")
    
    for _, cname in chapters:
        row = f"| {cname} |"
        for fname, _, _ in files_meta:
            fpath = os.path.join(out, fname)
            if os.path.exists(fpath):
                sections = extract_sections(fpath)
                chapter_names = [s[1] for s in sections if s[0] == 'chapter']
                row += " ✅ |" if cname in chapter_names else " ❌ |"
            else:
                row += " - |"
        report.append(row)
    
    report.append("\n---\n")
    
    # 2. Identify which items were added/removed between versions
    report.append("## 二、逐版本差异详情\n")
    
    prev_chapters = None
    for idx, (fname, start_date, end_date) in enumerate(files_meta):
        fpath = os.path.join(out, fname)
        if not os.path.exists(fpath):
            continue
        
        sections = extract_sections(fpath)
        curr_chapters = set(s[1] for s in sections if s[0] == 'chapter')
        
        period = f"{start_date} ~ {end_date}"
        report.append(f"### V{idx+1}: {period}\n")
        
        if prev_chapters is not None:
            added = curr_chapters - prev_chapters
            removed = prev_chapters - curr_chapters
            
            if added:
                report.append(f"**➕ 新增制度 ({len(added)}项):**\n")
                for a in sorted(added):
                    report.append(f"- ✅ {a}\n")
            
            if removed:
                report.append(f"**➖ 删除/合并制度 ({len(removed)}项):**\n")
                for r in sorted(removed):
                    report.append(f"- ❌ {r}\n")
            
            if not added and not removed:
                report.append("*制度目录无变化*\n")
        
        prev_chapters = curr_chapters
        report.append("")
    
    return ''.join(report)

def deep_compare_versions():
    """Deep content comparison between adjacent versions"""
    report = []
    report.append("# 教科院内控制度 - 深度内容差异分析\n")
    report.append(f"**分析时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    report.append("---\n")
    
    for idx in range(len(files_meta) - 1):
        fname1, s1, e1 = files_meta[idx]
        fname2, s2, e2 = files_meta[idx + 1]
        
        fpath1 = os.path.join(out, fname1)
        fpath2 = os.path.join(out, fname2)
        
        if not os.path.exists(fpath1) or not os.path.exists(fpath2):
            continue
        
        with open(fpath1, 'r', encoding='utf-8') as f:
            text1 = f.read()
        with open(fpath2, 'r', encoding='utf-8') as f:
            text2 = f.read()
        
        report.append(f"## V{idx+1}→V{idx+2}: {e1} → {s2}\n")
        
        # Compute line-level diff
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(lines1, lines2, 
                                          fromfile=f'V{idx+1}', 
                                          tofile=f'V{idx+2}',
                                          lineterm=''))
        
        # Summarize diff stats
        adds = sum(1 for d in diff if d.startswith('+') and not d.startswith('+++'))
        dels = sum(1 for d in diff if d.startswith('-') and not d.startswith('---'))
        
        report.append(f"- **新增行数:** {adds}\n")
        report.append(f"- **删除行数:** {dels}\n")
        report.append(f"- **净变化:** {adds - dels:+d} 行\n")
        
        # Extract key changed sections (non-trivial changes)
        changed_sections = set()
        for d in diff:
            if d.startswith('## ') and (d.startswith('+##') or d.startswith('-##')):
                changed_sections.add(d[1:].strip())
        
        # Find content additions (look for new ## headings or significant blocks)
        report.append("")
        
    return ''.join(report)

# Run comparison
report = compare_tocs({})
with open(os.path.join(out, '差异分析报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

print("TOC comparison report written.")

# Now do section-by-section deep comparison
sections_report = deep_compare_versions()
with open(os.path.join(out, '深度内容差异.md'), 'w', encoding='utf-8') as f:
    f.write(sections_report)

print("Deep comparison report written.")
print("Done!")
