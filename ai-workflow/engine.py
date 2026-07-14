#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
"""
AI自动化工作流 — 核心调度引擎
──────────────────────────────
这是整套AI自动化系统的"大脑"，负责：
  1. 读取工作流配置
  2. 按时间表触发Agent
  3. 监控所有Agent状态
  4. 异常升级和日志记录
  5. 生成运行状态报告

用法:
  python engine.py run        # 运行一次调度周期（检查该干什么）
  python engine.py status     # 查看所有Agent状态
  python engine.py report     # 生成运行报告
  python engine.py overseer   # 运行监工巡检

被cron驱动，不需要常驻进程。每次被触发时检查：
  - 当前时间该谁干活？
  - 有没有上次失败的重试任务？
  - 有没有需要升级给人类的异常？
"""

import os, sys, json, yaml, time, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

# 模型路由集成（加载时自动注册）
try:
    MODEL_ROUTING_PATH = Path(__file__).parent.parent / 'scripts' / 'model_routing.py'
    if MODEL_ROUTING_PATH.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location('model_routing', MODEL_ROUTING_PATH)
        if spec:
            model_routing = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(model_routing)
            ROUTING_AVAILABLE = True
        else:
            ROUTING_AVAILABLE = False
    else:
        ROUTING_AVAILABLE = False
except Exception:
    ROUTING_AVAILABLE = False

CST = timezone(timedelta(hours=8))
WORKFLOW_DIR = Path(__file__).parent
LOGS_DIR = WORKFLOW_DIR / 'logs'
TASKS_DIR = WORKFLOW_DIR / 'tasks'
CONFIG_PATH = WORKFLOW_DIR / 'config.yaml'
STATE_PATH = WORKFLOW_DIR / 'state.json'

# ================================================================
# 配置加载
# ================================================================

def load_config():
    if not CONFIG_PATH.exists():
        print(f'[!] 配置文件不存在: {CONFIG_PATH}')
        return None
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_state():
    if STATE_PATH.exists():
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_state()

def default_state():
    return {
        'version': '1.0',
        'started_at': '2026-07-05T00:00:00+08:00',
        'agent_states': {},
        'run_log': [],
        'escalations': [],
        'last_overseer_run': None,
        'last_engine_run': None,
        'consecutive_runs': 0,
        'total_tasks_completed': 0,
    }

def save_state(state):
    state['last_engine_run'] = datetime.now(CST).isoformat()
    state['consecutive_runs'] = state.get('consecutive_runs', 0) + 1
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ================================================================
# Agent 状态管理
# ================================================================

ALL_AGENTS = [
    'data_scout',       # 信息采集
    'knowledge_keeper', # 知识管理
    'tender_hunter',    # 招标采集
    'model_doctor',     # 模型健康检查
    'token_watcher',    # Token追踪
    'model_router',     # 路由控制器
]

AGENT_LABELS = {
    'data_scout': '📡 数据侦察兵',
    'knowledge_keeper': '📚 知识管理员',
    'tender_hunter': '🎯 招标猎手',
    'model_doctor': '🏥 模型医生',
    'token_watcher': '💰 Token监察员',
    'model_router': '🔀 路由控制器',
}

def init_agent_states(state):
    now = datetime.now(CST)
    for agent_id in ALL_AGENTS:
        if agent_id not in state['agent_states']:
            state['agent_states'][agent_id] = {
                'label': AGENT_LABELS.get(agent_id, agent_id),
                'status': 'idle',
                'last_run': None,
                'last_success': None,
                'last_failure': None,
                'fail_count': 0,
                'total_runs': 0,
                'current_task': None,
            }
    return state


# ================================================================
# 时间判断
# ================================================================

def is_quiet_hours(config):
    now = datetime.now(CST)
    hour = now.hour
    quiet = config.get('quiet_hours', {})
    start = int(quiet.get('start', '23:00').split(':')[0])
    end = int(quiet.get('end', '08:00').split(':')[0])
    if start > end:  # 跨午夜
        return hour >= start or hour < end
    return start <= hour < end

def is_weekday(target_days):
    """target_days: 如 'mon_wed_fri'"""
    today = datetime.now(CST).strftime('%a').lower()
    days = [d.strip().lower() for d in target_days.split('_')]
    return today in days

def should_run(schedule_str):
    """判断当前是否该执行
    schedule_str: 'daily_at_08:00' | 'mon_wed_fri_09:00' | 'daily_at_20:00'
    """
    now = datetime.now(CST)
    parts = schedule_str.split('_at_')
    if len(parts) != 2:
        return False
    
    day_part, time_part = parts
    target_hour = int(time_part.split(':')[0])
    
    # 时间窗口：目标小时 ± 30分钟
    if not (target_hour - 0.5 <= now.hour + now.minute/60 <= target_hour + 0.5):
        return False
    
    # 日期判断
    if day_part == 'daily':
        return True
    elif day_part in ('mon_wed_fri', 'mon_thu'):
        return is_weekday(day_part)
    
    return False


# ================================================================
# 任务队列
# ================================================================

def get_pending_tasks():
    """读取待执行任务"""
    tasks = []
    pending_dir = TASKS_DIR / 'pending'
    if pending_dir.exists():
        for f in pending_dir.glob('*.json'):
            try:
                task = json.loads(f.read_text(encoding='utf-8'))
                task['_file'] = str(f)
                tasks.append(task)
            except:
                pass
    return tasks

def add_task(task_id, task_type, payload):
    """添加任务到队列"""
    pending_dir = TASKS_DIR / 'pending'
    pending_dir.mkdir(parents=True, exist_ok=True)
    task = {
        'task_id': task_id,
        'type': task_type,
        'payload': payload,
        'created_at': datetime.now(CST).isoformat(),
        'retries': 0,
    }
    (pending_dir / f'{task_id}.json').write_text(
        json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')

def complete_task(task_file):
    """标记任务完成"""
    done_dir = TASKS_DIR / 'done'
    done_dir.mkdir(parents=True, exist_ok=True)
    src = Path(task_file)
    if src.exists():
        dst = done_dir / src.name
        src.rename(dst)


# ================================================================
# Agent 执行
# ================================================================

def run_agent(config, state, agent_id):
    """执行一个Agent的任务"""
    agent_cfg = config.get('agents', {}).get(agent_id, {})
    if not agent_cfg:
        print(f'  [!] Agent [{agent_id}] 配置不存在')
        return False

    label = agent_cfg.get('label', agent_id)
    tool = agent_cfg.get('tool', '')
    timeout = agent_cfg.get('timeout_minutes', 10) * 60

    print(f'\n  ▶ 启动 {label}...')
    timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M')

    success = False
    output = ''
    error = ''

    try:
        if not tool:
            print(f'    [跳过] 无执行工具')
            success = True
        elif tool.endswith('.py'):
            # Python脚本
            cmd = f'python -X utf8 {tool}'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=str(Path(__file__).parent.parent),
                encoding='utf-8', errors='replace'
            )
            output = result.stdout[-2000:]
            success = result.returncode == 0
            if not success:
                error = result.stderr[-500:]
        else:
            # HEARTBEAT引用（由主Agent处理）
            print(f'    [委托] {tool} → 需要主Agent执行')
            success = True  # 委托成功

    except subprocess.TimeoutExpired:
        success = False
        error = f'超时 ({timeout}秒)'
    except Exception as e:
        success = False
        error = str(e)

    # 更新Agent状态
    agent_state = state['agent_states'][agent_id]
    agent_state['last_run'] = timestamp
    agent_state['total_runs'] += 1

    if success:
        agent_state['status'] = 'idle'
        agent_state['last_success'] = timestamp
        agent_state['fail_count'] = 0
        state['total_tasks_completed'] += 1
        print(f'    ✅ 成功')
    else:
        agent_state['status'] = 'failed'
        agent_state['last_failure'] = timestamp
        agent_state['fail_count'] += 1
        error_short = error[:100].replace('\n', ' ')
        print(f'    ❌ 失败: {error_short}')

        # 升级判断
        max_retries = config.get('overseer', {}).get('escalation', {}).get('max_retries', 3)
        if agent_state['fail_count'] >= max_retries:
            escalation = {
                'agent': agent_id,
                'label': label,
                'fail_count': agent_state['fail_count'],
                'last_error': error[:300],
                'time': timestamp,
                'status': '需要人工介入',
            }
            state['escalations'].append(escalation)
            print(f'    🚨 已升级：{label} 连续失败 {agent_state["fail_count"]} 次！')

    # 记录日志
    state['run_log'].append({
        'agent': agent_id,
        'time': timestamp,
        'success': success,
        'error': error[:200] if error else None,
    })

    return success


# ================================================================
# 监工巡检
# ================================================================

def run_overseer(state):
    """监工Agent：检查所有Agent健康状态"""
    print(f'\n{"="*50}')
    print(f'  👁️ 监工巡检 — {datetime.now(CST).strftime("%Y-%m-%d %H:%M")}')
    print(f'{"="*50}')

    issues = []
    now = datetime.now(CST)

    for agent_id, agent_state in state['agent_states'].items():
        label = agent_state.get('label', agent_id)
        status = agent_state['status']
        
        # 检查1: Agent状态异常
        if status == 'failed':
            issues.append(f'  ❌ {label}: 上次执行失败 ({agent_state.get("last_failure","?")})')
        
        # 检查2: Agent长期未运行
        last_run = agent_state.get('last_run')
        if last_run:
            try:
                last_dt = datetime.fromisoformat(last_run)
                hours_since = (now - last_dt).total_seconds() / 3600
                if hours_since > 24:
                    issues.append(f'  ⚠️ {label}: {hours_since:.0f}小时未运行')
            except:
                pass

        # 检查3: 升级中项
        for esc in state.get('escalations', []):
            if esc.get('agent') == agent_id and esc.get('status') == '需要人工介入':
                issues.append(f'  🚨 {label}: 需要人工介入 (连续失败{esc.get("fail_count")}次)')

    if issues:
        print('\n  发现问题:')
        for issue in issues:
            print(issue)
    else:
        print('\n  ✅ 所有Agent正常')

    state['last_overseer_run'] = now.isoformat()
    return issues


# ================================================================
# 状态面板
# ================================================================

def show_status(state):
    """展示所有Agent运行状态"""
    now = datetime.now(CST)
    started = state.get('started_at', '?')
    try:
        started_dt = datetime.fromisoformat(started)
        days_running = (now - started_dt).days
    except:
        days_running = '?'

    print(f'\n{"="*60}')
    print(f'  🏭 AI自动化工厂 — 运行状态面板')
    print(f'{"="*60}')
    print(f'  启动时间: {started}')
    print(f'  连续运行: {days_running}天')
    print(f'  引擎调用: {state.get("consecutive_runs", 0)}次')
    print(f'  完成任务: {state.get("total_tasks_completed", 0)}个')
    print(f'  待升级项: {len(state.get("escalations", []))}个')
    print()

    print(f'  {"Agent":<20s} {"状态":<8s} {"上次运行":<20s} {"成功/失败":<10s}')
    print(f'  {"-"*20} {"-"*8} {"-"*20} {"-"*10}')

    for agent_id in ALL_AGENTS:
        agent_state = state['agent_states'].get(agent_id, {})
        label = AGENT_LABELS.get(agent_id, agent_id)
        status = agent_state.get('status', 'unknown')
        last_run = agent_state.get('last_run', '-')[:16] if agent_state.get('last_run') else '-'
        
        success_str = str(agent_state.get('total_runs', 0) - agent_state.get('fail_count', 0))
        fail_str = str(agent_state.get('fail_count', 0))
        sf = f'{success_str}/{fail_str}'

        status_icon = {'idle':'🟢','running':'🔵','failed':'🔴'}.get(status, '⚪')
        print(f'  {status_icon} {label:<16s} {status:<8s} {last_run:<20s} {sf:<10s}')

    # 最近日志
    print(f'\n  最近活动:')
    for log in state.get('run_log', [])[-5:]:
        icon = '✅' if log.get('success') else '❌'
        label = AGENT_LABELS.get(log.get('agent'), log.get('agent', '?'))
        time_str = log.get('time', '')[:16]
        print(f'    {icon} {time_str}  {label}')

    # 升级项
    escalations = state.get('escalations', [])
    if escalations:
        print(f'\n  🚨 待处理升级:')
        for esc in escalations:
            if esc.get('status') == '需要人工介入':
                print(f'    {esc.get("label","?")} — {esc.get("last_error","")[:100]}')

    print(f'\n{"="*60}\n')


# ================================================================
# 主调度
# ================================================================

def run_scheduler(config, state):
    """执行一次调度周期"""
    now = datetime.now(CST)
    print(f'\n⏰ 调度周期 — {now.strftime("%Y-%m-%d %H:%M")}')

    if is_quiet_hours(config):
        print(f'  [静默时间] 跳过常规任务')
        return

    # 检查每个Agent是否该运行
    agents_cfg = config.get('agents', {})
    for agent_id, agent_cfg in agents_cfg.items():
        schedule = agent_cfg.get('schedule', '')
        if not schedule:
            continue

        if should_run(schedule):
            # 检查是否在冷却期内（避免同周期重复跑）
            agent_state = state['agent_states'].get(agent_id, {})
            last_run = agent_state.get('last_run')
            if last_run:
                try:
                    last_dt = datetime.fromisoformat(last_run)
                    if (now - last_dt).total_seconds() < 1800:  # 30分钟冷却
                        continue
                except:
                    pass
            
            run_agent(config, state, agent_id)

    # 清理旧done任务(保留7天)
    done_dir = TASKS_DIR / 'done'
    if done_dir.exists():
        cutoff = now - timedelta(days=7)
        for f in done_dir.glob('*.json'):
            if datetime.fromtimestamp(f.stat().st_mtime, tz=CST) < cutoff:
                f.unlink()

    save_state(state)


# ================================================================
# 生成报告
# ================================================================

def generate_report(state):
    """生成运行报告（供定时推送）"""
    now = datetime.now(CST)
    lines = []
    lines.append(f'🏭 AI自动化工厂日报 — {now.strftime("%Y-%m-%d")}')
    lines.append('')
    
    total = state.get('total_tasks_completed', 0)
    runs = state.get('consecutive_runs', 0)
    lines.append(f'引擎调用: {runs}次 | 完成任务: {total}个')

    # 今日日志
    today = now.strftime('%Y-%m-%d')
    today_logs = [log for log in state.get('run_log', []) 
                  if log.get('time', '').startswith(today)]
    
    if today_logs:
        lines.append(f'\n今日活动 ({len(today_logs)}条):')
        for log in today_logs:
            icon = '✅' if log.get('success') else '❌'
            label = AGENT_LABELS.get(log.get('agent'), log.get('agent', '?'))
            lines.append(f'  {icon} {label}')

    escalations = [e for e in state.get('escalations', []) if e.get('status') == '需要人工介入']
    if escalations:
        lines.append(f'\n🚨 需关注:')
        for esc in escalations:
            lines.append(f'  {esc.get("label","?")} — 连续失败{esc.get("fail_count","?")}次')

    return '\n'.join(lines)


# ================================================================
# Main
# ================================================================

def trigger_agent(config, state, agent_id):
    """手动触发指定Agent"""
    if agent_id not in ALL_AGENTS:
        print(f'未知Agent: {agent_id}')
        print(f'可用Agent: {', '.join(ALL_AGENTS)}')
        return False
    print(f'[手动触发] {AGENT_LABELS.get(agent_id, agent_id)}')
    return run_agent(config, state, agent_id)


def main():
    if len(sys.argv) < 2:
        print('用法: python engine.py [run|status|report|overseer|init|trigger <agent_id>]')
        return

    config = load_config()
    if not config:
        return

    state = load_state()
    state = init_agent_states(state)

    cmd = sys.argv[1]

    if cmd == 'init':
        save_state(state)
        print('[OK] 工作流状态初始化完成')
        show_status(state)

    elif cmd == 'run':
        # 支持 --force 参数强制运行所有Agent
        force = '--force' in sys.argv
        if force:
            print('[强制模式] 跳过时间检查，运行所有Agent')
            for agent_id in ALL_AGENTS:
                trigger_agent(config, state, agent_id)
            # 强制模式也跑监工巡检
            run_overseer(state)
            save_state(state)
        else:
            run_scheduler(config, state)
            # 每次调度后也跑监工巡检
            run_overseer(state)
            save_state(state)

    elif cmd == 'trigger':
        if len(sys.argv) < 3:
            print('用法: python engine.py trigger <agent_id>')
            print(f'可用Agent: {', '.join(ALL_AGENTS)}')
            return
        agent_id = sys.argv[2]
        success = trigger_agent(config, state, agent_id)
        save_state(state)
        if not success:
            sys.exit(1)

    elif cmd == 'status':
        show_status(state)

    elif cmd == 'report':
        report = generate_report(state)
        print(report)

    elif cmd == 'overseer':
        issues = run_overseer(state)
        save_state(state)

    else:
        print(f'未知命令: {cmd}')
        print('用法: python engine.py [run|status|report|overseer|init|trigger <agent_id>]')


if __name__ == '__main__':
    main()
