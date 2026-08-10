#!/usr/bin/env python3
"""
微信/企微告警推送脚本
支持：
  1. 企微群机器人 Webhook（推荐）
  2. 钉钉群机器人 Webhook
  3. 飞书群机器人 Webhook
  
配置：
  在 dashboard 面板顶部输入 Webhook URL 即可自动保存
  或手动设置环境变量:
    set RONGCE_ALERT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

获取企微 Webhook:
  企微群 → 群设置 → 群机器人 → 添加 → 复制 Webhook 地址
"""
import urllib.request, json, sys, os

sys.stdout.reconfigure(encoding='utf-8')

DASHBOARD_API = "http://127.0.0.1:8765"

MSG_TEMPLATES = {
    "wecom": {
        "msgtype": "markdown",
        "markdown": {
            "content": ""
        }
    },
    "dingtalk": {
        "msgtype": "markdown",
        "markdown": {
            "title": "融策Agent告警",
            "text": ""
        }
    },
    "feishu": {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "融策Agent告警"},
                "template": "red"
            },
            "elements": [{"tag": "markdown", "content": ""}]
        }
    }
}

def detect_webhook_type(url):
    if "qyapi.weixin.qq.com" in url:
        return "wecom"
    elif "oapi.dingtalk.com" in url:
        return "dingtalk"
    elif "open.feishu.cn" in url:
        return "feishu"
    return "wecom"  # default

def format_alert_markdown(issues, summary):
    now = __import__('datetime').datetime.now().strftime('%H:%M:%S')
    lines = [
        f"## 🚨 融策Agent告警",
        f"",
        f"**时间**: {now}",
        f"**状态**: 总{summary['total']} | 运行{summary.get('working',0)} | 异常{summary.get('error',0)} | 卡住{summary.get('stuck',0)}",
        f"",
    ]

    if issues:
        lines.append(f"### ⚠ 异常Agent ({len(issues)}个)")
        for i, iss in enumerate(issues):
            sid = chr(ord('a') + i)
            status_emoji = "🔴" if iss["status"] == "error" else "🟡"
            lines.append(f"- {status_emoji} **{iss['name']}** [{iss['status']}]")
            if iss.get("error"):
                lines.append(f"  > {iss['error'][:80]}")
        # 修复指令
        lines.append(f"")
        lines.append(f"**📱 手机回复修复:**")
        lines.append(f"> 修复全部")
        for i, iss in enumerate(issues[:3]):
            lines.append(f"> 修复{iss['name']}")
            if i.get("error"):
                lines.append(f"  - {i['error'][:100]}")
        lines.append("")

    lines.append(f"[查看面板](http://127.0.0.1:8765)")
    return "\n".join(lines)

def push_to_wecom(webhook_url, content):
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    req = urllib.request.Request(webhook_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=5)
    result = json.loads(resp.read())
    return result.get("errcode") == 0

def push_to_dingtalk(webhook_url, content):
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": "融策Agent告警", "text": content}
    }
    req = urllib.request.Request(webhook_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)
    return True

def push_to_feishu(webhook_url, content):
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🚨 融策Agent告警"},
                "template": "red"
            },
            "elements": [{"tag": "markdown", "content": content}]
        }
    }
    req = urllib.request.Request(webhook_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)
    return True

def check_and_alert(webhook_url=None):
    """心跳检查 + 异常推送"""
    # 获取 webhook URL
    if not webhook_url:
        webhook_url = os.environ.get("RONGCE_ALERT_WEBHOOK", "")

    if not webhook_url:
        # 从面板获取
        try:
            r = urllib.request.urlopen(f"{DASHBOARD_API}/api/state", timeout=5)
            state = json.loads(r.read())
            webhook_url = state.get("webhookUrl", "")
        except:
            pass

    if not webhook_url:
        print("⚠ 未配置 Webhook URL，请设置:")
        print("  set RONGCE_ALERT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
        print("  或在面板 http://127.0.0.1:8765 顶部输入")
        return False

    # 检查状态
    try:
        r = urllib.request.urlopen(f"{DASHBOARD_API}/api/state", timeout=5)
        state = json.loads(r.read())
    except Exception as e:
        print(f"❌ 无法连接面板: {e}")
        return False

    issues = []
    summary = {"total": 0, "working": 0, "idle": 0, "stuck": 0, "error": 0}
    for aid, info in state["agents"].items():
        summary[info["status"]] = summary.get(info["status"], 0) + 1
        summary["total"] += 1
        if info["status"] in ("error", "stuck"):
            meta = state["agentMeta"].get(aid, {})
            issues.append({
                "agent": aid,
                "name": meta.get("name", aid),
                "status": info["status"],
                "error": info.get("lastError", ""),
            })

    if not issues:
        print("✅ 全部正常，无需推送")
        return True

    # 格式化并推送
    hook_type = detect_webhook_type(webhook_url)
    content = format_alert_markdown(issues, summary)

    print(f"🚨 发现 {len(issues)} 个异常，推送到 {hook_type}...")

    pushers = {
        "wecom": push_to_wecom,
        "dingtalk": push_to_dingtalk,
        "feishu": push_to_feishu,
    }

    ok = pushers.get(hook_type, push_to_wecom)(webhook_url, content)
    if ok:
        print(f"✅ 推送成功 ({hook_type})")
    else:
        print(f"❌ 推送失败 ({hook_type})")

    return ok

if __name__ == "__main__":
    webhook = sys.argv[1] if len(sys.argv) > 1 else None
    check_and_alert(webhook)
