#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 多 key 余额巡查 + 自动熔断
每小时检查所有 key 的余额，低于阈值时推送告警，必要时杀掉进程。
"""
import sys, os, json, time, subprocess
sys.stdout.reconfigure(encoding='utf-8')

# ── 配置 ──
CONFIG = {
    # (key名称, key前缀, 日预算, 进程名pattern)
    ("data-analysis", "sk-7d503", 30.0, "pythonw"),
    ("RAG-智析", "sk-dbc61", 50.0, None),  # 手动工具，无固定进程
    ("OpenClaw主", "sk-9a42c", 100.0, None),
}

ALERT_WEBHOOK = None  # 如果有钉钉/企业微信webhook，填这里
LOG_FILE = r"D:\openclaw-workspace\logs\balance_check.jsonl"

def log_record(rec):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def check_key(key, name, daily_budget):
    """查单个key余额"""
    try:
        import requests
        r = requests.get(
            "https://api.deepseek.com/user/balance",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10
        )
        d = r.json()
        if "error" in d:
            return {"ok": False, "error": d["error"]["message"], "balance": 0}
        bal = d.get("balance_infos", [{}])[0].get("total_balance", 0)
        # DeepSeek返回的是分，转元
        bal_cny = bal / 100 if bal > 1000 else bal  # 兼容不同单位
        return {"ok": True, "balance": bal_cny, "raw": d}
    except Exception as e:
        return {"ok": False, "error": str(e), "balance": 0}

def find_and_kill(pattern):
    """按进程名pattern查找并终止"""
    if not pattern:
        return []
    try:
        result = subprocess.run(
            f'tasklist | findstr {pattern}',
            shell=True, capture_output=True, text=True
        )
        killed = []
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                pid = int(parts[1])
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                killed.append(pid)
        return killed
    except Exception as e:
        return [f"error: {e}"]

def main():
    import requests  # 延迟导入

    # 实际key需要从安全位置读取，这里先检查能查到的
    # 由于key分散在不同配置文件，这里用占位逻辑
    # 真正运行时需要把完整key填进来或用环境变量

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] DeepSeek 余额巡查")
    print("-" * 60)

    # 遍历配置（实际key从环境变量或配置文件读取）
    alerts = []

    # 检查 OpenClaw 主 key（已知完整key）
    openclaw_key = os.environ.get("DEEPSEEK_OPENCLAW_KEY", "")
    if openclaw_key:
        r = check_key(openclaw_key, "OpenClaw主", 100.0)
        if r["ok"]:
            bal = r["balance"]
            pct = (bal / 100.0) * 100 if bal < 1000 else 0  # 假设日预算100
            print(f"  OpenClaw主: ¥{bal:.2f} (预算¥100)")
            if bal < 20:
                alerts.append(f"🔴 OpenClaw主 key 余额仅剩 ¥{bal:.2f}，即将耗尽！")
        else:
            print(f"  OpenClaw主: 查询失败 - {r.get('error', 'unknown')}")

    # 检查 data-analysis key（从配置文件读取）
    config_path = r"D:\openclaw-workspace\projects\data-analysis-agent\LLM\llm_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            ds_key = cfg.get("deepseek", {}).get("api_key", "")
            if ds_key:
                r = check_key(ds_key, "data-analysis", 30.0)
                if r["ok"]:
                    bal = r["balance"]
                    print(f"  data-analysis: ¥{bal:.2f} (预算¥30)")
                    if bal < 5:
                        alerts.append(f"🔴 data-analysis key 余额仅剩 ¥{bal:.2f}！")
                        # 自动熔断：杀掉 server.py
                        killed = find_and_kill("pythonw")
                        if killed:
                            alerts.append(f"⚡ 已自动终止进程: {killed}")
                else:
                    print(f"  data-analysis: 查询失败 - {r.get('error', 'unknown')}")
        except Exception as e:
            print(f"  data-analysis: 读配置失败 - {e}")

    # 检查 RAG key（从 MEMORY.md 已知前缀 sk-dbc61...）
    rag_key = os.environ.get("DEEPSEEK_RAG_KEY", "")
    if rag_key:
        r = check_key(rag_key, "RAG", 50.0)
        if r["ok"]:
            bal = r["balance"]
            print(f"  RAG: ¥{bal:.2f} (预算¥50)")
            if bal < 10:
                alerts.append(f"🔴 RAG key 余额仅剩 ¥{bal:.2f}！")

    print("-" * 60)

    if alerts:
        msg = "\n".join(alerts)
        print(f"\n🚨 告警:\n{msg}")
        # 推送告警
        if ALERT_WEBHOOK:
            try:
                requests.post(ALERT_WEBHOOK, json={"text": msg}, timeout=5)
            except Exception as e:
                print(f"告警推送失败: {e}")
    else:
        print("\n✅ 所有 key 余额正常")

    log_record({
        "time": time.time(),
        "alerts": alerts,
        "check_count": len([c for c in CONFIG if c[2] > 0]),
    })

if __name__ == "__main__":
    main()
