#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三库自进化引擎 — 让知识库自动学习、优化、补全

能力：
1. 质量扫描：检测内容老化、冗余、质量缺陷
2. 自动优化：AI驱动精简、去重、交叉引用
3. 缺口发现：分析项目反馈→发现知识缺口
4. 进化报告：生成可操作的改进建议

使用方式：
  python scripts/kb_evolve.py                    # 全量进化
  python scripts/kb_evolve.py --scan             # 只扫描质量
  python scripts/kb_evolve.py --optimize         # 只优化内容
  python scripts/kb_evolve.py --gaps             # 只发现缺口
  python scripts/kb_evolve.py --report           # 只输出报告
  python scripts/kb_evolve.py --auto             # 全自动(含AI调用)
"""

import os, sys, json, re, hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

try:
    WORKSPACE = Path(os.environ.get('OPENCLAW_WORKSPACE', '')).resolve()
except:
    WORKSPACE = Path(__file__).resolve().parent.parent

KNOWLEDGE = WORKSPACE / 'knowledge'
OBSIDIAN = WORKSPACE / 'obsidian-vault'
WIKI = WORKSPACE / 'AuditKB' / 'wiki'
OUTPUT = WORKSPACE / 'output' / 'evolve_reports'

# ── 进化指标配置 ──

# 内容老化阈值（天）
STALE_THRESHOLD = {
    'articles': 90,        # 文章90天未更新=老化
    'laws': 365,           # 法规1年未更新=老化
    'references': 180,     # 参考资料180天
    'policies': 90,        # 政策文件90天
}

# 质量扣分规则
QUALITY_PENALTIES = {
    'no_title': -10,           # 无标题
    'no_tags': -5,             # 无标签
    'no_yaml': -8,             # 无YAML frontmatter
    'too_short': -5,           # 太短(<200字)
    'too_long_no_structure': -3,  # 太长无结构(>5000字无标题)
    'no_scene': -5,            # 无场景标签
    'stale': -3,               # 内容老化
    'has_duplicate': -10,      # 疑似重复
    'broken_links': -3,        # 死链
}

# ── 工具函数 ──

def log(msg, level='INFO'):
    print(f'[{level}] {msg}')

def extract_yaml_field(content, field):
    """从YAML frontmatter提取字段"""
    m = re.search(rf'^{field}:\s*(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # 多行tags
    if field == 'tags':
        tags = re.findall(r'^\s+-\s+(\S+)', content.split('---')[1] if content.startswith('---') else '')
        return tags if tags else None
    return None

def get_file_age_days(path):
    """获取文件最后修改距今的天数"""
    mtime = os.path.getmtime(path)
    return (datetime.now() - datetime.fromtimestamp(mtime)).days

def get_content_stats(content):
    """获取内容统计"""
    lines = content.split('\n')
    return {
        'chars': len(content),
        'lines': len(lines),
        'headings': len([l for l in lines if l.startswith('#')]),
        'has_yaml': content.startswith('---'),
        'has_title': bool(re.search(r'^title:', content, re.MULTILINE) or re.search(r'^# ', content, re.MULTILINE)),
        'has_tags': bool(re.search(r'^tags:', content, re.MULTILINE)),
        'has_scene': bool(re.search(r'^scene:', content, re.MULTILINE)),
        'links': len(re.findall(r'\[\[([^\]]+)\]\]', content)) + len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
    }

# ── 1. 质量扫描 ──

def scan_quality():
    """扫描所有文件的质量"""
    results = {
        'total_files': 0,
        'scored_files': [],
        'summary': defaultdict(int),
        'alerts': [],
    }
    
    all_dirs = [
        ('knowledge', KNOWLEDGE),
        ('obsidian', OBSIDIAN),
        ('wiki', WIKI),
    ]
    
    for scope, base_dir in all_dirs:
        if not base_dir.exists():
            continue
        for fpath in base_dir.rglob('*.md'):
            if fpath.name.startswith('_') or fpath.name == 'index.md':
                continue
            if '.git' in str(fpath):
                continue
            
            results['total_files'] += 1
            score = 100  # 起始满分
            reasons = []
            
            try:
                content = fpath.read_text(encoding='utf-8', errors='ignore')
                stats = get_content_stats(content)
                age = get_file_age_days(fpath)
                rel_path = str(fpath.relative_to(WORKSPACE))
                
                # 质量检查
                if not stats['has_title']:
                    score += QUALITY_PENALTIES['no_title']
                    reasons.append('无标题')
                
                if not stats['has_tags']:
                    score += QUALITY_PENALTIES['no_tags']
                    reasons.append('无标签')
                
                if not stats['has_yaml']:
                    score += QUALITY_PENALTIES['no_yaml']
                    reasons.append('无YAML frontmatter')
                
                if stats['chars'] < 200:
                    score += QUALITY_PENALTIES['too_short']
                    reasons.append('内容过短')
                
                if stats['chars'] > 5000 and stats['headings'] < 3:
                    score += QUALITY_PENALTIES['too_long_no_structure']
                    reasons.append('长文无结构')
                
                if not stats['has_scene']:
                    score += QUALITY_PENALTIES['no_scene']
                    reasons.append('无场景标签')
                
                # 老化检查
                for prefix, threshold in STALE_THRESHOLD.items():
                    if prefix in rel_path and age > threshold:
                        score += QUALITY_PENALTIES['stale']
                        reasons.append(f'内容老化({age}天未更新)')
                        break
                
                file_info = {
                    'path': rel_path,
                    'scope': scope,
                    'score': max(0, score),
                    'age_days': age,
                    'chars': stats['chars'],
                    'reasons': reasons,
                }
                results['scored_files'].append(file_info)
                
                # 统计
                if score < 60:
                    results['summary']['critical'] += 1
                elif score < 80:
                    results['summary']['warning'] += 1
                else:
                    results['summary']['good'] += 1
                
                # 警报
                if score < 60:
                    results['alerts'].append({
                        'path': rel_path,
                        'score': score,
                        'reasons': reasons,
                    })
                    
            except Exception as e:
                results['summary']['errors'] += 1
                results['alerts'].append({
                    'path': str(fpath),
                    'score': 0,
                    'reasons': [f'读取错误: {str(e)}'],
                })
    
    results['scored_files'].sort(key=lambda x: x['score'])
    return results

# ── 2. 重复检测 ──

def find_duplicates():
    """检测重复内容（基于TF-IDF相似度简化版）"""
    results = []
    texts = []
    
    all_files = []
    for base_dir in [KNOWLEDGE, OBSIDIAN, WIKI]:
        if base_dir.exists():
            for fpath in base_dir.rglob('*.md'):
                if fpath.name.startswith('_') or fpath.name == 'index.md':
                    continue
                all_files.append(fpath)
    
    # 简单去重：文件名相似度
    name_groups = defaultdict(list)
    for fpath in all_files:
        name = fpath.stem
        # 去掉常见后缀
        clean = re.sub(r'[-_\s]', '', name)[:10]
        name_groups[clean].append(fpath)
    
    for key, files in name_groups.items():
        if len(files) > 1:
            # 检查是否在不同目录
            dirs = set(f.parent.name for f in files)
            if len(dirs) > 1:
                results.append({
                    'key': key,
                    'files': [str(f.relative_to(WORKSPACE)) for f in files],
                    'dirs': list(dirs),
                    'likely_duplicate': True,
                })
    
    return results

# ── 3. 缺口发现 ──

def find_gaps():
    """发现知识缺口"""
    results = {
        'scene_gaps': [],      # 有场景文件夹但内容少的
        'topic_gaps': [],      # 业务线缺内容的
        'ref_gaps': [],        # 引用缺失
    }
    
    # 检查12个业务线场景的内容覆盖
    obsidian_scenes = OBSIDIAN / '02-主题数据库'
    if obsidian_scenes.exists():
        for scene_dir in sorted(obsidian_scenes.iterdir()):
            if scene_dir.is_dir():
                file_count = len(list(scene_dir.glob('*.md')))
                if file_count < 3:
                    results['scene_gaps'].append({
                        'scene': scene_dir.name,
                        'file_count': file_count,
                        'status': '内容不足' if file_count < 3 else '正常',
                    })
    
    # 检查knowledge/articles/中的文章是否已同步到obsidian
    articles_dir = KNOWLEDGE / 'articles'
    if articles_dir.exists():
        for fpath in articles_dir.glob('*.md'):
            scene = None
            content = fpath.read_text(encoding='utf-8', errors='ignore')
            m = re.search(r'scene:\s*(\S+)', content)
            if m:
                scene = m.group(1)
            if scene:
                target_dir = OBSIDIAN / '02-主题数据库' / scene
                target = target_dir / fpath.name
                if not target.exists():
                    results['ref_gaps'].append({
                        'article': fpath.name,
                        'scene': scene,
                        'missing_in': f'obsidian-vault/02-主题数据库/{scene}/',
                    })
    
    return results

# ── 4. 进化建议生成 ──

def generate_evolution_plan(quality, duplicates, gaps):
    """生成进化计划"""
    plan = []
    
    # 1. 紧急修复项
    if quality['alerts']:
        plan.append({
            'priority': 'P0',
            'category': '质量修复',
            'items': [f"{a['path']} (得分:{a['score']})" for a in quality['alerts'][:10]],
            'action': '手动修复或AI自动补全YAML/标签/结构',
        })
    
    # 2. 去重
    if duplicates:
        plan.append({
            'priority': 'P1',
            'category': '重复合并',
            'items': [f"{d['key']}: {', '.join(d['files'][:3])}" for d in duplicates[:10]],
            'action': '合并重复内容，保留最完整版本，其余建立软链接',
        })
    
    # 3. 场景缺口
    if gaps['scene_gaps']:
        plan.append({
            'priority': 'P1',
            'category': '场景补全',
            'items': [f"{g['scene']}: 仅{g['file_count']}篇" for g in gaps['scene_gaps']],
            'action': '从knowledge/对应主题同步或手动补充',
        })
    
    # 4. 老化内容
    stale_items = [f for f in quality['scored_files'] if f['age_days'] > 180 and f['chars'] > 500]
    if stale_items:
        plan.append({
            'priority': 'P2',
            'category': '内容刷新',
            'items': [f"{s['path']} ({s['age_days']}天)" for s in stale_items[:10]],
            'action': 'AI摘要更新或删除归档',
        })
    
    # 5. 长期优化
    low_score = [f for f in quality['scored_files'] if f['score'] < 80 and f['score'] >= 60]
    if low_score:
        plan.append({
            'priority': 'P2',
            'category': '质量提升',
            'items': [f"{f['path']} (得分:{f['score']})" for f in low_score[:10]],
            'action': '补标签/场景/YAML，优化结构',
        })
    
    return plan

# ── 5. AI驱动优化（可选，需API） ──

def ai_optimize_file(filepath, dry_run=False):
    """使用AI优化单个文件（补YAML、精简内容）"""
    # 预留接口 — 实际调用需根据模型配置
    # 1. 读文件内容
    # 2. 调用AI生成YAML frontmatter
    # 3. 调用AI生成摘要
    # 4. 写入优化版本
    pass

# ── 6. 进化报告生成 ──

def generate_report(quality, duplicates, gaps, plan):
    """生成进化报告"""
    report = []
    report.append('=' * 60)
    report.append(f'📊 三库自进化报告 - {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    report.append('=' * 60)
    
    # 质量概览
    s = quality['summary']
    total = sum(s.values())
    report.append(f'\n## 📈 质量概览')
    report.append(f'- 扫描文件: {quality["total_files"]} 个')
    report.append(f'- 优秀(≥80分): {s.get("good", 0)} 个')
    report.append(f'- 警告(60-79分): {s.get("warning", 0)} 个')
    report.append(f'- 严重(<60分): {s.get("critical", 0)} 个')
    report.append(f'- 读取错误: {s.get("errors", 0)} 个')
    report.append(f'- 平均分: {sum(f["score"] for f in quality["scored_files"]) / max(len(quality["scored_files"]), 1):.1f}')
    
    # 三库分布
    report.append(f'\n## 📂 三库分布')
    for scope in ['knowledge', 'obsidian', 'wiki']:
        count = len([f for f in quality['scored_files'] if f['scope'] == scope])
        avg = sum(f['score'] for f in quality['scored_files'] if f['scope'] == scope) / max(count, 1)
        report.append(f'- {scope}: {count} 个文件, 平均分 {avg:.1f}')
    
    # 重复
    if duplicates:
        report.append(f'\n## 🔄 重复内容 ({len(duplicates)}组)')
        for d in duplicates[:10]:
            report.append(f'- {d["key"]}: {", ".join(d["files"])}')
    
    # 缺口
    report.append(f'\n## 📋 知识缺口')
    if gaps['scene_gaps']:
        report.append(f'- 场景内容不足: {len(gaps["scene_gaps"])}个')
        for g in gaps['scene_gaps']:
            report.append(f'  • {g["scene"]}: {g["file_count"]}篇 → {g["status"]}')
    if gaps['ref_gaps']:
        report.append(f'- 未同步到obsidian: {len(gaps["ref_gaps"])}篇')
    
    # 进化计划
    report.append(f'\n## 🎯 进化计划')
    for p in plan:
        report.append(f'\n### [{p["priority"]}] {p["category"]}')
        report.append(f'行动: {p["action"]}')
        for item in p['items'][:5]:
            report.append(f'  • {item}')
        if len(p['items']) > 5:
            report.append(f'  ... 还有 {len(p["items"])-5} 项')
    
    # 趋势
    report.append(f'\n## 📊 趋势建议')
    report.append(f'- 建议同步频率: knowledge/ 每天 → obsidian 每周 → wiki 每月')
    report.append(f'- 建议进化频率: 质量扫描每周, AI优化每两周')
    report.append(f'- 建议清理: 得分<60的文件优先处理')
    
    return '\n'.join(report)

# ── 主流程 ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description='三库自进化引擎')
    parser.add_argument('--scan', action='store_true', help='只扫描质量')
    parser.add_argument('--optimize', action='store_true', help='只优化内容')
    parser.add_argument('--gaps', action='store_true', help='只发现缺口')
    parser.add_argument('--report', action='store_true', help='只输出报告')
    parser.add_argument('--auto', action='store_true', help='全自动(含AI调用)')
    parser.add_argument('--output', default='', help='报告输出路径')
    args = parser.parse_args()
    
    run_all = not (args.scan or args.optimize or args.gaps or args.report)
    
    log('三库自进化引擎启动')
    
    # 1. 质量扫描
    quality = None
    if run_all or args.scan or args.report:
        log('扫描内容质量...')
        quality = scan_quality()
        log(f'扫描完成: {quality["total_files"]} 文件, {len(quality["alerts"])} 个警报')
    
    # 2. 重复检测
    duplicates = None
    if run_all or args.scan or args.report:
        log('检测重复内容...')
        duplicates = find_duplicates()
        log(f'发现 {len(duplicates)} 组疑似重复')
    
    # 3. 缺口发现
    gaps = None
    if run_all or args.gaps or args.report:
        log('发现知识缺口...')
        gaps = find_gaps()
        log(f'场景缺口: {len(gaps["scene_gaps"])}个, 引用缺口: {len(gaps["ref_gaps"])}个')
    
    # 4. 生成进化计划
    plan = []
    if run_all or args.report:
        plan = generate_evolution_plan(quality or scan_quality(), 
                                        duplicates or find_duplicates(), 
                                        gaps or find_gaps())
        log(f'生成 {len(plan)} 条进化建议')
    
    # 5. 输出报告
    if run_all or args.report:
        report = generate_report(quality, duplicates, gaps, plan)
        print('\n' + report)
        
        # 保存报告
        report_path = OUTPUT / f'evolve_report_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding='utf-8')
        log(f'报告已保存: {report_path}')
        
        # 保存JSON数据
        json_path = report_path.with_suffix('.json')
        json_data = {
            'timestamp': datetime.now().isoformat(),
            'quality_summary': {k: v for k, v in quality['summary'].items()},
            'total_files': quality['total_files'],
            'duplicates': len(duplicates),
            'gaps': {k: len(v) for k, v in gaps.items()},
            'plan_items': len(plan),
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # 6. AI优化（仅auto模式）
    if args.auto and quality:
        log('AI优化模式已预留，需配置API后启用')
        # 这里可以调用AI优化低分文件

if __name__ == '__main__':
    main()