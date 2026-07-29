#!/usr/bin/env python3
"""
融策自进化系统 L3 — 受限修改提案器 v1.0
═══════════════════════════════════════
"能改prompt/skill/hook/memory，但走PR形态、走git、设作用域分级。"

原则:
  - Agent只能提提案，不能直接改
  - 所有修改必须有diff记录
  - 作用域分级: L0冻结/L1人类独占/L2门控/L3自动
  - 提案必须通过L4评估才能合并

用法:
  python self_evolve/mutation_proposer.py propose --agent contract_hound --signal signals.json
  python self_evolve/mutation_proposer.py list
  python self_evolve/mutation_proposer.py review --id P-001
"""
import sys, os, json, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

MODULE_DIR = Path(__file__).parent
PROPOSALS_DIR = MODULE_DIR / 'proposals'
SNAPSHOTS_DIR = MODULE_DIR / 'snapshots'
os.makedirs(PROPOSALS_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# ═══════════════════════════════════════
#  提案模板
# ═══════════════════════════════════════

PROPOSAL_TEMPLATE = {
    'proposal_id': '',           # P-YYYYMMDD-序号
    'version': '1.0',
    'status': 'draft',           # draft → proposed → review → approved → applied → verified | rejected
    'agent': '',
    'created_at': '',
    'signal_source': {},         # 触发此提案的信号
    'target_files': [],          # 要修改的文件
    'mutation_level': '',        # L0/L1/L2/L3
    'change_summary': '',
    'before_snapshot': '',       # 修改前快照路径
    'diff': {},                  # {file: {old: ..., new: ...}}
    'eval_required': True,
    'eval_result': None,
    'governance_check': None,
    'reviews': [],               # [{reviewer, decision, comment, timestamp}]
    'applied_at': None,
    'rollback_snapshot': '',
}


# ═══════════════════════════════════════
#  快照管理
# ═══════════════════════════════════════

def create_snapshot(target_files):
    """为指定文件创建快照"""
    snapshot_id = datetime.now(CST).strftime('%Y%m%d_%H%M%S')
    snapshot = {
        'snapshot_id': snapshot_id,
        'created_at': datetime.now(CST).isoformat(),
        'files': {},
    }
    
    for tf in target_files:
        # 解析文件路径
        workspace = Path(__file__).parent.parent.parent
        full_path = workspace / tf
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                snapshot['files'][tf] = f.read()
    
    snapshot_path = SNAPSHOTS_DIR / f'snapshot_{snapshot_id}.json'
    with open(snapshot_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    
    return str(snapshot_path), snapshot_id


def restore_snapshot(snapshot_id):
    """回滚到指定快照"""
    snapshot_path = SNAPSHOTS_DIR / f'snapshot_{snapshot_id}.json'
    if not snapshot_path.exists():
        return {'error': f'快照 {snapshot_id} 不存在'}
    
    with open(snapshot_path, 'r', encoding='utf-8') as f:
        snapshot = json.load(f)
    
    workspace = Path(__file__).parent.parent.parent
    restored = []
    
    for tf, content in snapshot['files'].items():
        full_path = workspace / tf
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        restored.append(tf)
    
    return {
        'status': 'restored',
        'snapshot_id': snapshot_id,
        'restored_files': restored,
    }


# ═══════════════════════════════════════
#  提案管理
# ═══════════════════════════════════════

def create_proposal(agent, signal_data, target_files, change_summary):
    """创建修改提案"""
    now = datetime.now(CST)
    seq = len(list(PROPOSALS_DIR.glob('*.json'))) + 1
    proposal_id = f'P-{now.strftime("%Y%m%d")}-{seq:03d}'
    
    # 创建快照
    snapshot_path, snapshot_id = create_snapshot(target_files)
    
    proposal = dict(PROPOSAL_TEMPLATE)
    proposal.update({
        'proposal_id': proposal_id,
        'agent': agent,
        'created_at': now.isoformat(),
        'signal_source': signal_data,
        'target_files': target_files,
        'change_summary': change_summary,
        'before_snapshot': snapshot_path,
    })
    
    proposal_path = PROPOSALS_DIR / f'{proposal_id}.json'
    with open(proposal_path, 'w', encoding='utf-8') as f:
        json.dump(proposal, f, ensure_ascii=False, indent=2)
    
    return proposal


def list_proposals(status=None):
    """列出所有提案"""
    proposals = []
    for pf in sorted(PROPOSALS_DIR.glob('*.json')):
        with open(pf, 'r', encoding='utf-8') as f:
            p = json.load(f)
        if status and p.get('status') != status:
            continue
        proposals.append({
            'id': p['proposal_id'],
            'agent': p['agent'],
            'status': p['status'],
            'files': p['target_files'],
            'summary': p['change_summary'][:80],
            'created': p['created_at'],
        })
    return proposals


def review_proposal(proposal_id, decision, reviewer='human', comment=''):
    """审核提案"""
    proposal_path = PROPOSALS_DIR / f'{proposal_id}.json'
    if not proposal_path.exists():
        return {'error': f'提案 {proposal_id} 不存在'}
    
    with open(proposal_path, 'r', encoding='utf-8') as f:
        proposal = json.load(f)
    
    now = datetime.now(CST).isoformat()
    proposal['reviews'].append({
        'reviewer': reviewer,
        'decision': decision,
        'comment': comment,
        'timestamp': now,
    })
    
    if decision == 'approved':
        proposal['status'] = 'approved'
    elif decision == 'rejected':
        proposal['status'] = 'rejected'
    elif decision == 'needs_changes':
        proposal['status'] = 'needs_changes'
    
    with open(proposal_path, 'w', encoding='utf-8') as f:
        json.dump(proposal, f, ensure_ascii=False, indent=2)
    
    return {'status': 'reviewed', 'proposal_id': proposal_id, 'decision': decision}


def apply_proposal(proposal_id):
    """应用已批准的提案（实际修改文件）"""
    proposal_path = PROPOSALS_DIR / f'{proposal_id}.json'
    if not proposal_path.exists():
        return {'error': f'提案 {proposal_id} 不存在'}
    
    with open(proposal_path, 'r', encoding='utf-8') as f:
        proposal = json.load(f)
    
    if proposal['status'] != 'approved':
        return {'error': f'提案 {proposal_id} 状态为 {proposal["status"]}，不能应用'}
    
    workspace = Path(__file__).parent.parent.parent
    applied = []
    
    for tf, diff in proposal.get('diff', {}).items():
        full_path = workspace / tf
        new_content = diff.get('new', '')
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        applied.append(tf)
    
    proposal['status'] = 'applied'
    proposal['applied_at'] = datetime.now(CST).isoformat()
    
    with open(proposal_path, 'w', encoding='utf-8') as f:
        json.dump(proposal, f, ensure_ascii=False, indent=2)
    
    return {'status': 'applied', 'proposal_id': proposal_id, 'files': applied}


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策自进化 L3 受限修改提案器')
    sub = parser.add_subparsers(dest='command')
    
    p_propose = sub.add_parser('propose', help='创建修改提案')
    p_propose.add_argument('--agent', required=True, help='发起Agent')
    p_propose.add_argument('--signal', required=True, help='信号JSON文件')
    p_propose.add_argument('--files', nargs='+', required=True, help='目标文件列表')
    p_propose.add_argument('--summary', required=True, help='修改摘要')
    
    p_list = sub.add_parser('list', help='列出提案')
    p_list.add_argument('--status', default=None, help='按状态筛选')
    
    p_review = sub.add_parser('review', help='审核提案')
    p_review.add_argument('--id', required=True, help='提案ID')
    p_review.add_argument('--decision', required=True, choices=['approved', 'rejected', 'needs_changes'])
    p_review.add_argument('--comment', default='', help='审核意见')
    
    p_apply = sub.add_parser('apply', help='应用提案')
    p_apply.add_argument('--id', required=True, help='提案ID')
    
    p_rollback = sub.add_parser('rollback', help='回滚到快照')
    p_rollback.add_argument('--snapshot', required=True, help='快照ID')
    
    args = parser.parse_args()
    
    if args.command == 'propose':
        with open(args.signal, 'r', encoding='utf-8') as f:
            signal_data = json.load(f)
        proposal = create_proposal(args.agent, signal_data, args.files, args.summary)
        print(f'✅ 提案已创建: {proposal["proposal_id"]}')
        print(f'   文件: {proposal["target_files"]}')
        print(f'   快照: {proposal["before_snapshot"]}')
    
    elif args.command == 'list':
        proposals = list_proposals(args.status)
        if not proposals:
            print('暂无提案')
        else:
            for p in proposals:
                print(f'[{p["id"]}] {p["status"]:12s} | {p["agent"]:20s} | {p["summary"]}')
    
    elif args.command == 'review':
        result = review_proposal(args.id, args.decision, comment=args.comment)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'apply':
        result = apply_proposal(args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'rollback':
        result = restore_snapshot(args.snapshot)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
