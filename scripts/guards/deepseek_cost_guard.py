#!/usr/bin/env python3
"""
DeepSeek 费用守卫 (Cost Guard)
==============================
1. 每日费用监控 + 告警
2. API 调用限流装饰器
3. 自动熔断机制

用法:
  python deepseek_cost_guard.py check     # 检查今日费用，超限告警
  python deepseek_cost_guard.py daily     # 生成昨日日报
  python deepseek_cost_guard.py limit     # 显示当前限额状态

配置 (config/cost_guard.json):
  {
    "daily_budget_cny": 100,       # 每日预算(元)
    "warning_threshold": 0.7,      # 70%预警
    "critical_threshold": 0.9,     # 90%熔断
    "max_flash_requests_per_day": 5000,
    "max_v4pro_requests_per_day": 2000,
    "alert_channel": "console",    # console/webhook/none
    "webhook_url": ""
  }
"""

import argparse
import json
import sys
import os
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
}

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

# ── 费用计算 ──

def get_today_cost_from_csv():
    """从CSV读取今日费用"""
    if not COST_CSV.exists():
        return {"total": 0, "v4pro": 0, "flash": 0}
    
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    total = v4pro = flash = 0.0
    
    import csv
    with COST_CSV.open("r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["utc_date"] == today:
                c = float(row["cost"])
                total += c
                if "v4-pro" in row["model"]:
                    v4pro += c
                elif "v4-flash" in row["model"]:
                    flash += c
    
    return {"total": total, "v4pro": v4pro, "flash": flash}

def get_yesterday_cost_from_csv():
    """从CSV读取昨日费用"""
    if not COST_CSV.exists():
        return {"total": 0, "v4pro": 0, "flash": 0}
    
    yesterday = (datetime.now(TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    total = v4pro = flash = 0.0
    
    import csv
    with COST_CSV.open("r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["utc_date"] == yesterday:
                c = float(row["cost"])
                total += c
                if "v4-pro" in row["model"]:
                    v4pro += c
                elif "v4-flash" in row["model"]:
                    flash += c
    
    return {"total": total, "v4pro": v4pro, "flash": flash, "date": yesterday}

# ── 告警 ──

def send_alert(level, message, data=None):
    """发送告警"""
    cfg = load_config()
    ts = datetime.now(TZ).strftime("%m-%d %H:%M")
    
    full_msg = f"[{ts}] [{level}] {message}"
    if data:
        full_msg += f"\n  详情: {json.dumps(data, ensure_ascii=False)}"
    
    # Console 输出
    if cfg["alert_channel"] in ("console", ""):
        print(full_msg)
    
    # 写入告警日志
    alert_log = ROOT / "logs" / "cost_alerts.log"
    alert_log.parent.mkdir(parents=True, exist_ok=True)
    with alert_log.open("a", encoding="utf-8") as f:
        f.write(full_msg + "\n" + "-" * 40 + "\n")
    
    # Webhook (未来扩展)
    if cfg["alert_channel"] == "webhook" and cfg.get("webhook_url"):
        try:
            import requests
            requests.post(cfg["webhook_url"], json={
                "level": level,
                "message": message,
                "data": data,
                "timestamp": ts
            }, timeout=10)
        except:
            pass

# ── 熔断检查 ──

def check_circuit_breaker():
    """检查是否需要熔断"""
    cfg = load_config()
    if not cfg["enabled"]:
        return False, "守卫已禁用"
    
    today_cost = get_today_cost_from_csv()
    total = today_cost["total"]
    budget = cfg["daily_budget_cny"]
    ratio = total / budget if budget > 0 else 0
    
    if ratio >= cfg["critical_threshold"]:
        return True, f"🚨 费用熔断！今日已用 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)，暂停非必要API调用"
    elif ratio >= cfg["warning_threshold"]:
        return False, f"⚠️ 费用预警！今日已用 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)"
    else:
        return False, f"✅ 费用正常 ¥{total:.2f}/{budget} ({ratio*100:.0f}%)"

# ── API 限流装饰器 ──

def rate_limited(model="flash", max_calls=None):
    """
    API调用限流装饰器
    
    用法:
        @rate_limited(model="flash", max_calls=100)
        def my_api_func():
            ...
    """
    cfg = load_config()
    if max_calls is None:
        max_calls = cfg["max_flash_requests_per_day"] if model == "flash" else cfg["max_v4pro_requests_per_day"]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            state = load_guard_state()
            today = datetime.now(TZ).strftime("%Y-%m-%d")
            
            # 检查日期是否变化
            if state.get("date") != today:
                state = {"date": today, "flash_calls": 0, "v4pro_calls": 0}
            
            # 检查熔断
            tripped, msg = check_circuit_breaker()
            if tripped:
                send_alert("CRITICAL", f"API调用被熔断: {func.__name__}")
                raise RuntimeError(f"Cost guard circuit breaker tripped: {msg}")
            
            # 检查调用次数
            current_calls = state.get(f"{model}_calls", 0)
            if current_calls >= max_calls:
                send_alert("WARNING", f"{model} 日调用次数超限 ({current_calls}/{max_calls}): {func.__name__}")
                raise RuntimeError(f"Daily {model} API limit exceeded: {current_calls}/{max_calls}")
            
            # 执行调用
            state[f"{model}_calls"] = current_calls + 1
            save_guard_state(state)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ── 命令 ──

def cmd_check():
    """检查今日费用状态"""
    cfg = load_config()
    today_cost = get_today_cost_from_csv()
    
    tripped, msg = check_circuit_breaker()
    
    print(f"\n{'='*50}")
    print(f"DeepSeek 费用守卫检查")
    print(f"{'='*50}")
    print(f"今日费用: ¥{today_cost['total']:.2f} / ¥{cfg['daily_budget_cny']}")
    print(f"  V4 Pro: ¥{today_cost['v4pro']:.2f}")
    print(f"  Flash:  ¥{today_cost['flash']:.2f}")
    print(f"状态: {msg}")
    
    if tripped:
        print(f"\n🔴 已触发熔断！建议立即:")
        print(f"  1. 检查是否有脚本/Agent在空转")
        print(f"  2. 暂停批量处理任务")
        print(f"  3. 手动确认后再恢复")
    
    print(f"{'='*50}\n")
    
    return 1 if tripped else 0

def cmd_daily():
    """生成昨日日报"""
    yesterday = get_yesterday_cost_from_csv()
    
    print(f"\n📊 昨日 ({yesterday['date']}) 费用日报")
    print(f"{'='*50}")
    print(f"总费用: ¥{yesterday['total']:.2f}")
    print(f"V4 Pro: ¥{yesterday['v4pro']:.2f}")
    print(f"Flash:  ¥{yesterday['flash']:.2f}")
    
    cfg = load_config()
    if yesterday['total'] > cfg['daily_budget_cny']:
        print(f"\n⚠️ 超预算！¥{yesterday['total']:.2f} > ¥{cfg['daily_budget_cny']}")
    
    print(f"{'='*50}\n")

def cmd_limit():
    """显示限额状态"""
    cfg = load_config()
    state = load_guard_state()
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    
    print(f"\n{'='*50}")
    print(f"费用守卫配置")
    print(f"{'='*50}")
    print(f"每日预算: ¥{cfg['daily_budget_cny']}")
    print(f"预警阈值: {cfg['warning_threshold']*100:.0f}%")
    print(f"熔断阈值: {cfg['critical_threshold']*100:.0f}%")
    print(f"Flash 日限额: {cfg['max_flash_requests_per_day']} 次")
    print(f"V4 Pro 日限额: {cfg['max_v4pro_requests_per_day']} 次")
    print(f"守卫状态: {'启用' if cfg['enabled'] else '禁用'}")
    print()
    
    if state.get("date") == today:
        print(f"今日调用统计:")
        print(f"  Flash:  {state.get('flash_calls', 0)}/{cfg['max_flash_requests_per_day']}")
        print(f"  V4 Pro: {state.get('v4pro_calls', 0)}/{cfg['max_v4pro_requests_per_day']}")
    else:
        print("今日暂无调用记录")
    
    print(f"{'='*50}\n")

def cmd_init():
    """初始化配置文件"""
    save_config(DEFAULT_CONFIG)
    print(f"✅ 已创建默认配置: {CONFIG_PATH}")
    print(f"请编辑该文件调整预算和阈值")

def main():
    parser = argparse.ArgumentParser(description="DeepSeek 费用守卫")
    sub = parser.add_subparsers(dest="command")
    
    sub.add_parser("check", help="检查今日费用并告警")
    sub.add_parser("daily", help="昨日日报")
    sub.add_parser("limit", help="显示限额配置")
    sub.add_parser("init", help="初始化配置")
    
    args = parser.parse_args()
    
    if args.command == "check":
        sys.exit(cmd_check())
    elif args.command == "daily":
        cmd_daily()
    elif args.command == "limit":
        cmd_limit()
    elif args.command == "init":
        cmd_init()
    else:
        parser.print_help()
        print("\n💡 建议先运行: python deepseek_cost_guard.py init")

if __name__ == "__main__":
    import argparse
    main()
