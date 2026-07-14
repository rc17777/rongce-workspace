#!/usr/bin/env python3
"""
融策自动触发守护进程
监控 raw_data/ 目录 → 有新文件 → 自动启动对应 Agent 流程

用法:
    python auto_trigger.py                        # 前台运行，扫描一次
    python auto_trigger.py --watch                 # 持续监控模式
    python auto_trigger.py --project "XX项目"      # 指定项目名
    python auto_trigger.py --status               # 查看当前状态
"""

import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# 工作区根目录
WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
PROJECTS_DIR = WORKSPACE / "audit-blackboard" / "projects"
STATE_FILE = WORKSPACE / "audit-blackboard" / "trigger_state.json"

# 文件类型 → 触发的工作流配置
WORKFLOW_TRIGGERS = {
    # 审计类触发
    "招投标": {
        "patterns": ["投标文件", "开标一览表", "招标文件"],
        "agents": ["data_scout", "bid_hunter", "contract_hound"],
        "description": "招投标审计（串标围标检测）"
    },
    "合同": {
        "patterns": ["合同台账", "合同", "付款记录", "验收单"],
        "agents": ["contract_hound", "law_inspector"],
        "description": "合同审计"
    },
    "财务": {
        "patterns": ["序时账", "科目余额表", "报表", "银行流水", "凭证"],
        "agents": ["data_scout", "data_desensitizer"],
        "description": "财务数据审计"
    },
    
    # 绩效评价类触发
    "绩效": {
        "patterns": ["绩效目标申报", "自评报告", "事中监控", "满意度调查", "项目方案"],
        "agents": ["performance_evaluator", "data_scout"],
        "description": "绩效评价（目标审核+事中监控+事后评价）"
    },
    
    # 工程咨询类触发
    "预算": {
        "patterns": ["工程量清单", "预算书", "取费表", "控制价"],
        "agents": ["budget_estimator", "fiscal_reviewer"],
        "description": "工程预算审核"
    },
    "结算": {
        "patterns": ["结算书", "施工合同", "变更签证", "竣工图"],
        "agents": ["settlement_auditor", "fiscal_reviewer"],
        "description": "工程结算审计"
    },
    "财政评审": {
        "patterns": ["概算批复", "送审文件", "立项批复", "初设概算"],
        "agents": ["fiscal_reviewer", "budget_estimator"],
        "description": "财政投资评审"
    },
}


def scan_directory(path: Path) -> dict:
    """扫描目录，返回文件清单和指纹"""
    files = {}
    if not path.exists():
        return files
    
    for f in path.rglob("*"):
        if f.is_file():
            relative = str(f.relative_to(path))
            mtime = f.stat().st_mtime
            size = f.stat().st_size
            # 快速指纹：路径+大小+修改时间
            fingerprint = f"{relative}:{size}:{mtime}"
            files[relative] = {
                "path": str(f),
                "size": size,
                "mtime": mtime,
                "fingerprint": fingerprint
            }
    return files


def match_workflow(files: dict) -> list:
    """根据文件名匹配触发的工作流"""
    triggered = []
    file_list = list(files.keys())
    
    for workflow_name, config in WORKFLOW_TRIGGERS.items():
        matched_files = []
        for pattern in config["patterns"]:
            for fname in file_list:
                if pattern in fname or pattern in str(Path(fname).parent):
                    if fname not in matched_files:
                        matched_files.append(fname)
        
        if matched_files:
            triggered.append({
                "workflow": workflow_name,
                "description": config["description"],
                "agents": config["agents"],
                "matched_files": matched_files,
                "file_count": len(matched_files)
            })
    
    return triggered


def load_state() -> dict:
    """加载触发状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_scan": {}, "triggered_workflows": [], "completed_tasks": []}


def save_state(state: dict):
    """保存触发状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def find_new_files(current: dict, previous: dict) -> list:
    """对比两次扫描，找出新增/修改的文件"""
    new_files = []
    for fname, info in current.items():
        if fname not in previous:
            new_files.append({"file": fname, "status": "NEW", **info})
        elif info["fingerprint"] != previous[fname].get("fingerprint", ""):
            new_files.append({"file": fname, "status": "MODIFIED", **info})
    return new_files


def generate_trigger_message(project: str, workflows: list, new_files: list) -> str:
    """生成触发消息（发给 OpenClaw）"""
    lines = [f"🚨 自动触发：项目「{project}」有新数据"]
    lines.append("")
    
    if new_files:
        lines.append(f"**新增/修改文件** ({len(new_files)}个)：")
        for nf in new_files[:10]:
            size_kb = nf["size"] / 1024
            lines.append(f"- `{nf['file']}` ({size_kb:.1f}KB) [{nf['status']}]")
        if len(new_files) > 10:
            lines.append(f"- ... 及其他 {len(new_files) - 10} 个文件")
    
    lines.append("")
    lines.append("**匹配到的工作流**：")
    for wf in workflows:
        lines.append(f"- {wf['workflow']}: {wf['description']} (需启动: {', '.join(wf['agents'])})")
    
    lines.append("")
    lines.append("**建议操作**：")
    lines.append(f"对我说「开始审计{project}」或「开始{workflows[0]['workflow'] if workflows else '审计'}{project}」自动启动对应 Agent")
    
    return "\n".join(lines)


def scan_and_trigger(project: str = None, watch: bool = False):
    """主逻辑：扫描→匹配→触发"""
    state = load_state()
    
    if not project:
        # 自动发现项目：找 raw_data 有内容的项目
        for proj_dir in sorted(PROJECTS_DIR.glob("*"), reverse=True):
            if proj_dir.name.startswith("_"):
                continue
            raw_data = proj_dir / "raw_data"
            if raw_data.exists() and any(raw_data.iterdir()):
                project = proj_dir.name
                break
    
    if not project:
        print("[!] 未找到活跃项目，请在 projects/ 下创建项目并放入 raw_data/")
        return
    
    project_dir = PROJECTS_DIR / project
    raw_data_dir = project_dir / "raw_data"
    
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 扫描项目: {project}")
    print(f"  数据目录: {raw_data_dir}")
    
    # 扫描当前文件
    current_files = scan_directory(raw_data_dir)
    print(f"  文件数: {len(current_files)}")
    
    # 对比上次扫描
    previous_files = state.get("last_scan", {}).get(project, {})
    new_files = find_new_files(current_files, previous_files)
    
    # 匹配工作流
    all_files = current_files
    if new_files:
        # 只对新文件匹配
        new_file_dict = {nf["file"]: {"size": nf["size"], "mtime": nf["mtime"], 
                                       "fingerprint": f"{nf['file']}:{nf['size']}:{nf['mtime']}"} 
                        for nf in new_files}
        workflows = match_workflow(new_file_dict)
    else:
        workflows = match_workflow(all_files)
    
    # 只对有新变化的触发
    if new_files and workflows:
        message = generate_trigger_message(project, workflows, new_files)
        print("\n" + "=" * 60)
        print(message)
        print("=" * 60)
        
        # 记录触发
        state["triggered_workflows"].append({
            "project": project,
            "time": datetime.now().isoformat(),
            "workflows": [w["workflow"] for w in workflows],
            "new_files": [n["file"] for n in new_files]
        })
    else:
        print(f"  新文件: {len(new_files)}, 匹配工作流: {len(workflows)}")
        if not new_files:
            print("  → 无新文件，跳过")
        elif not workflows:
            print("  → 新文件不匹配任何工作流，请手动检查")
    
    # 更新状态
    state["last_scan"][project] = {
        fname: {"fingerprint": info["fingerprint"]} 
        for fname, info in current_files.items()
    }
    save_state(state)
    
    # 持续监控模式
    if watch:
        print(f"\n[持续监控] 每60秒扫描一次，Ctrl+C 停止...")
        try:
            while True:
                time.sleep(60)
                scan_and_trigger(project=project, watch=True)
                return  # 递归后退出
        except KeyboardInterrupt:
            print("\n[停止监控]")


def show_status():
    """显示当前触发状态"""
    if not STATE_FILE.exists():
        print("无触发记录")
        return
    
    state = load_state()
    
    print("=" * 60)
    print("融策自动触发器 状态")
    print("=" * 60)
    
    # 各项目文件数
    print("\n📂 监控中的项目：")
    for proj, files in state.get("last_scan", {}).items():
        raw_data = PROJECTS_DIR / proj / "raw_data"
        actual_count = len(list(raw_data.rglob("*"))) if raw_data.exists() else 0
        print(f"  {proj}: {len(files)} 文件(上次) / {actual_count} 文件(当前)")
    
    # 触发历史
    print("\n📋 触发历史（最近10次）：")
    for t in state.get("triggered_workflows", [])[-10:]:
        print(f"  {t['time'][:19]} | {t['project']} | {', '.join(t['workflows'])}")
    
    print(f"\n💡 运行 'python auto_trigger.py' 立即扫描")
    print(f"💡 运行 'python auto_trigger.py --watch' 持续监控")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="融策自动触发守护进程")
    parser.add_argument("--project", "-p", help="项目名称")
    parser.add_argument("--watch", "-w", action="store_true", help="持续监控模式")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    args = parser.parse_args()
    
    if args.status:
        show_status()
    else:
        scan_and_trigger(project=args.project, watch=args.watch)
