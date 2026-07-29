#!/usr/bin/env python3
"""
融策记忆系统 — 遗忘引擎 & 垃圾回收 v1.0
═══════════════════════════════════════════
实现 Agent 长期记忆的主动遗忘机制：

功能：
  1. issue-age     — 疑点自动老化（P2/OBS超过阈值→expired）
  2. chunk-decay   — RAG chunk时效性衰减标记
  3. memory-prune  — MEMORY.md 条目清理建议
  4. cross-cleanup — 跨项目冗余检测
  5. status        — 记忆系统健康报告

设计原则：
  - "不知道该不该删" → 归档（不真删）
  - "确认无用" → 标记待清理 → 人工确认后删除
  - 所有删除操作有审计日志

用法:
  python scripts/memory_gc.py status                    # 健康报告
  python scripts/memory_gc.py issue-age --days 180      # 老化180天以上的疑点
  python scripts/memory_gc.py issue-age --dry-run       # 预览模式
  python scripts/memory_gc.py chunk-decay               # RAG chunk衰减标记
  python scripts/memory_gc.py memory-prune              # MEMORY.md清理建议
  python scripts/memory_gc.py auto                      # 一键自动维护
"""
import sys, os, json, re, math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

# === 配置 ===
WORKSPACE = Path(__file__).parent.parent
BLACKBOARD = WORKSPACE / 'audit-blackboard'
PROJECTS = BLACKBOARD / 'projects'
MEMORY_FILE = WORKSPACE / 'MEMORY.md'
META_FILE = WORKSPACE / '.rag_index' / 'triple_meta.json'
GC_LOG = WORKSPACE / 'logs' / 'memory_gc_log.jsonl'
ARCHIVE_DIR = WORKSPACE / 'knowledge' / 'archive' / 'memory_gc'

os.makedirs(GC_LOG.parent, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# === 老化阈值配置 ===
AGING_CONFIG = {
    'p0_retain_days': float('inf'),   # P0 永不自动过期
    'p1_retain_days': 365,             # P1 保留1年
    'p2_retain_days': 180,             # P2 保留半年
    'obs_retain_days': 90,             # OBS 保留3个月
    'chunk_decay_half_life': 180,      # RAG chunk半衰期
    'memory_prune_min_importance': 3,   # MEMORY.md条目重要性低于此分→建议清理
    'memory_prune_max_age_days': 365,   # MEMORY.md条目超过此天数→建议归档
    'dry_run': False,
}


def _log(action, detail):
    """写入GC审计日志"""
    entry = {
        'timestamp': datetime.now(CST).isoformat(),
        'action': action,
        'detail': detail,
    }
    with open(GC_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════
#  1. 疑点自动老化
# ═══════════════════════════════════════

def age_issues(days_threshold=None, dry_run=False):
    """
    遍历所有项目的issue_registry，将过期疑点标记为expired
    
    规则：
    - P0: 永不过期
    - P1: 超过 retain_days → 标记 expired_warning
    - P2: 超过 retain_days → 标记 expired
    - OBS: 超过 retain_days → 标记 expired
    - 已核实的(confirmed/excluded/in_report)不参与老化
    - 仅 pending 状态的未核实疑点才会被老化
    """
    if not PROJECTS.exists():
        print('❌ 项目目录不存在')
        return {'error': 'PROJECTS_DIR_NOT_FOUND'}
    
    summary = {
        'scanned_projects': 0,
        'scanned_issues': 0,
        'aged_issues': 0,
        'archived_issues': 0,
        'details': [],
    }
    
    for proj_dir in sorted(PROJECTS.iterdir()):
        if not proj_dir.is_dir():
            continue
        
        registry_path = proj_dir / 'fusion' / 'issue_registry.json'
        if not registry_path.exists():
            continue
        
        summary['scanned_projects'] += 1
        registry = _load_json(registry_path)
        modified = False
        now = datetime.now(CST)
        
        for issue_id, issue in registry.items():
            summary['scanned_issues'] += 1
            
            # 只对 pending 状态做老化
            if issue.get('status') != 'pending':
                continue
            
            severity = issue.get('severity', 'P2')
            created_str = issue.get('created_at', '')
            
            if not created_str:
                continue
            
            try:
                created = datetime.fromisoformat(created_str)
            except:
                continue
            
            age_days = (now - created).days
            
            # 确定保留天数
            retain_days_map = {
                'P0': AGING_CONFIG['p0_retain_days'],
                'P1': AGING_CONFIG['p1_retain_days'],
                'P2': days_threshold or AGING_CONFIG['p2_retain_days'],
                'OBS': days_threshold or AGING_CONFIG['obs_retain_days'],
            }
            retain_days = retain_days_map.get(severity, AGING_CONFIG['p2_retain_days'])
            
            if age_days <= retain_days:
                continue  # 未过期
            
            # 需要老化
            new_status = 'expired_warning' if severity == 'P1' else 'expired'
            
            detail = {
                'project': proj_dir.name,
                'issue_id': issue_id,
                'severity': severity,
                'age_days': age_days,
                'title': issue.get('title', '')[:80],
                'old_status': issue['status'],
                'new_status': new_status,
            }
            summary['details'].append(detail)
            summary['aged_issues'] += 1
            
            if not dry_run:
                issue['status'] = new_status
                issue['exclusion_reason'] = f'自动老化: 超过{retain_days}天未核实 (已存{age_days}天)'
                issue['updated_at'] = now.isoformat()
                issue['history'].append({
                    'action': f'pending → {new_status}',
                    'notes': f'GC自动老化: {age_days}天 > {retain_days}天阈值',
                    'timestamp': now.isoformat(),
                })
                modified = True
        
        if modified and not dry_run:
            _save_json(registry_path, registry)
            _log('issue_age', {
                'project': proj_dir.name,
                'aged_count': sum(1 for d in summary['details'] if d['project'] == proj_dir.name),
            })
    
    return summary


# ═══════════════════════════════════════
#  2. RAG chunk衰减标记
# ═══════════════════════════════════════

def decay_chunks(dry_run=False):
    """
    扫描RAG元数据，标记时效性过低的chunk
    不删除，只标记——供检索时降权或跳过
    """
    if not os.path.exists(META_FILE):
        return {'error': 'META_NOT_FOUND', 'message': '请先运行 memory_triple_scorer.py index'}
    
    meta = _load_json(META_FILE)
    now = datetime.now(CST)
    half_life = AGING_CONFIG['chunk_decay_half_life']
    
    decayed = []
    for source, info in meta.items():
        recency = info.get('recency', 1.0)
        
        # 时效性 < 0.1 的chunk（权重近乎为0）
        if recency < 0.1:
            decayed.append({
                'source': source,
                'recency': recency,
                'date': info.get('date_extracted', 'unknown'),
                'importance': info.get('importance', 0),
            })
    
    # 按重要性排序（优先保留重要文件）
    decayed.sort(key=lambda x: -x['importance'])
    
    result = {
        'total_chunks': len(meta),
        'decayed_chunks': len(decayed),
        'decay_ratio': f'{len(decayed)/max(len(meta),1)*100:.1f}%',
        'samples': decayed[:20],
    }
    
    if not dry_run and decayed:
        # 写入归档建议文件
        archive_report = {
            'generated_at': now.isoformat(),
            'half_life_days': half_life,
            'decayed_files': decayed,
            'recommendation': '以下文件时效性<0.1，建议归档或更新。高重要性文件请优先更新而非删除。',
        }
        archive_path = ARCHIVE_DIR / f'chunk_decay_report_{now.strftime("%Y%m%d")}.json'
        _save_json(archive_path, archive_report)
        result['report_path'] = str(archive_path)
        _log('chunk_decay', {'decayed_count': len(decayed)})
    
    return result


# ═══════════════════════════════════════
#  3. MEMORY.md 清理建议
# ═══════════════════════════════════════

def prune_memory_suggestions(dry_run=False):
    """
    分析MEMORY.md结构，识别可以清理的条目
    
    策略：
    - 按日期标记的条目（## YYYY-MM-DD）超过365天 → 建议归档
    - 条目内容过短（<100字符）且无链接 → 建议清理
    - 重复信息 → 建议合并
    """
    if not MEMORY_FILE.exists():
        return {'error': 'MEMORY_NOT_FOUND'}
    
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    now = datetime.now(CST)
    
    suggestions = []
    sections = []
    current_section = {'date': None, 'title': '', 'lines': [], 'line_start': 0}
    
    for i, line in enumerate(lines):
        # 检测日期标题 (## 2026-07-21)
        date_match = re.match(r'^##\s+(\d{4}-\d{2}-\d{2})', line)
        if date_match and current_section['lines']:
            sections.append(current_section)
            current_section = {
                'date': date_match.group(1),
                'title': line,
                'lines': [line],
                'line_start': i,
            }
        else:
            current_section['lines'].append(line)
    
    if current_section['lines']:
        sections.append(current_section)
    
    for sec in sections:
        if not sec['date']:
            continue
        
        try:
            sec_date = datetime.strptime(sec['date'], '%Y-%m-%d').replace(tzinfo=CST)
        except:
            continue
        
        age_days = (now - sec_date).days
        content_len = sum(len(l) for l in sec['lines'])
        
        # 超过365天且内容较少
        if age_days > AGING_CONFIG['memory_prune_max_age_days']:
            suggestions.append({
                'type': 'old_section',
                'date': sec['date'],
                'title': sec['title'].strip(),
                'age_days': age_days,
                'content_length': content_len,
                'suggestion': f'建议归档到 memory/archive/{sec["date"]}.md',
                'line': sec['line_start'] + 1,
            })
        # 内容过短（可能是过时的简短记录）
        elif content_len < 500 and age_days > 180:
            suggestions.append({
                'type': 'short_old_section',
                'date': sec['date'],
                'title': sec['title'].strip(),
                'age_days': age_days,
                'content_length': content_len,
                'suggestion': '内容较短且较旧，建议合并或删除',
                'line': sec['line_start'] + 1,
            })
    
    # 检查MEMORY.md总大小
    total_size_kb = len(content.encode('utf-8')) / 1024
    
    result = {
        'file': str(MEMORY_FILE),
        'total_size_kb': round(total_size_kb, 1),
        'total_sections': len(sections),
        'suggestions': suggestions,
        'suggestion_count': len(suggestions),
        'warning': 'MEMORY.md已超过20KB，建议拆分到memory/archive/' if total_size_kb > 20 else None,
    }
    
    if not dry_run:
        report_path = ARCHIVE_DIR / f'memory_prune_report_{now.strftime("%Y%m%d")}.json'
        _save_json(report_path, result)
        result['report_path'] = str(report_path)
    
    return result


# ═══════════════════════════════════════
#  4. 跨项目冗余检测
# ═══════════════════════════════════════

def cross_project_dedup(dry_run=False):
    """
    检测跨项目的重复/相似疑点
    同一entity在不同项目中反复出现 → 可能是系统性问题，值得保留并关联
    """
    if not PROJECTS.exists():
        return {'error': 'PROJECTS_DIR_NOT_FOUND'}
    
    # 收集所有项目的疑点
    all_issues = []
    for proj_dir in sorted(PROJECTS.iterdir()):
        if not proj_dir.is_dir():
            continue
        registry_path = proj_dir / 'fusion' / 'issue_registry.json'
        if not registry_path.exists():
            continue
        
        registry = _load_json(registry_path)
        for issue_id, issue in registry.items():
            if issue.get('status') in ('expired', 'excluded', 'archived'):
                continue
            
            all_issues.append({
                'project': proj_dir.name,
                'id': issue_id,
                'title': issue.get('title', ''),
                'category': issue.get('category', ''),
                'amount': issue.get('amount'),
                'severity': issue.get('severity', ''),
            })
    
    # 按类别+金额范围聚类
    clusters = defaultdict(list)
    for issue in all_issues:
        key = issue['category']
        clusters[key].append(issue)
    
    # 找出跨项目重复
    cross_hits = []
    for cat, issues in clusters.items():
        projects_involved = set(i['project'] for i in issues)
        if len(projects_involved) >= 2:
            # 同一类别在多个项目中出现
            cross_hits.append({
                'category': cat,
                'project_count': len(projects_involved),
                'projects': list(projects_involved),
                'total_issues': len(issues),
                'sample_titles': [i['title'][:60] for i in issues[:3]],
                'recommendation': '跨项目共性问题，建议保留并建立关联索引' if len(projects_involved) >= 3 else '观察中',
            })
    
    cross_hits.sort(key=lambda x: -x['project_count'])
    
    return {
        'total_issues': len(all_issues),
        'total_projects': len(set(i['project'] for i in all_issues)),
        'cross_project_patterns': len(cross_hits),
        'patterns': cross_hits[:10],
    }


# ═══════════════════════════════════════
#  5. 记忆系统健康报告
# ═══════════════════════════════════════

def health_report():
    """生成记忆系统全面健康报告"""
    now = datetime.now(CST)
    report = {
        'generated_at': now.isoformat(),
        'components': {},
        'alerts': [],
        'recommendations': [],
    }
    
    # --- RAG索引 ---
    rag_index = WORKSPACE / '.rag_index' / 'rag_index.json'
    if rag_index.exists():
        import pickle
        with open(rag_index, 'rb') as f:
            data = pickle.load(f)
        chunks_count = len(data['chunks'])
        rag_size_mb = os.path.getsize(rag_index) / (1024 * 1024)
        
        report['components']['rag_index'] = {
            'status': '✅',
            'chunks': chunks_count,
            'size_mb': round(rag_size_mb, 1),
        }
        if chunks_count > 20000:
            report['alerts'].append(f'⚠️ RAG chunks已达{chunks_count}，超过20000建议运行chunk-decay')
    else:
        report['components']['rag_index'] = {'status': '❌ 未找到'}
        report['alerts'].append('❌ RAG索引不存在，请运行 scripts/rag_rebuild.py')
    
    # --- 三重评分元数据 ---
    if os.path.exists(META_FILE):
        meta = _load_json(META_FILE)
        report['components']['triple_meta'] = {
            'status': '✅',
            'files_indexed': len(meta),
        }
    else:
        report['components']['triple_meta'] = {'status': '⚠️ 未构建'}
        report['recommendations'].append('运行 memory_triple_scorer.py index 构建三重评分元数据')
    
    # --- 项目疑点统计 ---
    if PROJECTS.exists():
        total_issues = 0
        pending_issues = 0
        aged_issues = 0
        project_count = 0
        
        for proj_dir in PROJECTS.iterdir():
            if not proj_dir.is_dir():
                continue
            registry_path = proj_dir / 'fusion' / 'issue_registry.json'
            if not registry_path.exists():
                continue
            
            project_count += 1
            registry = _load_json(registry_path)
            total_issues += len(registry)
            
            for issue in registry.values():
                if issue.get('status') == 'pending':
                    pending_issues += 1
                if issue.get('status') in ('expired', 'expired_warning'):
                    aged_issues += 1
        
        report['components']['issue_registry'] = {
            'status': '✅',
            'projects': project_count,
            'total_issues': total_issues,
            'pending': pending_issues,
            'aged': aged_issues,
        }
        
        if pending_issues > 100:
            report['alerts'].append(f'⚠️ 累计{pending_issues}条待核实疑点，建议运行issue-age')
    else:
        report['components']['issue_registry'] = {'status': 'ℹ️ 无项目'}
    
    # --- MEMORY.md ---
    if MEMORY_FILE.exists():
        size_kb = os.path.getsize(MEMORY_FILE) / 1024
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = len(content.split('\n'))
        
        report['components']['memory_md'] = {
            'status': '✅',
            'size_kb': round(size_kb, 1),
            'lines': lines,
        }
        if size_kb > 20:
            report['alerts'].append(f'⚠️ MEMORY.md 已达{size_kb:.0f}KB，建议运行memory-prune')
    else:
        report['components']['memory_md'] = {'status': '❌ 未找到'}
    
    # --- GC日志 ---
    if os.path.exists(GC_LOG):
        gc_size = os.path.getsize(GC_LOG)
        report['components']['gc_log'] = {
            'status': '✅',
            'size_bytes': gc_size,
        }
    
    # --- 综合评分 ---
    alert_count = len(report['alerts'])
    if alert_count == 0:
        report['health_score'] = '🟢 健康'
    elif alert_count <= 2:
        report['health_score'] = '🟡 需关注'
    else:
        report['health_score'] = '🔴 需立即维护'
    
    return report


# ═══════════════════════════════════════
#  6. 一键自动维护
# ═══════════════════════════════════════

def auto_maintain():
    """一键运行所有维护任务"""
    print('═══ 融策记忆系统自动维护 ═══\n')
    
    # 1. 健康检查
    print('📊 健康检查...')
    health = health_report()
    print(f'   综合评分: {health["health_score"]}')
    for alert in health['alerts']:
        print(f'   {alert}')
    
    # 2. 疑点老化
    print('\n🗑️  疑点老化...')
    age_result = age_issues(dry_run=False)
    print(f'   扫描 {age_result["scanned_projects"]} 个项目, {age_result["scanned_issues"]} 条疑点')
    print(f'   老化 {age_result["aged_issues"]} 条')
    for detail in age_result.get('details', [])[:5]:
        print(f'   [{detail["severity"]}] {detail["project"]}: {detail["title"][:50]} → {detail["new_status"]}')
    
    # 3. Chunk衰减
    print('\n📉 Chunk衰减...')
    decay_result = decay_chunks(dry_run=False)
    if 'error' not in decay_result:
        print(f'   总chunks: {decay_result.get("total_chunks", "?")}')
        print(f'   低时效chunks: {decay_result.get("decayed_chunks", 0)} ({decay_result.get("decay_ratio", "?")})')
    
    # 4. MEMORY.md检查
    print('\n📝 MEMORY.md检查...')
    prune_result = prune_memory_suggestions(dry_run=False)
    if 'error' not in prune_result:
        print(f'   大小: {prune_result.get("total_size_kb", "?")}KB')
        print(f'   清理建议: {prune_result.get("suggestion_count", 0)} 条')
        if prune_result.get('warning'):
            print(f'   ⚠️ {prune_result["warning"]}')
    
    # 5. 跨项目冗余
    print('\n🔗 跨项目冗余检测...')
    cross = cross_project_dedup()
    if 'error' not in cross:
        print(f'   跨项目共性问题: {cross.get("cross_project_patterns", 0)} 类')
    
    print(f'\n✅ 维护完成。详细日志: {GC_LOG}')
    
    _log('auto_maintain', {'health_score': health['health_score']})
    
    return {
        'health': health,
        'aging': age_result,
        'decay': decay_result,
        'prune': prune_result,
        'cross': cross,
    }


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def print_health(report):
    """美化输出健康报告"""
    print(f'\n{"="*60}')
    print(f'🧠 融策记忆系统健康报告')
    print(f'   生成时间: {report["generated_at"]}')
    print(f'   综合评分: {report["health_score"]}')
    print(f'{"="*60}')
    
    for name, comp in report['components'].items():
        status = comp.get('status', '?')
        details = {k: v for k, v in comp.items() if k != 'status'}
        detail_str = ' | '.join(f'{k}: {v}' for k, v in details.items())
        print(f'  {status} {name}: {detail_str}')
    
    if report['alerts']:
        print(f'\n  🚨 告警:')
        for alert in report['alerts']:
            print(f'     {alert}')
    
    if report['recommendations']:
        print(f'\n  💡 建议:')
        for rec in report['recommendations']:
            print(f'     {rec}')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策记忆系统遗忘引擎 v1.0')
    sub = parser.add_subparsers(dest='command')
    
    p_status = sub.add_parser('status', help='记忆系统健康报告')
    
    p_age = sub.add_parser('issue-age', help='疑点自动老化')
    p_age.add_argument('--days', type=int, default=None, help='老化阈值天数（覆盖默认配置）')
    p_age.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改')
    
    p_decay = sub.add_parser('chunk-decay', help='RAG chunk衰减标记')
    p_decay.add_argument('--dry-run', action='store_true')
    
    p_prune = sub.add_parser('memory-prune', help='MEMORY.md清理建议')
    p_prune.add_argument('--dry-run', action='store_true')
    
    p_cross = sub.add_parser('cross-dedup', help='跨项目冗余检测')
    
    p_auto = sub.add_parser('auto', help='一键自动维护')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        report = health_report()
        print_health(report)
    
    elif args.command == 'issue-age':
        result = age_issues(days_threshold=args.days, dry_run=args.dry_run)
        if args.dry_run:
            print(f'\n🧪 预览模式 — 以下疑点将被老化:')
            for d in result.get('details', []):
                print(f'  [{d["severity"]}] {d["project"]:20s} | {d["age_days"]:4d}天 | {d["title"][:50]} → {d["new_status"]}')
        print(f'\n扫描 {result["scanned_projects"]} 个项目, {result["scanned_issues"]} 条疑点')
        print(f'老化 {result["aged_issues"]} 条')
        if not args.dry_run and result['aged_issues'] > 0:
            print(f'✅ 已写入，日志: {GC_LOG}')
    
    elif args.command == 'chunk-decay':
        result = decay_chunks(dry_run=args.dry_run)
        if 'error' in result:
            print(f'❌ {result["message"]}')
        else:
            print(f'总chunks: {result["total_chunks"]}')
            print(f'低时效chunks: {result["decayed_chunks"]} ({result["decay_ratio"]})')
            if result.get('samples'):
                print(f'\n示例（前5）:')
                for s in result['samples'][:5]:
                    print(f'  [{s["recency"]:.2f}] {s["source"]}')
            if result.get('report_path'):
                print(f'\n📄 报告: {result["report_path"]}')
    
    elif args.command == 'memory-prune':
        result = prune_memory_suggestions(dry_run=args.dry_run)
        if 'error' in result:
            print(f'❌ {result["message"]}')
        else:
            print(f'MEMORY.md: {result["total_size_kb"]}KB, {result["total_sections"]} 章节')
            print(f'清理建议: {result["suggestion_count"]} 条')
            if result.get('warning'):
                print(f'⚠️ {result["warning"]}')
            for s in result.get('suggestions', []):
                print(f'  [{s["type"]}] {s["date"]} ({s["age_days"]}天前): {s["title"][:60]}')
    
    elif args.command == 'cross-dedup':
        result = cross_project_dedup()
        if 'error' in result:
            print(f'❌ {result["message"]}')
        else:
            print(f'跨项目分析: {result["total_issues"]} 条疑点, {result["total_projects"]} 个项目')
            print(f'共性问题: {result["cross_project_patterns"]} 类\n')
            for p in result.get('patterns', []):
                print(f'  [{p["project_count"]}个项目] {p["category"]}')
                print(f'    {p["recommendation"]}')
                for t in p['sample_titles']:
                    print(f'    · {t}')
    
    elif args.command == 'auto':
        auto_maintain()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
