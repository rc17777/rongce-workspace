#!/usr/bin/env python3
"""
融策 Agent 状态监控面板 v1.0
============================
- 18 Agent 实时状态监控
- 模型层级/区域/成本可视化
- Webhook 告警推送
- 统计面板 & 告警日志
- 纯 stdlib，零依赖
"""

import json, time, threading, os, sys, signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ─── 配置 ───────────────────────────────────────────
PORT = 8765
DASHBOARD_DIR = Path(__file__).parent
STATE_FILE = DASHBOARD_DIR / "agent_state.json"
LOG_FILE = DASHBOARD_DIR / "agent_activity.log"
LOCK = threading.Lock()

# ─── Agent 定义（与 model_routing_v7.py 同步） ──────
AGENTS = [
    {"id": "data_scout",           "name": "数据侦察兵",   "cat": "核心审计", "icon": "🔍",
     "model": "deepseek-v4-pro",   "tier": "T1", "region": "国产", "cost": "免费",
     "desc": "数值分析/统计检测/Benford"},
    {"id": "contract_hound",       "name": "合同猎犬",     "cat": "核心审计", "icon": "🦮",
     "model": "claude-sonnet-5",   "tier": "T1", "region": "海外", "cost": "高",
     "desc": "合同条文/法规审查"},
    {"id": "bid_hunter",           "name": "招投标猎手",   "cat": "核心审计", "icon": "🎯",
     "model": "deepseek-v4-pro",   "tier": "T1", "region": "国产", "cost": "免费",
     "desc": "围标串标/模式检测"},
    {"id": "law_inspector",        "name": "法规检察官",   "cat": "核心审计", "icon": "⚖️",
     "model": "claude-sonnet-5",   "tier": "T1", "region": "海外", "cost": "高",
     "desc": "法律法规解读/合规"},
    {"id": "workpaper_crafter",    "name": "底稿工匠",     "cat": "核心审计", "icon": "📋",
     "model": "qwen3.7-plus",      "tier": "T1", "region": "国产", "cost": "低",
     "desc": "审计底稿/公文撰写"},
    {"id": "report_writer",        "name": "报告笔杆子",   "cat": "核心审计", "icon": "✍️",
     "model": "qwen3.7-plus",      "tier": "T1", "region": "国产", "cost": "低",
     "desc": "审计报告撰写/格式"},
    {"id": "review_sentinel",      "name": "复核哨兵",     "cat": "核心审计", "icon": "🛡️",
     "model": "claude-sonnet-5",   "tier": "T0→T1", "region": "海外", "cost": "高→极高",
     "desc": "终审复核/可触发Opus"},
    {"id": "budget_estimator",     "name": "预算工程师",   "cat": "工程咨询", "icon": "📐",
     "model": "deepseek-v4-pro",   "tier": "T1", "region": "国产", "cost": "免费",
     "desc": "工程量计算/造价"},
    {"id": "settlement_auditor",   "name": "结算审计师",   "cat": "工程咨询", "icon": "💰",
     "model": "deepseek-v4-pro",   "tier": "T1", "region": "国产", "cost": "免费",
     "desc": "结算审计/计算+合规"},
    {"id": "fiscal_reviewer",      "name": "财政评审员",   "cat": "工程咨询", "icon": "🏛️",
     "model": "claude-sonnet-5",   "tier": "T1", "region": "海外", "cost": "高",
     "desc": "财政评审/政策合规"},
    {"id": "performance_evaluator","name": "绩效评价师",   "cat": "绩效评价", "icon": "📊",
     "model": "deepseek-v4-pro",   "tier": "T1", "region": "国产", "cost": "免费",
     "desc": "绩效评价/指标打分"},
    {"id": "expert_bias_detector", "name": "评标偏离度",   "cat": "专项检测", "icon": "📈",
     "model": "deepseek-v4-pro",   "tier": "T1", "region": "国产", "cost": "免费",
     "desc": "专家打分偏差检测"},
    {"id": "meeting_minutes_analyzer","name": "会议纪要分析","cat": "专项检测", "icon": "📝",
     "model": "qwen3.7-plus",      "tier": "T1", "region": "国产", "cost": "低",
     "desc": "中文会议纪要分析"},
    {"id": "ocr_processor",        "name": "OCR预处理",    "cat": "数据运维", "icon": "👁️",
     "model": "deepseek-v4-flash", "tier": "T4", "region": "国产", "cost": "免费",
     "desc": "OCR后文本清洗/轻量"},
    {"id": "data_classifier",      "name": "数据分类员",   "cat": "数据运维", "icon": "🏷️",
     "model": "deepseek-v4-flash", "tier": "T4", "region": "国产", "cost": "免费",
     "desc": "分类归档/轻量任务"},
    {"id": "data_desensitizer",    "name": "数据脱敏",     "cat": "数据运维", "icon": "🔒",
     "model": "deepseek-v4-flash", "tier": "T4", "region": "国产", "cost": "免费",
     "desc": "敏感数据脱敏处理"},
    {"id": "adjustment_scribe",    "name": "调整分录师",   "cat": "数据运维", "icon": "📒",
     "model": "deepseek-v4-pro",   "tier": "T1", "region": "国产", "cost": "免费",
     "desc": "审计调整分录/财务精确"},
    {"id": "plan_writer",          "name": "方案撰写师",   "cat": "方案撰写", "icon": "📄",
     "model": "qwen3.7-plus",      "tier": "T1", "region": "国产", "cost": "低",
     "desc": "实施方案/审计方案"},
]

# 状态常量
STATUS = {
    "idle":       {"label": "空闲",    "color": "#6b7280", "icon": "⏸"},
    "working":    {"label": "运行中",  "color": "#10b981", "icon": "🟢"},
    "stuck":      {"label": "卡住",    "color": "#f59e0b", "icon": "🟡"},
    "error":      {"label": "异常",    "color": "#ef4444", "icon": "🔴"},
    "completed":  {"label": "完成",    "color": "#3b82f6", "icon": "✅"},
    "offline":    {"label": "离线",    "color": "#374151", "icon": "⬛"},
}

# ─── 状态存储 ───────────────────────────────────────
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return init_state()

def init_state():
    agents_state = {}
    for a in AGENTS:
        agents_state[a["id"]] = {
            "status": "idle",
            "statusAt": None,
            "taskCount": 0,
            "successCount": 0,
            "failCount": 0,
            "stuckCount": 0,
            "totalTimeMs": 0,
            "lastTask": None,
            "lastError": None,
            "currentTask": None,
            "modelUsed": a["model"],
            "tier": a["tier"],
        }
    state = {
        "agents": agents_state,
        "alerts": [],
        "stats": {
            "totalTasks": 0,
            "totalSuccess": 0,
            "totalFail": 0,
            "uptime": time.time(),
            "lastAlertAt": None,
        },
        "webhookUrl": "",
    }
    save_state(state)
    return state

def save_state(state):
    with LOCK:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

def log_activity(event_type, agent_id, detail=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {event_type} | {agent_id} | {detail}\n"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line)

def add_alert(state, level, agent_id, message):
    alert = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,  # info, warn, error
        "agentId": agent_id,
        "agentName": next((a["name"] for a in AGENTS if a["id"] == agent_id), agent_id),
        "message": message,
    }
    state["alerts"].insert(0, alert)
    if len(state["alerts"]) > 100:
        state["alerts"] = state["alerts"][:100]
    state["stats"]["lastAlertAt"] = time.time()
    save_state(state)

    # Webhook 推送
    webhook_url = state.get("webhookUrl", "")
    if webhook_url:
        try:
            import urllib.request
            payload = json.dumps({
                "msgtype": "text",
                "text": {
                    "content": f"🚨 融策Agent告警 [{level.upper()}]\nAgent: {alert['agentName']}\n{message}\n时间: {alert['time']}"
                }
            }).encode('utf-8')
            req = urllib.request.Request(webhook_url, data=payload,
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except:
            pass


# ─── API 处理 ────────────────────────────────────────
class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 静默 HTTP 日志

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, code=200):
        body = html.encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # 前端页面
        if path == "" or path == "/":
            html_path = DASHBOARD_DIR / "index.html"
            if html_path.exists():
                self._send_html(html_path.read_text(encoding='utf-8'))
            else:
                self._send_json({"error": "index.html not found"}, 404)
            return

        # API: 全量状态
        if path == "/api/state":
            state = load_state()
            # 注入 Agent 元数据
            agent_meta = {a["id"]: {k: v for k, v in a.items() if k != "id"} for a in AGENTS}
            result = {
                "agents": state["agents"],
                "agentMeta": agent_meta,
                "alerts": state["alerts"][:20],
                "stats": state["stats"],
                "webhookUrl": state.get("webhookUrl", ""),
                "serverTime": time.time(),
            }
            self._send_json(result)
            return

        # API: 单个 Agent 状态
        if path.startswith("/api/agent/"):
            agent_id = path.split("/api/agent/")[-1]
            state = load_state()
            if agent_id in state["agents"]:
                self._send_json(state["agents"][agent_id])
            else:
                self._send_json({"error": f"Unknown agent: {agent_id}"}, 404)
            return

        # API: 告警列表
        if path == "/api/alerts":
            state = load_state()
            limit = int(params.get("limit", [50])[0])
            self._send_json(state["alerts"][:limit])
            return

        # API: 任务统计
        if path == "/api/stats":
            state = load_state()
            self._send_json(state["stats"])
            return

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # 读取 body
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len else b"{}"
        try:
            data = json.loads(body)
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        # API: 更新 Agent 状态
        if path.startswith("/api/agent/") and path.endswith("/status"):
            agent_id = path.split("/api/agent/")[1].split("/status")[0]
            state = load_state()

            if agent_id not in state["agents"]:
                self._send_json({"error": f"Unknown agent: {agent_id}"}, 404)
                return

            new_status = data.get("status", "idle")
            if new_status not in STATUS:
                self._send_json({"error": f"Invalid status: {new_status}"}, 400)
                return

            prev_status = state["agents"][agent_id]["status"]
            state["agents"][agent_id]["status"] = new_status
            state["agents"][agent_id]["statusAt"] = time.time()

            # 状态转换逻辑
            if new_status == "working":
                state["agents"][agent_id]["taskCount"] += 1
                state["agents"][agent_id]["currentTask"] = data.get("task", "")
                state["stats"]["totalTasks"] += 1
                log_activity("TASK_START", agent_id, data.get("task", ""))

            elif new_status == "completed":
                state["agents"][agent_id]["successCount"] += 1
                state["agents"][agent_id]["lastTask"] = state["agents"][agent_id].get("currentTask", "")
                state["agents"][agent_id]["currentTask"] = None
                state["stats"]["totalSuccess"] += 1
                elapsed = data.get("elapsedMs", 0)
                state["agents"][agent_id]["totalTimeMs"] += elapsed
                log_activity("TASK_DONE", agent_id, f"耗时{elapsed}ms")

            elif new_status == "error":
                state["agents"][agent_id]["failCount"] += 1
                state["agents"][agent_id]["lastError"] = data.get("error", "未知错误")
                state["agents"][agent_id]["lastTask"] = state["agents"][agent_id].get("currentTask", "")
                state["agents"][agent_id]["currentTask"] = None
                state["stats"]["totalFail"] += 1
                err_msg = data.get("error", "未知错误")
                add_alert(state, "error", agent_id, err_msg)
                log_activity("TASK_ERROR", agent_id, err_msg)

            elif new_status == "stuck":
                state["agents"][agent_id]["stuckCount"] += 1
                reason = data.get("reason", "超时无响应")
                add_alert(state, "warn", agent_id, reason)
                log_activity("TASK_STUCK", agent_id, reason)

            save_state(state)
            self._send_json({"ok": True, "agent": agent_id, "status": new_status})
            return

        # API: 设置 Webhook URL
        if path == "/api/webhook":
            state = load_state()
            state["webhookUrl"] = data.get("url", "")
            save_state(state)
            self._send_json({"ok": True, "webhookUrl": state["webhookUrl"]})
            return

        # API: 批量重置
        if path == "/api/reset":
            if STATE_FILE.exists():
                STATE_FILE.unlink()
            state = init_state()
            self._send_json({"ok": True, "message": "All agents reset to idle"})
            return

        # API: 模拟心跳上报 (外部 cron/脚本调用)
        if path == "/api/heartbeat":
            agent_id = data.get("agent", "")
            status = data.get("status", "working")
            task = data.get("task", "")
            state = load_state()

            if agent_id in state["agents"]:
                state["agents"][agent_id]["status"] = status
                state["agents"][agent_id]["statusAt"] = time.time()
                if task:
                    state["agents"][agent_id]["currentTask"] = task
                save_state(state)
                self._send_json({"ok": True})
            else:
                self._send_json({"error": f"Unknown agent: {agent_id}"}, 404)
            return

        self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ─── 后台监控：检测 stuck agents ─────────────────────
STUCK_TIMEOUT_MS = 5 * 60 * 1000  # 5分钟无更新视为卡住

def stuck_monitor_loop():
    """每秒检查：working 超过5分钟的标记为 stuck"""
    while True:
        try:
            state = load_state()
            now = time.time()
            changed = False
            for agent_id, info in state["agents"].items():
                if info["status"] == "working" and info.get("statusAt"):
                    elapsed = (now - info["statusAt"]) * 1000
                    if elapsed > STUCK_TIMEOUT_MS:
                        info["status"] = "stuck"
                        info["stuckCount"] += 1
                        info["statusAt"] = now
                        changed = True
                        seconds = int(elapsed / 1000)
                        add_alert(state, "warn", agent_id, f"超时{seconds}秒无响应，自动标记卡住")
                        log_activity("AUTO_STUCK", agent_id, f"timeout {seconds}s")
            if changed:
                save_state(state)
        except:
            pass
        time.sleep(10)


# ─── 启动 ────────────────────────────────────────────
def main():
    # 确保初始状态文件存在
    load_state()

    # 启动卡住检测线程
    monitor_thread = threading.Thread(target=stuck_monitor_loop, daemon=True)
    monitor_thread.start()

    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"""
╔══════════════════════════════════════╗
║   融策 Agent 状态监控面板 v1.0       ║
║   启动成功！                         ║
║   http://127.0.0.1:{PORT}              ║
║   API: http://127.0.0.1:{PORT}/api/state ║
║   Ctrl+C 停止                        ║
╚══════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 监控面板已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
