#!/usr/bin/env python3
"""
融策 Skill 体系控制面板 v1.0
基于三篇文章启示打造的统一管理入口

功能:
  python scripts/skill_hub.py audit     — 技能审计扫描
  python scripts/skill_hub.py dashboard — 控制面板总览
  python scripts/skill_hub.py trace     — 执行追踪概览
  python scripts/skill_hub.py tasks     — 异步任务概览
  python scripts/skill_hub.py recommend — 场景路由推荐
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path.home() / '.openclaw' / 'workspace'
SCRIPTS = WORKSPACE / 'scripts'
CONFIG_DIR = WORKSPACE / 'config'
LOGS_DIR = WORKSPACE / 'logs'


def load_routing_config():
    cfg_path = CONFIG_DIR / 'skill_routing.json'
    if cfg_path.exists():
        with open(cfg_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_audit_report():
    report_path = LOGS_DIR / 'skill_audit.json'
    if report_path.exists():
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def cmd_audit():
    """Run skill audit scan."""
    print('🔍 正在扫描技能体系...')
    result = subprocess.run(
        [sys.executable, '-X', 'utf8', str(SCRIPTS / 'skills_audit.py')],
        capture_output=True, text=True, encoding='utf-8'
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_dashboard():
    """Show control panel dashboard."""
    config = load_routing_config()
    report = load_audit_report()
    
    print('=' * 65)
    print('  🏗️  融策 Skill 体系控制面板')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 65)
    
    # Section 1: Skill Overview
    print('\n📊 一、技能总览')
    total = report.get('total_skills', '?')
    cats = report.get('categories', {})
    print(f'  总计: {total} 个技能')
    print(f'  常驻: {len(config.get("load_strategy", {}).get("global_always_load", []))} 个')
    print(f'  场景: {len(config.get("scenes", {}))} 个场景分组')
    
    # Category breakdown
    cat_labels = {
        'audit_core': '🔴 审计核心', 'audit_method': '🟡 审计方法',
        'bidding_doc': '🟢 标书文档', 'visual_design': '🎨 可视化',
        'data_analysis': '📊 数据分析', 'research': '🔍 研究检索',
        'system': '⚙️ 系统工具', 'media': '📁 媒体处理', 'wecom': '💬 企业微信',
    }
    for cat_key, cat_info in cats.items():
        label = cat_labels.get(cat_key, cat_key)
        count = cat_info.get('count', 0)
        names = ', '.join(cat_info.get('names', [])[:3])
        if count > 3:
            names += '...'
        print(f'  {label}: {count}个 ({names})')
    
    # Section 2: Scene Routing
    print('\n🔀 二、场景路由表')
    scenes = config.get('scenes', {})
    for scene_key, scene_info in scenes.items():
        skills_count = len(scene_info.get('skills', []))
        triggers = ', '.join(scene_info.get('trigger_keywords', [])[:3])
        print(f'  {scene_info["label"]}: {skills_count}个技能 ← 触发词: {triggers}')
    
    # Section 3: Async Tasks
    print('\n🔄 三、异步任务')
    async_dir = LOGS_DIR / 'async_tasks'
    if async_dir.exists():
        running = list(async_dir.glob('bg_*.json'))
        active = [f for f in running if not f.name.startswith('._')]
        if active:
            for tf in sorted(active, key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
                with open(tf, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                status_icon = '🔄' if meta['status'] == 'running' else ('✅' if meta['status'] == 'completed' else '❌')
                print(f'  {status_icon} {meta["bg_id"]}: {meta.get("label", meta["command"][:50])} [{meta["status"]}]')
        else:
            print('  无活跃任务')
    else:
        print('  无任务记录')
    
    # Section 4: Execution Traces
    print('\n📈 四、执行追踪')
    trace_dir = LOGS_DIR / 'traces'
    if trace_dir.exists():
        traces = list(trace_dir.glob('trace_*.json'))
        if traces:
            recent = sorted(traces, key=lambda p: p.stat().st_mtime, reverse=True)[:5]
            for tp in recent:
                with open(tp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                m = data.get('metrics', {})
                score = m.get('overall_score', '?')
                steps = len(data.get('steps', []))
                tokens = m.get('tokens', {}).get('total', 0)
                print(f'  [{score}] {data["task_name"]}: {steps}步 | {tokens} tokens')
        else:
            print('  无追踪记录')
    else:
        print('  无追踪记录')
    
    # Section 5: Warnings
    print('\n⚠️ 五、预警')
    oversized = config.get('size_warnings', {}).get('oversized', [])
    if oversized:
        print(f'  {len(oversized)} 个超大技能（>{config.get("size_warnings", {}).get("max_skill_kb", 500)}KB）:')
        for s in oversized:
            print(f'    📦 {s["name"]}: {s["size_kb"]} KB → {s["action"]}')
    
    # Check stale skills (from audit report)
    recs = report.get('recommendations', [])
    for rec in recs:
        if rec.get('type') == 'stale_skills':
            count = len(rec.get('skills', []))
            if count > 0:
                print(f'  🕐 {count} 个技能超过45天未更新')
    
    print()
    print('─' * 65)
    print('  快速命令:')
    print('  python scripts/skill_hub.py audit      扫描技能')
    print('  python scripts/skill_hub.py recommend  场景路由推荐')
    print('  python scripts/skill_hub.py trace      追踪详情')
    print('  python scripts/skill_hub.py tasks      任务详情')


def cmd_recommend():
    """Recommend which skills to load based on task description."""
    if len(sys.argv) < 3:
        print('Usage: python skill_hub.py recommend <任务描述>')
        print('Example: python skill_hub.py recommend "绩效评价报告复核"')
        return
    
    task = ' '.join(sys.argv[2:])
    config = load_routing_config()
    scenes = config.get('scenes', {})
    global_skills = set(config.get('load_strategy', {}).get('global_always_load', []))
    
    matched_scenes = []
    for scene_key, scene_info in scenes.items():
        keywords = scene_info.get('trigger_keywords', [])
        matches = [kw for kw in keywords if kw in task]
        if matches:
            matched_scenes.append((scene_key, scene_info, matches))
    
    print(f'🔀 场景路由推荐: "{task}"')
    print()
    
    if matched_scenes:
        all_skills = set()
        for sk, si, matches in matched_scenes:
            skills = set(si.get('skills', []))
            all_skills.update(skills)
            print(f'  📌 {si["label"]} (触发词: {", ".join(matches)})')
            for s in sorted(skills):
                is_global = '⭐' if s in global_skills else ''
                print(f'      {s} {is_global}')
        
        # Deduplicate and show final load list
        final = all_skills | global_skills
        print()
        print(f'  建议加载: {len(final)} 个技能 (常驻{len(global_skills)} + 场景{len(all_skills)})')
        print(f'  对比全量{sum(len(s.get("skills", [])) for s in scenes.values()) + len(global_skills)}个 → 节省 {sum(len(s.get("skills", [])) for s in scenes.values()) + len(global_skills) - len(final)} 个')
    else:
        print('  ⚠️ 未匹配到特定场景，使用常驻技能集')
        print(f'  常驻({len(global_skills)}): {", ".join(sorted(global_skills))}')


def cmd_trace():
    """Show execution trace details."""
    subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPTS / 'task_trace.py'), 'stats', '--days=30'])


def cmd_tasks():
    """Show async task status."""
    subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPTS / 'async_task.py'), 'status'])


def main():
    if len(sys.argv) < 2:
        cmd_dashboard()
        return
    
    cmd = sys.argv[1]
    handlers = {
        'audit': cmd_audit,
        'dashboard': cmd_dashboard,
        'trace': cmd_trace,
        'tasks': cmd_tasks,
        'recommend': cmd_recommend,
    }
    
    handler = handlers.get(cmd)
    if handler:
        handler()
    else:
        print(f'Unknown command: {cmd}')
        print('Available: audit, dashboard, trace, tasks, recommend')


if __name__ == '__main__':
    main()
