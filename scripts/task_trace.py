#!/usr/bin/env python3
"""
任务执行追踪系统 (Task Execution Trace System)
基于 Skill-insight 设计理念的三维评测 + 过程级追溯

用法:
  python scripts/task_trace.py start --task "绩效审计-数据核查" --skill audit-report-review
  python scripts/task_trace.py step --name "读取数据" --tool exec --input "python analyze.py"
  python scripts/task_trace.py step --name "生成结论" --tool llm --model v4-pro
  python scripts/task_trace.py finish --result "通过" --output_file "findings.json"
  python scripts/task_trace.py report --trace-id xxx
  python scripts/task_trace.py list [--days 7]
"""
import os
import sys
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

TRACE_DIR = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'traces'

# Three-dimensional evaluation rubrics
EVAL_DIMENSIONS = {
    'effectiveness': {
        'label': '执行精准度',
        'factors': ['path_deviation', 'skip_rate', 'extra_ops', 'result_correctness'],
        'weight': 0.5,
    },
    'efficiency': {
        'label': '端到端时效',
        'factors': ['total_duration', 'llm_rounds', 'context_load_time', 'tool_wait_time'],
        'weight': 0.3,
    },
    'cost': {
        'label': '计算成本',
        'factors': ['input_tokens', 'output_tokens', 'total_tokens', 'model_unit_price'],
        'weight': 0.2,
    },
}

class TaskTrace:
    def __init__(self, task_name, skill=None, model=None):
        self.trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.task_name = task_name
        self.skill = skill
        self.model = model
        self.started_at = datetime.now().isoformat()
        self.steps = []
        self.result = None
        self.output_file = None
        self.tags = []
        self.errors = []
    
    def add_step(self, name, tool, input_text, output_text=None, duration_ms=0, 
                 tokens_in=0, tokens_out=0, model=None, status='ok', error=None):
        step = {
            'seq': len(self.steps) + 1,
            'name': name,
            'tool': tool,
            'input': input_text[:500],
            'output': output_text[:500] if output_text else None,
            'duration_ms': duration_ms,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'model': model,
            'status': status,
            'error': error,
            'timestamp': datetime.now().isoformat(),
        }
        self.steps.append(step)
        return step
    
    def finish(self, result, output_file=None, errors=None):
        self.result = result
        self.output_file = output_file
        self.finished_at = datetime.now().isoformat()
        if errors:
            self.errors = errors
    
    def compute_metrics(self):
        """Compute 3D evaluation metrics."""
        total_duration = sum(s['duration_ms'] for s in self.steps)
        total_tokens_in = sum(s['tokens_in'] for s in self.steps)
        total_tokens_out = sum(s['tokens_out'] for s in self.steps)
        total_tokens = total_tokens_in + total_tokens_out
        llm_rounds = sum(1 for s in self.steps if s['tool'] == 'llm')
        error_steps = sum(1 for s in self.steps if s['status'] == 'error')
        
        metrics = {
            'total_duration_ms': total_duration,
            'total_duration_s': round(total_duration / 1000, 1),
            'step_count': len(self.steps),
            'llm_rounds': llm_rounds,
            'error_steps': error_steps,
            'tokens': {
                'input': total_tokens_in,
                'output': total_tokens_out,
                'total': total_tokens,
            },
            'success_rate': 1 - error_steps / max(len(self.steps), 1),
            'avg_step_duration_ms': round(total_duration / max(len(self.steps), 1)),
        }
        
        # Efficiency score (lower is better)
        if self.steps:
            metrics['efficiency_score'] = _score_efficiency(total_duration, llm_rounds)
            metrics['cost_score'] = _score_cost(total_tokens_in, total_tokens_out)
            metrics['overall_score'] = round(
                metrics['success_rate'] * 0.5 + 
                metrics['efficiency_score'] * 0.3 + 
                metrics['cost_score'] * 0.2, 2
            )
        
        return metrics
    
    def to_mermaid(self):
        """Generate Mermaid flowchart of execution."""
        lines = ['```mermaid', 'graph TD']
        for step in self.steps:
            icon = '✅' if step['status'] == 'ok' else ('⚠️' if step['status'] == 'warning' else '❌')
            node_id = f"S{step['seq']}"
            label = f"{step['name']}<br/>{step['tool']} ({step['duration_ms']}ms)"
            lines.append(f'    {node_id}["{icon} {label}"]')
            if step['seq'] > 1:
                lines.append(f'    S{step["seq"]-1} --> {node_id}')
        lines.append('```')
        return '\n'.join(lines)
    
    def to_dict(self):
        metrics = self.compute_metrics()
        return {
            'trace_id': self.trace_id,
            'task_name': self.task_name,
            'skill': self.skill,
            'model': self.model,
            'started_at': self.started_at,
            'finished_at': getattr(self, 'finished_at', None),
            'steps': self.steps,
            'result': self.result,
            'output_file': self.output_file,
            'errors': self.errors,
            'metrics': metrics,
            'mermaid': self.to_mermaid(),
        }
    
    def save(self):
        TRACE_DIR.mkdir(parents=True, exist_ok=True)
        path = TRACE_DIR / f'{self.trace_id}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return path


def _score_efficiency(total_duration_ms, llm_rounds):
    """Score efficiency: 1.0 = excellent, 0.0 = terrible"""
    duration_score = max(0, 1 - total_duration_ms / 300000)  # 5min baseline
    rounds_score = max(0, 1 - llm_rounds / 10)  # 10 rounds baseline
    return round(duration_score * 0.6 + rounds_score * 0.4, 2)


def _score_cost(input_tokens, output_tokens):
    """Score cost efficiency"""
    total = input_tokens + output_tokens
    return max(0, 1 - total / 50000)  # 50k tokens baseline


# --- CLI ---

def cmd_start(args):
    task_name = None
    skill = None
    model = None
    for a in args:
        if a.startswith('--task='):
            task_name = a.split('=', 1)[1]
        elif a.startswith('--skill='):
            skill = a.split('=', 1)[1]
        elif a.startswith('--model='):
            model = a.split('=', 1)[1]
    
    if not task_name:
        print('Usage: python task_trace.py start --task="任务名" [--skill=xxx] [--model=xxx]')
        return
    
    trace = TaskTrace(task_name, skill, model)
    trace.save()
    
    # Write active trace pointer
    ptr_path = TRACE_DIR / '.active_trace'
    ptr_path.write_text(trace.trace_id)
    
    print(f'✅ Trace started: {trace.trace_id}')
    print(f'   任务: {task_name}')
    print(f'   技能: {skill or "N/A"}')
    print(f'   模型: {model or "N/A"}')


def cmd_step(args):
    ptr_path = TRACE_DIR / '.active_trace'
    if not ptr_path.exists():
        print('❌ No active trace. Run "start" first.')
        return
    
    trace_id = ptr_path.read_text().strip()
    trace_path = TRACE_DIR / f'{trace_id}.json'
    if not trace_path.exists():
        print(f'❌ Trace file not found: {trace_path}')
        return
    
    with open(trace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    trace = TaskTrace.__new__(TaskTrace)
    trace.trace_id = data['trace_id']
    trace.task_name = data['task_name']
    trace.skill = data.get('skill')
    trace.model = data.get('model')
    trace.started_at = data['started_at']
    trace.steps = data.get('steps', [])
    trace.result = data.get('result')
    trace.output_file = data.get('output_file')
    trace.errors = data.get('errors', [])
    
    # Parse step args
    step_name = None
    tool = 'exec'
    input_text = ''
    duration_ms = 0
    tokens_in = 0
    tokens_out = 0
    model = None
    status = 'ok'
    error = None
    
    for a in args:
        if a.startswith('--name='):
            step_name = a.split('=', 1)[1]
        elif a.startswith('--tool='):
            tool = a.split('=', 1)[1]
        elif a.startswith('--input='):
            input_text = a.split('=', 1)[1]
        elif a.startswith('--duration='):
            try:
                duration_ms = int(a.split('=', 1)[1])
            except:
                pass
        elif a.startswith('--tokens-in='):
            try:
                tokens_in = int(a.split('=', 1)[1])
            except:
                pass
        elif a.startswith('--tokens-out='):
            try:
                tokens_out = int(a.split('=', 1)[1])
            except:
                pass
        elif a.startswith('--model='):
            model = a.split('=', 1)[1]
        elif a.startswith('--status='):
            status = a.split('=', 1)[1]
        elif a.startswith('--error='):
            error = a.split('=', 1)[1]
    
    if not step_name:
        print('Usage: python task_trace.py step --name="步骤名" [--tool=exec|llm|read|write] ...')
        return
    
    trace.add_step(step_name, tool, input_text, duration_ms=duration_ms,
                   tokens_in=tokens_in, tokens_out=tokens_out, model=model, 
                   status=status, error=error)
    trace.save()
    
    step_num = len(trace.steps)
    print(f'✅ Step {step_num}: {step_name} ({tool})')


def cmd_finish(args):
    ptr_path = TRACE_DIR / '.active_trace'
    if not ptr_path.exists():
        print('❌ No active trace.')
        return
    
    trace_id = ptr_path.read_text().strip()
    trace_path = TRACE_DIR / f'{trace_id}.json'
    if not trace_path.exists():
        print(f'❌ Trace file not found: {trace_path}')
        return
    
    with open(trace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    trace = TaskTrace.__new__(TaskTrace)
    trace.trace_id = data['trace_id']
    trace.task_name = data['task_name']
    trace.skill = data.get('skill')
    trace.model = data.get('model')
    trace.started_at = data['started_at']
    trace.steps = data.get('steps', [])
    
    result = 'completed'
    output_file = None
    for a in args:
        if a.startswith('--result='):
            result = a.split('=', 1)[1]
        elif a.startswith('--output='):
            output_file = a.split('=', 1)[1]
    
    trace.finish(result, output_file)
    trace.save()
    
    # Clear active pointer
    ptr_path.unlink(missing_ok=True)
    
    metrics = trace.compute_metrics()
    print(f'✅ Trace finished: {trace_id}')
    print(f'   结果: {result}')
    print(f'   步骤数: {len(trace.steps)}')
    print(f'   总耗时: {metrics["total_duration_s"]}s')
    print(f'   LLM轮次: {metrics["llm_rounds"]}')
    print(f'   Token消耗: {metrics["tokens"]["total"]}')
    print(f'   综合评分: {metrics.get("overall_score", "N/A")}')


def cmd_report(args):
    trace_id = None
    for a in args:
        if a.startswith('--trace-id='):
            trace_id = a.split('=', 1)[1]
    
    if trace_id:
        trace_path = TRACE_DIR / f'{trace_id}.json'
        if not trace_path.exists():
            print(f'❌ Trace not found: {trace_id}')
            return
        _print_report(trace_path)
    else:
        # Show latest
        traces = sorted(TRACE_DIR.glob('trace_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        if traces:
            _print_report(traces[0])
        else:
            print('No traces found.')


def _print_report(trace_path):
    with open(trace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    m = data.get('metrics', {})
    print('=' * 60)
    print(f'📊 执行追踪报告: {data["trace_id"]}')
    print('=' * 60)
    print(f'任务: {data["task_name"]}')
    print(f'技能: {data.get("skill", "N/A")}')
    print(f'模型: {data.get("model", "N/A")}')
    print(f'时间: {data["started_at"]}')
    print(f'结果: {data.get("result", "N/A")}')
    print()
    print('--- 三维评测 ---')
    print(f'  🎯 执行精准度: 成功率 {m.get("success_rate", 0)*100:.0f}%')
    print(f'  ⚡ 端到端时效: {m.get("total_duration_s", 0)}s / {m.get("llm_rounds", 0)}轮LLM')
    print(f'  💰 计算成本: {m.get("tokens", {}).get("total", 0)} tokens')
    print(f'  📈 综合评分: {m.get("overall_score", "N/A")}')
    print()
    print('--- 步骤详情 ---')
    for step in data.get('steps', []):
        status_icon = '✅' if step['status'] == 'ok' else '⚠️'
        print(f'  {status_icon} [{step["seq"]}] {step["name"]}')
        print(f'     工具: {step["tool"]} | 耗时: {step["duration_ms"]}ms | Tokens: {step["tokens_in"]}+{step["tokens_out"]}')
        if step.get('error'):
            print(f'     错误: {step["error"]}')
    
    print()
    print('--- 执行流程 ---')
    print(data.get('mermaid', 'N/A'))


def cmd_list(args):
    days = 7
    for a in args:
        if a.startswith('--days='):
            try:
                days = int(a.split('=', 1)[1])
            except:
                pass
    
    cutoff = datetime.now() - timedelta(days=days)
    traces = sorted(TRACE_DIR.glob('trace_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    
    print(f'📋 近{days}天执行追踪 ({len(traces)} 条):')
    print()
    
    for tp in traces:
        mtime = datetime.fromtimestamp(tp.stat().st_mtime)
        if mtime < cutoff:
            continue
        with open(tp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        m = data.get('metrics', {})
        score = m.get('overall_score', '?')
        tokens = m.get('tokens', {}).get('total', 0)
        print(f'  [{score}] {data["trace_id"]} | {data["task_name"]}')
        print(f'       {mtime.strftime("%m-%d %H:%M")} | {m.get("total_duration_s", "?")}s | {tokens} tokens | {data.get("result", "?")}')


def cmd_stats(args):
    """Aggregate statistics across all traces."""
    days = 30
    for a in args:
        if a.startswith('--days='):
            try:
                days = int(a.split('=', 1)[1])
            except:
                pass
    
    cutoff = datetime.now() - timedelta(days=days)
    traces = sorted(TRACE_DIR.glob('trace_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    
    total_tokens = 0
    total_duration = 0
    scores = []
    by_skill = defaultdict(lambda: {'count': 0, 'tokens': 0, 'scores': []})
    
    for tp in traces:
        mtime = datetime.fromtimestamp(tp.stat().st_mtime)
        if mtime < cutoff:
            continue
        with open(tp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        m = data.get('metrics', {})
        total_tokens += m.get('tokens', {}).get('total', 0)
        total_duration += m.get('total_duration_ms', 0)
        score = m.get('overall_score')
        if score:
            scores.append(score)
        
        skill = data.get('skill', 'unknown')
        by_skill[skill]['count'] += 1
        by_skill[skill]['tokens'] += m.get('tokens', {}).get('total', 0)
        if score:
            by_skill[skill]['scores'].append(score)
    
    count = len([tp for tp in traces if datetime.fromtimestamp(tp.stat().st_mtime) >= cutoff])
    
    print('=' * 60)
    print(f'📊 近{days}天执行统计')
    print('=' * 60)
    print(f'总任务数: {count}')
    print(f'总Token: {total_tokens:,}')
    print(f'总耗时: {total_duration/1000:.0f}s')
    print(f'平均评分: {sum(scores)/len(scores):.2f}' if scores else 'N/A')
    print()
    print('--- 按技能统计 ---')
    for skill, stats in sorted(by_skill.items(), key=lambda x: -x[1]['count']):
        avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
        print(f'  {skill}: {stats["count"]}次 | {stats["tokens"]:,} tokens | 均分 {avg_score:.2f}')


def main():
    if len(sys.argv) < 2:
        print('Task Execution Trace System')
        print('Usage: python task_trace.py <command> [args]')
        print()
        print('Commands:')
        print('  start   --task="..." [--skill=...] [--model=...]')
        print('  step    --name="..." [--tool=...] [--duration=...] [--tokens-in=...]')
        print('  finish  --result="..." [--output=...]')
        print('  report  [--trace-id=...]')
        print('  list    [--days=7]')
        print('  stats   [--days=30]')
        return
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    {
        'start': cmd_start,
        'step': cmd_step,
        'finish': cmd_finish,
        'report': cmd_report,
        'list': cmd_list,
        'stats': cmd_stats,
    }.get(cmd, lambda a: print(f'Unknown command: {cmd}'))(args)


if __name__ == '__main__':
    main()
