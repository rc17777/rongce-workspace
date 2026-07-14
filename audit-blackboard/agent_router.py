#!/usr/bin/env python3
"""
融策 Agent 路由调度系统
管理 13 个虚拟员工的配置注册表 + 消息路由规则

用法:
    python agent_router.py list                          # 列出所有员工
    python agent_router.py route "@预算工程师 帮我审清单"  # 解析路由目标
    python agent_router.py info 预算工程师                 # 查看某个员工的配置
"""

import json, os, re, sys
from pathlib import Path

SPEC_DIR = Path(r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\agent_specs")
ROUTER_CONFIG = Path(r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\agent_registry.json")


def load_agents():
    """加载所有 Agent 配置"""
    agents = {}
    for f in sorted(SPEC_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            agents[data["name"]] = {
                "file": f.name,
                "name": data["name"],
                "desc": data.get("desc", ""),
                "prompt": data.get("prompt", ""),
                "tools": data.get("tools", []),
                "applicable_biz": data.get("applicable_biz", []),
                "shortcuts": [],  # will be populated
            }
    return agents


def build_shortcuts(name):
    """为 Agent 名称生成各种快捷称呼"""
    shortcuts = [name]
    # 去掉常见后缀
    for suffix in ["师", "员", "兵", "犬", "手", "匠", "人"]:
        if name.endswith(suffix):
            shortcuts.append(name[:-1])
    # 关键词提取
    keywords = {
        "数据侦察兵": ["数据", "侦察", "scout", "data"],
        "合同猎犬": ["合同", "猎犬", "hound", "contract"],
        "招投标猎手": ["招投标", "投标", "bid", "串标", "围标", "猎手"],
        "法规检查员": ["法规", "法律", "law", "合规", "检查"],
        "底稿工匠": ["底稿", "工匠", "craft", "workpaper"],
        "报告笔杆子": ["报告", "笔杆子", "report", "writer"],
        "复核哨兵": ["复核", "哨兵", "review", "sentinel", "检查"],
        "脱敏专员": ["脱敏", "desensitize", "隐私"],
        "评标偏离度检测": ["偏离", "偏倚", "bias", "expert", "评标偏差"],
        "预算工程师": ["预算", "estimator", "造价", "定额"],
        "结算审计师": ["结算", "settlement", "auditor", "竣工"],
        "财政评审员": ["财政", "fiscal", "财评", "概算", "评审"],
        "绩效评价师": ["绩效", "performance", "evaluator", "评价"],
    }
    if name in keywords:
        shortcuts.extend(keywords[name])
    return shortcuts


def route_message(message: str) -> dict:
    """解析消息，识别目标 Agent 和实际内容"""
    agents = load_agents()
    shortcut_map = {}
    for aname, info in agents.items():
        for sc in build_shortcuts(aname):
            shortcut_map[sc.lower()] = aname

    # 模式1: @Agent名称 消息内容
    m = re.match(r'@([^\s]+)\s+(.*)', message, re.DOTALL)
    if m:
        target = m.group(1).lower()
        content = m.group(2).strip()
        if target in shortcut_map:
            return {
                "matched": True,
                "agent": shortcut_map[target],
                "alias_used": m.group(1),
                "message": content,
                "method": "at_mention"
            }

    # 模式2: 关键词匹配（无@前缀时）
    words = set(message.lower().split())
    scores = {}
    for shortcut, aname in shortcut_map.items():
        score = 0
        if shortcut in words:
            score += 10  # 完整匹配
        elif shortcut in message.lower():
            score += 5   # 部分匹配
        if score > 0:
            scores[aname] = scores.get(aname, 0) + score

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] >= 10:
            return {
                "matched": True,
                "agent": best,
                "alias_used": best,
                "message": message,
                "method": "keyword_match",
                "score": scores[best]
            }

    return {
        "matched": False,
        "message": message,
        "available": list(agents.keys())
    }


def format_agent_list():
    """格式化 Agent 列表"""
    agents = load_agents()
    lines = ["融策 13 虚拟员工花名册", "=" * 50, ""]
    for i, (name, info) in enumerate(agents.items(), 1):
        shortcuts = build_shortcuts(name)
        sc_display = ", ".join(shortcuts[:4])
        lines.append(f"{i:2d}. {name}")
        lines.append(f"    快捷称呼: {sc_display}")
        lines.append(f"    职责: {info['desc'][:80]}")
        lines.append(f"    业务线: {', '.join(info['applicable_biz'][:3])}")
        lines.append("")
    return "\n".join(lines)


def format_agent_info(name: str):
    """格式化单个 Agent 详细信息"""
    agents = load_agents()
    for aname, info in agents.items():
        if name in aname or name in build_shortcuts(aname):
            shortcuts = build_shortcuts(aname)
            lines = [
                f"员工档案: {aname}",
                "=" * 50,
                f"文件: {info['file']}",
                f"快捷称呼: {', '.join(shortcuts)}",
                f"职责: {info['desc']}",
                f"业务线: {', '.join(info['applicable_biz'])}",
                f"工具: {', '.join(info['tools']) if info['tools'] else '无限制'}",
                "",
                "--- 系统提示词（前500字） ---",
                info['prompt'][:500] + ("..." if len(info['prompt']) > 500 else "")
            ]
            return "\n".join(lines)
    return f"未找到员工: {name}"


def generate_registry():
    """生成 Agent 注册表 JSON"""
    agents = load_agents()
    registry = {}
    for name, info in agents.items():
        registry[name] = {
            "file": info["file"],
            "shortcuts": build_shortcuts(name),
            "desc": info["desc"],
            "applicable_biz": info["applicable_biz"],
        }
    with open(ROUTER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"注册表已生成: {ROUTER_CONFIG}")
    print(f"共 {len(registry)} 个员工")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python agent_router.py list            # 列出所有员工")
        print("  python agent_router.py info <名称>     # 查看某个员工")
        print("  python agent_router.py route <消息>    # 解析路由")
        print("  python agent_router.py registry       # 生成注册表")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list":
        print(format_agent_list())
    elif cmd == "info":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        print(format_agent_info(name))
    elif cmd == "route":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        result = route_message(msg)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "registry":
        generate_registry()
    else:
        print(f"未知命令: {cmd}")
