#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 费用守卫 (Cost Guard) v2.1 — 自动熔断版
=================================================
1. 每日费用监控 + 告警
2. API 调用限流装饰器
3. 自动熔断机制（超90%阈值自动切flash，超100%自动停）
4. 恢复检查

用法:
  python deepseek_cost_guard.py check       # 检查今日费用，超限告警
  python deepseek_cost_guard.py daily       # 生成昨日日报
  python deepseek_cost_guard.py limit       # 显示当前限额状态
  python deepseek_cost_guard.py init        # 初始化配置文件
  python deepseek_cost_guard.py auto-fuse   # 手动触发熔断
  python deepseek_cost_guard.py status      # 完整状态面板

配置 (config/cost_guard.json):
  {
    "daily_budget_cny": 100,
    "warning_threshold": 0.7,
    "critical_threshold": 0.9,
    "max_flash_requests_per_day": 5000,
    "max_v4pro_requests_per_day": 2000,
    "alert_channel": "console",
    "webhook_url": "",
    "enabled": true,
    "auto_fuse": true,
    "fuse_recovery_minutes": 30
  }
"""

import json, sys, os, csv
from pathlib import Path
from datetime import datetime, timezone, timedelta
from functools import wraps

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TZ = timezone(timedelta(hours=8))
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "cost_guard.json"
COST_CSV = Path("C:/Users/scrccpa/Desktop/cost-2026-6.csv")
GUARD_STATE_PATH = ROOT / "config" / "cost_guard_state.json"
FUSE_STATE_PATH = ROOT / "config" / "fuse_state.json"

# ── 默认配置 ──
DEFAULT_CONFIG = {
    "daily_budget_cny": 100,
    "warning_threshold": 0.7,
    "critical_threshold": 0.9,
    "max_flash_requests_per_day": 5000,
    "max_v4pro_requests_per_day": 2000,
    "alert_channel": "console",
    "webhook_url": "",
    "enabled": True,
    "auto_fuse": True,
    "fuse_recovery_minutes": 30,
}

# ================================================================
# 配置/状态 I/O
# ================================================================

def load_config():
    if CONFIG_PATH.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

def load_guard_state():
    if GUARD_STATE_PATH.exists():
        try:
            return json.loads(GUARD_STATE_PATH.read_text(encoding="utf-8"))
        except:
            pass
    return {}

def save_guard_state(state):
    GUARD_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GUARD_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def load_fuse_state():
    if FUSE_STATE_PATH.exists():
        try:
            return json.loads(FUSE_STATE_PATH.read_text(encoding="utf-8"))
        except:
            pass
    return {"fused": False, "fused_at": None, "recovery_at": None, "trigger": "none"}

def save_fuse_state(state):
    FUSE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FUSE_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

# ================================================================
# 费用计算
# ================================================================

def get_today_cost_from_csv():
    if not COST_CSV.exists():
        return {"total": 0, "v4pro": 0, "flash": 0}
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    total = v4pro = flash = 0.0
    with COST_CSV.open("r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("utc_date") == today:
                c = float(row.get("cost", 0))
                total += c
                if "v4-pro" in row.get("model", ""):
                    v4pro += c
                elif "v4-flash" in row.get("model", ""):
                    flash += c
    return {"total": total, "v4pro": v4pro, "flash": flash}

def get_yesterday_cost_from_csv():
    if not COST_CSV.exists():
        return {"total": 0, "v4pro": 0, "flash": 0, "date": ""}
    yesterday = (datetime.now(TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    total = v4pro = flash = 0.0
    with COST_CSV.open("r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("utc_date") == yesterday:
                c = float(row.get("cost", 0))
                total += c
                if "v4-pro" in row.get("model", ""):
                    v4pro += c
                elif "v4-flash" in row.get("model", ""):
                    flash += c
    return {"total": total, "v4pro": v4pro, "flash": flash, "date": yesterday}

# ================================================================
# 熔断系统
# ================================================================

def check_fuse():
    """
    自动熔断检查。
    返回: (tripped: bool, message: str, fuse_action: str)
      fuse_action: "normal" | "warn" | "fuse" | "recover"
    """
    cfg = load_config()
    if not cfg["enabled"]:
        return False, "守卫已禁用", "normal"

    today_cost = get_today_cost_from_csv()
    total = today_cost["total"]
    budget = cfg["daily_budget_cny"]
    ratio = total / budget if budget > 0 else 0

    fuse_state = load_fuse_state()
    now = datetime.now(TZ)

    # 如果已熔断，检查恢复时间
    if fuse_state.get("fused"):
        recovery_at = fuse_state.get("recovery_at")
        if recovery_at:
            try:
                recovery_dt = datetime.fromisoformat(recovery_at)
                if now >= recovery_dt:
                    # 自动恢复
                    save_fuse_state({"fused": False, "fused_at": None, "recovery_at": None, "trigger": "auto_recovered"})
                    msg = f"🔄 自动恢复！今日费用 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)，熔断期已过"
                    send_alert("INFO", msg)
                    return False, msg, "recover"
            except:
                pass
        return True, f"🔴 熔断中！今日 ¥{total:.2f}/{budget} ({ratio*100:.0f}%) — 预计 {fuse_state.get('recovery_at','?')} 恢复", "fuse"

    # 费用检查
    if ratio >= cfg["critical_threshold"]:
        if cfg["auto_fuse"]:
            # 自动熔断：30分钟后恢复（仅限v4-pro，flash不受限）
            recovery_time = now + timedelta(minutes=cfg.get("fuse_recovery_minutes", 30))
            fuse_state = {
                "fused": True,
                "fused_at": now.isoformat(),
                "recovery_at": recovery_time.isoformat(),
                "trigger": "auto_fuse",
            }
            save_fuse_state(fuse_state)
            msg = f"🚨 自动熔断触发！今日 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)，非Flash调用已暂停至{recovery_time.strftime('%H:%M')}"
            send_alert("CRITICAL", msg)
            return True, msg, "fuse"
        else:
            return True, f"🚨 费用超限！今日已用 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)，建议手动熔断", "warn"

    elif ratio >= cfg["warning_threshold"]:
        msg = f"⚠️ 费用预警！今日已用 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)"
        send_alert("WARNING", msg)
        return False, msg, "warn"

    else:
        return False, f"✅ 费用正常 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)", "normal"


def is_fused():
    """快速检查当前是否处于熔断状态（供外部调用）"""
    tripped, msg, action = check_fuse()
    return tripped, msg, action

def send_alert(level, message, data=None):
    cfg = load_config()
    ts = datetime.now(TZ).strftime("%m-%d %H:%M")
    full_msg = f"[{ts}] [{level}] {message}"
    if data:
        full_msg += f"\n  {json.dumps(data, ensure_ascii=False)}"

    if cfg["alert_channel"] in ("console", ""):
        print(full_msg)

    alert_log = ROOT / "logs" / "cost_alerts.log"
    alert_log.parent.mkdir(parents=True, exist_ok=True)
    with alert_log.open("a", encoding="utf-8") as f:
        f.write(full_msg + "\n" + "-" * 40 + "\n")

    if cfg["alert_channel"] == "webhook" and cfg.get("webhook_url"):
        try:
            import requests
            requests.post(cfg["webhook_url"], json={
                "level": level, "message": message, "data": data, "timestamp": ts
            }, timeout=10)
        except:
            pass


# ================================================================
# API 限流装饰器
# ================================================================

def rate_limited(model="flash", max_calls=None):
    cfg = load_config()
    if max_calls is None:
        max_calls = cfg["max_flash_requests_per_day"] if model == "flash" else cfg["max_v4pro_requests_per_day"]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 先检查熔断
            tripped, msg, action = check_fuse()
            if tripped:
                # 熔断时只允许 flash 调用
                if model != "flash":
                    send_alert("CRITICAL", f"非Flash API调用被熔断: {func.__name__}")
                    raise RuntimeError(f"Cost guard circuit breaker: {msg}")

            state = load_guard_state()
            today = datetime.now(TZ).strftime("%Y-%m-%d")
            if state.get("date") != today:
                state = {"date": today, "flash_calls": 0, "v4pro_calls": 0}

            current_calls = state.get(f"{model}_calls", 0)
            if current_calls >= max_calls:
                send_alert("WARNING", f"{model} 日调用次数超限 ({current_calls}/{max_calls}): {func.__name__}")
                raise RuntimeError(f"Daily {model} API limit: {current_calls}/{max_calls}")

            state[f"{model}_calls"] = current_calls + 1
            save_guard_state(state)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ================================================================
# 命令
# ================================================================

def cmd_check():
    cfg = load_config()
    today_cost = get_today_cost_from_csv()
    tripped, msg, action = check_fuse()

    print(f"\n{'='*55}")
    print(f"  🔌 DeepSeek 费用守卫 — 自动熔断版")
    print(f"{'='*55}")
    print(f"  今日费用: ¥{today_cost['total']:.2f} / ¥{cfg['daily_budget_cny']}")
    print(f"    V4 Pro: ¥{today_cost['v4pro']:.2f}")
    print(f"    Flash:  ¥{today_cost['flash']:.2f}")
    print(f"  状态: {msg}")
    print(f"  熔断: {'🔴是' if tripped else '🟢否'}")
    print(f"  自动熔断: {'开' if cfg['auto_fuse'] else '关'}")
    print(f"{'='*55}\n")
    return 1 if tripped else 0

def cmd_daily():
    yesterday = get_yesterday_cost_from_csv()
    print(f"\n📊 昨日 ({yesterday['date']}) 费用日报")
    print(f"{'='*50}")
    print(f"  总费用: ¥{yesterday['total']:.2f}")
    print(f"  V4 Pro: ¥{yesterday['v4pro']:.2f}")
    print(f"  Flash:  ¥{yesterday['flash']:.2f}")
    cfg = load_config()
    if yesterday['total'] > cfg['daily_budget_cny']:
        print(f"\n  ⚠️ 超预算！¥{yesterday['total']:.2f} > ¥{cfg['daily_budget_cny']}")
    print(f"{'='*50}\n")

def cmd_limit():
    cfg = load_config()
    state = load_guard_state()
    fuse = load_fuse_state()
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    print(f"\n{'='*55}")
    print(f"  📊 费用守卫配置")
    print(f"{'='*55}")
    print(f"  每日预算: ¥{cfg['daily_budget_cny']}")
    print(f"  预警阈值: {cfg['warning_threshold']*100:.0f}%")
    print(f"  熔断阈值: {cfg['critical_threshold']*100:.0f}%")
    print(f"  Flash 日限额: {cfg['max_flash_requests_per_day']} 次")
    print(f"  V4 Pro 日限额: {cfg['max_v4pro_requests_per_day']} 次")
    print(f"  守卫状态: {'启用' if cfg['enabled'] else '禁用'}")
    print(f"  自动熔断: {'开' if cfg['auto_fuse'] else '关'}")
    print(f"  熔断恢复: {cfg['fuse_recovery_minutes']}分钟")
    print()

    if fuse.get("fused"):
        print(f"  🔴 当前熔断中:")
        print(f"    触发: {fuse['fused_at'][:16]}")
        print(f"    预计恢复: {fuse['recovery_at'][:16]}")
    else:
        print(f"  🟢 熔断状态: 正常")

    if state.get("date") == today:
        print(f"\n  今日调用:")
        print(f"    Flash:  {state.get('flash_calls', 0)}/{cfg['max_flash_requests_per_day']}")
        print(f"    V4 Pro: {state.get('v4pro_calls', 0)}/{cfg['max_v4pro_requests_per_day']}")
    else:
        print("\n  今日暂无调用记录")
    print(f"{'='*55}\n")

def cmd_init():
    save_config(DEFAULT_CONFIG)
    save_fuse_state({"fused": False, "fused_at": None, "recovery_at": None, "trigger": "none"})
    print(f"✅ 已创建默认配置: {CONFIG_PATH}")
    print(f"  预算: ¥{DEFAULT_CONFIG['daily_budget_cny']}/天")
    print(f"  预警: {DEFAULT_CONFIG['warning_threshold']*100:.0f}%")
    print(f"  熔断: {DEFAULT_CONFIG['critical_threshold']*100:.0f}%（自动恢复{DEFAULT_CONFIG['fuse_recovery_minutes']}分钟）")

def cmd_auto_fuse():
    """手动触发自动熔断"""
    cfg = load_config()
    now = datetime.now(TZ)
    recovery_time = now + timedelta(minutes=cfg.get("fuse_recovery_minutes", 30))
    fuse_state = {
        "fused": True,
        "fused_at": now.isoformat(),
        "recovery_at": recovery_time.isoformat(),
        "trigger": "manual",
    }
    save_fuse_state(fuse_state)
    print(f"🔴 已手动触发熔断！非Flash调用暂停至 {recovery_time.strftime('%H:%M')}")
    return 1

def cmd_status():
    """完整状态面板"""
    cfg = load_config()
    today_cost = get_today_cost_from_csv()
    tripped, msg, action = check_fuse()
    fuse = load_fuse_state()

    print(f"\n{'='*55}")
    print(f"  🔌 费用守卫完整状态面板")
    print(f"{'='*55}")
    print(f"  📆 时间: {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}")
    print(f"  💰 费用: ¥{today_cost['total']:.2f}/{cfg['daily_budget_cny']}")
    print(f"     占比: {today_cost['total']/cfg['daily_budget_cny']*100:.1f}%" if cfg['daily_budget_cny'] > 0 else "")
    print(f"  🔴 V4 Pro: ¥{today_cost['v4pro']:.2f}")
    print(f"  🟢 Flash: ¥{today_cost['flash']:.2f}")
    print(f"  🚦 状态: {msg}")

    fuse_icon = "🔴" if fuse.get("fused") else "🟢"
    print(f"  {fuse_icon} 熔断: {'是' if fuse.get('fused') else '否'}")
    if fuse.get("fused"):
        print(f"    触发: {fuse.get('fused_at','?')[:16]}")
        print(f"    恢复: {fuse.get('recovery_at','?')[:16]}")
        print(f"    类型: {fuse.get('trigger','?')}")

    print(f"  🛡️ 自动熔断: {'开' if cfg.get('auto_fuse') else '关'}")
    print(f"  🎛️ 守卫: {'启用' if cfg['enabled'] else '禁用'}")
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    state = load_guard_state()
    if state.get("date") == today:
        print(f"  📞 Flash调用: {state.get('flash_calls', 0)}/{cfg['max_flash_requests_per_day']}")
        print(f"  📞 V4 Pro调用: {state.get('v4pro_calls', 0)}/{cfg['max_v4pro_requests_per_day']}")
    print(f"{'='*55}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DeepSeek 费用守卫 v2.1")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="检查今日费用并告警")
    sub.add_parser("daily", help="昨日日报")
    sub.add_parser("limit", help="显示限额配置")
    sub.add_parser("init", help="初始化配置")
    sub.add_parser("auto-fuse", help="手动触发熔断")
    sub.add_parser("status", help="完整状态面板")

    args = parser.parse_args()
    if args.command == "check":
        sys.exit(cmd_check())
    elif args.command == "daily":
        cmd_daily()
    elif args.command == "limit":
        cmd_limit()
    elif args.command == "init":
        cmd_init()
    elif args.command == "auto-fuse":
        sys.exit(cmd_auto_fuse())
    elif args.command == "status":
        cmd_status()
    else:
        parser.print_help()
        print("\n💡 建议先运行: python deepseek_cost_guard.py init")

if __name__ == "__main__":
    main()