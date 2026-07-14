#!/usr/bin/env python3
"""
技能审计扫描器
扫描所有技能目录，生成分类报告、重复检测、使用建议。
"""
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

SKILL_ROOTS = [
    Path.home() / '.openclaw' / 'extensions' / 'wecom-openclaw-plugin' / 'skills',
    Path.home() / '.openclaw' / 'skills',
    Path.home() / '.openclaw' / 'workspace' / '.agents' / 'skills',
    Path.home() / '.openclaw' / 'workspace' / 'skills',
]

# Business scene categories
CATEGORIES = {
    'audit_core': {
        'label': '🔴 审计核心',
        'keywords': ['audit', '审计', '经责', '绩效', '预算', '资金', '采购', '招投标', '串标', '围标',
                     '财务', '工程审计', '能源', '补贴', '专项债', '监督检查', '国资', '资产清查',
                     'benford', 'fraud', 'procurement', 'subsidy', 'fiscal', 'budget', 'bond',
                     'energy', 'engineering', 'bim', 'spatial'],
        'scene': '审计业务',
        'always_load': True,
    },
    'audit_method': {
        'label': '🟡 审计方法',
        'keywords': ['分析方法', '数字化审计', '知识图谱', '数据标准', '非结构化', 'apriori',
                     'methodology', 'knowledge-graph', 'data-standard', 'unstructured',
                     'digital-audit', 'cot-capture', '思维链', 'workflow-embedder', '嵌入'],
        'scene': '审计方法论',
        'always_load': False,
    },
    'bidding_doc': {
        'label': '🟢 标书文档',
        'keywords': ['bid', '标书', '投标', 'bidding', '格式', '排版', '公文', 'doc-formatter',
                     'markdown-converter', 'copy-editing', 'copywriting', 'humanizer',
                     'content-polish', 'summarize', 'report-review', '复核'],
        'scene': '标书/文档',
        'always_load': False,
    },
    'visual_design': {
        'label': '🎨 可视化设计',
        'keywords': ['ppt', 'drawio', 'chart', 'diagram', 'arch', 'fireworks', 'huashu',
                     'visual', '封面', '架构图', '流程图'],
        'scene': '设计/展示',
        'always_load': False,
    },
    'data_analysis': {
        'label': '📊 数据分析',
        'keywords': ['data-analyst', 'forecast', 'sql', 'deepseek-charting', '模拟'],
        'scene': '数据分析',
        'always_load': False,
    },
    'research': {
        'label': '🔍 研究检索',
        'keywords': ['tavily', 'browser', 'deep-research', 'prompt-reverse', 'web'],
        'scene': '研究/检索',
        'always_load': False,
    },
    'system': {
        'label': '⚙️ 系统工具',
        'keywords': ['memory', 'note', 'prompt-librarian', 'skill-manager', 'find-skills',
                     'debugging', 'reflection', 'scheduled-report', 'healthcheck',
                     'openclaw', 'clawhub', 'github', 'weather', 'skill-creator',
                     'agent-data-standard', 'zhixi', 'obsidian', 'qmd'],
        'scene': '系统/基建',
        'always_load': True,  # system skills always needed
    },
    'media': {
        'label': '📁 媒体处理',
        'keywords': ['pdf', 'video', 'visual-toolkit', 'whisper', 'officecli',
                     'docx', 'pptx', 'xlsx'],
        'scene': '文件处理',
        'always_load': False,
    },
    'wecom': {
        'label': '💬 企业微信',
        'keywords': ['wecom', 'meeting', 'todo', 'schedule', 'contact', 'smartsheet', 'msg'],
        'scene': '企业微信',
        'always_load': False,
    },
}

def classify_skill(name, desc):
    """Classify a skill into a category based on name and description."""
    text = f"{name} {desc}".lower()
    for cat_key, cat_info in CATEGORIES.items():
        for kw in cat_info['keywords']:
            if kw.lower() in text:
                return cat_key
    return 'uncategorized'

def scan_skills():
    """Scan all skill directories and collect metadata."""
    skills = {}
    for root in SKILL_ROOTS:
        if not root.exists():
            continue
        for skill_dir in root.iterdir():
            if not skill_dir.is_dir():
                continue
            name = skill_dir.name
            sk_md = skill_dir / 'SKILL.md'
            if not sk_md.exists():
                continue
            
            stat = sk_md.stat()
            content = sk_md.read_text(encoding='utf-8', errors='ignore')
            
            # Extract description (first paragraph after title)
            lines = content.split('\n')
            desc = ''
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('---'):
                    desc = line[:200]
                    break
            
            # Count files
            file_count = sum(1 for _ in skill_dir.rglob('*') if _.is_file())
            total_size = sum(_.stat().st_size for _ in skill_dir.rglob('*') if _.is_file())
            
            skills[name] = {
                'name': name,
                'path': str(skill_dir),
                'root': str(root),
                'description': desc,
                'size_kb': round(total_size / 1024, 1),
                'file_count': file_count,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'content_lines': len(lines),
                'category': classify_skill(name, desc),
            }
    
    return skills

def find_similar(skills):
    """Find potentially duplicate/overlapping skills using simple heuristics."""
    pairs = []
    names = list(skills.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a, b = names[i], names[j]
            sa, sb = skills[a], skills[b]
            
            # Check keyword overlap in descriptions
            words_a = set(sa['description'].lower().split())
            words_b = set(sb['description'].lower().split())
            if len(words_a) > 0 and len(words_b) > 0:
                overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
                if overlap > 0.3:
                    pairs.append((a, b, round(overlap*100)))
            
            # Check name similarity
            name_sim = len(set(a.lower().split('-')) & set(b.lower().split('-')))
            if name_sim >= 2:
                pairs.append((a, b, name_sim * 20))
    
    # Deduplicate and sort
    seen = set()
    unique = []
    for a, b, score in sorted(pairs, key=lambda x: -x[2]):
        key = tuple(sorted([a, b]))
        if key not in seen:
            seen.add(key)
            unique.append((a, b, score))
    
    return unique[:20]

def generate_recommendations(skills):
    """Generate recommendations based on scan results."""
    recs = []
    
    # Count by category
    by_cat = defaultdict(list)
    for name, s in skills.items():
        by_cat[s['category']].append(name)
    
    # Recommendation 1: Global vs scene-specific
    global_candidates = []
    scene_specific = []
    for name, s in skills.items():
        cat_info = CATEGORIES.get(s['category'], {})
        if cat_info.get('always_load', False):
            global_candidates.append(name)
        else:
            scene_specific.append(name)
    
    recs.append({
        'type': 'load_strategy',
        'title': '按场景热加载分組',
        'detail': f'全局加载 {len(global_candidates)} 个 (系统+审计核心)，按场景动态加载 {len(scene_specific)} 个',
        'global': sorted(global_candidates),
        'by_scene': {cat: names for cat, names in by_cat.items() if not CATEGORIES.get(cat, {}).get('always_load', False)},
    })
    
    # Recommendation 2: Size warnings
    large_skills = [(n, s['size_kb']) for n, s in skills.items() if s['size_kb'] > 500]
    if large_skills:
        recs.append({
            'type': 'size_warning',
            'title': f'{len(large_skills)} 个技能超过500KB（注意token消耗）',
            'skills': sorted(large_skills, key=lambda x: -x[1]),
        })
    
    # Recommendation 3: Stale skills
    cutoff = '2026-05-01'
    stale = [(n, s['last_modified']) for n, s in skills.items() if s['last_modified'] < cutoff]
    if stale:
        recs.append({
            'type': 'stale_skills',
            'title': f'{len(stale)} 个技能超过45天未更新',
            'skills': sorted(stale),
        })
    
    return recs

def main():
    print('=' * 70)
    print('  融策 Skill 体系审计扫描')
    print(f'  扫描时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)
    
    skills = scan_skills()
    print(f'\n📊 总计: {len(skills)} 个技能')
    
    # Category breakdown
    by_cat = defaultdict(list)
    for name, s in skills.items():
        by_cat[s['category']].append(name)
    
    print('\n--- 分类统计 ---')
    for cat_key in CATEGORIES:
        names = by_cat.get(cat_key, [])
        cat_info = CATEGORIES[cat_key]
        always = '⭐ 常驻' if cat_info['always_load'] else ''
        print(f'  {cat_info["label"]}: {len(names)} 个 {always}')
    
    uncat = by_cat.get('uncategorized', [])
    if uncat:
        print(f'  ❓ 未分类: {len(uncat)} 个 → {uncat}')
    
    # Size analysis
    total_kb = sum(s['size_kb'] for s in skills.values())
    print(f'\n--- 规模分析 ---')
    print(f'  总大小: {total_kb:.0f} KB ({total_kb/1024:.1f} MB)')
    print(f'  平均: {total_kb/len(skills):.0f} KB/技能')
    
    sizes = sorted([(n, s['size_kb']) for n, s in skills.items()], key=lambda x: -x[1])
    print(f'  最大: {sizes[0][0]} ({sizes[0][1]:.0f} KB)')
    print(f'  最小: {sizes[-1][0]} ({sizes[-1][1]:.0f} KB)')
    
    # Top 10 largest
    print('\n  Top 10 最大技能:')
    for name, size in sizes[:10]:
        print(f'    {name}: {size:.0f} KB')
    
    # Similar skills detection
    similar = find_similar(skills)
    if similar:
        print(f'\n--- 疑似重复/重叠技能 ({len(similar)} 对) ---')
        for a, b, score in similar:
            print(f'  [{score}%] {a} ↔ {b}')
    
    # Recommendations
    recs = generate_recommendations(skills)
    print(f'\n--- 优化建议 ---')
    for rec in recs:
        print(f'\n  📌 {rec["title"]}')
        if rec['type'] == 'load_strategy':
            print(f'  {rec["detail"]}')
            print(f'  常驻({len(rec["global"])}): {", ".join(rec["global"][:10])}...')
            for scene, names in rec['by_scene'].items():
                if names:
                    label = CATEGORIES.get(scene, {}).get('label', scene)
                    print(f'  {label}: {", ".join(names[:5])}{"..." if len(names)>5 else ""}')
        elif rec['type'] == 'size_warning':
            for n, s in rec['skills']:
                print(f'    ⚠️ {n}: {s:.0f} KB')
        elif rec['type'] == 'stale_skills':
            for n, d in rec['skills']:
                print(f'    🕐 {n}: 最后更新 {d}')
    
    # Save report
    report = {
        'scan_time': datetime.now().isoformat(),
        'total_skills': len(skills),
        'skills': skills,
        'categories': {k: {'count': len(v), 'names': v} for k, v in by_cat.items()},
        'similar_pairs': similar,
        'recommendations': recs,
    }
    
    out_path = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'skill_audit.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f'\n📄 完整报告: {out_path}')
    
    return report

if __name__ == '__main__':
    main()
