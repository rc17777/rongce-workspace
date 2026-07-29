#!/usr/bin/env python3
"""
融策自进化系统 L6 — 治理边界强制执行 v1.0
══════════════════════════════════════════
原则："元层永不让agent自治。边界本身就是系统稳定性的承重墙。"

功能：
  - check:  检查一个修改提案是否越界
  - audit:  审计所有历史修改的合规性
  - gates:  列出所有卡门线及其状态
  - enforce: 强制执行治理规则（拒绝越界修改）

用法:
  python self_evolve/governance.py check --proposal proposals/p001.json
  python self_evolve/governance.py audit --since 2026-07-01
  python self_evolve/governance.py gates
"""
import sys, os, json, yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

MODULE_DIR = Path(__file__).parent
BOUNDARY_FILE = MODULE_DIR / 'boundary.yaml'
AUDIT_LOG = MODULE_DIR / 'governance_audit.jsonl'

try:
    import yaml
except ImportError:
    print('⚠️ PyYAML未安装，尝试 pip install pyyaml')
    yaml = None


def load_boundary():
    """加载治理边界配置"""
    if not BOUNDARY_FILE.exists():
        return {'error': 'boundary.yaml not found'}
    if yaml is None:
        # Fallback: simple yaml reader
        return _simple_yaml_load(BOUNDARY_FILE)
    with open(BOUNDARY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _simple_yaml_load(path):
    """简单的YAML加载器（不需要PyYAML）"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 简单解析：只支持基本结构
    import re
    result = {}
    current_section = None
    for line in content.split('\n'):
        line = line.rstrip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^(\w[\w_]*):\s*$', line)
        if m:
            current_section = m.group(1)
            result[current_section] = {}
        elif current_section:
            km = re.match(r'^\s+(\w[\w_]*):\s*["\']?(.*?)["\']?\s*$', line)
            if km:
                val = km.group(2).strip()
                try:
                    val = int(val)
                except:
                    pass
                result[current_section][km.group(1)] = val
    return result


def log_action(action, detail):
    """写入治理审计日志"""
    entry = {
        'timestamp': datetime.now(CST).isoformat(),
        'action': action,
        **detail,
    }
    with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def find_mutation_level(file_path, boundary):
    """确定文件属于哪个mutation level"""
    if isinstance(boundary, dict) and 'error' in boundary:
        return None, 'boundary_not_loaded'
    
    levels = boundary.get('mutation_levels', {})
    for level_name, level_cfg in levels.items():
        scope = level_cfg.get('scope', [])
        for pattern in scope:
            if pattern.endswith('/'):
                if str(file_path).startswith(pattern) or f'/{pattern}' in str(file_path):
                    return level_cfg.get('approver', 'unknown'), level_name
            elif pattern in str(file_path) or str(file_path).endswith(pattern):
                return level_cfg.get('approver', 'unknown'), level_name
    
    return 'human', 'level_1_human_only'  # 默认：未分类=人类独占


# ═══════════════════════════════════════
#  1. 修改提案合规检查
# ═══════════════════════════════════════

def check_proposal(proposal):
    """
    检查修改提案是否越界
    
    proposal格式:
    {
        "proposal_id": "P-001",
        "agent": "contract_hound",
        "target_files": ["agent_specs/contract_hound.json"],
        "change_type": "prompt_update",
        "description": "优化合同审查提示词"
    }
    
    返回: {status: "APPROVED"|"REJECTED"|"NEEDS_REVIEW", details: [...]}
    """
    boundary = load_boundary()
    if isinstance(boundary, dict) and 'error' in boundary:
        return {'status': 'ERROR', 'details': [boundary['error']]}
    
    target_files = proposal.get('target_files', [])
    agent = proposal.get('agent', 'unknown')
    violations = []
    warnings = []
    
    for tf in target_files:
        # 检查四条禁止
        for rule in boundary.get('forbidden_actions', []):
            scope_patterns = rule.get('scope', [])
            for pattern in scope_patterns:
                if pattern in str(tf) or str(tf).endswith(pattern):
                    violations.append({
                        'rule': rule['id'],
                        'severity': rule['severity'],
                        'file': tf,
                        'message': rule['message'],
                    })
        
        if violations:
            continue  # 已被禁止，不需要继续检查
        
        # 确定mutation level
        approver, level = find_mutation_level(tf, boundary)
        
        if approver == 'NONE':
            violations.append({
                'rule': 'FORBID_FROZEN',
                'severity': 'CRITICAL',
                'file': tf,
                'message': f'文件 {tf} 属于冻结层(L0)，任何agent都不能修改',
            })
        elif approver == 'auto':
            pass  # 自动层，无需警告
        elif approver == 'human':
            warnings.append({
                'file': tf,
                'level': level,
                'message': f'文件 {tf} 需要人类批准 (级别: {level})',
            })
    
    if violations:
        status = 'REJECTED'
        result = {'status': status, 'violations': violations, 'warnings': warnings}
    elif warnings:
        status = 'NEEDS_REVIEW'
        result = {'status': status, 'violations': [], 'warnings': warnings}
    else:
        status = 'APPROVED'
        result = {'status': status, 'violations': [], 'warnings': []}
    
    log_action('check_proposal', {
        'proposal_id': proposal.get('proposal_id', 'unknown'),
        'agent': agent,
        'status': status,
        'violation_count': len(violations),
        'target_files': target_files,
    })
    
    return result


# ═══════════════════════════════════════
#  2. 卡门线检查
# ═══════════════════════════════════════

def check_gates(proposal, eval_result=None):
    """检查所有卡门线"""
    boundary = load_boundary()
    gates = boundary.get('gates', [])
    
    gate_results = []
    all_passed = True
    
    for gate in gates:
        result = {'gate_id': gate['id'], 'description': gate['description'], 'status': 'PASS'}
        
        if gate['id'] == 'GATE_EVAL_PASS':
            if eval_result is None:
                result['status'] = 'BLOCKED'
            elif not eval_result.get('passed', False):
                result['status'] = 'BLOCKED'
                result['reason'] = '评估未通过'
        
        elif gate['id'] == 'GATE_ROLLBACK_READY':
            # 检查是否有快照
            snapshot_dir = MODULE_DIR / 'snapshots'
            if not list(snapshot_dir.glob('*.json')) if snapshot_dir.exists() else True:
                result['status'] = 'BLOCKED'
                result['reason'] = '没有找到回滚快照'
        
        elif gate['id'] == 'GATE_RATE_LIMIT':
            # 检查今日修改频率
            today = datetime.now(CST).strftime('%Y-%m-%d')
            today_count = 0
            if AUDIT_LOG.exists():
                with open(AUDIT_LOG, 'r', encoding='utf-8') as f:
                    for line in f:
                        if today in line and 'mutation_applied' in line:
                            today_count += 1
            max_per_day = gate.get('max_per_day', 5)
            if today_count >= max_per_day:
                result['status'] = 'BLOCKED'
                result['reason'] = f'今日修改已达上限({today_count}/{max_per_day})'
        
        if result['status'] != 'PASS':
            all_passed = False
        gate_results.append(result)
    
    return {'all_passed': all_passed, 'gates': gate_results}


# ═══════════════════════════════════════
#  3. 合规审计
# ═══════════════════════════════════════

def audit_history(since_date=None):
    """审计所有历史修改的合规性"""
    if not AUDIT_LOG.exists():
        return {'total_actions': 0, 'violations': []}
    
    entries = []
    with open(AUDIT_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except:
                continue
    
    if since_date:
        entries = [e for e in entries if e.get('timestamp', '') >= since_date]
    
    violations = [e for e in entries if e.get('status') == 'REJECTED']
    reviews = [e for e in entries if e.get('status') == 'NEEDS_REVIEW']
    approved = [e for e in entries if e.get('status') == 'APPROVED']
    
    return {
        'total_actions': len(entries),
        'approved': len(approved),
        'needs_review': len(reviews),
        'violations': len(violations),
        'recent_violations': violations[-5:],
    }


# ═══════════════════════════════════════
#  4. 强制执行（拒绝越界修改）
# ═══════════════════════════════════════

def enforce(proposal, auto_reject=True):
    """
    强制执行治理规则
    
    返回:
    - 如果auto_reject=True且发现违规 → 直接拒绝，记录日志
    - 如果auto_reject=False → 返回检查结果，由上层决定
    """
    result = check_proposal(proposal)
    
    if result['status'] == 'REJECTED' and auto_reject:
        log_action('enforce_reject', {
            'proposal_id': proposal.get('proposal_id', 'unknown'),
            'reason': 'governance_violation',
            'violations': result['violations'],
        })
        return {
            'enforced': True,
            'action': 'REJECTED',
            'message': f"治理边界强制执行: 发现 {len(result['violations'])} 项违规",
            'details': result['violations'],
        }
    
    log_action('enforce_pass', {
        'proposal_id': proposal.get('proposal_id', 'unknown'),
        'status': result['status'],
    })
    
    return {
        'enforced': True,
        'action': result['status'],
        'message': f"治理检查通过 (状态: {result['status']})",
        'details': result.get('warnings', []),
    }


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策自进化 L6 治理边界强制执行')
    sub = parser.add_subparsers(dest='command')
    
    p_check = sub.add_parser('check', help='检查修改提案是否越界')
    p_check.add_argument('--proposal', required=True, help='提案JSON文件路径')
    p_check.add_argument('--eval-result', default=None, help='评估结果JSON')
    
    p_audit = sub.add_parser('audit', help='审计历史修改合规性')
    p_audit.add_argument('--since', default=None, help='起始日期 (YYYY-MM-DD)')
    
    p_gates = sub.add_parser('gates', help='列出所有卡门线')
    
    p_enforce = sub.add_parser('enforce', help='强制执行治理规则')
    p_enforce.add_argument('--proposal', required=True, help='提案JSON文件路径')
    p_enforce.add_argument('--no-auto-reject', action='store_true', help='不自动拒绝（仅返回检查结果）')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        with open(args.proposal, 'r', encoding='utf-8') as f:
            proposal = json.load(f)
        
        eval_result = None
        if args.eval_result:
            with open(args.eval_result, 'r', encoding='utf-8') as f:
                eval_result = json.load(f)
        
        result = check_proposal(proposal)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if eval_result is not None:
            gate_result = check_gates(proposal, eval_result)
            print('\n卡门线检查:')
            print(json.dumps(gate_result, ensure_ascii=False, indent=2))
    
    elif args.command == 'audit':
        result = audit_history(args.since)
        print(f'治理审计报告')
        print(f'  总操作: {result["total_actions"]}')
        print(f'  已批准: {result["approved"]}')
        print(f'  待审核: {result["needs_review"]}')
        print(f'  违规: {result["violations"]}')
        if result['recent_violations']:
            print(f'\n  最近违规:')
            for v in result['recent_violations']:
                print(f'    {v.get("timestamp", "")} | {v.get("proposal_id", "")} | {v.get("status", "")}')
    
    elif args.command == 'gates':
        boundary = load_boundary()
        gates = boundary.get('gates', [])
        print('卡门线:')
        for g in gates:
            print(f'  [{g["id"]}] {g["description"]}')
            print(f'    触发: {g["trigger"]} → {g["action"]}')
            if 'on_fail' in g:
                print(f'    失败时: {g["on_fail"]}')
    
    elif args.command == 'enforce':
        with open(args.proposal, 'r', encoding='utf-8') as f:
            proposal = json.load(f)
        result = enforce(proposal, auto_reject=not args.no_auto_reject)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
