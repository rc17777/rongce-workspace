#!/usr/bin/env python3
"""
OpenRouter 免费模型监控脚本
每次运行：调 API → 对比快照 → 输出变化 → 更新快照

输出格式：
  - 无变化：静默，只更新快照时间戳
  - 有变化：输出 JSON 报告到 stdout，供 AI 助手读取后推送通知
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Fix Windows GBK encoding hell
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests

# 配置
API_URL = "https://openrouter.ai/api/v1/models"
SNAPSHOT_PATH = Path(__file__).parent.parent / "config" / "openrouter_free_models.json"
TZ = timezone(timedelta(hours=8))  # Asia/Shanghai

def fetch_free_models() -> list[dict]:
    """从 OpenRouter API 获取当前所有免费模型"""
    resp = requests.get(API_URL, timeout=30)
    resp.raise_for_status()
    all_models = resp.json()["data"]

    free = []
    for m in all_models:
        pricing = m.get("pricing", {})
        if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
            free.append({
                "id": m["id"],
                "name": m.get("name", ""),
                "context_length": m.get("context_length", 0),
                "modality": m.get("architecture", {}).get("modality", ""),
                "description": (m.get("description", "") or "")[:200],
                "created": m.get("created", 0),
            })
    return sorted(free, key=lambda x: x["id"])

def load_snapshot() -> dict:
    """加载本地快照"""
    if SNAPSHOT_PATH.exists():
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return {"models": {}, "last_updated": None, "count": 0}

def save_snapshot(models: list[dict]) -> dict:
    """保存新快照"""
    snapshot = {
        "last_updated": datetime.now(TZ).isoformat(),
        "count": len(models),
        "models": {m["id"]: m for m in models},
    }
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot

def compare(old_snapshot: dict, new_models: list[dict]) -> dict:
    """对比新旧快照，返回变化报告"""
    old_ids = set(old_snapshot.get("models", {}).keys())
    new_ids = {m["id"] for m in new_models}
    new_map = {m["id"]: m for m in new_models}
    old_map = old_snapshot.get("models", {})

    added = []
    removed = []
    changed = []

    for mid in new_ids - old_ids:
        m = new_map[mid]
        added.append(f'➕ {m["name"] or mid} ({mid}) | ctx={m["context_length"]} | {m["modality"]}')

    for mid in old_ids - new_ids:
        om = old_map.get(mid, {})
        removed.append(f'➖ {om.get("name", mid)} ({mid})')

    for mid in old_ids & new_ids:
        om = old_map.get(mid, {})
        nm = new_map[mid]
        if om.get("context_length") != nm["context_length"] or om.get("modality") != nm["modality"]:
            changed.append(f'🔄 {nm["name"] or mid} ({mid}): ctx {om.get("context_length")}→{nm["context_length"]}, {om.get("modality")}→{nm["modality"]}')

    return {
        "has_changes": bool(added or removed or changed),
        "is_first_run": not old_snapshot.get("last_updated"),
        "timestamp": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
        "total_free": len(new_models),
        "old_total": old_snapshot.get("count", 0),
        "added": added,
        "removed": removed,
        "changed": changed,
        "last_updated": old_snapshot.get("last_updated", "首次运行"),
    }

def main():
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}] 正在获取 OpenRouter 免费模型列表...")

    models = fetch_free_models()
    old = load_snapshot()
    report = compare(old, models)
    save_snapshot(models)

    if report["is_first_run"]:
        print(f"✅ 首次运行！已保存 {report['total_free']} 个免费模型的快照。")
        print(f"\n当前免费模型 ({report['total_free']} 个):")
        for m in models:
            print(f"  • {m['name']:<45} {m['id']:<55} ctx={m['context_length']:>7}  {m['modality']}")
        print("\n💡 下次心跳时将自动对比变化。")
    elif report["has_changes"]:
        print(f"🚨 检测到变化！免费模型数: {report['old_total']} → {report['total_free']}")
        for line in report["added"]:
            print(f"  {line}")
        for line in report["removed"]:
            print(f"  {line}")
        for line in report["changed"]:
            print(f"  {line}")
    else:
        print(f"✅ 无变化。当前免费模型数: {report['total_free']}，上次更新: {report['last_updated']}")

    # 输出 JSON 报告供 AI 解析
    print("\n---JSON_REPORT---")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
