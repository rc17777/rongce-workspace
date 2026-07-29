"""
Skill Description Quality Audit + Large File Split Suggestions
Based on: Description = 做什么 + 怎么做 + 什么时候用
"""
import os, json, re, sys
from pathlib import Path
from collections import defaultdict

SKILL_DIRS = [
    Path.home() / '.openclaw' / 'skills',
    Path.home() / '.openclaw' / 'workspace' / 'skills',
    Path.home() / '.openclaw' / 'workspace' / '.agents' / 'skills',
    Path.home() / '.openclaw' / 'extensions' / 'wecom-openclaw-plugin' / 'skills',
]

# Also check AppData paths
appdata_skills = Path.home() / 'AppData' / 'Local' / 'Programs' / 'OneClaw' / 'resources' / 'resources' / 'gateway.asar' / 'node_modules' / 'openclaw' / 'skills'
if appdata_skills.exists():
    SKILL_DIRS.append(appdata_skills)

def find_skills():
    skills = {}
    for base in SKILL_DIRS:
        if not base.exists():
            continue
        for d in base.iterdir():
            if d.is_dir():
                md = d / 'SKILL.md'
                if md.exists():
                    if d.name not in skills:
                        skills[d.name] = {'path': str(d), 'size_kb': 0}
    return skills

def get_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except:
                pass
    return round(total / 1024, 1)

def parse_skill_md(path):
    """Parse SKILL.md frontmatter and body"""
    md_path = Path(path) / 'SKILL.md'
    if not md_path.exists():
        return None
    
    try:
        content = md_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return None
    
    lines = content.split('\n')
    body_start = 0
    has_frontmatter = False
    fm = {}
    
    if lines and lines[0].strip() == '---':
        has_frontmatter = True
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                body_start = i + 1
                break
            match = re.match(r'^(\w[\w-]*)\s*:\s*(.*)', line)
            if match:
                fm[match.group(1)] = match.group(2).strip().strip('"').strip("'")
    
    body = '\n'.join(lines[body_start:])
    body_lines = len(lines[body_start:])
    body_chars = len(body)
    
    # Count subsidiary files
    skill_dir = Path(path)
    files = list(skill_dir.rglob('*'))
    file_list = [str(f.relative_to(skill_dir)) for f in files if f.is_file() and f.name != 'SKILL.md']
    file_list.sort()
    
    return {
        'has_frontmatter': has_frontmatter,
        'frontmatter': fm,
        'body_lines': body_lines,
        'body_chars': body_chars,
        'subsidiary_files': file_list,
        'subsidiary_count': len(file_list),
        'raw_frontmatter_str': '\n'.join(lines[:body_start]) if has_frontmatter else ''
    }

def score_description(desc, name):
    """Score description quality: 0-100, based on 做什么/怎么做/什么时候用"""
    if not desc:
        return {'score': 0, 'grade': 'F', 'issues': ['无description字段'], 'suggestions': []}
    
    issues = []
    suggestions = []
    score = 0
    
    # 1. 做什么 (What) - up to 35 points
    has_what = any(word in desc.lower() for word in [
        'extract', 'generate', 'review', 'audit', 'analyze', 'create', 'search',
        'send', 'query', 'check', 'convert', 'manage', 'format', 'draw', 'design',
        'detect', 'polish', 'edit', 'compile', 'fetch', 'lookup', 'list', 'get',
        '提取', '生成', '复核', '审计', '分析', '创建', '搜索',
        '发送', '查询', '检查', '转换', '管理', '格式', '绘制', '设计',
        '检测', '润色', '编辑', '编写', '获取', '查找', '列出'
    ])
    action_verbs = re.findall(r'\b(extract|generate|review|audit|analyze|create|search|send|query|check|convert|manage|format|draw|design|detect|polish|edit|compile|fetch|lookup|handle|process|build|write|produce|output)\w*\b', desc.lower())
    if action_verbs:
        score += min(30, len(action_verbs) * 10)
    elif has_what:
        score += 15
    else:
        issues.append('缺少具体动作动词')
        suggestions.append('用动词开头描述这个技能到底做什么')
    
    # 2. 怎么做 (How) - up to 30 points
    how_indicators = ['using', 'via', 'through', 'by', 'with', 'based on', 'against',
                      '使用', '通过', '基于', '按照']
    has_how = any(ind in desc.lower() for ind in how_indicators)
    # Also check for methodology mention
    has_method = bool(re.search(r'\b(tf-idf|benford|apriori|ocr|rag|sql|pattern|rule|checklist|template|framework)\b', desc.lower()))
    if has_how or has_method:
        score += 30
    else:
        # Check if it's implicitly clear
        if len(desc.split()) > 10:
            score += 15
        else:
            issues.append('缺少方法说明（怎么做）')
            suggestions.append('补充方法论或工具名')
    
    # 3. 什么时候用 (When) - up to 25 points
    when_words = ['use when', 'trigger', 'for', '适用于', '触发', '用于', 'when the user',
                  'when working', '场景']
    has_when = any(w in desc.lower() for w in when_words)
    if has_when:
        score += 25
    else:
        if len(desc.split()) > 15:
            score += 10  # longer descriptions might implicitly convey this
        else:
            issues.append('缺少触发条件（什么时候用）')
            suggestions.append('添加 "Use when..." 或触发场景说明')
    
    # 4. Description length quality - up to 10 points
    word_count = len(desc.split())
    if word_count < 5:
        score += 2
        issues.append('描述过短（<5词），模型难以匹配')
    elif word_count < 10:
        score += 5
    elif word_count < 30:
        score += 8
    else:
        score += 10
    
    # 5. Ambiguity check
    vague_words = ['handle', 'process', 'do', 'thing', 'stuff', 'manage', '处理']
    vague_count = sum(1 for w in vague_words if w in desc.lower())
    if vague_count >= 2:
        issues.append(f'含{vague_count}个模糊词，语义边界不清')
        suggestions.append('用更具体的动词替换模糊词')
        score -= 10
    
    score = max(0, min(100, score))
    
    if score >= 80:
        grade = 'A'
    elif score >= 65:
        grade = 'B'
    elif score >= 50:
        grade = 'C'
    elif score >= 30:
        grade = 'D'
    else:
        grade = 'F'
    
    return {
        'score': score,
        'grade': grade,
        'issues': issues,
        'suggestions': suggestions,
        'word_count': word_count
    }

def suggest_split(skill_name, parsed, size_kb):
    """Suggest file splitting based on size and structure"""
    suggestions = []
    body_lines = parsed['body_lines']
    body_chars = parsed['body_chars']
    sub_files = parsed['subsidiary_files']
    
    # Estimate tokens (rough: 1 token ≈ 4 chars for English, 2 chars for Chinese)
    est_tokens = body_chars // 3
    
    # Large body (>500 lines) → split suggestion
    if body_lines > 500:
        suggestions.append({
            'priority': 'P0',
            'action': f'SKILL.md过大（{body_lines}行，~{est_tokens} tokens）→ 拆分为导航页+详情页',
            'detail': 'SKILL.md只保留概述+引用，详细内容拆到 reference.md / examples.md / rules.md'
        })
    elif body_lines > 200:
        suggestions.append({
            'priority': 'P1',
            'action': f'SKILL.md偏大（{body_lines}行，~{est_tokens} tokens）→ 考虑拆分',
            'detail': '将长章节拆到子文件，SKILL.md保留核心指令'
        })
    
    # Overall directory size >500KB
    if size_kb > 500:
        suggestions.append({
            'priority': 'P0',
            'action': f'目录过大（{size_kb}KB）→ 需检查是否有大文件可外置',
            'detail': '检查 node_modules / 数据文件 / 图片是否必要；大型辅助数据可放到 workspace 共享目录'
        })
    elif size_kb > 100:
        suggestions.append({
            'priority': 'P2',
            'action': f'目录偏大（{size_kb}KB），检查是否有冗余资源'
        })
    
    # No subsidiary files but large body → should definitely split
    if body_lines > 200 and len(sub_files) == 0:
        suggestions.append({
            'priority': 'P1',
            'action': '无子文件但正文很长 → 强烈建议拆分为 SKILL.md + reference.md',
            'detail': '按"导航页+详情页"模式拆分，可节省 78-98% 无关任务 Token'
        })
    
    return suggestions

def detect_boundary_conflicts(all_skills):
    """Detect skills with overlapping descriptions"""
    # Focus on skills with similar names or functions
    groups = [
        # Audit-related
        ['audit-report-review', 'audit-jingze', 'audit-data-analysis-methods', 
         'audit-knowledge-graph', 'digital-audit-methodology'],
        # Chart/diagram
        ['deepseek-charting', 'multi-chart-draw', 'arch-diagrammer', 
         'architecture-diagram-generator', 'baoyu-diagram', 'fireworks-tech-graph'],
        # Document/format
        ['doc-formatter', 'content-polish', 'copy-editing', 'baoyu-format-markdown',
         'markdown-converter', 'copywriting'],
        # PPT
        ['ppt-master', 'dashi-ppt', 'baoyu-slide-deck', 'bruce-pptx-generator', 'huashu-design'],
        # PDF/media
        ['pdf', 'openai-whisper', 'video-toolkit'],
        # Image gen
        ['baoyu-image-gen', 'baoyu-cover-image', 'baoyu-infographic', 'baoyu-xhs-images', 'baoyu-comic'],
        # WeCom (they share prefix, need clear boundaries)
        ['wecom-msg', 'wecom-send-media', 'wecom-send-template-card'],
        ['wecom-meeting-create', 'wecom-meeting-manage', 'wecom-meeting-query'],
        ['wecom-get-todo-list', 'wecom-get-todo-detail', 'wecom-edit-todo'],
        # Audit special
        ['financial-fraud-detection', 'procurement-audit-models', 'apriori-audit'],
        ['special-bond-audit', 'special-fund-audit', 'subsidy-audit', 'gov-subsidy-penetration-audit'],
        ['budget-audit', 'engineering-audit', 'energy-audit', 'bim-engineering-audit'],
    ]
    
    conflicts = []
    for group in groups:
        present = [s for s in group if s in all_skills]
        if len(present) >= 2:
            descs = {s: all_skills[s].get('description', '') for s in present}
            # Check if descriptions are too similar or too vague
            short_descs = [(s, d) for s, d in descs.items() if d and len(d.split()) < 8]
            if len(short_descs) >= 2:
                conflicts.append({
                    'group': present,
                    'issue': '多个技能描述过短，模型难以区分',
                    'skills': [s for s, _ in short_descs]
                })
    return conflicts

def main():
    print('=' * 80)
    print('  融策 Skill Description 质量审查 + 大文件拆分建议')
    print('  评分标准: 做什么(35) + 怎么做(30) + 什么时候用(25) + 长度(10)')
    print('=' * 80)
    
    skills = find_skills()
    print(f'\n共发现 {len(skills)} 个技能\n')
    
    # Analyze each
    results = {}
    grade_counts = defaultdict(int)
    
    for name in sorted(skills.keys()):
        info = skills[name]
        size_kb = get_size(info['path'])
        info['size_kb'] = size_kb
        parsed = parse_skill_md(info['path'])
        
        if not parsed:
            info['description'] = None
            info['desc_score'] = {'score': 0, 'grade': '?', 'issues': ['无法读取SKILL.md'], 'suggestions': []}
            info['split_suggestions'] = []
            continue
        
        desc = parsed['frontmatter'].get('description', '')
        info['description'] = desc
        info['parsed'] = parsed
        
        # Score description
        score = score_description(desc, name)
        info['desc_score'] = score
        grade_counts[score['grade']] += 1
        
        # Split suggestions
        splits = suggest_split(name, parsed, size_kb)
        info['split_suggestions'] = splits
        
        results[name] = info
    
    # Print ranked by grade
    print('\n' + '─' * 80)
    print('  📊 DESCRIPTION 质量排名')
    print('─' * 80)
    
    grade_order = ['F', 'D', 'C', 'B', 'A']
    for grade in grade_order:
        grade_skills = [(n, r) for n, r in results.items() if r['desc_score']['grade'] == grade]
        if not grade_skills:
            continue
        print(f'\n  【{grade}级】({len(grade_skills)}个)')
        for name, r in sorted(grade_skills, key=lambda x: x[1]['desc_score']['score'], reverse=True):
            desc = r.get('description', 'N/A') or 'N/A'
            sc = r['desc_score']
            print(f'  [{sc["score"]:3d}] {name}')
            print(f'       desc: {desc[:120]}{"..." if len(desc)>120 else ""}')
            for iss in sc['issues']:
                print(f'       ❌ {iss}')
            for sug in sc['suggestions']:
                print(f'       💡 {sug}')
    
    # Grade distribution
    print('\n' + '─' * 80)
    print('  📊 评分分布')
    print('─' * 80)
    for g in grade_order:
        if g in grade_counts:
            bar = '█' * grade_counts[g]
            print(f'  {g}: {grade_counts[g]} {bar}')
    
    # Split suggestions summary
    print('\n' + '─' * 80)
    print('  📦 大文件拆分建议')
    print('─' * 80)
    
    p0_splits = []
    p1_splits = []
    p2_splits = []
    
    for name, r in sorted(results.items()):
        for sug in r['split_suggestions']:
            entry = (name, sug['action'], sug.get('detail', ''))
            if sug['priority'] == 'P0':
                p0_splits.append(entry)
            elif sug['priority'] == 'P1':
                p1_splits.append(entry)
            else:
                p2_splits.append(entry)
    
    if p0_splits:
        print('\n  🔴 P0 - 必须拆分:')
        for name, action, detail in p0_splits:
            print(f'     [{name}] {action}')
            if detail:
                print(f'           → {detail}')
    
    if p1_splits:
        print('\n  🟡 P1 - 建议拆分:')
        for name, action, detail in p1_splits:
            print(f'     [{name}] {action}')
            if detail:
                print(f'           → {detail}')
    
    if p2_splits:
        print('\n  🟢 P2 - 可选优化:')
        for name, action, detail in p2_splits:
            print(f'     [{name}] {action}')
    
    # Boundary conflicts
    print('\n' + '─' * 80)
    print('  ⚠️  边界冲突检测')
    print('─' * 80)
    
    conflicts = detect_boundary_conflicts(results)
    if conflicts:
        for c in conflicts:
            print(f'\n  群组: {", ".join(c["group"])}')
            print(f'  问题: {c["issue"]}')
            print(f'  需改进: {", ".join(c["skills"])}')
            # Suggest rewrites
            for s in c['skills']:
                if s in results:
                    print(f'     [{s}] 当前: {results[s].get("description", "N/A")[:100]}')
    else:
        print('\n  ✅ 无明显边界冲突')
    
    # Top issues summary
    print('\n' + '─' * 80)
    print('  🔑 全局改进建议')
    print('─' * 80)
    
    no_desc = [n for n, r in results.items() if not r.get('description')]
    if no_desc:
        print(f'\n  1. {len(no_desc)}个技能完全缺少description字段（模型无法自动触发）：')
        for n in no_desc[:10]:
            print(f'     - {n}')
    
    short_desc = [(n, r['description']) for n, r in results.items() 
                  if r.get('description') and len(r['description'].split()) < 5]
    if short_desc:
        print(f'\n  2. {len(short_desc)}个技能描述过短（<5词），模型匹配困难：')
        for n, d in short_desc[:10]:
            print(f'     - {n}: "{d}"')
    
    missing_when = [(n, r['description']) for n, r in results.items()
                    if r.get('description') and not any(w in r['description'].lower() 
                        for w in ['use when', 'trigger', 'when the user', 'when working', '适用于', '触发', '用于'])]
    if missing_when:
        print(f'\n  3. {len(missing_when)}个技能缺少触发条件（什么时候用）：')
        for n, d in missing_when[:10]:
            print(f'     - {n}')
    
    # Save detailed report
    report = {
        'timestamp': '2026-07-28',
        'total_skills': len(skills),
        'grade_distribution': dict(grade_counts),
        'skills': {
            name: {
                'grade': r['desc_score']['grade'],
                'score': r['desc_score']['score'],
                'description': r.get('description', ''),
                'body_lines': r.get('parsed', {}).get('body_lines', 0),
                'size_kb': r.get('size_kb', 0),
                'issues': r['desc_score']['issues'],
                'suggestions': r['desc_score']['suggestions'],
                'split_suggestions': [(s['priority'], s['action']) for s in r['split_suggestions']]
            }
            for name, r in results.items()
        }
    }
    
    out = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'skill_desc_audit.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n📄 详细报告: {out}')

if __name__ == '__main__':
    main()
