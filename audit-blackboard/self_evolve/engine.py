#!/usr/bin/env python3
"""
融策自进化系统 主引擎 v1.0
═══════════════════════════════════════
整合L1-L6六层架构，实现Agent系统"开发→部署→运行→观测→评估→改写→回滚"闭环。

架构:
  L1 运行时  — agent能跑、自我探查 (已有: orchestrate_v3 + AgentDebugX)
  L2 观测层  — signal_extractor: 失败/效率/能力缺口信号
  L3 修改层  — mutation_proposer: 受限修改提案(PR+git+分级)
  L4 验证层  — eval_runner: 独立评估(回归+能力+对抗)
  L5 决策层  — decision_engine: 规则引擎→LLM-as-judge
  L6 治理层  — governance: 四条禁止+卡门线+人类最终裁决

闭环:
  L2喂信号 → L5决策 → L3提提案 → L6治理检查 → L4验证 → 合并 → L1生效

用法:
  # 完整闭环
  python self_evolve/engine.py run
  
  # 分步执行
  python self_evolve/engine.py observe     # L2: 提取信号
  python self_evolve/engine.py decide      # L5: 基于信号决策
  python self_evolve/engine.py propose     # L3: 生成修改提案
  python self_evolve/engine.py validate    # L6+L4: 治理检查+评估验证
  python self_evolve/engine.py apply       # 应用通过验证的修改
  
  # 状态
  python self_evolve/engine.py status
  python self_evolve/engine.py dashboard
"""
import sys, os, json, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

MODULE_DIR = Path(__file__).parent
WORKSPACE = MODULE_DIR.parent.parent
STATE_FILE = MODULE_DIR / 'evolution_state.json'
LOG_FILE = MODULE_DIR / 'evolution_log.jsonl'


def log_event(phase, detail):
    """写入进化日志"""
    entry = {
        'timestamp': datetime.now(CST).isoformat(),
        'phase': phase,
        **detail,
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'version': '1.0',
        'last_full_cycle': None,
        'cycles_completed': 0,
        'last_signal_extraction': None,
        'last_decision_run': None,
        'pending_proposals': [],
        'applied_mutations': [],
    }


def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════
#  L2: 观测 — 提取信号
# ═══════════════════════════════════════

def observe():
    """L2: 信号提取"""
    print('═══ L2 观测层: 信号提取 ═══')
    
    result = subprocess.run(
        ['python', '-X', 'utf8', str(MODULE_DIR / 'signal_extractor.py'), 'extract', '--all'],
        capture_output=True, text=True, timeout=60,
        cwd=str(WORKSPACE)
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # 找到最新信号文件
    signals_dir = MODULE_DIR / 'signals'
    signal_files = sorted(signals_dir.glob('signals_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if signal_files:
        state = load_state()
        state['last_signal_extraction'] = datetime.now(CST).isoformat()
        state['latest_signals'] = str(signal_files[0])
        save_state(state)
        log_event('L2_observe', {'signals_file': str(signal_files[0])})
        return str(signal_files[0])
    
    return None


# ═══════════════════════════════════════
#  L5: 决策 — 基于信号决策
# ═══════════════════════════════════════

def decide(signals_file=None):
    """L5: 决策引擎"""
    print('═══ L5 决策层: 规则匹配 ═══')
    
    if signals_file is None:
        state = load_state()
        signals_file = state.get('latest_signals')
    
    if not signals_file or not os.path.exists(signals_file):
        print('❌ 无可用信号，请先运行 observe')
        return None
    
    result = subprocess.run(
        ['python', '-X', 'utf8', str(MODULE_DIR / 'decision_engine.py'), 'decide', '--signals', signals_file],
        capture_output=True, text=True, timeout=60,
        cwd=str(WORKSPACE)
    )
    
    print(result.stdout)
    
    state = load_state()
    state['last_decision_run'] = datetime.now(CST).isoformat()
    save_state(state)
    log_event('L5_decide', {'signals_file': signals_file})
    
    return True


# ═══════════════════════════════════════
#  L3+L6+L4: 提案 → 治理检查 → 评估验证
# ═══════════════════════════════════════

def propose_and_validate(agent='data_scout', target_files=None, summary='自动优化'):
    """L3+L6+L4: 创建提案 → 治理检查 → 评估验证"""
    print('═══ L3 修改层: 创建提案 ═══')
    
    state = load_state()
    
    # 如果没有信号，先提取
    signals_file = state.get('latest_signals')
    if not signals_file:
        print('⚠️ 无信号，先提取...')
        signals_file = observe()
        if not signals_file:
            return None
    
    if target_files is None:
        target_files = [f'agent_specs/{agent}.json']
    
    # L3: 创建提案
    result = subprocess.run(
        ['python', '-X', 'utf8', str(MODULE_DIR / 'mutation_proposer.py'), 'propose',
         '--agent', agent, '--signal', signals_file,
         '--files'] + target_files +
         ['--summary', summary],
        capture_output=True, text=True, timeout=30,
        cwd=str(WORKSPACE)
    )
    print(result.stdout)
    
    # 找最新提案
    proposals_dir = MODULE_DIR / 'proposals'
    proposal_files = sorted(proposals_dir.glob('P-*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not proposal_files:
        return None
    
    proposal_path = str(proposal_files[0])
    
    # L6: 治理检查
    print('\n═══ L6 治理层: 边界检查 ═══')
    result = subprocess.run(
        ['python', '-X', 'utf8', str(MODULE_DIR / 'governance.py'), 'check',
         '--proposal', proposal_path],
        capture_output=True, text=True, timeout=30,
        cwd=str(WORKSPACE)
    )
    print(result.stdout)
    
    # L4: 评估验证
    print('\n═══ L4 验证层: 独立评估 ═══')
    result = subprocess.run(
        ['python', '-X', 'utf8', str(MODULE_DIR / 'eval_runner.py'), 'run',
         '--agent', agent],
        capture_output=True, text=True, timeout=120,
        cwd=str(WORKSPACE)
    )
    print(result.stdout)
    
    state['pending_proposals'].append(str(proposal_files[0].name))
    save_state(state)
    log_event('L3+L6+L4_propose_validate', {
        'proposal': str(proposal_files[0].name),
        'agent': agent,
    })
    
    return str(proposal_files[0])


# ═══════════════════════════════════════
#  完整闭环
# ═══════════════════════════════════════

def run_full_cycle():
    """运行完整L2→L5→L3→L6→L4闭环"""
    print('╔══════════════════════════════════════╗')
    print('║  融策Agent自进化 — 完整闭环         ║')
    print('║  L2观测 → L5决策 → L3提案 →         ║')
    print('║  L6治理 → L4验证 → 合并生效         ║')
    print('╚══════════════════════════════════════╝')
    
    state = load_state()
    state['cycles_completed'] += 1
    
    # Step 1: L2
    signals_file = observe()
    if not signals_file:
        print('⚠️ 无信号生成，闭环结束')
        return
    
    # Step 2: L5
    decide(signals_file)
    
    # Step 3: L3+L6+L4
    proposal = propose_and_validate()
    
    # Step 4: 如果有通过验证的提案，标记待人类审批
    if proposal:
        print(f'\n📋 提案 {os.path.basename(proposal)} 已通过L6+L4检查')
        print('   下一步: 人类审批 → mutation_proposer.py review --id <提案ID> --decision approved')
        print('   然后: mutation_proposer.py apply --id <提案ID>')
    
    state['last_full_cycle'] = datetime.now(CST).isoformat()
    save_state(state)
    log_event('full_cycle_complete', {'proposal': os.path.basename(proposal) if proposal else None})
    
    print(f'\n✅ 闭环完成 (第{state["cycles_completed"]}次)')


# ═══════════════════════════════════════
#  状态面板
# ═══════════════════════════════════════

def dashboard():
    """自进化系统仪表盘"""
    state = load_state()
    boundary = None
    try:
        import yaml
        with open(MODULE_DIR / 'boundary.yaml', 'r', encoding='utf-8') as f:
            boundary = yaml.safe_load(f)
    except:
        pass
    
    print('╔══════════════════════════════════════╗')
    print('║  融策Agent自进化系统 — 状态面板     ║')
    print('╚══════════════════════════════════════╝')
    print(f'  版本: v{state["version"]}')
    print(f'  完整闭环次数: {state["cycles_completed"]}')
    print(f'  上次闭环: {state["last_full_cycle"] or "从未"}')
    print(f'  上次观测: {state["last_signal_extraction"] or "从未"}')
    print(f'  上次决策: {state["last_decision_run"] or "从未"}')
    print(f'  待审批提案: {len(state["pending_proposals"])}')
    print(f'  已应用变更: {len(state["applied_mutations"])}')
    
    # 各层状态
    print(f'\n  L1运行时: ✅ orchestrate_v3 + AgentDebugX')
    
    signals_dir = MODULE_DIR / 'signals'
    signal_count = len(list(signals_dir.glob('*.json'))) if signals_dir.exists() else 0
    print(f'  L2观测层: {"✅" if signal_count > 0 else "⚠️"} 信号文件: {signal_count}个')
    
    proposals_dir = MODULE_DIR / 'proposals'
    prop_count = len(list(proposals_dir.glob('*.json'))) if proposals_dir.exists() else 0
    print(f'  L3修改层: ✅ 提案: {prop_count}个')
    
    eval_dir = MODULE_DIR / 'eval_results'
    eval_count = len(list(eval_dir.glob('*.json'))) if eval_dir.exists() else 0
    print(f'  L4验证层: {"✅" if eval_count > 0 else "⚠️"} 评估报告: {eval_count}个')
    
    rules_file = MODULE_DIR / 'decision_rules.json'
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        print(f'  L5决策层: ✅ 规则: {len(rules["rules"])}条')
    else:
        print(f'  L5决策层: ⚠️ 规则未初始化')
    
    print(f'  L6治理层: ✅ boundary.yaml + governance.py')
    
    # 治理边界摘要
    if boundary:
        forbidden = boundary.get('forbidden_actions', [])
        gates = boundary.get('gates', [])
        print(f'\n  治理边界: {len(forbidden)}条禁止 + {len(gates)}道卡门线')
    
    print(f'\n  日志: {LOG_FILE}')


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策自进化系统 主引擎 v1.0')
    sub = parser.add_subparsers(dest='command')
    
    p_run = sub.add_parser('run', help='运行完整L2→L5→L3→L6→L4闭环')
    p_observe = sub.add_parser('observe', help='L2: 提取信号')
    p_decide = sub.add_parser('decide', help='L5: 基于信号决策')
    p_propose = sub.add_parser('propose', help='L3+L6+L4: 提案→治理→验证')
    p_propose.add_argument('--agent', default='data_scout', help='Agent名称')
    p_propose.add_argument('--files', nargs='+', default=None, help='目标文件')
    p_propose.add_argument('--summary', default='自动优化', help='修改摘要')
    p_status = sub.add_parser('status', help='查看自进化系统状态')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        run_full_cycle()
    elif args.command == 'observe':
        observe()
    elif args.command == 'decide':
        decide()
    elif args.command == 'propose':
        propose_and_validate(args.agent, args.files, args.summary)
    elif args.command in ('status', 'dashboard'):
        dashboard()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
