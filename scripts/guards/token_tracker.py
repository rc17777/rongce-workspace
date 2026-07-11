#!/usr/bin/env python3
"""
Token 用量追踪器
==============
基于 session_status 的 context 值做增量追踪。

存储: logs/token_usage.jsonl（每行一条JSON）
用法:
  python token_tracker.py snapshot --context 45000 --limit 200000 --session agent:main:xxx --note "任务名"
  python token_tracker.py report --date 2026-06-25
  python token_tracker.py summary --days 7
  python token_tracker.py today

原理:
  - 定期记录 context_used 快照
  - 相邻快照的增量 ≈ 期间消耗的 token（含输入+输出）
  - context 下降视为 compaction/restart，不计入消耗
"""

import json
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# Fix Windows GBK
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TZ = timezone(timedelta(hours=8))
ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "logs" / "token_usage.jsonl"

# ── 核心函数 ──

def ensure_log():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")

def write_record(record: dict):
    ensure_log()
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def read_records() -> list[dict]:
    ensure_log()
    records = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records

def parse_date(ts_str: str) -> datetime:
    """解析 ISO 时间字符串"""
    # 处理 +08:00 和 Z
    ts_str = ts_str.replace("Z", "+00:00")
    if ts_str.endswith("+08:00"):
        return datetime.fromisoformat(ts_str)
    # 兜底
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return datetime.strptime(ts_str.split("+")[0].split(".")[0], "%Y-%m-%dT%H:%M:%S")

def calc_daily_usage(records: list[dict], target_date: str) -> dict:
    """
    计算某日的 token 消耗。
    逻辑：按 session 分组，同一 session 内相邻快照的增量累加。
    context 下降（compaction/restart）时，只取上升部分。
    """
    from collections import defaultdict

    day_start = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=TZ)
    day_end = day_start + timedelta(days=1)

    # 筛选当日记录
    day_records = []
    for r in records:
        ts = parse_date(r["ts"])
        if day_start <= ts < day_end:
            day_records.append(r)

    if not day_records:
        return {"date": target_date, "total": 0, "sessions": 0, "snapshots": 0, "details": []}

    # 按 session 分组并按时间排序
    by_session = defaultdict(list)
    for r in day_records:
        by_session[r.get("session", "unknown")].append(r)

    total = 0
    details = []

    for session, snaps in by_session.items():
        snaps.sort(key=lambda x: parse_date(x["ts"]))
        session_total = 0
        notes = []
        for i in range(1, len(snaps)):
            prev = snaps[i - 1]["context_used"]
            curr = snaps[i]["context_used"]
            delta = curr - prev
            if delta > 0:
                session_total += delta
            # 收集 note
            if snaps[i].get("note"):
                notes.append(snaps[i]["note"])

        total += session_total
        details.append({
            "session": session,
            "snapshots": len(snaps),
            "usage": session_total,
            "notes": list(dict.fromkeys(notes))[:5],  # 去重，最多5条
        })

    return {
        "date": target_date,
        "total": total,
        "sessions": len(by_session),
        "snapshots": len(day_records),
        "details": details,
    }

# ── 命令处理 ──

def cmd_snapshot(args):
    record = {
        "ts": datetime.now(TZ).isoformat(),
        "session": args.session or "unknown",
        "context_used": args.context,
        "context_limit": args.limit or 200000,
        "note": args.note or "",
    }
    write_record(record)
    print(f"✅ 已记录: {args.context}/{args.limit or 200000} tokens [{args.note or '无备注'}]")

def cmd_report(args):
    date = args.date or datetime.now(TZ).strftime("%Y-%m-%d")
    records = read_records()
    report = calc_daily_usage(records, date)

    print(f"\n📊 Token 用量报告 — {date}")
    print("=" * 50)
    print(f"当日总计: {report['total']:,} tokens")
    print(f"涉及会话: {report['sessions']} 个")
    print(f"快照数量: {report['snapshots']} 条")
    print()

    if report["details"]:
        print("分会话明细:")
        for d in report["details"]:
            print(f"  • {d['session']}: {d['usage']:,} tokens ({d['snapshots']} 次快照)")
            if d["notes"]:
                for n in d["notes"]:
                    print(f"    └─ {n}")
    else:
        print("当日无记录。")
    print()

def cmd_summary(args):
    days = args.days or 7
    records = read_records()

    print(f"\n📈 最近 {days} 天 Token 用量汇总")
    print("=" * 50)

    today = datetime.now(TZ)
    grand_total = 0

    for i in range(days - 1, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        report = calc_daily_usage(records, date)
        bar = "█" * min(report["total"] // 5000, 20)  # 每5000一个█，最多20个
        print(f"{date}: {report['total']:>8,} tokens {bar}")
        grand_total += report["total"]

    print(f"\n累计: {grand_total:,} tokens (近 {days} 天)")
    avg = grand_total // days if days > 0 else 0
    print(f"日均: {avg:,} tokens")
    print()

def cmd_today(_args):
    """快速查看今天"""
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    records = read_records()
    report = calc_daily_usage(records, today)

    print(f"\n📊 今日 ({today}) Token 用量")
    print("=" * 40)
    print(f"已消耗: {report['total']:,} tokens")
    print(f"快照数: {report['snapshots']} 条")

    if report["details"]:
        for d in report["details"]:
            print(f"  • {d['session']}: {d['usage']:,}")
    print()

def cmd_reset(args):
    """标记一次 context reset（compaction 或 session 重启）"""
    record = {
        "ts": datetime.now(TZ).isoformat(),
        "session": args.session or "unknown",
        "context_used": args.context or 0,
        "context_limit": args.limit or 200000,
        "note": args.note or "context reset/compaction",
        "type": "reset",
    }
    write_record(record)
    print(f"🔄 已记录 context reset: {args.context or 0} tokens")

# ── 主入口 ──

def main():
    parser = argparse.ArgumentParser(description="Token 用量追踪器")
    sub = parser.add_subparsers(dest="command")

    # snapshot
    p_snap = sub.add_parser("snapshot", help="记录一次快照")
    p_snap.add_argument("--context", "-c", type=int, required=True, help="当前 context 使用量")
    p_snap.add_argument("--limit", "-l", type=int, default=200000, help="context 上限")
    p_snap.add_argument("--session", "-s", default="", help="session key")
    p_snap.add_argument("--note", "-n", default="", help="备注")

    # report
    p_rep = sub.add_parser("report", help="生成某日报告")
    p_rep.add_argument("--date", "-d", help="日期 (YYYY-MM-DD)，默认今天")

    # summary
    p_sum = sub.add_parser("summary", help="汇总最近N天")
    p_sum.add_argument("--days", type=int, default=7, help="天数，默认7")

    # today
    sub.add_parser("today", help="快速查看今天")

    # reset
    p_reset = sub.add_parser("reset", help="标记 context reset")
    p_reset.add_argument("--context", "-c", type=int, default=0)
    p_reset.add_argument("--session", "-s", default="")
    p_reset.add_argument("--note", "-n", default="")
    p_reset.add_argument("--limit", "-l", type=int, default=200000)

    args = parser.parse_args()

    if args.command == "snapshot":
        cmd_snapshot(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "summary":
        cmd_summary(args)
    elif args.command == "today":
        cmd_today(args)
    elif args.command == "reset":
        cmd_reset(args)
    else:
        parser.print_help()
        print("\n💡 提示: 先用 'snapshot' 记录，再用 'report' 或 'summary' 查看。")

if __name__ == "__main__":
    main()
