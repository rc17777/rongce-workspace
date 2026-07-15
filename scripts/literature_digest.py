"""
literature_digest.py — 文献精选推送

用于 OpenClaw 心跳/cron，读取当日或最新精选，
生成可推送的摘要文本。

用法：
  python scripts/literature_digest.py                       # 今日精选
  python scripts/literature_digest.py --latest              # 最新一期
  python scripts/literature_digest.py --date 2026-07-15     # 指定日期
  python scripts/literature_digest.py --summary             # 仅统计
"""

import json, sys, os
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(__file__).resolve().parent.parent
DIGEST_DIR = WORKSPACE / "knowledge" / "literature" / "digests"
LITERATURE_DIR = WORKSPACE / "knowledge" / "literature"


def get_latest_digest() -> tuple:
    """获取最新一期精选的文件路径和日期"""
    if not DIGEST_DIR.exists():
        return None, None
    digests = sorted(DIGEST_DIR.glob("*.md"), reverse=True)
    if not digests:
        return None, None
    latest = digests[0]
    date_str = latest.stem  # YYYY-MM-DD
    return latest, date_str


def read_digest(path: Path) -> str:
    """读取精选文件内容"""
    return path.read_text(encoding="utf-8")


def count_literature() -> dict:
    """统计文献库情况"""
    if not LITERATURE_DIR.exists():
        return {"total": 0, "by_year": {}}

    total = 0
    by_year = {}
    for f in LITERATURE_DIR.rglob("*.md"):
        if f.parent.name == "digests":
            continue
        total += 1
        parts = f.relative_to(LITERATURE_DIR).parts
        if len(parts) >= 1:
            year = parts[0][:4]
            by_year[year] = by_year.get(year, 0) + 1

    return {"total": total, "by_year": dict(sorted(by_year.items()))}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="文献精选推送")
    parser.add_argument("--latest", action="store_true", help="获取最新一期")
    parser.add_argument("--date", type=str, default="", help="指定日期 YYYY-MM-DD")
    parser.add_argument("--summary", action="store_true", help="仅统计")
    args = parser.parse_args()

    if args.summary:
        stats = count_literature()
        print(f"📊 文献库统计")
        print(f"   总计: {stats['total']} 篇")
        for year, count in stats["by_year"].items():
            print(f"   {year}: {count} 篇")
        return

    if args.date:
        digest_path = DIGEST_DIR / f"{args.date}.md"
        if not digest_path.exists():
            print(f"❌ 未找到 {args.date} 的精选")
            return
        content = read_digest(digest_path)
        print(content)
        return

    if args.latest:
        digest_path, date_str = get_latest_digest()
        if not digest_path:
            print("📭 尚未有精选摘要")
            return
        stats = count_literature()
        print(f"📚 文献库: {stats['total']} 篇")
        print()
        content = read_digest(digest_path)
        print(content)
        return

    # 默认：今日精选
    today = date.today().isoformat()
    digest_path = DIGEST_DIR / f"{today}.md"
    if digest_path.exists():
        print(read_digest(digest_path))
    else:
        print(f"📭 今日 ({today}) 尚无精选，请先运行 literature_collector.py")


if __name__ == "__main__":
    main()