# -*- coding: utf-8 -*-
"""
疑点融合中枢 v1.0 — Issue Fusion Hub
====================================
三模型联合评审一致认定的最致命缺失。

功能：
  accept:  接收各Agent的findings/*.json，标准化入库
  cluster: 跨Agent聚类——同一问题被多个Agent发现→合并
  dedup:   去重——去除重复/高度相似的疑点
  resolve: 冲突消解——Agent A说异常Agent B说合规→标记人工裁决
  index:   统一编号（F-001, F-002...），生成待核实清单
  track:   状态流转——pending→confirmed→excluded→in_report→archived
  chain:   证据链追踪——每个疑点绑定的原始证据+Agent推理链

用法:
  python issue_fusion.py accept --project "XX项目"
  python issue_fusion.py cluster --project "XX项目"
  python issue_fusion.py report --project "XX项目"
  python issue_fusion.py track --project "XX项目" --id "F-001" --status "confirmed"
"""
import os, sys, json, argparse, hashlib, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

# === 路径 ===
WORKSPACE = Path(__file__).parent.parent
PROJECTS = WORKSPACE / 'audit-blackboard' / 'projects'

# === 疑点状态机 ===
ISSUE_STATES = ['pending', 'confirmed', 'excluded', 'in_report', 'archived']
STATE_TRANSITIONS = {
    'pending':    ['confirmed', 'excluded'],
    'confirmed':  ['in_report', 'excluded', 'pending'],
    'excluded':   ['pending'],  # 可重新激活
    'in_report':  ['archived', 'pending'],
    'archived':   [],
}

# === 疑点严重度 ===
SEVERITY = {'P0': '重大问题', 'P1': '重要问题', 'P2': '一般问题', 'OBS': '观察项'}

# ============================================================
#  1. 接收Agent发现，标准化入库
# ============================================================
def accept_findings(project_slug):
    """读取 findings/*.json → 标准化 → 写入 issue_registry.json"""
    project_dir = PROJECTS / project_slug
    findings_dir = project_dir / 'findings'
    fusion_dir = project_dir / 'fusion'
    fusion_dir.mkdir(exist_ok=True)

    registry_path = fusion_dir / 'issue_registry.json'
    existing = _load_json(registry_path) if registry_path.exists() else {}

    findings_files = list(findings_dir.glob('*.json')) if findings_dir.exists() else []

    accepted = 0
    for ff in findings_files:
        agent_name = ff.stem
        data = _load_json(ff)
        if not data:
            continue

        items = data if isinstance(data, list) else data.get('findings', [])
        if not isinstance(items, list):
            items = [items]

        for item in items:
            # 生成唯一ID（基于内容哈希）
            content_str = json.dumps(item, ensure_ascii=False, sort_keys=True)
            item_hash = hashlib.md5(content_str.encode()).hexdigest()[:12]
            issue_id = f"F-{item_hash}"

            if issue_id in existing:
                # 已有此疑点 → 追加来源Agent
                existing[issue_id]['sources'].append(agent_name)
                existing[issue_id]['source_count'] = len(set(existing[issue_id]['sources']))
            else:
                # 新疑点
                existing[issue_id] = {
                    'id': issue_id,
                    'sources': [agent_name],
                    'source_count': 1,
                    'title': item.get('title', item.get('issue', item.get('finding', ''))),
                    'description': item.get('description', item.get('detail', '')),
                    'category': item.get('category', '未分类'),
                    'amount': item.get('amount', item.get('涉及金额', None)),
                    'law_ref': item.get('law_ref', item.get('法规依据', '')),
                    'evidence': item.get('evidence', item.get('证据', [])),
                    'confidence': item.get('confidence', item.get('置信度', 'medium')),
                    'severity': item.get('severity', item.get('严重度', 'P2')),
                    'status': 'pending',
                    'created_at': datetime.now(CST).isoformat(),
                    'updated_at': datetime.now(CST).isoformat(),
                    'history': [{
                        'action': 'created',
                        'agent': agent_name,
                        'timestamp': datetime.now(CST).isoformat(),
                    }],
                    'human_notes': '',
                    'human_status': '',
                    'exclusion_reason': '',
                    'verified_by': '',
                    'verified_at': '',
                    'linked_issues': [],
                    'report_section': '',
                }
                accepted += 1

    # 写回registry
    _save_json(registry_path, existing)

    # 按严重度统计
    severity_counts = defaultdict(int)
    source_counts = defaultdict(int)
    for issue in existing.values():
        severity_counts[issue['severity']] += 1
        for src in issue['sources']:
            source_counts[src] += 1

    return {
        'status': 'accepted',
        'project': project_slug,
        'total_issues': len(existing),
        'newly_accepted': accepted,
        'by_severity': dict(severity_counts),
        'by_agent': dict(source_counts),
        'multi_source': sum(1 for i in existing.values() if i['source_count'] > 1),
        'registry_path': str(registry_path),
    }


# ============================================================
#  2. 跨Agent聚类：合并相同疑点
# ============================================================
def cluster_issues(project_slug):
    """对registry中的疑点做聚类合并"""
    project_dir = PROJECTS / project_slug
    registry_path = project_dir / 'fusion' / 'issue_registry.json'

    if not registry_path.exists():
        return {'status': 'error', 'message': '请先运行 accept'}

    registry = _load_json(registry_path)

    # 聚类规则：按 类别+涉及金额范围+关键词 合并
    clusters = defaultdict(list)
    for issue_id, issue in registry.items():
        # 聚类键：类别 + 金额万级
        amount_key = 'no_amount'
        if issue.get('amount'):
            try:
                amt = float(str(issue['amount']).replace(',', '').replace('元', '').replace('万', ''))
                amount_key = f"{int(amt // 10000)}万级"
            except:
                pass
        cluster_key = f"{issue.get('category', '')}|{amount_key}"
        clusters[cluster_key].append(issue_id)

    # 合并：同一cluster中相似的issue
    merges = []
    for key, ids in clusters.items():
        if len(ids) < 2:
            continue
        # 简单合并策略：保留第一个，其余标记为duplicate
        primary = ids[0]
        for dup_id in ids[1:]:
            # 标题相似度检查（简单关键词重叠）
            primary_title = set(registry[primary]['title'])
            dup_title = set(registry[dup_id]['title'])
            overlap = len(primary_title & dup_title) / max(len(primary_title | dup_title), 1)

            if overlap > 0.3 or registry[primary]['amount'] == registry[dup_id]['amount']:
                # 合并
                registry[primary]['sources'] = list(set(
                    registry[primary]['sources'] + registry[dup_id]['sources']
                ))
                registry[primary]['source_count'] = len(set(registry[primary]['sources']))
                registry[primary]['linked_issues'].append(dup_id)
                registry[primary]['description'] += f"\n[合并自{dup_id}]: {registry[dup_id]['description']}"
                registry[primary]['evidence'].extend(registry[dup_id].get('evidence', []))
                registry[primary]['history'].append({
                    'action': 'merged',
                    'merged_from': dup_id,
                    'reason': f'内容相似度{overlap:.0%}',
                    'timestamp': datetime.now(CST).isoformat(),
                })
                # 标记被合并的为duplicate
                registry[dup_id]['status'] = 'excluded'
                registry[dup_id]['exclusion_reason'] = 'auto_merged'
                registry[dup_id]['history'].append({
                    'action': 'merged_into',
                    'merged_into': primary,
                    'timestamp': datetime.now(CST).isoformat(),
                })
                merges.append(f"{dup_id} → {primary}")

    _save_json(registry_path, registry)

    active = sum(1 for i in registry.values() if i['status'] != 'excluded')

    return {
        'status': 'clustered',
        'project': project_slug,
        'total_before': len(registry),
        'total_after': active,
        'merges': len(merges),
        'merge_details': merges[:10],
    }


# ============================================================
#  3. 生成统一疑点清单（待现场核实用）
# ============================================================
def generate_report(project_slug):
    """生成分级疑点清单"""
    project_dir = PROJECTS / project_slug
    registry_path = project_dir / 'fusion' / 'issue_registry.json'

    if not registry_path.exists():
        return {'status': 'error', 'message': '请先运行 accept → cluster'}

    registry = _load_json(registry_path)

    # 仅取active的疑点
    active = {k: v for k, v in registry.items() if v['status'] != 'excluded'}
    pending = {k: v for k, v in active.items() if v['status'] == 'pending'}

    # 按严重度分组
    by_severity = defaultdict(list)
    for issue in pending.values():
        by_severity[issue['severity']].append(issue)

    # 按多源确认>单源排序
    for sev in by_severity:
        by_severity[sev].sort(key=lambda x: -x['source_count'])

    # 生成待核实清单
    checklist = []
    counter = 1
    for sev in ['P0', 'P1', 'P2', 'OBS']:
        for issue in by_severity.get(sev, []):
            checklist.append({
                '序号': counter,
                '编号': issue['id'],
                '严重度': sev,
                '来源': ' + '.join(issue['sources']),
                '多源确认': '★' * issue['source_count'] if issue['source_count'] > 1 else '',
                '问题描述': issue['title'],
                '涉及金额': issue.get('amount', ''),
                '法规依据': issue.get('law_ref', ''),
                '证据清单': issue.get('evidence', []),
                'AI置信度': issue.get('confidence', ''),
                '核实状态': '待核实',
                '现场核实结果': '',
                '核实人': '',
                '备注': '',
            })
            counter += 1

    # 输出
    report_path = project_dir / 'outputs' / '问题清单' / '疑点核实清单.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _save_json(report_path, {'issues': checklist, 'generated_at': datetime.now(CST).isoformat()})

    # 也生成Markdown版
    md_path = project_dir / 'outputs' / '问题清单' / '疑点核实清单.md'
    md_lines = [
        f"# 疑点核实清单 — {project_slug}",
        f"生成时间：{datetime.now(CST).strftime('%Y-%m-%d %H:%M')}",
        f"共 {len(checklist)} 条疑点（P0: {len(by_severity.get('P0',[]))} / P1: {len(by_severity.get('P1',[]))} / P2: {len(by_severity.get('P2',[]))}）",
        "",
        "| 序号 | 编号 | 严重度 | 来源 | 多源确认 | 问题描述 | 涉及金额 | 核实状态 |",
        "|:--:|:--|:--:|------|:--:|------|:--:|:--:|",
    ]
    for item in checklist:
        md_lines.append(
            f"| {item['序号']} | {item['编号']} | **{item['严重度']}** | {item['来源']} | "
            f"{item['多源确认']} | {item['问题描述'][:40]} | {item['涉及金额']} | {item['核实状态']} |"
        )
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')

    return {
        'status': 'generated',
        'project': project_slug,
        'total_active': len(active),
        'total_pending': len(pending),
        'by_severity': {s: len(v) for s, v in by_severity.items()},
        'multi_source_count': sum(1 for i in pending.values() if i['source_count'] > 1),
        'report_path': str(report_path),
        'md_path': str(md_path),
    }


# ============================================================
#  4. 状态追踪
# ============================================================
def track_issue(project_slug, issue_id, new_status, notes='', verified_by=''):
    """更新单条疑点状态"""
    project_dir = PROJECTS / project_slug
    registry_path = project_dir / 'fusion' / 'issue_registry.json'

    if not registry_path.exists():
        return {'status': 'error', 'message': 'issue_registry.json 不存在'}

    registry = _load_json(registry_path)

    if issue_id not in registry:
        return {'status': 'error', 'message': f'疑点 {issue_id} 不存在'}

    issue = registry[issue_id]
    old_status = issue['status']

    if new_status not in ISSUE_STATES:
        return {'status': 'error', 'message': f'无效状态: {new_status}，可选: {ISSUE_STATES}'}

    issue['status'] = new_status
    issue['updated_at'] = datetime.now(CST).isoformat()

    if notes:
        issue['human_notes'] = notes
    if verified_by:
        issue['verified_by'] = verified_by
        issue['verified_at'] = datetime.now(CST).isoformat()

    if new_status == 'excluded':
        issue['exclusion_reason'] = notes or '人工排除'
    elif new_status == 'confirmed':
        issue['human_status'] = 'confirmed_by_human'

    issue['history'].append({
        'action': f'{old_status} → {new_status}',
        'notes': notes,
        'verified_by': verified_by,
        'timestamp': datetime.now(CST).isoformat(),
    })

    _save_json(registry_path, registry)

    return {
        'status': 'updated',
        'issue_id': issue_id,
        'old_status': old_status,
        'new_status': new_status,
        'title': issue['title'],
    }


# ============================================================
#  5. 证据链报告（单条疑点的完整追踪）
# ============================================================
def evidence_chain(project_slug, issue_id):
    """输出单条疑点的完整证据链"""
    project_dir = PROJECTS / project_slug
    registry_path = project_dir / 'fusion' / 'issue_registry.json'

    if not registry_path.exists():
        return {'status': 'error', 'message': 'issue_registry.json 不存在'}

    registry = _load_json(registry_path)

    if issue_id not in registry:
        return {'status': 'error', 'message': f'疑点 {issue_id} 不存在'}

    issue = registry[issue_id]

    chain = {
        'issue_id': issue_id,
        'title': issue['title'],
        'status': issue['status'],
        'severity': issue['severity'],
        'evidence_chain': {
            'discovery': {
                'agents': issue['sources'],
                'source_count': issue['source_count'],
                'reliability': '高（多源交叉确认）' if issue['source_count'] > 1 else '中（单源，待验证）',
            },
            'description': issue['description'],
            'amount': issue.get('amount'),
            'law_basis': issue.get('law_ref'),
            'raw_evidence': issue.get('evidence', []),
            'confidence': issue.get('confidence'),
        },
        'verification': {
            'status': issue['status'],
            'verified_by': issue.get('verified_by', ''),
            'verified_at': issue.get('verified_at', ''),
            'human_notes': issue.get('human_notes', ''),
            'exclusion_reason': issue.get('exclusion_reason', ''),
        },
        'linked_issues': issue.get('linked_issues', []),
        'history': issue['history'],
    }

    return chain


# ============================================================
#  6. 冲突检测：标记Agent结论矛盾
# ============================================================
def detect_conflicts(project_slug):
    """检测registry中是否存在Agent结论矛盾（需人工裁决）"""
    project_dir = PROJECTS / project_slug
    registry_path = project_dir / 'fusion' / 'issue_registry.json'

    if not registry_path.exists():
        return {'status': 'error', 'message': '请先运行 accept'}

    registry = _load_json(registry_path)

    conflicts = []
    for issue_id, issue in registry.items():
        if issue['status'] == 'excluded':
            continue
        # 检查confidence标记
        if issue.get('confidence') in ('low', 'uncertain'):
            conflicts.append({
                'issue_id': issue_id,
                'title': issue['title'],
                'reason': f"AI置信度低（{issue['confidence']}），建议人工确认",
                'action': 'manual_review',
            })

    return {
        'status': 'detected',
        'project': project_slug,
        'conflict_count': len(conflicts),
        'conflicts': conflicts,
    }


# ============================================================
#  工具函数
# ============================================================
def _load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
#  CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='疑点融合中枢 v1.0')
    subparsers = parser.add_subparsers(dest='command')

    # accept
    p = subparsers.add_parser('accept', help='接收各Agent发现→标准化入库')
    p.add_argument('--project', required=True)

    # cluster
    p = subparsers.add_parser('cluster', help='跨Agent聚类+去重+冲突标记')
    p.add_argument('--project', required=True)

    # report
    p = subparsers.add_parser('report', help='生成统一疑点核实清单')
    p.add_argument('--project', required=True)

    # track
    p = subparsers.add_parser('track', help='更新疑点状态')
    p.add_argument('--project', required=True)
    p.add_argument('--id', required=True, help='疑点编号（如 F-abc123）')
    p.add_argument('--status', required=True, choices=ISSUE_STATES)
    p.add_argument('--notes', default='')
    p.add_argument('--verified-by', default='')

    # chain
    p = subparsers.add_parser('chain', help='查看单条疑点的完整证据链')
    p.add_argument('--project', required=True)
    p.add_argument('--id', required=True)

    # conflicts
    p = subparsers.add_parser('conflicts', help='检测Agent结论矛盾')
    p.add_argument('--project', required=True)

    # full
    p = subparsers.add_parser('full', help='一键执行 accept → cluster → report → conflicts')
    p.add_argument('--project', required=True)

    args = parser.parse_args()

    if args.command == 'accept':
        result = accept_findings(args.project)
    elif args.command == 'cluster':
        result = cluster_issues(args.project)
    elif args.command == 'report':
        result = generate_report(args.project)
    elif args.command == 'track':
        result = track_issue(args.project, args.id, args.status, args.notes, getattr(args, 'verified_by', ''))
    elif args.command == 'chain':
        result = evidence_chain(args.project, args.id)
    elif args.command == 'conflicts':
        result = detect_conflicts(args.project)
    elif args.command == 'full':
        print(">>> Step 1/4: 接收Agent发现...")
        r1 = accept_findings(args.project)
        print(json.dumps(r1, ensure_ascii=False, indent=2))

        print("\n>>> Step 2/4: 跨Agent聚类去重...")
        r2 = cluster_issues(args.project)
        print(json.dumps(r2, ensure_ascii=False, indent=2))

        print("\n>>> Step 3/4: 生成统一疑点清单...")
        r3 = generate_report(args.project)
        print(json.dumps(r3, ensure_ascii=False, indent=2))

        print("\n>>> Step 4/4: 检测Agent结论冲突...")
        r4 = detect_conflicts(args.project)
        print(json.dumps(r4, ensure_ascii=False, indent=2))
        return
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
