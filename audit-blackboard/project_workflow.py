# -*- coding: utf-8 -*-
"""
融策项目工作流 v1.0 — Project Workflow
========================================
一键串联审计项目的完整生命周期：penetrate → spawn → collect → fuse → archive

对标 ZLink 的 create_worktree → bind → claim → execute → complete → keep/remove。
融策的审计场景不需要 worktree（Agent 产 findings 而非改代码），
但需要完整的安全收尾流程。

工作流阶段：
  init     → 创建项目目录 + 初始化状态
  plan     → penetrate 生成并行任务（含 token 预算警告）
  run      → 输出 sessions_spawn 指令（给主 Agent 执行）
  fuse     → issue_fusion 疑点融合（收集→聚类→去重→冲突消解）
  archive  → 安全检查 → 归档到 _archive/

一键全流程：
  python project_workflow.py full "XX项目" --biz 招投标 --files "contracts:500"

用法：
  python project_workflow.py init "XX项目" --biz 预算执行
  python project_workflow.py plan "XX项目" --files "contracts:200,meetings:50"
  python project_workflow.py run "XX项目"
  python project_workflow.py fuse "XX项目"
  python project_workflow.py archive "XX项目"
  python project_workflow.py full "XX项目" --biz 预算执行  # 一键全流程
"""

import sys, json, subprocess, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

PROJECTS = Path(__file__).parent / 'projects'
ARCHIVE = PROJECTS / '_archive'


# ═══════════════════════════════════════════
# Stage 1: init — 创建项目
# ═══════════════════════════════════════════

def init_project(project_name, biz_type, description=''):
    """创建项目目录结构和初始状态"""
    proj_dir = PROJECTS / project_name.replace(' ', '_')

    if proj_dir.exists():
        return {'ok': False, 'error': f'项目已存在: {proj_dir}', 'proj_dir': str(proj_dir)}

    # 创建目录
    for d in ['findings', 'handovers', 'collision', 'workpapers', 'output', 'tasks',
              'raw_data', '_tmp']:
        (proj_dir / d).mkdir(parents=True, exist_ok=True)

    # 写入初始状态
    status = {
        'project_id': project_name.replace(' ', '_'),
        'project_name': project_name,
        'biz_type': biz_type,
        'description': description,
        'created_at': datetime.now(CST).isoformat(),
        'phase': 'init',
        'phases_completed': [],
        'expected_agents': [],
        'handover_chain': [],
        'logs': [f'[{datetime.now(CST).strftime("%H:%M")}] 项目创建: {biz_type}'],
    }
    (proj_dir / 'status.json').write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

    return {
        'ok': True,
        'proj_dir': str(proj_dir),
        'status': status,
    }


# ═══════════════════════════════════════════
# Stage 2: plan — 穿透 + token预算
# ═══════════════════════════════════════════

def plan_project(project_name, biz_type=None, file_counts=None):
    """
    执行 penetrate + token 预算检查。

    file_counts: {'contracts': 200, 'meetings': 50} 或 None
    """
    # 调用 orchestrate_v3.penetrate
    try:
        from orchestrate_v3 import penetrate
    except ImportError:
        return {'ok': False, 'error': '无法加载 orchestrate_v3'}

    proj_dir = PROJECTS / project_name.replace(' ', '_')
    if not proj_dir.exists():
        return {'ok': False, 'error': f'项目不存在: {proj_dir}，请先 init'}

    # 读取状态获取 biz_type
    sf = proj_dir / 'status.json'
    if sf.exists():
        status = json.loads(sf.read_text(encoding='utf-8'))
        biz_type = biz_type or status.get('biz_type', '')

    plan = penetrate(project_name, biz_type, str(proj_dir))
    if not plan:
        return {'ok': False, 'error': '穿透计划生成失败'}

    # ★ v3.1: Token 预算警告
    budget_warnings = []
    if file_counts:
        try:
            from context_guard import estimate_task_tokens
            for agent_name, count_text in file_counts.items():
                count = int(count_text) if isinstance(count_text, str) else count_text
                est = estimate_task_tokens(
                    f'处理{count}个{agent_name}', file_count=count,
                    agent_name=agent_name
                )
                if est['risk_level'] == 'critical':
                    budget_warnings.append({
                        'agent': agent_name,
                        'files': count,
                        'estimated_tokens': est['estimated_total'],
                        'recommendation': est['batch_recommendation'],
                        'risk': 'critical',
                    })
                elif est['risk_level'] == 'warning':
                    budget_warnings.append({
                        'agent': agent_name,
                        'files': count,
                        'estimated_tokens': est['estimated_total'],
                        'recommendation': est['batch_recommendation'],
                        'risk': 'warning',
                    })
        except ImportError:
            pass

    # 更新状态
    if sf.exists():
        status['phase'] = 'planned'
        status['phases_completed'] = status.get('phases_completed', []) + ['plan']
        status['expected_agents'] = plan.get('expected_agents', list(set(
            t['agent_id'] for t in plan['parallel_tasks']
        )))
        status['logs'].append(
            f'[{datetime.now(CST).strftime("%H:%M")}] 穿透计划: '
            f'{len(plan["coordinates"])}坐标系 → {len(plan["parallel_tasks"])} Agent'
        )
        sf.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

    return {
        'ok': True,
        'plan': plan,
        'budget_warnings': budget_warnings,
        'has_critical': any(w['risk'] == 'critical' for w in budget_warnings),
    }


# ═══════════════════════════════════════════
# Stage 3: run — 输出 spawn 指令
# ═══════════════════════════════════════════

def run_project(project_name):
    """
    读取穿透计划 → 输出 sessions_spawn 指令。

    输出格式化为可直接复制给 OpenClaw 主 Agent 的指令文本。
    """
    proj_dir = PROJECTS / project_name.replace(' ', '_')
    plan_path = proj_dir / 'tasks' / 'penetrate_plan_v3.json'

    if not plan_path.exists():
        return {'ok': False, 'error': f'穿透计划不存在: {plan_path}，请先 plan'}

    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    tasks = plan['parallel_tasks']

    # 生成 spawn 指令
    spawn_commands = []
    for t in tasks:
        cmd = {
            'agent': t['agent_id'],
            'coordinate': t['coordinate'],
            'spawn_instruction': (
                f"sessions_spawn(\n"
                f"  agentId: \"{t['agent_id']}\",\n"
                f"  task: \"\"\"\n{t['spawn_task'][:200]}...\n\"\"\",\n"
                f"  runTimeoutSeconds: 600,\n"
                f"  mode: \"run\",\n"
                f"  cleanup: \"keep\"\n"
                f")"
            ),
            'output_file': t['output_file'],
            'features': t.get('v3_1_features', []),
        }
        spawn_commands.append(cmd)

    # 更新状态
    sf = proj_dir / 'status.json'
    if sf.exists():
        status = json.loads(sf.read_text(encoding='utf-8'))
        status['phase'] = 'running'
        status['phases_completed'] = status.get('phases_completed', []) + ['run']
        status['logs'].append(
            f'[{datetime.now(CST).strftime("%H:%M")}] spawn 指令已生成: {len(tasks)} 个 Agent'
        )
        sf.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

    return {
        'ok': True,
        'project': project_name,
        'total_agents': len(tasks),
        'spawn_commands': spawn_commands,
        'cli': '\n'.join([
            f'# {t["agent_id"]} ({t["coordinate"]}坐标系)\n'
            f'# 输出 → {t["output_file"]}\n'
            for t in tasks
        ]),
    }


# ═══════════════════════════════════════════
# Stage 4: fuse — 疑点融合
# ═══════════════════════════════════════════

def fuse_project(project_name):
    """调用 issue_fusion 进行疑点融合"""
    try:
        from issue_fusion import accept_findings, cluster_findings, dedup_findings

        proj_slug = project_name.replace(' ', '_')
        proj_dir = PROJECTS / proj_slug

        if not proj_dir.exists():
            return {'ok': False, 'error': f'项目不存在: {proj_dir}'}

        # Step 1: 接收所有 Agent findings
        accept_result = accept_findings(proj_slug)
        accepted_count = accept_result.get('total', 0) if isinstance(accept_result, dict) else 0

        # Step 2: 聚类
        cluster_result = cluster_findings(proj_slug) if accepted_count > 0 else {}
        clusters = len(cluster_result.get('clusters', [])) if isinstance(cluster_result, dict) else 0

        # Step 3: 去重
        dedup_result = dedup_findings(proj_slug) if accepted_count > 0 else {}
        removed = dedup_result.get('removed', 0) if isinstance(dedup_result, dict) else 0

        # 更新状态
        sf = proj_dir / 'status.json'
        if sf.exists():
            status = json.loads(sf.read_text(encoding='utf-8'))
            status['phase'] = 'fused'
            status['phases_completed'] = status.get('phases_completed', []) + ['fuse']
            status['fusion'] = {
                'accepted': accepted_count,
                'clusters': clusters,
                'dedup_removed': removed,
                'fused_at': datetime.now(CST).isoformat(),
            }
            status['logs'].append(
                f'[{datetime.now(CST).strftime("%H:%M")}] 疑点融合: '
                f'接收{accepted_count} → {clusters}聚类 → 去重{removed}'
            )
            sf.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

        return {
            'ok': True,
            'accepted': accepted_count,
            'clusters': clusters,
            'dedup_removed': removed,
        }

    except ImportError as e:
        return {'ok': False, 'error': f'无法加载 issue_fusion: {e}'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ═══════════════════════════════════════════
# Stage 5: archive — 安全检查 + 归档
# ═══════════════════════════════════════════

def archive_project(project_name, force=False):
    """安全检查 → 归档"""
    try:
        from file_safety import archive_project as fs_archive
        result = fs_archive(project_name, force=force)
        return result
    except ImportError as e:
        return {'ok': False, 'error': f'无法加载 file_safety: {e}'}


# ═══════════════════════════════════════════
# 一键全流程
# ═══════════════════════════════════════════

def full_workflow(project_name, biz_type, description='', file_counts=None, force_archive=False):
    # 解析 file_counts 字符串
    if isinstance(file_counts, str) and file_counts:
        fc = {}
        for pair in file_counts.split(','):
            k, v = pair.split(':')
            fc[k.strip()] = int(v.strip())
        file_counts = fc
    """
    一键全流程：init → plan → run → (等待Agent完成) → fuse → archive

    注意：run 阶段只输出 spawn 指令，实际执行需要主 Agent 手动 spawn。
    这里 run 之后会暂停，提示用户去 spawn Agent。

    如果所有 findings 已存在，可以跳过 run 直接 fuse + archive。
    """
    results = {'project': project_name, 'stages': {}}

    # Stage 1: init
    r = init_project(project_name, biz_type, description)
    results['stages']['init'] = r
    if not r['ok']:
        return results
    print(f'✅ [1/5] init: {r["proj_dir"]}')

    # Stage 2: plan
    r = plan_project(project_name, biz_type, file_counts)
    results['stages']['plan'] = r
    if not r['ok']:
        return results
    print(f'✅ [2/5] plan: {len(r["plan"]["parallel_tasks"])} Agent 任务')
    if r.get('has_critical'):
        print(f'   🚨 Token预算警告:')
        for w in r['budget_warnings']:
            if w['risk'] == 'critical':
                print(f'      {w["agent"]}: {w["files"]}文件 → {w["recommendation"]}')

    # Stage 3: run
    r = run_project(project_name)
    results['stages']['run'] = r
    if not r['ok']:
        return results
    print(f'✅ [3/5] run: {r["total_agents"]} 条 spawn 指令已生成')
    print(f'   ⏳ 请在 OpenClaw 中手动 spawn 各 Agent，完成后继续...')

    return results


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='融策项目工作流 v1.0')
    sub = parser.add_subparsers(dest='cmd')

    p_init = sub.add_parser('init', help='创建项目')
    p_init.add_argument('name', help='项目名称')
    p_init.add_argument('--biz', required=True, help='审计类型')
    p_init.add_argument('--desc', default='', help='项目描述')

    p_plan = sub.add_parser('plan', help='穿透+预算检查')
    p_plan.add_argument('name', help='项目名称')
    p_plan.add_argument('--biz', default=None, help='审计类型（覆盖项目已记录的类型）')
    p_plan.add_argument('--files', default=None, help='文件数预估，格式: contracts:500,meetings:50')

    p_run = sub.add_parser('run', help='输出spawn指令')
    p_run.add_argument('name', help='项目名称')

    p_fuse = sub.add_parser('fuse', help='疑点融合')
    p_fuse.add_argument('name', help='项目名称')

    p_archive = sub.add_parser('archive', help='安全归档')
    p_archive.add_argument('name', help='项目名称')
    p_archive.add_argument('--force', action='store_true', help='强制归档（跳过检查）')

    p_full = sub.add_parser('full', help='一键全流程')
    p_full.add_argument('name', help='项目名称')
    p_full.add_argument('--biz', required=True, help='审计类型')
    p_full.add_argument('--desc', default='', help='项目描述')
    p_full.add_argument('--files', default=None, help='文件数预估')

    p_status = sub.add_parser('status', help='查看项目状态')
    p_status.add_argument('name', help='项目名称')

    args = parser.parse_args()

    if args.cmd == 'init':
        r = init_project(args.name, args.biz, args.desc)
        if r['ok']:
            print(f'✅ 项目已创建: {r["proj_dir"]}')
        else:
            print(f'❌ {r["error"]}')

    elif args.cmd == 'plan':
        file_counts = None
        if args.files:
            file_counts = {}
            for pair in args.files.split(','):
                k, v = pair.split(':')
                file_counts[k.strip()] = int(v.strip())
        r = plan_project(args.name, args.biz, file_counts)
        if r['ok']:
            print(f'✅ 穿透计划: {len(r["plan"]["parallel_tasks"])} Agent')
            if r.get('has_critical'):
                print('\n🚨 Token预算严重警告:')
                for w in r['budget_warnings']:
                    if w['risk'] == 'critical':
                        print(f'  {w["agent"]}: {w["files"]} 文件 → {w["recommendation"]}')
            elif r.get('budget_warnings'):
                print('\n⚠️  Token预算提醒:')
                for w in r['budget_warnings']:
                    print(f'  {w["agent"]}: {w["files"]} 文件 → {w["recommendation"]}')
        else:
            print(f'❌ {r.get("error")}')

    elif args.cmd == 'run':
        r = run_project(args.name)
        if r['ok']:
            print(f'=== Spawn 指令: {args.name} ===\n')
            print(f'共 {r["total_agents"]} 个 Agent，可同时 spawn:\n')
            for c in r['spawn_commands']:
                print(f'# {c["agent"]} ({c["coordinate"]}坐标系) → {c["output_file"]}')
                print(f'# 特性: {", ".join(c["features"])}')
                print(f'sessions_spawn(agentId: "{c["agent"]}", task: """...""", runTimeoutSeconds: 600, mode: "run", cleanup: "keep")\n')
        else:
            print(f'❌ {r.get("error")}')

    elif args.cmd == 'fuse':
        r = fuse_project(args.name)
        if r['ok']:
            print(f'✅ 疑点融合完成: 接收{r["accepted"]} → {r["clusters"]}聚类 → 去重{r["dedup_removed"]}')
        else:
            print(f'❌ {r["error"]}')

    elif args.cmd == 'archive':
        r = archive_project(args.name, args.force)
        if r['ok']:
            print(f'✅ 已归档: {r["archived_to"]}')
        else:
            print(f'❌ 归档失败: {r.get("error")}')
            if 'safety' in r:
                for e in r['safety'].get('errors', []):
                    print(f'  ❌ {e}')
                for w in r['safety'].get('warnings', []):
                    print(f'  ⚠️  {w}')

    elif args.cmd == 'full':
        r = full_workflow(args.name, args.biz, args.desc, file_counts=args.files)
        print(f'\n=== 全流程完成 ===')
        for stage, result in r['stages'].items():
            icon = '✅' if result.get('ok') else '❌'
            print(f'  {icon} {stage}')
        if r['stages'].get('run', {}).get('ok'):
            print(f'\n⏳ 下一步: 在 OpenClaw 中 spawn {r["stages"]["run"]["total_agents"]} 个 Agent')
            print(f'   完成后: python project_workflow.py fuse "{args.name}"')
            print(f'   最后:   python project_workflow.py archive "{args.name}"')

    elif args.cmd == 'status':
        sf = PROJECTS / args.name.replace(' ', '_') / 'status.json'
        if sf.exists():
            s = json.loads(sf.read_text(encoding='utf-8'))
            print(f'=== {s["project_name"]} ===')
            print(f'类型: {s["biz_type"]}')
            print(f'阶段: {s["phase"]}')
            print(f'已完成: {", ".join(s.get("phases_completed", []))}')
            if 'fusion' in s:
                print(f'融合: 接收{s["fusion"]["accepted"]} → {s["fusion"]["clusters"]}聚类 → 去重{s["fusion"]["dedup_removed"]}')
            print(f'\n日志:')
            for log in s.get('logs', [])[-5:]:
                print(f'  {log}')
        else:
            print(f'项目不存在: {args.name}')

    else:
        parser.print_help()
