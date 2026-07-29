#!/usr/bin/env python3
"""
融策自进化系统 L2 — 信号提取器 v1.0
═══════════════════════════════════════
"trace一切，把原始日志蒸馏成可触发修改的信号"

三类信号:
  1. 失败信号 — agent执行失败、交接断裂、发现质量低
  2. 效率信号 — token浪费、重复执行、延迟过高
  3. 能力缺口信号 — 某类任务持续低分、某Agent从未被调用

用法:
  python self_evolve/signal_extractor.py extract --project "XX项目"
  python self_evolve/signal_extractor.py extract --all
"""
import sys, os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

WORKSPACE = Path(__file__).parent.parent.parent
BLACKBOARD = WORKSPACE / 'audit-blackboard'
PROJECTS = BLACKBOARD / 'projects'
SIGNALS_OUT = BLACKBOARD / 'self_evolve' / 'signals'
os.makedirs(SIGNALS_OUT, exist_ok=True)

SIGNAL_THRESHOLDS = {
    'failure_rate_high': 0.3,       # 失败率>30%
    'failure_rate_warn': 0.15,      # 失败率>15%警告
    'token_waste_high': 50000,       # 单项目token>50k
    'duplicate_findings_warn': 3,    # 重复发现>3条
    'handover_break_warn': 1,        # 任何交接断裂
    'agent_unused_days': 30,         # 30天未使用
    'eval_score_low': 0.5,           # 评估分<50%
}


def extract_project_signals(project_dir):
    """从单个项目提取信号"""
    signals = {
        'project': project_dir.name,
        'extracted_at': datetime.now(CST).isoformat(),
        'failure_signals': [],
        'efficiency_signals': [],
        'capability_gap_signals': [],
    }
    
    # 读取status.json
    sf = project_dir / 'status.json'
    if not sf.exists():
        return signals
    
    with open(sf, 'r', encoding='utf-8') as f:
        status = json.load(f)
    
    logs = status.get('logs', [])
    phase = status.get('phase', 'unknown')
    
    # --- 失败信号 ---
    
    # 1. 交接断裂检测
    handover_dir = project_dir / 'handovers'
    if handover_dir.exists():
        handovers = list(handover_dir.glob('*.json'))
        if not handovers and phase in ('penetrated', 'running'):
            signals['failure_signals'].append({
                'type': 'handover_break',
                'severity': 'high',
                'message': '项目已进入penetrated阶段但无交接包生成',
                'suggested_action': '检查Agent spawn是否成功执行',
            })
    
    # 2. 发现质量检测
    findings_dir = project_dir / 'findings'
    if findings_dir.exists():
        finding_files = list(findings_dir.glob('*.json'))
        total_findings = 0
        by_agent = defaultdict(int)
        
        for ff in finding_files:
            try:
                with open(ff, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                items = data if isinstance(data, list) else data.get('findings', [])
                agent = ff.stem.split('_')[0]
                by_agent[agent] += len(items)
                total_findings += len(items)
            except:
                pass
        
        # 某些Agent零发现 → 能力缺口
        for agent_name in ['contract_hound', 'bid_hunter', 'data_scout', 'law_inspector']:
            if agent_name in status.get('penetration', {}).get('agents', []):
                if by_agent.get(agent_name, 0) == 0:
                    signals['capability_gap_signals'].append({
                        'type': 'agent_zero_findings',
                        'agent': agent_name,
                        'severity': 'medium',
                        'message': f'Agent {agent_name} 被派发但无任何发现',
                        'suggested_action': f'检查{agent_name}的任务分配是否合理或需要能力增强',
                    })
        
        # P0发现占比过低
        severity_counts = defaultdict(int)
        if total_findings > 0:
            signals['efficiency_signals'].append({
                'type': 'project_metrics',
                'total_findings': total_findings,
                'agents_with_findings': len([a for a, c in by_agent.items() if c > 0]),
                'total_agents': len(by_agent),
            })
    
    # --- 效率信号 ---
    
    # 3. 阶段耗时检测
    if phase in ('running', 'penetrated') and len(logs) > 20:
        signals['efficiency_signals'].append({
            'type': 'long_running_phase',
            'phase': phase,
            'log_entries': len(logs),
            'message': f'项目在{phase}阶段停留较久（{len(logs)}条日志）',
            'suggested_action': '检查是否有Agent卡住或空转',
        })
    
    # 4. Token预算超额
    token_info = status.get('token_budget', {})
    if token_info:
        used = token_info.get('used', 0)
        limit = token_info.get('limit', 100000)
        if used > limit * 0.8:
            signals['efficiency_signals'].append({
                'type': 'token_budget_warning',
                'used': used,
                'limit': limit,
                'ratio': f'{used/limit*100:.0f}%',
                'severity': 'high' if used > limit else 'medium',
                'suggested_action': '考虑压缩Agent任务或切换到低成本模型',
            })
    
    return signals


def extract_global_signals():
    """提取全局信号（跨项目）"""
    signals = {
        'extracted_at': datetime.now(CST).isoformat(),
        'failure_signals': [],
        'efficiency_signals': [],
        'capability_gap_signals': [],
    }
    
    if not PROJECTS.exists():
        return signals
    
    # Agent使用频率
    agent_usage = defaultdict(lambda: {'projects': [], 'findings': 0, 'last_used': None})
    
    for proj_dir in PROJECTS.iterdir():
        if not proj_dir.is_dir():
            continue
        
        # 检查是否有该项目使用了哪些agent
        tasks_dir = proj_dir / 'tasks'
        plan_file = tasks_dir / 'penetrate_plan_v3.json'
        if plan_file.exists():
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    plan = json.load(f)
                for task in plan.get('parallel_tasks', []):
                    agent = task['agent_id']
                    agent_usage[agent]['projects'].append(proj_dir.name)
            except:
                pass
        
        # 检查发现数量
        findings_dir = proj_dir / 'findings'
        if findings_dir.exists():
            for ff in findings_dir.glob('*.json'):
                try:
                    with open(ff, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    items = data if isinstance(data, list) else data.get('findings', [])
                    agent = ff.stem.split('_')[0]
                    agent_usage[agent]['findings'] += len(items)
                except:
                    pass
    
    # 检测长期未使用的Agent
    all_known_agents = [
        'data_scout', 'contract_hound', 'bid_hunter', 'law_inspector',
        'workpaper_crafter', 'report_writer', 'review_sentinel',
        'budget_estimator', 'settlement_auditor', 'fiscal_reviewer',
        'performance_evaluator', 'expert_bias_detector',
    ]
    
    for agent in all_known_agents:
        usage = agent_usage.get(agent, {})
        proj_count = len(usage.get('projects', []))
        if proj_count == 0:
            signals['capability_gap_signals'].append({
                'type': 'agent_never_used',
                'agent': agent,
                'severity': 'low',
                'message': f'Agent {agent} 从未在任何项目中被调用',
                'suggested_action': '评估该Agent是否仍然需要，或需要调整触发条件',
            })
    
    return signals


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策自进化 L2 信号提取器')
    sub = parser.add_subparsers(dest='command')
    
    p_extract = sub.add_parser('extract', help='提取信号')
    p_extract.add_argument('--project', default=None, help='项目名称（不指定=所有项目）')
    p_extract.add_argument('--all', action='store_true', help='提取全局信号')
    p_extract.add_argument('--output', default=None, help='输出文件路径')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        results = {}
        
        if args.project:
            proj_dir = PROJECTS / args.project.replace(' ', '_')
            if proj_dir.exists():
                results[args.project] = extract_project_signals(proj_dir)
            else:
                print(f'❌ 项目不存在: {args.project}')
                return
        elif args.all:
            results['global'] = extract_global_signals()
            for proj_dir in PROJECTS.iterdir():
                if proj_dir.is_dir():
                    results[proj_dir.name] = extract_project_signals(proj_dir)
        else:
            # 默认：当前活跃项目
            for proj_dir in PROJECTS.iterdir():
                if not proj_dir.is_dir():
                    continue
                sf = proj_dir / 'status.json'
                if sf.exists():
                    with open(sf, 'r', encoding='utf-8') as f:
                        status = json.load(f)
                    if status.get('phase') != 'completed':
                        results[proj_dir.name] = extract_project_signals(proj_dir)
            results['global'] = extract_global_signals()
        
        # 汇总
        total_failures = sum(
            len(r.get('failure_signals', [])) for r in results.values()
        )
        total_efficiency = sum(
            len(r.get('efficiency_signals', [])) for r in results.values()
        )
        total_gaps = sum(
            len(r.get('capability_gap_signals', [])) for r in results.values()
        )
        
        summary = {
            'extracted_at': datetime.now(CST).isoformat(),
            'projects_analyzed': len([k for k in results if k != 'global']),
            'global_signals': True if 'global' in results else False,
            'total_signals': total_failures + total_efficiency + total_gaps,
            'failure_signals': total_failures,
            'efficiency_signals': total_efficiency,
            'capability_gap_signals': total_gaps,
            'details': results,
        }
        
        output_path = args.output or str(SIGNALS_OUT / f'signals_{datetime.now(CST).strftime("%Y%m%d_%H%M")}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f'📡 信号提取完成')
        print(f'   项目: {summary["projects_analyzed"]}个')
        print(f'   失败信号: {total_failures}')
        print(f'   效率信号: {total_efficiency}')
        print(f'   能力缺口: {total_gaps}')
        print(f'   输出: {output_path}')
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
