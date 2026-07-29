#!/usr/bin/env python3
"""
融策自进化系统 L5 — 决策引擎 v1.0
═══════════════════════════════════════
"什么时候改、改什么。规则引擎起步，LLM-as-judge进阶，RL是终局。"

用法:
  python self_evolve/decision_engine.py decide --signals signals.json
  python self_evolve/decision_engine.py rules
"""
import sys, os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

MODULE_DIR = Path(__file__).parent
RULES_FILE = MODULE_DIR / 'decision_rules.json'

# ═══════════════════════════════════════
#  默认决策规则
# ═══════════════════════════════════════

DEFAULT_RULES = {
    'version': '1.0',
    'rules': [
        {
            'id': 'R001',
            'name': '交接断裂自动告警',
            'condition': {
                'signal_type': 'handover_break',
                'min_severity': 'medium',
            },
            'action': 'alert',
            'priority': 'P0',
            'message': '检测到Agent交接断裂，建议检查spawn流程',
        },
        {
            'id': 'R002',
            'name': 'Agent零发现触发能力审查',
            'condition': {
                'signal_type': 'agent_zero_findings',
                'min_severity': 'medium',
            },
            'action': 'propose_review',
            'priority': 'P1',
            'message': 'Agent被派发但无任何发现，建议审查任务分配或增强能力',
        },
        {
            'id': 'R003',
            'name': 'Token超预算切换低成本模型',
            'condition': {
                'signal_type': 'token_budget_warning',
                'min_severity': 'high',
            },
            'action': 'propose_model_switch',
            'priority': 'P0',
            'message': 'Token超预算，建议切换到低成本模型或压缩Agent任务',
        },
        {
            'id': 'R004',
            'name': '长期未使用Agent评估下线',
            'condition': {
                'signal_type': 'agent_never_used',
                'min_severity': 'low',
            },
            'action': 'propose_review',
            'priority': 'P2',
            'message': 'Agent长期未使用，建议评估是否仍需要',
        },
        {
            'id': 'R005',
            'name': '评估未通过阻止合并',
            'condition': {
                'signal_type': 'eval_failed',
            },
            'action': 'block',
            'priority': 'P0',
            'message': '修改提案未通过L4评估，阻止合并',
        },
        {
            'id': 'R006',
            'name': '高失败率触发根因分析',
            'condition': {
                'signal_type': 'failure_rate_high',
                'min_severity': 'high',
            },
            'action': 'propose_deep_debug',
            'priority': 'P1',
            'message': 'Agent失败率过高，建议触发AgentDebugX深度调试',
        },
        {
            'id': 'R007',
            'name': '发现密度过低触发提示词优化',
            'condition': {
                'signal_type': 'agent_zero_findings',
                'min_severity': 'medium',
            },
            'action': 'propose_prompt_optimize',
            'priority': 'P1',
            'message': '建议优化Agent提示词以提高发现密度',
        },
        {
            'id': 'R008',
            'name': '评估分数持续下降触发能力加固',
            'condition': {
                'signal_type': 'eval_declining',
                'min_severity': 'medium',
            },
            'action': 'propose_capability_hardening',
            'priority': 'P1',
            'message': 'Agent评估分数持续下降，建议能力加固',
        },
    ],
    # 决策策略（仅人类可修改）
    'decision_policy': {
        'auto_trigger_threshold': 'P0',         # P0自动触发，P1-P2需要人类确认
        'max_auto_actions_per_day': 3,           # 每天最多自动执行3个动作
        'require_human_for': ['model_switch', 'agent_removal', 'schema_change'],
        'cooldown_minutes': 60,                   # 相同规则冷却60分钟
    },
}


def save_default_rules():
    """保存默认决策规则"""
    with open(RULES_FILE, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_RULES, f, ensure_ascii=False, indent=2)


def load_rules():
    """加载决策规则"""
    if not RULES_FILE.exists():
        save_default_rules()
    with open(RULES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_signals(signals_data, rules):
    """将信号匹配到决策规则"""
    decisions = []
    
    # 提取所有信号
    all_signals = []
    details = signals_data.get('details', {})
    
    for project_name, project_data in details.items():
        if project_name == 'global':
            continue
        for signal_type in ['failure_signals', 'efficiency_signals', 'capability_gap_signals']:
            for sig in project_data.get(signal_type, []):
                sig['_project'] = project_name
                sig['_type'] = signal_type.rstrip('s')
                all_signals.append(sig)
    
    # 全局信号
    global_data = details.get('global', {})
    for signal_type in ['failure_signals', 'efficiency_signals', 'capability_gap_signals']:
        for sig in global_data.get(signal_type, []):
            sig['_project'] = 'global'
            sig['_type'] = signal_type.rstrip('s')
            all_signals.append(sig)
    
    # 匹配规则
    for sig in all_signals:
        sig_type = sig.get('type', '')
        
        for rule in rules.get('rules', []):
            condition = rule.get('condition', {})
            
            # 信号类型匹配
            if condition.get('signal_type') != sig_type:
                continue
            
            # 严重度匹配
            min_sev = condition.get('min_severity', 'low')
            sev_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
            sig_sev = sig.get('severity', 'low')
            if sev_order.get(sig_sev, 0) < sev_order.get(min_sev, 0):
                continue
            
            decisions.append({
                'triggered_rule': rule['id'],
                'rule_name': rule['name'],
                'action': rule['action'],
                'priority': rule['priority'],
                'message': rule['message'],
                'source_signal': sig,
            })
    
    # 按优先级排序
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
    decisions.sort(key=lambda d: priority_order.get(d['priority'], 99))
    
    return decisions


def decide(signals_file):
    """基于信号做决策"""
    if not RULES_FILE.exists():
        save_default_rules()
    
    rules = load_rules()
    
    with open(signals_file, 'r', encoding='utf-8') as f:
        signals_data = json.load(f)
    
    decisions = match_signals(signals_data, rules)
    
    policy = rules.get('decision_policy', {})
    auto_threshold = policy.get('auto_trigger_threshold', 'P0')
    
    # 分级: P0自动执行，P1-P2需人类确认
    auto_actions = [d for d in decisions if d['priority'] <= auto_threshold]
    human_actions = [d for d in decisions if d['priority'] > auto_threshold]
    
    return {
        'decided_at': datetime.now(CST).isoformat(),
        'total_signals': signals_data.get('total_signals', 0),
        'total_decisions': len(decisions),
        'auto_actions': auto_actions,
        'human_review_actions': human_actions,
        'all_decisions': decisions,
    }


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策自进化 L5 决策引擎')
    sub = parser.add_subparsers(dest='command')
    
    p_decide = sub.add_parser('decide', help='基于信号做决策')
    p_decide.add_argument('--signals', required=True, help='信号JSON文件')
    
    p_rules = sub.add_parser('rules', help='查看决策规则')
    p_rules.add_argument('--init', action='store_true', help='初始化默认规则')
    
    args = parser.parse_args()
    
    if args.command == 'decide':
        result = decide(args.signals)
        print(f'🧠 决策完成')
        print(f'   信号: {result["total_signals"]}条')
        print(f'   决策: {result["total_decisions"]}条')
        print(f'   自动执行: {len(result["auto_actions"])}条')
        print(f'   需人工: {len(result["human_review_actions"])}条')
        
        if result['auto_actions']:
            print(f'\n--- 自动执行 (P0) ---')
            for a in result['auto_actions']:
                print(f'  [{a["priority"]}] {a["rule_name"]}: {a["message"]}')
        
        if result['human_review_actions']:
            print(f'\n--- 需人工审核 ---')
            for a in result['human_review_actions']:
                print(f'  [{a["priority"]}] {a["rule_name"]}: {a["message"]}')
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'rules':
        if args.init:
            save_default_rules()
            print(f'✅ 默认决策规则已保存到 {RULES_FILE}')
        else:
            rules = load_rules()
            print(f'决策规则 ({len(rules["rules"])}条):')
            for r in rules['rules']:
                print(f'  [{r["priority"]}] {r["id"]}: {r["name"]}')
                print(f'    条件: {r["condition"]["signal_type"]}')
                print(f'    动作: {r["action"]}')
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
