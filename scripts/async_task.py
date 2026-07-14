#!/usr/bin/env python3
"""
异步任务管理器 (Async Task Manager)
基于 Agent 架构演进理念：慢操作不阻塞 agent_loop，结果以通知形式注入

核心设计（来自第5篇文章）：
1. 判断逻辑：模型显式 background=true 优先 + 关键词启发式兜底
2. 生命周期：background_tasks + background_results + Lock
3. 通知注入：<task_notification> 独立于 tool_result，不破坏 API 配对

用法:
  python scripts/async_task.py start --cmd="python long_ocr.py" --label="批量OCR"
  python scripts/async_task.py status                    # 查看所有后台任务
  python scripts/async_task.py status --id=bg_0001       # 查看单个任务
  python scripts/async_task.py collect                   # 收集已完成任务的通知
  python scripts/async_task.py wait --id=bg_0001 --timeout=300  # 等待任务完成
  python scripts/async_task.py cleanup                   # 清理已完成的任务
"""
import os
import sys
import json
import time
import uuid
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

TASK_DIR = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'async_tasks'
TASK_DIR.mkdir(parents=True, exist_ok=True)

# Slow operation keywords (heuristic fallback)
SLOW_KEYWORDS = [
    'install', 'build', 'test', 'deploy', 'compile',
    'docker build', 'pip install', 'npm install',
    'cargo build', 'pytest', 'make', 'ocr',
    'pdf', 'convert', 'analyze', 'train',
    'download', 'upload', 'backup', 'restore',
]

# Background task registry
_bg_counter = 0
_background_tasks: dict = {}   # bg_id → {tool_use_id, command, status, pid, started_at, label}
_background_results: dict = {} # bg_id → {output, exit_code, finished_at}
_background_lock = threading.Lock()


def is_slow_operation(command: str) -> bool:
    """Heuristic: check if command is likely slow."""
    cmd_lower = command.lower()
    return any(kw in cmd_lower for kw in SLOW_KEYWORDS)


def start_background_task(command: str, label: str = '', cwd: str = None, 
                          env: dict = None, timeout: int = None) -> str:
    """
    Start a background task. Returns bg_id.
    
    Design principles:
    - daemon-like: process runs independently
    - state persisted to disk (survives restarts)
    - returns immediately with bg_id handle
    """
    global _bg_counter
    
    # Load counter from disk
    counter_file = TASK_DIR / '.counter'
    if counter_file.exists():
        _bg_counter = int(counter_file.read_text().strip())
    _bg_counter += 1
    counter_file.write_text(str(_bg_counter))
    
    bg_id = f"bg_{_bg_counter:04d}"
    task_file = TASK_DIR / f'{bg_id}.json'
    
    task_meta = {
        'bg_id': bg_id,
        'command': command,
        'label': label,
        'cwd': cwd or str(Path.cwd()),
        'status': 'running',
        'pid': None,
        'started_at': datetime.now().isoformat(),
        'finished_at': None,
        'timeout': timeout,
    }
    
    def worker():
        try:
            actual_cwd = cwd or str(Path.cwd())
            actual_env = {**os.environ, **(env or {})}
            
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=actual_cwd,
                env=actual_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
            )
            
            # Update pid
            with _background_lock:
                _background_tasks[bg_id]['pid'] = proc.pid
                task_meta['pid'] = proc.pid
                _save_task(task_file, task_meta)
            
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                exit_code = -1
                stderr = f'(timeout after {timeout}s)\n{stderr}'
            
            output = stdout
            if stderr:
                output += f'\n[stderr]\n{stderr}'
            
            result = {
                'output': output[:10000],
                'exit_code': exit_code,
                'stdout_len': len(stdout),
                'stderr_len': len(stderr),
                'finished_at': datetime.now().isoformat(),
            }
            
            status = 'completed' if exit_code == 0 else 'failed'
            
            with _background_lock:
                _background_tasks[bg_id]['status'] = status
                _background_tasks[bg_id]['finished_at'] = result['finished_at']
                _background_results[bg_id] = result
            
            task_meta['status'] = status
            task_meta['finished_at'] = result['finished_at']
            task_meta['exit_code'] = exit_code
            task_meta['output_preview'] = output[:500]
            _save_task(task_file, task_meta)
            
            # Save full output
            output_file = TASK_DIR / f'{bg_id}_output.txt'
            output_file.write_text(output, encoding='utf-8', errors='replace')
            
        except Exception as e:
            with _background_lock:
                _background_tasks[bg_id]['status'] = 'error'
                _background_results[bg_id] = {'output': str(e), 'exit_code': -1, 'error': str(e)}
            
            task_meta['status'] = 'error'
            task_meta['error'] = str(e)
            _save_task(task_file, task_meta)
    
    # Register BEFORE starting thread (prevents race condition)
    with _background_lock:
        _background_tasks[bg_id] = task_meta
    
    _save_task(task_file, task_meta)
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    
    return bg_id


def _save_task(task_file, meta):
    """Persist task metadata to disk."""
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def collect_notifications() -> list:
    """
    Collect completed task notifications in <task_notification> format.
    After collection, move completed tasks to history.
    """
    notifications = []
    
    with _background_lock:
        # Also scan disk for tasks not in memory (survived restart)
        for tf in sorted(TASK_DIR.glob('bg_*.json')):
            if tf.name.startswith('bg_') and tf.name.endswith('.json'):
                bg_id = tf.stem
                with open(tf, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                if meta['status'] in ('completed', 'failed', 'error'):
                    if bg_id in _background_tasks:
                        task = _background_tasks.pop(bg_id)
                    else:
                        task = meta
                    output = _background_results.pop(bg_id, {}).get('output', meta.get('output_preview', ''))
                    summary = output[:200] if output else '(no output)'
                    
                    notification = (
                        f'<task_notification>\n'
                        f'  <task_id>{bg_id}</task_id>\n'
                        f'  <label>{task.get("label", "")}</label>\n'
                        f'  <status>{task["status"]}</status>\n'
                        f'  <command>{task["command"][:200]}</command>\n'
                        f'  <exit_code>{meta.get("exit_code", "?")}</exit_code>\n'
                        f'  <summary>{summary}</summary>\n'
                        f'</task_notification>'
                    )
                    notifications.append(notification)
                    
                    # Move to history
                    history_dir = TASK_DIR / 'history'
                    history_dir.mkdir(exist_ok=True)
                    tf.rename(history_dir / tf.name)
                    
                    # Also move output file
                    output_file = TASK_DIR / f'{bg_id}_output.txt'
                    if output_file.exists():
                        output_file.rename(history_dir / output_file.name)
    
    return notifications


def get_status(bg_id: str = None) -> list:
    """Get status of background tasks."""
    tasks = []
    
    if bg_id:
        task_file = TASK_DIR / f'{bg_id}.json'
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                tasks.append(json.load(f))
    else:
        for tf in sorted(TASK_DIR.glob('bg_*.json'), key=lambda p: p.stat().st_mtime, reverse=True):
            if tf.name.endswith('.json') and not tf.name.startswith('._'):
                with open(tf, 'r', encoding='utf-8') as f:
                    tasks.append(json.load(f))
    
    return tasks


def wait_for_task(bg_id: str, timeout: int = 300) -> dict:
    """Wait for a background task to complete."""
    start = time.time()
    while time.time() - start < timeout:
        task_file = TASK_DIR / f'{bg_id}.json'
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            if meta['status'] in ('completed', 'failed', 'error'):
                return meta
        time.sleep(1)
    return {'status': 'timeout', 'bg_id': bg_id}


def cleanup():
    """Move all completed tasks to history."""
    history_dir = TASK_DIR / 'history'
    history_dir.mkdir(exist_ok=True)
    
    for tf in TASK_DIR.glob('bg_*.json'):
        with open(tf, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta['status'] in ('completed', 'failed', 'error'):
            tf.rename(history_dir / tf.name)
            output_file = TASK_DIR / f'{tf.stem}_output.txt'
            if output_file.exists():
                output_file.rename(history_dir / output_file.name)
            print(f'  Archived: {tf.stem}')


# --- CLI ---

def cmd_start(args):
    command = None
    label = ''
    cwd = None
    timeout = None
    
    for a in args:
        if a.startswith('--cmd='):
            command = a.split('=', 1)[1]
        elif a.startswith('--label='):
            label = a.split('=', 1)[1]
        elif a.startswith('--cwd='):
            cwd = a.split('=', 1)[1]
        elif a.startswith('--timeout='):
            try:
                timeout = int(a.split('=', 1)[1])
            except:
                pass
    
    if not command:
        print('Usage: python async_task.py start --cmd="command" [--label=...] [--cwd=...] [--timeout=300]')
        return
    
    # Check if slow
    if not is_slow_operation(command):
        print(f'⚠️  Command may not be slow: "{command[:80]}"')
        print('   Add --force to run anyway, or use exec for fast commands.')
        if '--force' not in args:
            return
    
    bg_id = start_background_task(command, label, cwd, timeout=timeout)
    
    print(f'✅ Background task started: {bg_id}')
    print(f'   命令: {command[:100]}')
    print(f'   标签: {label or "N/A"}')
    print()
    print('  <task_notification>')
    print(f'    <task_id>{bg_id}</task_id>')
    print(f'    <status>running</status>')
    print(f'    <command>{command[:200]}</command>')
    print('  </task_notification>')


def cmd_status(args):
    bg_id = None
    for a in args:
        if a.startswith('--id='):
            bg_id = a.split('=', 1)[1]
    
    tasks = get_status(bg_id)
    
    if not tasks:
        print('No background tasks.')
        return
    
    running = [t for t in tasks if t['status'] == 'running']
    done = [t for t in tasks if t['status'] != 'running']
    
    if running:
        print(f'🔄 运行中 ({len(running)}):')
        for t in running:
            elapsed = ''
            if t.get('started_at'):
                try:
                    start = datetime.fromisoformat(t['started_at'])
                    elapsed = f' | 已运行 {(datetime.now() - start).total_seconds():.0f}s'
                except:
                    pass
            print(f'  {t["bg_id"]}: {t.get("label", t["command"][:60])}{elapsed}')
    
    if done:
        print(f'\n✅ 已完成 ({len(done)}):')
        for t in done:
            status_icon = '✅' if t['status'] == 'completed' else '❌'
            print(f'  {status_icon} {t["bg_id"]}: {t.get("label", t["command"][:60])} | 状态={t["status"]} | 退出码={t.get("exit_code", "?")}')


def cmd_collect(args):
    notifications = collect_notifications()
    if notifications:
        print(f'📬 {len(notifications)} 个任务通知:')
        print()
        for n in notifications:
            print(n)
            print()
    else:
        print('No completed tasks to collect.')


def cmd_wait(args):
    bg_id = None
    timeout = 300
    for a in args:
        if a.startswith('--id='):
            bg_id = a.split('=', 1)[1]
        elif a.startswith('--timeout='):
            try:
                timeout = int(a.split('=', 1)[1])
            except:
                pass
    
    if not bg_id:
        print('Usage: python async_task.py wait --id=bg_0001 [--timeout=300]')
        return
    
    print(f'⏳ Waiting for {bg_id} (timeout: {timeout}s)...')
    result = wait_for_task(bg_id, timeout)
    
    if result['status'] == 'timeout':
        print(f'⏰ Timeout after {timeout}s')
    elif result['status'] == 'completed':
        print(f'✅ Completed (exit code: {result.get("exit_code")})')
    else:
        print(f'❌ {result["status"]} (exit code: {result.get("exit_code")})')


def cmd_output(args):
    """Read full output of a completed task."""
    bg_id = None
    for a in args:
        if a.startswith('--id='):
            bg_id = a.split('=', 1)[1]
    
    if not bg_id:
        print('Usage: python async_task.py output --id=bg_0001')
        return
    
    output_file = TASK_DIR / f'{bg_id}_output.txt'
    history_file = TASK_DIR / 'history' / f'{bg_id}_output.txt'
    
    for f in [output_file, history_file]:
        if f.exists():
            content = f.read_text(encoding='utf-8', errors='replace')
            print(content[:5000])
            if len(content) > 5000:
                print(f'\n... ({len(content)} total chars, use --full to see all)')
            return
    
    print(f'No output file found for {bg_id}')


def main():
    if len(sys.argv) < 2:
        print('Async Task Manager')
        print('Usage: python async_task.py <command> [args]')
        print()
        print('Commands:')
        print('  start   --cmd="..." [--label=...] [--timeout=300]')
        print('  status  [--id=bg_0001]')
        print('  collect')
        print('  wait    --id=bg_0001 [--timeout=300]')
        print('  output  --id=bg_0001')
        print('  cleanup')
        return
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    handlers = {
        'start': cmd_start,
        'status': cmd_status,
        'collect': cmd_collect,
        'wait': cmd_wait,
        'output': cmd_output,
        'cleanup': lambda a: cleanup(),
    }
    
    handler = handlers.get(cmd)
    if handler:
        handler(args)
    else:
        print(f'Unknown command: {cmd}')


if __name__ == '__main__':
    main()
