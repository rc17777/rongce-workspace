#!/usr/bin/env python3
"""
Agent 状态上报 & 监控工具 v2.0
用法：
  # 心跳检查（返回JSON，供脚本消费）
  python report.py --heartbeat

  # 心跳检查（人类可读输出）
  python report.py --heartbeat --format text

  # 每日统计报告
  python report.py --daily
"""
import urllib.request, json, argparse, sys, os
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')

API = "http://127.0.0.1:8765"
LOG_FILE = os.path.join(os.path.dirname(__file__), "agent_activity.log")

FLASH_AGENTS = ["ocr_processor", "data_classifier", "data_desensitizer"]
PRO_AGENTS = ["data_scout", "bid_hunter", "budget_estimator", "settlement_auditor",
              "performance_evaluator", "expert_bias_detector", "adjustment_scribe"]
QWEN_AGENTS = ["workpaper_crafter", "report_writer", "meeting_minutes_analyzer", "plan_writer"]
SONNET_AGENTS = ["contract_hound", "law_inspector", "review_sentinel", "fiscal_reviewer"]

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

def report_status(agent, status, task="", elapsed=0, error=""):
    data = {"status": status}
    if task: data["task"] = task
    if elapsed: data["elapsedMs"] = elapsed
    if error: data["error"] = error
    return api_post(f"/api/agent/{agent}/status", data)

def heartbeat_check():
    """检查所有agent，返回 (ok, issues, summary)"""
    state = api_get("/api/state")
    issues = []
    summary = {"total": 0, "working": 0, "idle": 0, "stuck": 0, "error": 0, "completed": 0}

    for aid, info in state["agents"].items():
        meta = state["agentMeta"].get(aid, {})
        summary[info["status"]] = summary.get(info["status"], 0) + 1
        summary["total"] += 1

        if info["status"] in ("error", "stuck"):
            issues.append({
                "agent": aid,
                "name": meta.get("name", aid),
                "model": meta.get("model", ""),
                "status": info["status"],
                "error": info.get("lastError", ""),
                "taskCount": info.get("taskCount", 0),
                "failCount": info.get("failCount", 0),
            })

    return len(issues) == 0, issues, summary

def daily_report():
    """生成昨日统计报告"""
    state = api_get("/api/state")
    stats = state["stats"]
    agents = state["agents"]
    agent_meta = state["agentMeta"]

    # 计算各Agent成功率
    agent_stats = []
    for aid, info in agents.items():
        if info["taskCount"] > 0:
            meta = agent_meta.get(aid, {})
            rate = round(info["successCount"] / info["taskCount"] * 100)
            agent_stats.append({
                "name": meta.get("name", aid),
                "tasks": info["taskCount"],
                "success": info["successCount"],
                "fail": info["failCount"],
                "stuck": info["stuckCount"],
                "rate": rate,
                "avgTime": round(info["totalTimeMs"] / max(info["taskCount"], 1)),
            })

    agent_stats.sort(key=lambda x: x["tasks"], reverse=True)
    top_errors = [a for a in agent_stats if a["fail"] > 0]
    top_stuck = [a for a in agent_stats if a["stuck"] > 0]

    report = []
    report.append("📊 融策Agent 每日报告")
    report.append(f"总任务: {stats['totalTasks']} | 成功: {stats['totalSuccess']} | 失败: {stats['totalFail']}")
    rate = round(stats["totalSuccess"] / max(stats["totalTasks"], 1) * 100)
    report.append(f"成功率: {rate}%")

    if agent_stats:
        report.append(f"\n🏆 最忙Agent: {agent_stats[0]['name']} ({agent_stats[0]['tasks']}任务)")

    if top_errors:
        report.append(f"\n⚠ 异常Agent ({len(top_errors)}个):")
        for a in top_errors[:3]:
            report.append(f"  • {a['name']}: {a['fail']}次失败 / 成功率{a['rate']}%")

    if top_stuck:
        report.append(f"\n🟡 卡住Agent ({len(top_stuck)}个):")
        for a in top_stuck[:3]:
            report.append(f"  • {a['name']}: {a['stuck']}次卡住")

    report.append(f"\n🔗 面板: http://127.0.0.1:8765")

    return "\n".join(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="融策 Agent 监控")
    sub = parser.add_subparsers(dest="cmd")

    # heartbeat
    hb = sub.add_parser("heartbeat", help="心跳检查")
    hb.add_argument("--format", choices=["json", "text"], default="json")

    # daily
    sub.add_parser("daily", help="每日统计")

    # report (单个状态上报)
    rp = sub.add_parser("report", help="状态上报")
    rp.add_argument("--agent", required=True)
    rp.add_argument("--status", required=True)
    rp.add_argument("--task", default="")
    rp.add_argument("--elapsed", type=int, default=0)
    rp.add_argument("--error", default="")

    # 兼容旧参数
    parser.add_argument("--agent")
    parser.add_argument("--status")
    parser.add_argument("--task", default="")
    parser.add_argument("--elapsed", type=int, default=0)
    parser.add_argument("--error", default="")
    parser.add_argument("--heartbeat", action="store_true")
    parser.add_argument("--daily", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="json")

    args = parser.parse_args()

    if args.heartbeat or (hasattr(args, 'cmd') and args.cmd == "heartbeat"):
        ok, issues, summary = heartbeat_check()

        if args.format == "text":
            print(f"📡 Agent监控: 总{summary['total']} | 运行{summary.get('working',0)} "
                  f"| 空闲{summary.get('idle',0)} | 异常{summary.get('error',0)} "
                  f"| 卡住{summary.get('stuck',0)}")
            if issues:
                print(f"\n⚠ {len(issues)}个异常:")
                for i in issues:
                    print(f"  [{i['status']}] {i['name']} — {i.get('error', '无详情')}")
                print(f"\n🔗 http://127.0.0.1:8765")
            else:
                print("✅ 全部正常")
        else:
            print(json.dumps({"ok": ok, "issues": issues, "summary": summary}, ensure_ascii=False))

    elif args.daily or (hasattr(args, 'cmd') and args.cmd == "daily"):
        print(daily_report())

    elif args.agent and args.status:
        result = report_status(args.agent, args.status, args.task, args.elapsed, args.error)
        print(json.dumps(result, ensure_ascii=False))

    else:
        parser.print_help()
