#!/usr/bin/env python3
"""
Agent 远程修复工具 — 手机发指令即可修复异常
用法：
  python repair.py --agent settlement_auditor --fix reset     # 重置为空闲
  python repair.py --agent data_scout --fix retry             # 重试
  python repair.py --fix all                                  # 一键修复全部异常
  python repair.py --fix restart                              # 重启面板服务
  python repair.py --status                                   # 查看异常列表
"""
import urllib.request, json, sys, os, time, subprocess

sys.stdout.reconfigure(encoding='utf-8')

API = "http://127.0.0.1:8765"

FIX_ACTIONS = {
    "reset": {
        "desc": "重置为空闲状态，清除错误",
        "status": "idle",
        "extra": {}
    },
    "retry": {
        "desc": "重试上一个失败任务",
        "status": "working",
        "extra": {"task": "🔄 自动重试中..."}
    },
    "pause": {
        "desc": "暂停Agent，避免持续报错",
        "status": "offline",
        "extra": {}
    },
    "skip": {
        "desc": "标记完成，跳过此任务",
        "status": "completed",
        "extra": {}
    },
}

def api_get(path):
    r = urllib.request.urlopen(f"{API}{path}", timeout=5)
    return json.loads(r.read())

def api_post(path, data):
    req = urllib.request.Request(f"{API}{path}",
        data=json.dumps(data).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST")
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())

def list_issues():
    """列出所有异常Agent"""
    state = api_get("/api/state")
    issues = []
    for aid, info in state["agents"].items():
        if info["status"] in ("error", "stuck"):
            meta = state["agentMeta"].get(aid, {})
            issues.append({
                "agent": aid,
                "name": meta.get("name", aid),
                "model": meta.get("model", ""),
                "status": info["status"],
                "error": info.get("lastError", ""),
                "currentTask": info.get("currentTask", ""),
                "lastTask": info.get("lastTask", ""),
            })
    return issues, state

def fix_agent(agent_id, action):
    """修复单个Agent"""
    if action not in FIX_ACTIONS:
        return False, f"未知修复动作: {action}，可选: {list(FIX_ACTIONS.keys())}"

    fix = FIX_ACTIONS[action]

    # 如果操作是 reset/offline/completed，直接设状态
    if action in ("reset", "pause", "skip"):
        data = {"status": fix["status"]}
        if action == "reset":
            data["error"] = ""  # 清除错误信息
        try:
            result = api_post(f"/api/agent/{agent_id}/status", data)
            return True, f"{fix['desc']}"
        except Exception as e:
            return False, str(e)

    # retry: 设为 working + 附带任务信息
    elif action == "retry":
        state = api_get("/api/state")
        info = state["agents"].get(agent_id, {})
        last_task = info.get("lastTask", "") or info.get("currentTask", "") or "自动重试"
        data = {"status": "working", "task": f"🔄 {last_task}"}
        try:
            api_post(f"/api/agent/{agent_id}/status", data)
            return True, f"重试任务: {last_task}"
        except Exception as e:
            return False, str(e)

    return False, "未知错误"

def fix_all():
    """一键修复全部异常Agent"""
    issues, state = list_issues()
    if not issues:
        return "✅ 无异常Agent，无需修复"

    results = []
    for issue in issues:
        action = "reset"
        # 如果是 stuck，重置；如果是 error，也重置（让下次任务自动重试）
        ok, msg = fix_agent(issue["agent"], action)
        emoji = "✅" if ok else "❌"
        results.append(f"{emoji} {issue['name']}: {msg}")

    return "\n".join(results)

def restart_dashboard():
    """重启面板服务"""
    # 杀掉旧进程再启动（通过脚本）
    script = os.path.join(os.path.dirname(__file__), "server.py")
    try:
        subprocess.run(["taskkill", "/F", "/FI", "IMAGENAME eq python.exe", "/FI", "WINDOWTITLE eq *server.py*"], 
                      capture_output=True, timeout=5)
    except:
        pass
    # 后台重启
    subprocess.Popen([sys.executable, script], 
                     creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0)
    time.sleep(2)
    # 验证
    try:
        api_get("/api/state")
        return "✅ 面板已重启成功"
    except:
        return "⚠ 面板重启中，请稍后刷新"

def get_status_report():
    """生成状态报告"""
    issues, state = list_issues()
    summary = {"working": 0, "idle": 0, "stuck": 0, "error": 0, "completed": 0}
    for aid, info in state["agents"].items():
        summary[info["status"]] = summary.get(info["status"], 0) + 1

    lines = []
    lines.append(f"📡 融策Agent状态")
    lines.append(f"运行{summary['working']} | 空闲{summary['idle']} | 异常{summary['error']} | 卡住{summary['stuck']}")

    if issues:
        lines.append(f"\n⚠ {len(issues)}个异常:")
        for i, issue in enumerate(issues):
            sid = chr(ord('a') + i)
            lines.append(f"  {sid}) [{issue['status']}] {issue['name']}")
            if issue.get("error"):
                lines.append(f"     {issue['error'][:60]}")
        lines.append(f"\n修复: 修复全部 | 修复{sid} | 重试{sid}")
    else:
        lines.append("✅ 全部正常")

    return "\n".join(lines)


def parse_command(cmd_text):
    """
    解析自然语言修复指令
    支持:
      "修复全部" / "fix all"
      "修复 数据侦察兵" / "fix data_scout"
      "重试 结算审计师"
      "重置 XXX"
      "暂停 XXX"
      "状态" / "status"
      "重启面板"
    """
    cmd = cmd_text.strip().lower()

    # 状态查询
    if cmd in ("状态", "status", "报告", "report"):
        return ("status", None, None)

    # 一键修复
    if cmd in ("修复全部", "修复所有", "fix all", "修复", "fix"):
        return ("fix_all", None, None)

    # 重启
    if cmd in ("重启面板", "重启", "restart"):
        return ("restart", None, None)

    # 带目标的修复
    import re
    patterns = [
        (r"(?:修复|fix|重置|reset)\s+(.+)", "reset"),
        (r"(?:重试|retry)\s+(.+)", "retry"),
        (r"(?:暂停|pause|stop)\s+(.+)", "pause"),
        (r"(?:跳过|skip)\s+(.+)", "skip"),
    ]

    for pattern, action in patterns:
        m = re.match(pattern, cmd)
        if m:
            target = m.group(1).strip()
            # 尝试匹配 agent ID 或中文名
            state = api_get("/api/state")
            agent_id = None
            for aid, info in state["agents"].items():
                meta = state["agentMeta"].get(aid, {})
                if target in aid.lower() or target in meta.get("name", ""):
                    agent_id = aid
                    break
            if agent_id:
                return ("fix_one", agent_id, action)
            else:
                return ("error", None, f"未找到Agent: {target}")

    return ("error", None, f"无法解析指令: {cmd_text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 无参数默认显示状态
        print(get_status_report())
        sys.exit(0)

    # 文本指令模式
    cmd_text = " ".join(sys.argv[1:])
    op, target, action = parse_command(cmd_text)

    if op == "status":
        print(get_status_report())
    elif op == "fix_all":
        print("🔧 一键修复全部异常...\n")
        print(fix_all())
        print(f"\n{get_status_report()}")
    elif op == "restart":
        print(restart_dashboard())
    elif op == "fix_one":
        print(f"🔧 {action}: {target}...")
        ok, msg = fix_agent(target, action)
        print(f"{'✅' if ok else '❌'} {msg}")
    elif op == "error":
        print(f"❌ {action}")
        print("\n可用指令:")
        print("  状态 / 修复全部 / 修复 <Agent名>")
        print("  重试 <Agent名> / 暂停 <Agent名> / 跳过 <Agent名>")
        print("  重启面板")
    else:
        print(get_status_report())
