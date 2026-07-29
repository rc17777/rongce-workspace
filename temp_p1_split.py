"""Batch split 14 remaining oversized SKILL.md files"""
from pathlib import Path
import re

BASES = [
    Path.home() / '.openclaw' / 'skills',
    Path.home() / '.openclaw' / 'workspace' / 'skills',
]

def find(name):
    for b in BASES:
        p = b / name / 'SKILL.md'
        if p.exists():
            return p
    return None

def read(name):
    p = find(name)
    return p.read_text(encoding='utf-8', errors='ignore'), p

def split(skill_name, section_title, ref_title, nav_text, keep_before=True):
    """Split at ## section_title. keep_before=True → SKILL.md keeps content before split"""
    content, path = read(skill_name)
    idx = content.find(f'\n## {section_title}')
    if idx == -1:
        # Try ###
        idx = content.find(f'\n### {section_title}')
    if idx == -1:
        print(f'  ⚠️ {skill_name}: section "{section_title}" not found')
        return
    
    if keep_before:
        core = content[:idx].rstrip()
        ref = content[idx:].strip()
    else:
        core = content[idx:].strip()
        ref = content[:idx].rstrip()
    
    core += f'\n\n---\n\n## 📖 {nav_text}\n\n详见 `reference.md`。按需加载，不占用无关任务上下文。\n'
    
    path.write_text(core, encoding='utf-8')
    (path.parent / 'reference.md').write_text(f'# {ref_title}\n\n{ref}', encoding='utf-8')
    
    old_lines = len(content.splitlines())
    new_lines = len(core.splitlines())
    ref_lines = len(ref.splitlines())
    print(f'  ✅ {skill_name}: {old_lines}→{new_lines}行 (+{ref_lines} ref)')

# ============================================================
# 1. llm-wiki: Move workflows 3-10 to reference
# ============================================================
content, path = read('llm-wiki')
# Find "工作流 3" section
wf3 = content.find('\n## 工作流 3')
if wf3 > 0:
    core = content[:wf3].rstrip()
    ref = content[wf3:].strip()
    core += '\n\n---\n\n## 📖 工作流 3-10 详细操作\n\n知识库搜索、生成报告、智能问答、健康检查、知识图谱、删除素材、结晶化等高级工作流详见 `reference.md`。\n'
    path.write_text(core, encoding='utf-8')
    (path.parent / 'reference.md').write_text('# llm-wiki — 高级工作流参考\n\n' + ref, encoding='utf-8')
    print(f'  ✅ llm-wiki: {len(content.splitlines())}→{len(core.splitlines())}行 (+{len(ref.splitlines())} ref)')

# ============================================================
# 2. fireworks-tech-graph: Move styles section to reference
# ============================================================
split('fireworks-tech-graph', 'Styles', 'Fireworks Tech Graph — 样式参考', 'SVG样式库')

# ============================================================
# 3. obsidian-bases: Move detailed schema/formula/YAML to ref
# ============================================================
split('obsidian-bases', 'Filter Syntax', 'Obsidian Bases — 高级语法参考', '筛选器语法/公式/排序/YAML规则')

# ============================================================
# 4. sql-master: Move audit SQL templates to reference
# ============================================================
split('sql-master', '审计专用SQL模板', 'SQL Master — 审计SQL模板库', '审计专用SQL模板（预算执行/采购/经责等）')

# ============================================================
# 5. tavily: Move detailed API params + error handling to ref
# ============================================================
split('tavily', 'Resources', 'Tavily Search — API参考与依赖', 'API详细参数/错误处理/依赖/资源')

# ============================================================
# 6. bid-document: Move SQL appendix to reference
# ============================================================
content, path = read('bid-document')
sql_appendix = content.find('\n## 📎 附录：审计SQL模型速查表')
if sql_appendix > 0:
    # Keep the SQL appendix after frontmatter ends (it's the first section)
    # Move it to reference, keep core competency modules
    core_competency = content.find('\n## 💼 核心能力模块')
    if core_competency > 0:
        # The SQL appendix is between frontmatter and core competency
        sql_content = content[sql_appendix:core_competency]
        core = content[:sql_appendix].rstrip() + '\n\n' + content[core_competency:].strip()
        core += '\n\n---\n\n## 📖 审计SQL模型速查表\n\n预算执行/采购/经责等审计SQL模板详见 `reference.md`。\n'
        path.write_text(core, encoding='utf-8')
        (path.parent / 'reference.md').write_text('# 标书撰写 — 审计SQL模型速查表\n\n' + sql_content.strip(), encoding='utf-8')
        print(f'  ✅ bid-document: {len(content.splitlines())}→{len(core.splitlines())}行 (+{len(sql_content.splitlines())} ref)')

# ============================================================
# 7. scheduled-report: Move Steps 4-5 + edge cases to ref
# ============================================================
content, path = read('scheduled-report')
step4 = content.find('\n## Step 4：')
if step4 > 0:
    core = content[:step4].rstrip()
    ref = content[step4:].strip()
    core += '\n\n---\n\n## 📖 Step 4-5 及边界场景\n\nCron创建、边界场景处理、常见错误模式详见 `reference.md`。\n'
    path.write_text(core, encoding='utf-8')
    (path.parent / 'reference.md').write_text('# 定时任务编排 — 详细步骤与边界处理\n\n' + ref, encoding='utf-8')
    print(f'  ✅ scheduled-report: {len(content.splitlines())}→{len(core.splitlines())}行 (+{len(ref.splitlines())} ref)')

# ============================================================
# 8. special-bond-audit: Move detailed 环节 2-5 to ref
# ============================================================
content, path = read('special-bond-audit')
# Find second 环节 start
second = content.find('\n## 第二环节')
if second == -1:
    second = content.find('\n## 二、')
if second > 0:
    core = content[:second].rstrip()
    ref = content[second:].strip()
    core += '\n\n---\n\n## 📖 专项债四环节详细审计\n\n第二至第五环节（使用/管理/偿还/发现）详见 `reference.md`。\n'
    path.write_text(core, encoding='utf-8')
    (path.parent / 'reference.md').write_text('# 专项债审计 — 详细环节参考\n\n' + ref, encoding='utf-8')
    print(f'  ✅ special-bond-audit: {len(content.splitlines())}→{len(core.splitlines())}行 (+{len(ref.splitlines())} ref)')

# ============================================================
# 9. baoyu-format-markdown: Move typos + notes to ref
# ============================================================
split('baoyu-format-markdown', 'Typos Found', 'Format Markdown — 拼写纠错与扩展', '拼写纠错/注意事项/扩展支持')

# ============================================================
# 10. baoyu-comic: Move page modification + notes to ref
# ============================================================
split('baoyu-comic', 'Page Modification', 'Comic Creator — 修改与偏好设置', '页面修改/注意事项/偏好设置')

# ============================================================
# 11. drawio: Move audit review + troubleshooting to ref
# ============================================================
split('drawio', '🔍 审计图表审查报告', 'DrawIO — 审计审查与排错', '审计图表审查报告/排错指南/XML规范')

# ============================================================
# 12. baoyu-infographic: Move references to ref
# ============================================================
split('baoyu-infographic', 'References', 'Infographic — 参考资料', '参考资料与偏好设置')

# ============================================================
# 13. bim-engineering-audit: Move 异常预警+建议+附件 to ref
# ============================================================
split('bim-engineering-audit', '四、异常预警', 'BIM工程审计 — 异常预警与建议', '异常预警/审计建议/附件')

# ============================================================
# 14. pdf: Move library details to ref
# ============================================================
content, path = read('pdf')
quick_ref = content.find('\n## Quick Reference')
if quick_ref > 0:
    core = content[:quick_ref].rstrip()
    ref = content[quick_ref:].strip()
    core += '\n\n---\n\n## 📖 快速参考与扩展\n\nQuick Reference 和 Next Steps 详见 `reference.md`。\n'
    path.write_text(core, encoding='utf-8')
    (path.parent / 'reference.md').write_text('# PDF Toolkit — 快速参考\n\n' + ref, encoding='utf-8')
    print(f'  ✅ pdf: {len(content.splitlines())}→{len(core.splitlines())}行 (+{len(ref.splitlines())} ref)')

print('\n✅ 14 P1 splits complete')
