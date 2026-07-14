#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具使用追踪器 (Tool Usage Tracker) v1.0
=========================================
追踪"造工具 vs 用工具"的比例。
每次心跳时自动运行，量化"工具工厂"的生产效率。

输出: 工具使用率 = 已产生交付物的工具数 / 工具总数
目标: 工具使用率 ≥ 70%
"""
import json, os, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
TZ = timezone(timedelta(hours=8))
STATE_PATH = ROOT / "config" / "tool_usage.json"

def get_skill_count():
    """获取当前技能数"""
    skills_dir = os.path.expanduser(r'~/.openclaw/skills')
    if not os.path.isdir(skills_dir):
        return 0
    return len([s for s in os.listdir(skills_dir) 
                if os.path.isdir(os.path.join(skills_dir, s)) 
                and os.path.isfile(os.path.join(skills_dir, s, 'SKILL.md'))])

def get_project_count():
    """获取项目数"""
    projects_dir = ROOT / "projects"
    if not projects_dir.exists():
        return 0
    return len([p for p in projects_dir.iterdir() if p.is_dir()])

def get_audit_project_count():
    """获取audit-blackboard项目数"""
    proj_dir = ROOT / "audit-blackboard" / "projects"
    if not proj_dir.exists():
        return 0
    return len([p for p in proj_dir.iterdir() if p.is_dir()])

def get_engine_task_count():
    """获取engine已完成任务数"""
    state_path = ROOT / "ai-workflow" / "state.json"
    if not state_path.exists():
        return 0
    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
        return state.get('total_tasks_completed', 0)
    except:
        return 0

def get_output_count():
    """获取outputs目录中的交付物数"""
    output_dir = ROOT / "outputs"
    if not output_dir.exists():
        return 0
    return len([f for f in output_dir.rglob('*') if f.is_file() and f.suffix in ('.docx', '.pptx', '.xlsx', '.pdf', '.md', '.html')])

def get_temp_file_count():
    """获取根目录临时文件数"""
    temp_count = 0
    for f in ROOT.iterdir():
        name = f.name
        if f.is_file() and (name.startswith('tmp_') or name.startswith('temp_')):
            temp_count += 1
    return temp_count

def show_report():
    """显示使用报告"""
    now = datetime.now(TZ)
    skills = get_skill_count()
    projects = get_project_count()
    audit_projects = get_audit_project_count()
    engine_tasks = get_engine_task_count()
    outputs = get_output_count()
    temps = get_temp_file_count()

    # 工具使用率 = 有交付物的项目数 / 技能数
    # 更合理的：engine有产出的Agent数 / 总Agent数
    agent_usage = f"{engine_tasks}/6 (Agent任务完成数)"
    
    # 产出/工具比
    if skills > 0:
        output_ratio = outputs / skills
    else:
        output_ratio = 0

    print(f"\n{'='*55}")
    print(f"  🛠️ 工具使用率追踪 — {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")
    print(f"  📦 技能总数: {skills}")
    print(f"  📋 项目数: {projects}")
    print(f"  🔲 审计项目数: {audit_projects}")
    print(f"  🏭 引擎任务完成: {engine_tasks}")
    print(f"  📄 交付物数: {outputs}")
    print(f"  📊 产出/工具比: {output_ratio:.2f}")
    print(f"  🗑️ 临时文件数: {temps}")
    print(f"  🤖 Agent使用率: {agent_usage}")
    print()

    # 评估
    if engine_tasks >= skills * 0.1:
        print(f"  🟢 使用率良好：每个技能平均被使用 {engine_tasks/skills:.1f} 次")
    elif engine_tasks >= 3:
        print(f"  🟡 使用率一般：有产出但需提升")
    else:
        print(f"  🔴 使用率低：{skills}个技能只有{engine_tasks}次引擎任务完成")

    if output_ratio >= 1:
        print(f"  🟢 产出健康：每项技能对应≥1个交付物")
    else:
        print(f"  🟡 产出待提升：每{1/output_ratio:.0f}项技能才有1个交付物")

    if temps <= 5:
        print(f"  🟢 工作区整洁：临时文件仅{temps}个")
    elif temps <= 15:
        print(f"  🟡 工作区一般：{temps}个临时文件建议清理")
    else:
        print(f"  🔴 工作区杂乱：{temps}个临时文件需要清理")

    print(f"{'='*55}\n")

    # 保存状态
    state = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "skills": skills,
        "projects": projects,
        "audit_projects": audit_projects,
        "engine_tasks": engine_tasks,
        "outputs": outputs,
        "temp_files": temps,
        "output_ratio": round(output_ratio, 2),
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return state

def cmd_history():
    """查看历史趋势"""
    path = ROOT / "config" / "tool_usage_history.jsonl"
    if not path.exists():
        print("暂无历史数据")
        return
    print(f"\n📈 工具使用率历史趋势")
    print(f"{'='*55}")
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
                print(f"  {row['date']} {row['time']} | 技能:{row['skills']:3d} | 任务:{row['engine_tasks']:3d} | 交付物:{row['outputs']:3d} | 比值:{row['output_ratio']:.2f}")
            except:
                pass
    print(f"{'='*55}\n")

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'history':
        cmd_history()
    else:
        state = show_report()
        # 追加历史
        history_path = ROOT / "config" / "tool_usage_history.jsonl"
        with open(history_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(state, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    main()