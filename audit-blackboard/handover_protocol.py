#!/usr/bin/env python3
"""
融策Agent状态交接协议 v1.0 — Handover Protocol
================================================
每个Agent完成后自动生成标准化交接包，解决Agent B重读全部文件的痛点。

交接包结构:
  {
    "handover_version": "1.0",
    "source_agent": "contract_hound",
    "target_coordinate": "物理",
    "project_id": "XX局预算执行审计",
    "timestamp": "ISO8601",
    "goal": "精确的任务目标",
    "confirmed_facts": ["已确认的事实清单"],
    "excluded_items": ["已排除的事项"],
    "completed_checks": ["已完成的核查项"],
    "pending_checks": ["待完成的核查项"],
    "findings_summary": { "total": N, "by_severity": {...}, "ids": [...] },
    "data_artifacts": ["产出文件路径列表"],
    "context_snapshot": "当前阶段的人类可读描述",
    "warnings": ["下游Agent需要注意的风险信号"],
    "parent_handover": "上一棒交接包ID（溯源链）"
  }

用法:
    python handover_protocol.py emit --project "XX项目" --agent "contract_hound"
    python handover_protocol.py read --project "XX项目"
    python handover_protocol.py chain --project "XX项目"
"""

import os, sys, json, argparse, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

# === 路径 ===
WORKSPACE = Path(__file__).parent.parent
PROJECTS = WORKSPACE / 'audit-blackboard' / 'projects'
SCHEMA_DIR = WORKSPACE / 'audit-blackboard' / 'schemas'

# === 交接包模板 ===
HANDOVER_TEMPLATE = {
    "handover_version": "1.0",
    "handover_id": "",           # 自动生成
    "source_agent": "",
    "project_id": "",
    "timestamp": "",
    "goal": "",
    "confirmed_facts": [],
    "excluded_items": [],
    "completed_checks": [],
    "pending_checks": [],
    "findings_summary": {
        "total": 0,
        "by_severity": {"P0": 0, "P1": 0, "P2": 0, "OBS": 0},
        "ids": []
    },
    "data_artifacts": [],
    "context_snapshot": "",
    "warnings": [],
    "parent_handover": None
}


def _now_iso():
    return datetime.now(CST).isoformat()


def _load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def emit_handover(project_slug, source_agent, goal=None, confirmed_facts=None,
                  excluded_items=None, completed_checks=None, pending_checks=None,
                  warnings=None, target_coordinate=None, parent_handover=None):
    """
    生成交接包。
    自动扫描 findings/ 目录统计发现数量和严重度。
    """
    project_dir = PROJECTS / project_slug
    handover_dir = project_dir / 'handovers'
    handover_dir.mkdir(parents=True, exist_ok=True)

    packet = HANDOVER_TEMPLATE.copy()
    packet['handover_id'] = f"H-{source_agent}-{datetime.now(CST).strftime('%Y%m%d%H%M%S')}"
    packet['source_agent'] = source_agent
    packet['project_id'] = project_slug
    packet['timestamp'] = _now_iso()
    packet['goal'] = goal or ""
    packet['confirmed_facts'] = confirmed_facts or []
    packet['excluded_items'] = excluded_items or []
    packet['completed_checks'] = completed_checks or []
    packet['pending_checks'] = pending_checks or []
    packet['warnings'] = warnings or []
    packet['target_coordinate'] = target_coordinate or ""
    packet['parent_handover'] = parent_handover

    # 自动扫描 findings 目录
    findings_dir = project_dir / 'findings'
    if findings_dir.exists():
        for f in sorted(findings_dir.glob('*.json')):
            packet['data_artifacts'].append(f'findings/{f.name}')
            try:
                finding = _load_json(f)
                if isinstance(finding, list):
                    for item in finding:
                        sev = item.get('severity', 'OBS')
                        packet['findings_summary']['by_severity'][sev] = \
                            packet['findings_summary']['by_severity'].get(sev, 0) + 1
                        packet['findings_summary']['total'] += 1
                        fid = item.get('id', '')
                        if fid:
                            packet['findings_summary']['ids'].append(fid)
                elif isinstance(finding, dict) and 'findings' in finding:
                    for item in finding['findings']:
                        sev = item.get('severity', 'OBS')
                        packet['findings_summary']['by_severity'][sev] = \
                            packet['findings_summary']['by_severity'].get(sev, 0) + 1
                        packet['findings_summary']['total'] += 1
                        fid = item.get('id', '')
                        if fid:
                            packet['findings_summary']['ids'].append(fid)
            except Exception as e:
                packet['warnings'].append(f"Failed to parse {f.name}: {e}")

    # 生成上下文快照
    facts_str = "; ".join(packet['confirmed_facts'][:5]) if packet['confirmed_facts'] else "无"
    checks_str = ", ".join(packet['completed_checks'][:5]) if packet['completed_checks'] else "无"
    pending_str = ", ".join(packet['pending_checks'][:3]) if packet['pending_checks'] else "无"
    packet['context_snapshot'] = (
        f"[{source_agent}] 已完成: {checks_str}. "
        f"已确认: {facts_str}. "
        f"待处理: {pending_str}. "
        f"共发现{packet['findings_summary']['total']}条疑点."
    )

    # 保存
    filename = f"{packet['handover_id']}.json"
    filepath = handover_dir / filename
    _save_json(filepath, packet)

    # ===== 新：Goal+Eval 状态注入 (v1.1) =====
    try:
        from goal_evaluator import GoalEvaluator
        evaluator = GoalEvaluator()
        output = load_agent_output(project_dir, source_agent)
        eval_result = evaluator.evaluate(source_agent, output, str(project_dir))
        packet['goal_status'] = {
            'status': eval_result.goal_status,
            'score': eval_result.total_score,
            'checks_passed': eval_result.checks_passed,
            'checks_total': eval_result.checks_total,
            'auto_action': eval_result.auto_action,
            'recommendation': eval_result.recommendation,
            'failures': [{'check': f['check'], 'msg': f['msg']} for f in eval_result.failures]
        }
        print(f"   Goal+Eval: {eval_result.goal_status} ({eval_result.total_score:.0%})")
    except ImportError:
        print(f"   Goal+Eval: evaluator 未就绪（跳过）")
    except Exception as e:
        print(f"   Goal+Eval: 评估异常 - {e}")

    # 更新项目状态
    _update_project_status(project_dir, packet)

    print(f"✅ 交接包已生成: {filename}")
    print(f"   源Agent: {source_agent}")
    print(f"   目标坐标系: {target_coordinate or '未指定'}")
    print(f"   发现疑点: {packet['findings_summary']['total']}条 "
          f"(P0:{packet['findings_summary']['by_severity']['P0']} "
          f"P1:{packet['findings_summary']['by_severity']['P1']} "
          f"P2:{packet['findings_summary']['by_severity']['P2']})")
    return packet


def read_handovers(project_slug, latest_only=False):
    """读取项目的所有交接包，按时间排序。"""
    project_dir = PROJECTS / project_slug
    handover_dir = project_dir / 'handovers'
    if not handover_dir.exists():
        return []

    packets = []
    for f in sorted(handover_dir.glob('H-*.json'), reverse=True):
        packets.append(_load_json(f))

    if latest_only and packets:
        return [packets[0]]

    return packets


def build_chain(project_slug):
    """追溯完整交接链，从最新到最初。"""
    packets = read_handovers(project_slug)
    if not packets:
        print("暂无交接记录")
        return

    chain = []
    current = packets[0]  # 最新的
    while current:
        chain.append({
            'handover_id': current['handover_id'],
            'source_agent': current['source_agent'],
            'timestamp': current['timestamp'],
            'findings_count': current['findings_summary']['total'],
            'context_snapshot': current['context_snapshot'][:120]
        })
        parent_id = current.get('parent_handover')
        if parent_id:
            current = next((p for p in packets if p['handover_id'] == parent_id), None)
        else:
            break

    print(f"\n{'='*60}")
    print(f"项目: {project_slug} | 共有 {len(chain)} 棒交接")
    print(f"{'='*60}")
    for i, link in enumerate(reversed(chain)):
        arrow = "→" if i < len(chain) - 1 else "●"
        print(f"  [{i+1}] {link['source_agent']:20s} {arrow} {link['findings_count']}条疑点")
        print(f"      {link['timestamp'][:19]}")
        print(f"      {link['context_snapshot']}")
        print()


def get_context_for_next_agent(project_slug):
    """
    下游Agent专用的快速上下文读取。
    返回一个精简的上下文摘要，Agent B不需要重读所有文件。
    """
    packets = read_handovers(project_slug, latest_only=True)
    if not packets:
        return {"status": "no_handover", "message": "暂无前任Agent的交接包，请从原始数据开始分析"}

    latest = packets[0]
    all_packets = read_handovers(project_slug)

    # 汇总所有Agent的成果
    total_findings = sum(p['findings_summary']['total'] for p in all_packets)
    all_warnings = []
    all_facts = []
    for p in all_packets:
        all_warnings.extend(p['warnings'])
        all_facts.extend(p['confirmed_facts'])

    context = {
        "status": "ready",
        "project_id": project_slug,
        "latest_handover": latest['handover_id'],
        "latest_agent": latest['source_agent'],
        "latest_timestamp": latest['timestamp'],
        "total_findings_so_far": total_findings,
        "latest_goal": latest['goal'],
        "accumulated_facts": list(set(all_facts)),
        "accumulated_warnings": list(set(all_warnings)),
        "pending_checks": latest['pending_checks'],
        "context_snapshot": latest['context_snapshot'],
        "available_artifacts": latest['data_artifacts'],
        "handover_chain_length": len(all_packets)
    }

    return context


def _update_project_status(project_dir, packet):
    """更新项目状态文件。"""
    status_path = project_dir / 'status.json'
    status = _load_json(status_path) if status_path.exists() else {}

    if 'handover_chain' not in status:
        status['handover_chain'] = []

    status['handover_chain'].append({
        'handover_id': packet['handover_id'],
        'source_agent': packet['source_agent'],
        'timestamp': packet['timestamp'],
        'findings_count': packet['findings_summary']['total']
    })
    status['last_handover'] = packet['timestamp']
    status['last_agent'] = packet['source_agent']

    # 追加Goal+Eval状态
    if 'goal_status' in packet:
        if 'goal_eval_history' not in status:
            status['goal_eval_history'] = []
        status['goal_eval_history'].append({
            'agent': packet['source_agent'],
            'handover_id': packet['handover_id'],
            'status': packet['goal_status']['status'],
            'score': packet['goal_status']['score']
        })

    _save_json(status_path, status)


def load_agent_output(project_dir, agent_name):
    """加载Agent输出（用于Goal+Eval评估）"""
    findings_dir = project_dir / 'findings'
    output = {}
    if findings_dir.exists():
        for fname in findings_dir.glob('*.json'):
            if agent_name.lower().replace(' ', '') in fname.stem.lower().replace(' ', ''):
                return _load_json(fname)
    # fallback: 加载所有findings
    all_findings = []
    if findings_dir.exists():
        for fname in findings_dir.glob('*.json'):
            all_findings.append(_load_json(fname))
    return {'findings': all_findings} if all_findings else output


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='融策Agent状态交接协议')
    sub = parser.add_subparsers(dest='cmd')

    emit_p = sub.add_parser('emit', help='生成交接包')
    emit_p.add_argument('--project', required=True)
    emit_p.add_argument('--agent', required=True)
    emit_p.add_argument('--goal', default='')
    emit_p.add_argument('--facts', nargs='*', default=[])
    emit_p.add_argument('--excluded', nargs='*', default=[])
    emit_p.add_argument('--completed', nargs='*', default=[])
    emit_p.add_argument('--pending', nargs='*', default=[])
    emit_p.add_argument('--warnings', nargs='*', default=[])
    emit_p.add_argument('--coordinate', default='')
    emit_p.add_argument('--parent', default=None)

    read_p = sub.add_parser('read', help='读取交接包')
    read_p.add_argument('--project', required=True)

    chain_p = sub.add_parser('chain', help='查看交接链')
    chain_p.add_argument('--project', required=True)

    ctx_p = sub.add_parser('context', help='下游Agent获取上下文')
    ctx_p.add_argument('--project', required=True)

    eval_p = sub.add_parser('evaluate', help='Goal+Eval评估（v1.1新增）')
    eval_p.add_argument('--project', required=True)
    eval_p.add_argument('--agent', required=True)
    eval_p.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    if args.cmd == 'emit':
        emit_handover(args.project, args.agent,
                      goal=args.goal, confirmed_facts=args.facts,
                      excluded_items=args.excluded, completed_checks=args.completed,
                      pending_checks=args.pending, warnings=args.warnings,
                      target_coordinate=args.coordinate, parent_handover=args.parent)
    elif args.cmd == 'read':
        packets = read_handovers(args.project)
        for p in packets:
            print(f"\n--- {p['handover_id']} ---")
            print(f"Agent: {p['source_agent']} @ {p['timestamp'][:19]}")
            print(f"Goal: {p['goal']}")
            print(f"Context: {p['context_snapshot']}")
            print(f"Findings: {p['findings_summary']['total']}")
            print(f"Warnings: {len(p['warnings'])}")
    elif args.cmd == 'chain':
        build_chain(args.project)
    elif args.cmd == 'context':
        ctx = get_context_for_next_agent(args.project)
        print(json.dumps(ctx, ensure_ascii=False, indent=2))
    elif args.cmd == 'evaluate':
        from goal_evaluator import GoalEvaluator
        evaluator = GoalEvaluator()
        output = load_agent_output(PROJECTS / args.project, args.agent)
        result = evaluator.evaluate(args.agent, output, str(PROJECTS / args.project))
        icon = {"PASS": "✅", "FAIL": "❌", "PARTIAL": "⚠️"}.get(result.goal_status, "❓")
        print(f"\n{icon} {result.agent_name}: {result.goal_status}")
        print(f"   分数: {result.total_score:.1%} ({result.checks_passed}/{result.checks_total})")
        print(f"   决策: {result.auto_action}")
        print(f"   {result.recommendation}")
        if result.failures:
            print(f"   失败项:")
            for f in result.failures:
                print(f"     ❌ {f['check']}: {f['msg']}")
        if args.verbose:
            print(f"\n{json.dumps(asdict(result) if 'asdict' in dir() else result.__dict__, ensure_ascii=False, indent=2)}")
    else:
        parser.print_help()
