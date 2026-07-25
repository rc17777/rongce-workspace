#!/usr/bin/env python3
"""
交接协议编排集成 — 在 orchestrate_v3.py 的 collect 阶段挂载 handover emit
============================================================
v1.1: 新增 AgentDebugX 调试自动触发

无需修改 orchestrate_v3.py 主体，在 collect 阶段后自动生成交接包。

用法:
    集成到 orchestrate_v3.py 的 collect 函数:
        from handover_protocol import emit_handover
        emit_handover(project, agent_name, goal=goal, completed_checks=checks)

    或独立调用:
        python handover_hook.py --project "XX项目" --agent "contract_hound"
        python handover_hook.py --project "XX项目" --agent "contract_hound" --debug  # 带调试检测
"""

import sys, os, json
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handover_protocol import emit_handover, get_context_for_next_agent, read_handovers

# ★ v1.1: 接入 AgentDebugX 调试工具箱
_DEBUG_TOOLS_LOADED = False
_agent_debug_rules = None
_agent_deep_debug = None
_agent_error_hub = None

def _lazy_load_debug():
    """延迟加载调试模块（避免循环导入）。"""
    global _DEBUG_TOOLS_LOADED, _agent_debug_rules, _agent_deep_debug, _agent_error_hub
    if not _DEBUG_TOOLS_LOADED:
        try:
            from agent_debug_rules import AgentDebugRules
            from agent_deep_debug import DeepDebugger
            from agent_error_hub import ErrorHub
            _agent_debug_rules = AgentDebugRules
            _agent_deep_debug = DeepDebugger
            _agent_error_hub = ErrorHub
            _DEBUG_TOOLS_LOADED = True
        except ImportError:
            pass

CST = timezone(timedelta(hours=8))
PROJECTS = Path(__file__).parent / 'projects'


def parse_findings_for_checks(project_slug, agent_name):
    """
    从 finder 的输出文件自动解析出:
    - 完成的核查项
    - 发现数量
    """
    findings_dir = PROJECTS / project_slug / 'findings'
    if not findings_dir.exists():
        return [], 0

    checks = []
    total = 0
    for f in sorted(findings_dir.glob('*.json')):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except:
            continue

        items = data if isinstance(data, list) else data.get('findings', [])
        for item in items:
            total += 1
            check_type = item.get('check_type', '') or item.get('type', '') or ''
            if check_type and check_type not in checks:
                checks.append(check_type)

    return checks, total


def get_pending_checks(project_slug):
    """
    从项目 status.json 和坐标映射找出尚未完成的检查项。
    """
    status_path = PROJECTS / project_slug / 'status.json'
    if not status_path.exists():
        return []

    with open(status_path, 'r', encoding='utf-8') as f:
        status = json.load(f)

    done_agents = []
    if 'handover_chain' in status:
        done_agents = [h['source_agent'] for h in status['handover_chain']]

    all_agents = status.get('expected_agents', [])
    pending = [a for a in all_agents if a not in done_agents]

    return pending


def auto_emit(project_slug, agent_name, goal=None, parent_handover=None):
    """
    自动交接：从一个Agent的findings输出自动生成交接包。
    应该放在 orchestrate_v3.py collect 阶段的最后调用。

    v1.2: 新增文件清单自动生成（file_safety集成）。
    """
    completed_checks, total_findings = parse_findings_for_checks(project_slug, agent_name)
    pending_checks = get_pending_checks(project_slug)

    last_packets = read_handovers(project_slug)
    parent_id = parent_handover
    if not parent_id and last_packets:
        parent_id = last_packets[0]['handover_id']

    # ★ v1.2: 生成文件清单
    try:
        from file_safety import generate_file_manifest
        findings_files = [
            str(f.relative_to(PROJECTS / project_slug))
            for f in (PROJECTS / project_slug / 'findings').glob(f'{agent_name}_*.json')
        ]
        manifest = generate_file_manifest(project_slug, agent_name, extra_files=findings_files)
        print(f'📋 文件清单: {manifest["total_files"]} 个文件')
        if manifest['warnings']:
            for w in manifest['warnings']:
                print(f'  ⚠️  {w}')
    except Exception as e:
        print(f'⚠️  文件清单生成失败: {e}')

    return emit_handover(
        project_slug,
        agent_name,
        goal=goal or f"审计项目 {project_slug} — {agent_name} 完成分析",
        completed_checks=completed_checks,
        pending_checks=[f"待Agent {a} 完成" for a in pending_checks] if pending_checks else ["所有Agent已完成"],
        parent_handover=parent_id
    )


def debug_after_emit(project_slug, agent_name):
    """v1.1: 交接后自动触发 AgentDebugX 快速检测。"""
    _lazy_load_debug()
    if _agent_debug_rules:
        print(f"\n🔍 [AgentDebugX] 自动触发规则检测...")
        r = _agent_debug_rules(project_slug, agent_name)
        report = r.run_all()
        if report['stats']['issues_found'] > 0:
            print(f"\n⚠️  [AgentDebugX] 发现 {report['stats']['issues_found']} 个问题")
            if _agent_error_hub:
                hub = _agent_error_hub()
                hub.store(project_slug)
        return report
    return None


# ═══════════════════════════════════════════
# CLI: 独立调用
# ═══════════════════════════════════════════
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='交接协议编排集成钩子')
    parser.add_argument('--project', required=True)
    parser.add_argument('--agent', required=True)
    parser.add_argument('--goal', default='')
    parser.add_argument('--parent', default=None)
    parser.add_argument('--debug', action='store_true', help='交接后自动触发AgentDebugX检测')
    args = parser.parse_args()

    auto_emit(args.project, args.agent, goal=args.goal, parent_handover=args.parent)

    ctx = get_context_for_next_agent(args.project)
    if ctx['status'] == 'ready':
        print(f"\n📋 下游Agent可用上下文:")
        print(f"   累积发现: {ctx['total_findings_so_far']}条")
        print(f"   已确认事实: {len(ctx['accumulated_facts'])}条")
        print(f"   警告信号: {len(ctx['accumulated_warnings'])}条")
        print(f"   待检查: {ctx['pending_checks']}")

    if args.debug:
        debug_after_emit(args.project, args.agent)
