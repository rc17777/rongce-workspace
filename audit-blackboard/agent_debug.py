# -*- coding: utf-8 -*-
"""
AgentDebugX 四步闭环调试 — 一键入口
=====================================
整合三个模块：
  agent_debug_rules.py   → Detect（确定性规则检测）
  agent_deep_debug.py   → Attribute（根因定位）
  agent_error_hub.py    → Recover + Rerun（修复建议 + 错误库回归测试）

用法：
  # 完整闭环
  python agent_debug.py run "XX项目" --agent "contract_hound"

  # 只检测
  python agent_debug.py detect "XX项目" --agent "contract_hound"

  # 只归因
  python agent_debug.py attribute "XX项目" --mode deepdebug

  # 回归测试
  python agent_debug.py rerun "XX项目"
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from agent_debug_rules import AgentDebugRules
from agent_deep_debug import DeepDebugger
from agent_error_hub import ErrorHub


def run_full_cycle(project, agent=None):
    """
    完整四步闭环：Detect → Attribute → Recover → Rerun
    """
    print("""
╔══════════════════════════════════════════════════╗
║  🔬 AgentDebugX 调试闭环 v1.0                    ║
║  Detect → Attribute → Recover → Rerun          ║
╚══════════════════════════════════════════════════╝
""")

    # ── Step 1: Detect ──
    print("#" * 50)
    print("# STEP 1/4: DETECT（确定性规则检测）")
    print("#" * 50)
    rules = AgentDebugRules(project, agent)
    rules_report = rules.run_all()

    # ── Step 2: Store to Error Hub ──
    print("\n" + "#" * 50)
    print("# Store → Error Hub")
    print("#" * 50)
    hub = ErrorHub()
    hub.store(project)

    # ── Step 3: Attribute ──
    print("\n" + "#" * 50)
    print("# STEP 3/4: ATTRIBUTE（根因定位）")
    print("#" * 50)
    debugger = DeepDebugger(project)

    if rules_report['issues']:
        print(f"检测到 {len(rules_report['issues'])} 个问题，启动DeepDebug...")
        suspect_agents = set(i.get('agent', '') for i in rules_report['issues'] if i.get('agent'))
        if suspect_agents:
            for sa in suspect_agents:
                if sa and sa != 'unknown':
                    debugger.run_handover_probe(sa)
        debug_report = debugger.run_deepdebug()
    else:
        print("✅ 未检测到问题，跳过DeepDebug")
        debug_report = None

    # ── Step 4: Rerun ──
    print("\n" + "#" * 50)
    print("# STEP 4/4: RERUN（回归测试验证）")
    print("#" * 50)

    # 先存储诊断结果
    if debug_report:
        hub.store(project)

    # 运行回归测试
    hub.run_regression(project)

    # 汇总
    print(f"\n{'='*60}")
    print("📊 调试闭环完成")
    print(f"{'='*60}")
    print(f"  Detect:  {rules_report['stats']['issues_found']} 个问题")
    print(f"  Store:   {hub.index['stats']['total']} 条错误入库")
    print(f"  Attribute: {'已完成' if debug_report else '跳过（无问题）'}")
    print(f"  Error Hub 总计: {hub.index['stats']['total']} 条")

    return {
        'detect': rules_report,
        'attribute': debug_report,
        'error_hub_stats': hub.index['stats'],
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='AgentDebugX 调试闭环')
    sub = parser.add_subparsers(dest='cmd')

    run_p = sub.add_parser('run', help='完整闭环')
    run_p.add_argument('project')
    run_p.add_argument('--agent', default=None)

    detect_p = sub.add_parser('detect', help='规则检测')
    detect_p.add_argument('project')
    detect_p.add_argument('--agent', default=None)

    attr_p = sub.add_parser('attribute', help='根因定位')
    attr_p.add_argument('project')
    attr_p.add_argument('--mode', choices=['deepdebug', 'binary', 'handover'], default='deepdebug')
    attr_p.add_argument('--error-step', type=int, default=0)
    attr_p.add_argument('--suspect-agent', default=None)

    rerun_p = sub.add_parser('rerun', help='回归测试')
    rerun_p.add_argument('project')

    args = parser.parse_args()

    if args.cmd == 'run':
        run_full_cycle(args.project, args.agent)
    elif args.cmd == 'detect':
        rules = AgentDebugRules(args.project, args.agent)
        rules.run_all()
    elif args.cmd == 'attribute':
        d = DeepDebugger(args.project)
        if args.mode == 'deepdebug':
            d.run_deepdebug()
        elif args.mode == 'binary':
            d.run_binary_search(args.error_step)
        elif args.mode == 'handover':
            d.run_handover_probe(args.suspect_agent or 'unknown')
    elif args.cmd == 'rerun':
        hub = ErrorHub()
        hub.run_regression(args.project)
    else:
        parser.print_help()
