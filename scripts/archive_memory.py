# -*- coding: utf-8 -*-
"""Extract archive files from MEMORY.md backup (UTF-16 encoded)."""
import re, os

# Read backup
backup = r'D:\openclaw-workspace\memory\MEMORY_BACKUP_20260621.md'
with open(backup, 'r', encoding='utf-16-le') as f:
    content = f.read()
content = content.lstrip('\ufeff')

archive_dir = r'D:\openclaw-workspace\memory\archive'
os.makedirs(archive_dir, exist_ok=True)

# Find all ## sections
lines = content.split('\n')
sections = []
current_h = ''; current_lines = []
for line in lines:
    if line.startswith('## ') and current_lines:
        sections.append((current_h, '\n'.join(current_lines)))
        current_lines = [line]
        current_h = line.strip()
    elif line.startswith('# '):
        if current_lines:
            sections.append((current_h, '\n'.join(current_lines)))
        current_lines = [line]
        current_h = line.strip()
    else:
        current_lines.append(line)
if current_lines:
    sections.append((current_h, '\n'.join(current_lines)))

print(f'Found {len(sections)} sections')

# Define archive mapping: (output_filename, section_header_keywords)
archives = {
    'bidding-technical-foundation.md': '串标围标检测体系',
    'digital-audit-knowledge.md': '数字化审计知识体系',
    'five-pillars-skills.md': '五大基石',
    'data-audit-85-articles.md': '数据化审计',
    'procurement-cases-batch.md': '招投标',
    'huli-college-audit.md': '护理学院',
    'chart-system-research.md': '图表',
    '15th-five-year-plan.md': '十五五',
    'obsidian-wiki-setup.md': 'Obsidian|Wiki知识库',
    'natural-resources-product.md': '自然资源|AI\\+审计场景',
    'claude-for-legal-archive.md': 'claude-for-legal',
    'video-creator-archive.md': 'video-creator',
    'skills-install-history.md': '已安装核心技能|重要决策记录|drawio|DeepSeek image|LLM Wiki',
    '数智审Lab五篇文章分析.md': '数智审Lab五篇文章',
    '经济责任审计量化评价体系.md': '经济责任审计量化评价|经济责任审计整合模板',
}

saved = {}
for fname, keywords in archives.items():
    patterns = keywords.split('|')
    found_sections = []
    for hdr, body in sections:
        for pat in patterns:
            if pat in hdr:
                found_sections.append((hdr, body))
                break
    if found_sections:
        outpath = os.path.join(archive_dir, fname)
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(f'> 从 MEMORY.md 归档 | 归档日期: 2026-06-21\n\n')
            for hdr, body in found_sections:
                f.write(body + '\n\n---\n\n')
        saved[fname] = len(found_sections)
        print(f'  {fname}: {len(found_sections)} sections -> {os.path.getsize(outpath)} bytes')
    else:
        print(f'  {fname}: NOT FOUND')

# Create consolidated case archive
case_sections = []
for hdr, body in sections:
    if any(k in hdr for k in ['审计数据专员','校服采购','护理学院','国资处','PaperBanana','Cocoon-AI','aud-bench','艺术团','宿舍监理','急救实训室','新项目经验','招投标审计 v3','阜新审计局']):
        case_sections.append((hdr, body))

if case_sections:
    outpath = os.path.join(archive_dir, 'procurement-cases-batch.md')
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(f'> 从 MEMORY.md 归档 | 归档日期: 2026-06-21\n\n')
        f.write('# 招投标审计案例与技术底座汇总\n\n')
        for hdr, body in case_sections:
            f.write(body + '\n\n---\n\n')
    print(f'  procurement-cases-batch.md: {len(case_sections)} sections -> {os.path.getsize(outpath)} bytes')

# Create Aloudata/审计大模型 archive
misc_sections = []
for hdr, body in sections:
    if any(k in hdr for k in ['Aloudata','审计大模型·范式重构',"audit-card-generator"]):
        misc_sections.append((hdr, body))
if misc_sections:
    outpath = os.path.join(archive_dir, 'misc-research-archive.md')
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(f'> 从 MEMORY.md 归档 | 归档日期: 2026-06-21\n\n')
        for hdr, body in misc_sections:
            f.write(body + '\n\n---\n\n')
    print(f'  misc-research-archive.md: {len(misc_sections)} sections')

# Create Git/OpenRouter utility archive  
util_sections = []
for hdr, body in sections:
    if any(k in hdr for k in ['Git 自动同步','OpenRouter']):
        util_sections.append((hdr, body))
if util_sections:
    outpath = os.path.join(archive_dir, 'utility-configs.md')
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(f'> 从 MEMORY.md 归档 | 归档日期: 2026-06-21\n\n')
        for hdr, body in util_sections:
            f.write(body + '\n\n---\n\n')
    print(f'  utility-configs.md: {len(util_sections)} sections')

print('\nDone!')
print(f'\nArchive files created in: {archive_dir}')
for f in sorted(os.listdir(archive_dir)):
    print(f'  {f} ({os.path.getsize(os.path.join(archive_dir, f))} bytes)')
