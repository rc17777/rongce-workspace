#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
融策智审平台 — 统一操作入口
=============================
融策会计师事务所智能审计平台 All-in-One 入口。
支持审计分析、模型运行、知识库查询、报告生成等全部功能。

使用方式：
  py run.py              # 启动交互菜单
  py run.py 2            # 直接运行菜单第2项
  py run.py status       # 快捷命令
"""

import sys
import os
import subprocess
import json
import textwrap
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
SKILLS_DIR = Path.home() / ".openclaw" / "workspace" / "skills"


# ===== 菜单定义 =====

MENU = {
    "1": {
        "title": "📊 数据基座管理",
        "items": [
            ("1.1", "初始化数据基座", 'py skills/rongce-platform/index.py init'),
            ("1.2", "查看数据基座状态", 'py skills/rongce-platform/index.py status'),
            ("1.3", "注册新数据源", None),
            ("1.4", "查看风控规则库", 'py skills/rongce-platform/index.py status'),
        ]
    },
    "2": {
        "title": "🔍 审计分析模型",
        "items": [
            ("2.1", "费用舞弊风险评分", 'py skills/rongce-platform/index.py run "费用舞弊"'),
            ("2.2", "预算执行分析", 'py skills/rongce-platform/index.py run "预算执行"'),
            ("2.3", "资金异常流动检测", 'py skills/rongce-platform/index.py run "资金异常"'),
            ("2.4", "审计风险排序", 'py skills/rongce-platform/index.py run "风险排序"'),
            ("2.5", "🔄 运行全部模型", 'py skills/rongce-platform/index.py run 全部'),
        ]
    },
    "3": {
        "title": "🛡️ 专项审计工具",
        "items": [
            ("3.1", "串标围标审计", 'py audit/bid_collusion.py'),
            ("3.2", "Benford定律异常检测", 'py audit/benford_analysis.py'),
            ("3.3", "三法交叉异常检测", 'py audit/anomaly_detection.py'),
            ("3.4", "合同合规分析", 'py audit/contract_analyzer.py'),
            ("3.5", "数据质量审计", 'py audit/data_quality_audit.py'),
            ("3.6", "两重建设项目审计清单", None),
            ("3.7", "两新补贴审计清单", None),
        ]
    },
    "4": {
        "title": "📚 审计知识库",
        "items": [
            ("4.1", "查询风控规则", None),
            ("4.2", "查询审计法规", None),
            ("4.3", "查询审计案例", None),
            ("4.4", "审计盲区速查", None),
            ("4.5", "AI+审计场景速查", None),
        ]
    },
    "5": {
        "title": "📝 报告与文档",
        "items": [
            ("5.1", "生成审计报告初稿", None),
            ("5.2", "生成审计底稿模板", None),
            ("5.3", "投标技术方案生成", None),
            ("5.4", "审计问题定性查法规", None),
        ]
    },
    "0": {
        "title": "🚪 退出",
        "items": []
    }
}


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    print("=" * 58)
    print("       融 策 智 审 平 台  v1.0")
    print("        RongCe Intelligent Audit Platform")
    print(f"        {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 58)


def print_main_menu():
    """打印主菜单"""
    print_header()
    print()
    for key, group in MENU.items():
        if key == "0":
            continue
        print(f"  [{key}] {group['title']}")
    print()
    print(f"  [0] 退出")
    print()
    print("-" * 58)


def print_sub_menu(group_key):
    """打印子菜单"""
    group = MENU[group_key]
    clear_screen()
    print_header()
    print(f"  → {group['title']}")
    print("-" * 58)
    print()
    for item_id, title, _ in group["items"]:
        print(f"  [{item_id}] {title}")
    print()
    print(f"  [0] 返回主菜单")
    print("-" * 58)


def run_command(cmd):
    """执行命令并显示输出"""
    if cmd is None:
        print("\n  📌 该功能需通过对话指令调用")
        print("  💬 直接对我说就行：")
        print("     比如：「帮我查XX项目的预算执行异常」")
        print("     比如：「做一下串标围标分析」")
        return

    clear_screen()
    print(f"  ▶️  执行: {cmd}")
    print("=" * 58)
    # 确保用UTF-8模式运行Python脚本
    if cmd.startswith('py '):
        cmd = cmd.replace('py ', 'py -X utf8 ', 1)
    subprocess.run(cmd, shell=True, cwd=str(BASE.parent))
    print()
    print("=" * 58)
    input("  按回车返回...")


def handle_sub_menu(group_key):
    """处理子菜单交互"""
    while True:
        print_sub_menu(group_key)
        choice = input("  请选择功能 [1.x / 0]: ").strip()

        if choice == "0":
            break

        # 匹配子菜单项
        matched = None
        for item_id, title, cmd in MENU[group_key]["items"]:
            if choice == item_id:
                matched = cmd
                break
            # 也支持输入序号
            if choice == item_id.split(".")[1]:
                matched = cmd
                break

        if matched is not None:
            run_command(matched)
        else:
            print("  ❌ 无效选择")


def handle_quick_cmd(args):
    """处理快捷命令参数"""
    quick_map = {
        "init": "1.1",
        "status": "1.2",
        "fraud": "2.1",
        "budget": "2.2",
        "fund": "2.3",
        "risk": "2.4",
        "all": "2.5",
        "benford": "3.2",
        "collusion": "3.1",
        "anomaly": "3.3",
        "contract": "3.4",
        "quality": "3.5",
    }

    # 直接数字 = 子菜单ID
    if args[0].replace(".", "").isdigit():
        parts = args[0].split(".")
        main_key = parts[0]
        sub_key = parts[1] if len(parts) > 1 else None
        if main_key in MENU and sub_key:
            for item_id, _, cmd in MENU[main_key]["items"]:
                if item_id == args[0]:
                    run_command(cmd)
                    return
        elif main_key in MENU and main_key != "0":
            handle_sub_menu(main_key)
            return

    # 快捷命令
    if args[0] in quick_map:
        target = quick_map[args[0]]
        for item_id, _, cmd in MENU[target.split(".")[0]]["items"]:
            if item_id == target:
                try:
                    run_command(cmd)
                except (EOFError, KeyboardInterrupt):
                    pass
                return

    print(f"  未知命令: {args[0]}")
    print(f"  可用快捷命令: {', '.join(quick_map.keys())}")


def main():
    # 命令行快捷模式
    if len(sys.argv) > 1:
        try:
            handle_quick_cmd(sys.argv[1:])
        except (EOFError, KeyboardInterrupt):
            pass
        return

    # 交互菜单模式
    while True:
        clear_screen()
        print_main_menu()
        choice = input("  请选择功能 [1-5 / 0]: ").strip()

        if choice == "0":
            clear_screen()
            print_header()
            print("\n  🫡 融策智审平台已退出，随时找我继续")
            print("=" * 58)
            break

        if choice in MENU and choice != "0":
            handle_sub_menu(choice)
        else:
            print("  ❌ 无效选择，请选 1-5 或 0")


if __name__ == "__main__":
    main()
