#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manually ingest the carbon peak action plan into knowledge base"""

import shutil, os

src = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\laws\_incoming\十五五碳达峰行动方案_国发2026年22号.md'

# 1. Copy to knowledge/laws/
dst_laws = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\laws\十五五碳达峰行动方案_国发2026年22号.md'
shutil.copy2(src, dst_laws)
print('1. knowledge/laws/ OK')

# 2. Generate Obsidian version with YAML frontmatter
with open(src, 'r', encoding='utf-8') as f:
    text = f.read()

frontmatter_lines = []
frontmatter_lines.append('---')
frontmatter_lines.append('title: "十五五碳达峰行动方案"')
frontmatter_lines.append('category: 政策文件')
frontmatter_lines.append('publish_date: 2026-07-05')
frontmatter_lines.append('doc_id: 国发〔2026〕22号')
frontmatter_lines.append('source_file: 十五五碳达峰行动方案_国发2026年22号.md')
frontmatter_lines.append('ingest_date: 2026-07-16')
frontmatter_lines.append('tags:')
frontmatter_lines.append('  - 法规/政策文件')
frontmatter_lines.append('  - 碳达峰碳中和')
frontmatter_lines.append('  - 能源审计')
frontmatter_lines.append('  - 节能降碳')
frontmatter_lines.append('  - 绩效评价')
frontmatter_lines.append('---')
frontmatter_lines.append('')

frontmatter = '\n'.join(frontmatter_lines)

obsidian_content = frontmatter + text
dst_obsidian = r'C:\Users\scrccpa\.openclaw\workspace\obsidian-vault\laws\十五五碳达峰行动方案_国发2026年22号.md'
os.makedirs(os.path.dirname(dst_obsidian), exist_ok=True)
with open(dst_obsidian, 'w', encoding='utf-8') as f:
    f.write(obsidian_content)
print('2. obsidian-vault/laws/ OK')

# 3. Remove from _incoming
os.remove(src)
print('3. _incoming/ cleaned up OK')

print()
print('Manual ingest complete!')