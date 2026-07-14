#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Token usage tracker based on session_status context snapshots.

Storage: logs/token_usage.jsonl
Usage:
  python token_tracker.py snapshot -c 45000 -n "task name" -s session_key
  python token_tracker.py report -d 2026-07-06
  python token_tracker.py summary --days 7
  python token_tracker.py today
"""

import json
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TZ = timezone(timedelta(hours=8))
ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "logs" / "token_usage.jsonl"


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
    ts_str = ts_str.replace("Z", "+00:00")
    if ts_str.endswith("+08:00"):
        return datetime.fromisoformat(ts_str)
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return datetime.strptime(
            ts_str.split("+")[0].split(".")[0], "%Y-%m-%dT%H:%M:%S"
        )


def calc_daily_usage(records: list[dict], target_date: str) -> dict:
    day_start = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=TZ)
    day_end = day_start + timedelta(days=1)

    day_records = [
        r for r in records if day_start <= parse_date(r["ts"]) < day_end
    ]
    if not day_records:
        return {
            "date": target_date, "total": 0,
            "sessions": 0, "snapshots": 0, "details": []
        }

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
            if snaps[i].get("note"):
                notes.append(snaps[i]["note"])
        total += session_total
        details.append({
            "session": session,
            "snapshots": len(snaps),
            "usage": session_total,
            "notes": list(dict.fromkeys(notes))[:5],
        })

    return {
        "date": target_date, "total": total,
        "sessions": len(by_session), "snapshots": len(day_records),
        "details": details,
    }


def cmd_snapshot(args):
    record = {
        "ts": datetime.now(TZ).isoformat(),
        "session": args.session or "unknown",
        "context_used": args.context,
        "context_limit": args.limit or 200000,
        "note": args.note or "",
    }
    write_record(record)
    print(f"[OK] Recorded: {args.context}/{args.limit or 200000} tokens [{args.note or 'no note'}]")


def cmd_report(args):
    date = args.date or datetime.now(TZ).strftime("%Y-%m-%d")
    records = read_records()
    report = calc_daily_usage(records, date)

    print(f"\nToken Usage Report - {date}")
    print("=" * 50)
    print(f"Daily total: {report['total']:,} tokens")
    print(f"Sessions: {report['sessions']}")
    print(f"Snapshots: {report['snapshots']}")
    print()
    if report["details"]:
        print("By session:")
        for d in report["details"]:
            print(f"  - {d['session']}: {d['usage']:,} tokens ({d['snapshots']} snaps)")
            if d["notes"]:
                for n in d["notes"]:
                    print(f"      {n}")
    else:
        print("No records for this date.")
    print()


def cmd_summary(args):
    days = args.days or 7
    records = read_records()
    print(f"\nToken Usage Summary (last {days} days)")
    print("=" * 50)
    today = datetime.now(TZ)
    grand_total = 0
    for i in range(days - 1, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        report = calc_daily_usage(records, date)
        bar = "#" * min(report["total"] // 5000, 20)
        print(f"{date}: {report['total']:>8,} tokens {bar}")
        grand_total += report["total"]
    avg = grand_total // days if days > 0 else 0
    print(f"\nTotal: {grand_total:,} tokens ({days} days)")
    print(f"Daily avg: {avg:,} tokens")
    print()


def cmd_today(_args):
    today_str = datetime.now(TZ).strftime("%Y-%m-%d")
    records = read_records()
    report = calc_daily_usage(records, today_str)
    print(f"\nToday ({today_str}) Token Usage")
    print("=" * 40)
    print(f"Used: {report['total']:,} tokens")
    print(f"Snapshots: {report['snapshots']}")
    if report["details"]:
        for d in report["details"]:
            print(f"  - {d['session']}: {d['usage']:,}")
    print()


def cmd_reset(args):
    record = {
        "ts": datetime.now(TZ).isoformat(),
        "session": args.session or "unknown",
        "context_used": args.context or 0,
        "context_limit": args.limit or 200000,
        "note": args.note or "context reset/compaction",
        "type": "reset",
    }
    write_record(record)
    print(f"[RESET] Recorded context reset: {args.context or 0} tokens")


def main():
    parser = argparse.ArgumentParser(description="Token Usage Tracker")
    sub = parser.add_subparsers(dest="command")

    p_snap = sub.add_parser("snapshot", help="Record a snapshot")
    p_snap.add_argument("-c", "--context", type=int, required=True)
    p_snap.add_argument("-l", "--limit", type=int, default=200000)
    p_snap.add_argument("-s", "--session", default="")
    p_snap.add_argument("-n", "--note", default="")

    p_rep = sub.add_parser("report", help="Generate daily report")
    p_rep.add_argument("-d", "--date", help="YYYY-MM-DD")

    p_sum = sub.add_parser("summary", help="Summary of last N days")
    p_sum.add_argument("--days", type=int, default=7)

    sub.add_parser("today", help="Quick today view")

    p_reset = sub.add_parser("reset", help="Record a context reset")
    p_reset.add_argument("-c", "--context", type=int, default=0)
    p_reset.add_argument("-s", "--session", default="")
    p_reset.add_argument("-n", "--note", default="")
    p_reset.add_argument("-l", "--limit", type=int, default=200000)

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
        print("\nTip: Use 'snapshot' before/after tasks, then 'today' or 'summary' to view.")


if __name__ == "__main__":
    main()
