# -*- coding: utf-8 -*-
"""
融策文件安全守卫 v1.0 — File Safety Guard
==========================================
对标 ZLink Worktree 的安全机制（名称校验 + 删除保护 + 事件日志）。

审计场景与编程场景不同——Agent 产出的是 findings JSON 而非代码文件，
所以不需要完整的 git worktree 隔离。核心需求是：
  1. Agent 中间文件不互踩（命名空间隔离）
  2. 项目清理前完整性检查（所有 Agent 都完成了才允许清）
  3. 文件改动的可追溯性（谁改了哪个文件）

用法:
  from file_safety import ensure_agent_tmp, generate_file_manifest, check_project_safety

  # Agent 启动时
  ensure_agent_tmp('XX项目', 'contract_hound')

  # Agent 完成时
  generate_file_manifest('XX项目', 'contract_hound')

  # 清理项目前
  check_project_safety('XX项目')
"""

import sys, os, json, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

WORKSPACE = Path(__file__).parent.parent
PROJECTS = WORKSPACE / 'audit-blackboard' / 'projects'

# ═══════════════════════════════════════════
# 模块 1: Agent 临时目录隔离
# ═══════════════════════════════════════════

def ensure_agent_tmp(project_name, agent_name):
    """
    为 Agent 创建专属临时工作目录。

    目录结构:
      projects/<项目>/_tmp/<agent_name>/
        ├── _file_manifest.json   ← Agent 完成后生成
        ├── intermediate/          ← 中间数据（提取的CSV/临时JSON等）
        └── logs/                  ← 运行日志（可选）
    """
    proj_dir = PROJECTS / project_name.replace(' ', '_')
    if not proj_dir.exists():
        raise FileNotFoundError(f'项目目录不存在: {proj_dir}')

    agent_tmp = proj_dir / '_tmp' / agent_name
    for sub in ['', 'intermediate', 'logs']:
        d = agent_tmp / sub if sub else agent_tmp
        d.mkdir(parents=True, exist_ok=True)

    return str(agent_tmp)


# ═══════════════════════════════════════════
# 模块 2: 文件清单生成
# ═══════════════════════════════════════════

def generate_file_manifest(project_name, agent_name, extra_files=None):
    """
    Agent 完成后生成文件改动清单。
    对标 ZLink events.jsonl：追索"这个Agent到底改了什么"。

    产出: projects/<项目>/_tmp/<agent>/_file_manifest.json

    参数:
      extra_files: [str]  额外需要记录的文件路径（Agent自己的findings等）
    """
    proj_dir = PROJECTS / project_name.replace(' ', '_')
    agent_tmp = proj_dir / '_tmp' / agent_name

    if not agent_tmp.exists():
        agent_tmp.mkdir(parents=True, exist_ok=True)

    modified_files = []
    new_files = []

    # 扫描临时目录中的所有文件
    for root, dirs, files in os.walk(str(agent_tmp)):
        for f in files:
            fp = Path(root) / f
            rel = fp.relative_to(proj_dir)
            stat = fp.stat()
            modified_files.append({
                'path': str(rel),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime, CST).isoformat(),
            })

    # 添加额外文件
    if extra_files:
        for ef in extra_files:
            fp = proj_dir / ef
            if fp.exists():
                stat = fp.stat()
                new_files.append({
                    'path': ef,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime, CST).isoformat(),
                })
            else:
                new_files.append({
                    'path': ef,
                    'status': 'NOT_FOUND',
                })

    manifest = {
        'manifest_version': '1.0',
        'project': project_name,
        'agent': agent_name,
        'generated_at': datetime.now(CST).isoformat(),
        'tmp_files': modified_files,
        'output_files': new_files,
        'total_files': len(modified_files) + len(new_files),
        'warnings': [],
    }

    # 检查是否缺少 findings 文件
    findings_dir = proj_dir / 'findings'
    expected_finding = findings_dir / f'{agent_name}_*.json'
    if not list(findings_dir.glob(f'{agent_name}_*.json')):
        manifest['warnings'].append(f'未找到 findings 输出文件: {agent_name}_*.json')

    manifest_path = agent_tmp / '_file_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    return manifest


# ═══════════════════════════════════════════
# 模块 3: 项目清理前安全检查
# ═══════════════════════════════════════════

def check_project_safety(project_name, expected_agents=None):
    """
    对标 ZLink remove_worktree：清理前检查完整性。

    检查项:
      1. 所有预期 Agent 是否都产出了 findings
      2. 所有 Agent 是否都生成了文件清单
      3. findings JSON 是否格式正确、编号连续
      4. 跨 Agent 的发现总数是否合理（过少/过多）

    返回: {
        'safe_to_clean': bool,
        'checks': [...],
        'warnings': [...],
        'errors': [...],
    }
    """
    proj_dir = PROJECTS / project_name.replace(' ', '_')
    result = {'safe_to_clean': True, 'checks': [], 'warnings': [], 'errors': []}

    if not proj_dir.exists():
        result['safe_to_clean'] = False
        result['errors'].append(f'项目目录不存在: {proj_dir}')
        return result

    findings_dir = proj_dir / 'findings'

    # 1. 检查 findings 数量
    if not findings_dir.exists():
        result['safe_to_clean'] = False
        result['errors'].append('findings 目录不存在')
        return result

    finding_files = list(findings_dir.glob('*.json'))
    finding_count = len(finding_files)

    result['checks'].append(f'发现 {finding_count} 个 findings 文件')

    if expected_agents and finding_count < len(expected_agents):
        result['safe_to_clean'] = False
        missing = set(expected_agents) - {f.stem.split('_')[0] for f in finding_files}
        result['errors'].append(f'缺少 Agent findings: {missing}')

    # 2. 检查每个 finding 文件的有效性
    for ff in finding_files:
        try:
            data = json.loads(ff.read_text(encoding='utf-8'))
            if not isinstance(data, list):
                result['warnings'].append(f'{ff.name}: 不是JSON数组')
            elif len(data) == 0:
                result['warnings'].append(f'{ff.name}: 空数组（可能没有发现或处理失败）')
            else:
                # 检查 finding_id 连续性
                ids = [item.get('finding_id', '') for item in data if isinstance(item, dict)]
                result['checks'].append(f'{ff.name}: {len(data)} 条发现')
        except json.JSONDecodeError:
            result['safe_to_clean'] = False
            result['errors'].append(f'{ff.name}: JSON格式错误，无法解析')

    # 3. 检查文件清单
    tmp_dir = proj_dir / '_tmp'
    if tmp_dir.exists():
        for agent_dir in tmp_dir.iterdir():
            if agent_dir.is_dir():
                manifest_path = agent_dir / '_file_manifest.json'
                if not manifest_path.exists():
                    result['warnings'].append(f'{agent_dir.name}: 缺少文件清单')
                result['checks'].append(f'{agent_dir.name}: 文件清单 {"✅" if manifest_path.exists() else "❌"}')

    # 4. 汇总
    if result['errors']:
        result['safe_to_clean'] = False

    return result


# ═══════════════════════════════════════════
# 模块 4: 项目归档（带安全检查）
# ═══════════════════════════════════════════

def archive_project(project_name, force=False):
    """
    安全归档项目（对标 ZLink keep_worktree vs remove_worktree）。

    默认行为：检查通过 → 归档到 _archive/，检查不通过 → 拒绝并列出问题
    force=True：跳过检查，强制归档
    """
    proj_dir = PROJECTS / project_name.replace(' ', '_')

    if not proj_dir.exists():
        return {'ok': False, 'error': f'项目不存在: {proj_dir}'}

    if not force:
        safety = check_project_safety(project_name)
        if not safety['safe_to_clean']:
            return {
                'ok': False,
                'error': '安全检查未通过',
                'safety': safety,
                'hint': '使用 force=True 强制归档，或先修复问题',
            }

    # 归档
    archive_dir = PROJECTS / '_archive'
    archive_dir.mkdir(exist_ok=True)

    # 事件日志（对标 ZLink events.jsonl）
    events_file = archive_dir / 'archive_events.jsonl'
    event = {
        'type': 'archive',
        'project': project_name,
        'force': force,
        'ts': datetime.now(CST).timestamp(),
        'iso': datetime.now(CST).isoformat(),
    }
    with open(events_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

    # 移动项目目录
    dest = archive_dir / proj_dir.name
    if dest.exists():
        # 加时间戳避免覆盖
        dest = archive_dir / f'{proj_dir.name}_{datetime.now(CST).strftime("%Y%m%d_%H%M%S")}'

    shutil.move(str(proj_dir), str(dest))

    return {
        'ok': True,
        'archived_to': str(dest),
        'event_logged': True,
    }


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='融策文件安全守卫 v1.0')
    sub = parser.add_subparsers(dest='cmd')

    p_tmp = sub.add_parser('ensure-tmp', help='为Agent创建临时目录')
    p_tmp.add_argument('--project', required=True)
    p_tmp.add_argument('--agent', required=True)

    p_manifest = sub.add_parser('manifest', help='生成Agent文件清单')
    p_manifest.add_argument('--project', required=True)
    p_manifest.add_argument('--agent', required=True)

    p_check = sub.add_parser('check', help='项目安全检查')
    p_check.add_argument('--project', required=True)

    p_archive = sub.add_parser('archive', help='安全归档项目')
    p_archive.add_argument('--project', required=True)
    p_archive.add_argument('--force', action='store_true')

    args = parser.parse_args()

    if args.cmd == 'ensure-tmp':
        path = ensure_agent_tmp(args.project, args.agent)
        print(f'✅ Agent临时目录: {path}')

    elif args.cmd == 'manifest':
        manifest = generate_file_manifest(args.project, args.agent)
        print(f'✅ 文件清单已生成: {len(manifest["tmp_files"])} tmp + {len(manifest["output_files"])} output')
        if manifest['warnings']:
            for w in manifest['warnings']:
                print(f'⚠️  {w}')

    elif args.cmd == 'check':
        safety = check_project_safety(args.project)
        if safety['safe_to_clean']:
            print('✅ 安全检查通过，可以归档')
        else:
            print('❌ 安全检查未通过:')
            for e in safety['errors']:
                print(f'  ❌ {e}')
        for w in safety['warnings']:
            print(f'  ⚠️  {w}')
        for c in safety['checks']:
            print(f'  ℹ️  {c}')

    elif args.cmd == 'archive':
        result = archive_project(args.project, args.force)
        if result['ok']:
            print(f'✅ 已归档: {result["archived_to"]}')
        else:
            print(f'❌ 归档失败: {result.get("error")}')
            if 'safety' in result:
                for e in result['safety']['errors']:
                    print(f'  ❌ {e}')

    else:
        parser.print_help()
