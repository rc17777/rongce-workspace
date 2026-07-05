#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a health report for the Rongce audit knowledge base.

This script is read-only: it inspects the Obsidian catalog, selected markdown
files, v2.0 training list, and scene sync copies, then writes a markdown report.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

VAULT = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault")
CATALOG = VAULT / "审计资料清单.json"
CASE_ROOT = VAULT / "审计案例库-OCR"
V2_ROOT = CASE_ROOT / "融策标准作业体系 v2.0"
TRAINING = V2_ROOT / "01-训练清单" / "场景-审计逻辑-可复用方法训练清单 v2.0.md"
REPORT = V2_ROOT / "00-知识库健康体检报告.md"

CORE_SCENES = {
    "工程审计", "政策落实审计", "国企审计", "信息系统审计", "农业农村审计",
    "预算执行审计", "绩效审计", "经济责任审计", "社保民生审计", "资源环境审计",
    "专项资金审计", "金融审计", "内部审计", "教科文卫审计", "其他审计",
}
GENERATED_MARKERS = [
    "案例卡片", "模板", "标准作业包", "实战试点包", "训练清单", "方法词典",
    "资料总览", "老板版", "融策标准作业体系", "覆盖率与同步机制", "逐篇审计逻辑提炼",
]


def load_catalog() -> list[dict]:
    if not CATALOG.exists():
        raise FileNotFoundError(f"Missing catalog: {CATALOG}")
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def combined_text(item: dict) -> str:
    return " ".join(str(item.get(k, "")) for k in ("path", "filename", "title", "scene"))


def is_generated_or_noncase(item: dict) -> bool:
    text = combined_text(item)
    return item.get("scene") not in CORE_SCENES or any(marker in text for marker in GENERATED_MARKERS)


def is_scene_sync_copy(item: dict) -> bool:
    rel = item.get("path", "")
    parts = re.split(r"[\\/]", rel)
    return len(parts) == 3 and parts[0] == "审计案例库-OCR" and parts[1] in CORE_SCENES


def physical_path(item: dict) -> Path:
    return VAULT / item["path"]


def file_has_logic(item: dict) -> bool:
    path = physical_path(item)
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "## 融策审计逻辑提炼" in text


def bucket_generated(item: dict) -> str:
    text = combined_text(item)
    for marker in GENERATED_MARKERS:
        if marker in text:
            return marker
    return item.get("scene") or "未分类"


def source_bucket(item: dict) -> str:
    rel = item.get("path", "")
    parts = re.split(r"[\\/]", rel)
    if is_scene_sync_copy(item):
        return "场景库同步副本"
    if len(parts) >= 2 and parts[0] in {"审计案例库-OCR", "审计案例库", "杂志资料"}:
        return parts[0] if parts[0] != "审计案例库-OCR" else "OCR原始/专题资料"
    return parts[0] if parts else "未知来源"


def main() -> None:
    data = load_catalog()
    real = [item for item in data if not is_generated_or_noncase(item)]
    generated = [item for item in data if is_generated_or_noncase(item)]
    scene_sync = [item for item in real if is_scene_sync_copy(item)]
    originals = [item for item in real if not is_scene_sync_copy(item)]

    training_text = TRAINING.read_text(encoding="utf-8", errors="replace") if TRAINING.exists() else ""
    training_missed = []
    for item in real:
        title = item.get("title") or item.get("filename") or ""
        rel_path = item.get("path", "")
        if title not in training_text and rel_path not in training_text:
            training_missed.append(item)

    logic_missing = [item for item in originals if not file_has_logic(item)]
    missing_files = [item for item in real if not physical_path(item).exists()]

    title_groups: dict[str, list[dict]] = defaultdict(list)
    for item in real:
        title = item.get("title") or Path(item.get("filename", "")).stem
        title_groups[title].append(item)
    duplicate_titles = {title: items for title, items in title_groups.items() if len(items) > 1}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.append("# 融策审计知识库健康体检报告")
    lines.append("")
    lines.append(f"> 生成时间：{now}")
    lines.append(f"> 索引文件：`{CATALOG}`")
    lines.append("")
    lines.append("## 一、总体口径")
    lines.append("")
    lines.append(f"- 索引总条目：{len(data)}")
    lines.append(f"- 真实案例/文章/政策资料：{len(real)}")
    lines.append(f"- 原始真实资料：{len(originals)}")
    lines.append(f"- 场景库同步副本：{len(scene_sync)}")
    lines.append(f"- 二次产物或非核心场景资料：{len(generated)}")
    lines.append(f"- v2.0 Markdown 文件数：{len(list(V2_ROOT.rglob('*.md'))) if V2_ROOT.exists() else 0}")
    lines.append("")
    lines.append("> 注意：索引总条目包含场景同步副本和二次产物，不能直接等同于原始案例数量。")
    lines.append("")
    lines.append("## 二、覆盖率")
    lines.append("")
    lines.append(f"- 训练清单覆盖：{len(real) - len(training_missed)}/{len(real)}")
    lines.append(f"- 训练清单漏项：{len(training_missed)}")
    lines.append(f"- 原始资料审计逻辑提炼漏项：{len(logic_missing)}")
    lines.append(f"- 索引指向但文件不存在：{len(missing_files)}")
    lines.append("")
    lines.append("## 三、真实资料场景分布")
    lines.append("")
    lines.append("| 场景 | 条目数 |")
    lines.append("|---|---:|")
    for scene, count in Counter(item.get("scene") or "未分类" for item in real).most_common():
        lines.append(f"| {scene} | {count} |")
    lines.append("")
    lines.append("## 四、来源结构")
    lines.append("")
    lines.append("| 来源 | 条目数 |")
    lines.append("|---|---:|")
    for source, count in Counter(source_bucket(item) for item in real).most_common():
        lines.append(f"| {source} | {count} |")
    lines.append("")
    lines.append("## 五、二次产物结构")
    lines.append("")
    lines.append("| 类型 | 条目数 |")
    lines.append("|---|---:|")
    for bucket, count in Counter(bucket_generated(item) for item in generated).most_common():
        lines.append(f"| {bucket} | {count} |")
    lines.append("")
    lines.append("## 六、重复标题提示")
    lines.append("")
    lines.append(f"- 重复标题组数：{len(duplicate_titles)}")
    lines.append("- 说明：场景同步副本会造成重复标题；这不是问题，但汇报数量时要剔除副本。")
    lines.append("")

    if training_missed:
        lines.append("## 七、训练清单漏项样例")
        lines.append("")
        for item in training_missed[:30]:
            lines.append(f"- {item.get('scene')}｜{item.get('title')}｜`{item.get('path')}`")
        lines.append("")

    if logic_missing:
        lines.append("## 八、审计逻辑提炼漏项样例")
        lines.append("")
        for item in logic_missing[:30]:
            lines.append(f"- {item.get('scene')}｜{item.get('title')}｜`{item.get('path')}`")
        lines.append("")

    if missing_files:
        lines.append("## 九、缺失文件样例")
        lines.append("")
        for item in missing_files[:30]:
            lines.append(f"- {item.get('scene')}｜{item.get('title')}｜`{item.get('path')}`")
        lines.append("")

    lines.append("## 十、建议")
    lines.append("")
    if not training_missed and not logic_missing and not missing_files:
        lines.append("- 当前知识库主链路健康：真实资料已进入训练清单，原始资料已具备审计逻辑提炼，索引未发现缺失文件。")
    else:
        lines.append("- 先处理漏项和缺失文件，再刷新训练清单与覆盖率。")
    lines.append("- 后续新增资料时，继续使用：`build_catalog.py` → `enrich_and_sync_scene_cases.py` → `rongce_v2_sync.py` → `audit_v2_coverage.py`。")
    lines.append("- 对外汇报时分开使用“原始真实资料”“场景同步副本”“二次产物”三个口径。")
    lines.append("")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT {REPORT}")
    print(f"TOTAL_CATALOG {len(data)}")
    print(f"REAL_CASES {len(real)}")
    print(f"ORIGINAL_REAL {len(originals)}")
    print(f"SCENE_SYNC_COPIES {len(scene_sync)}")
    print(f"GENERATED_OR_NONCASE {len(generated)}")
    print(f"TRAINING_MISSED {len(training_missed)}")
    print(f"LOGIC_MISSING {len(logic_missing)}")
    print(f"MISSING_FILES {len(missing_files)}")


if __name__ == "__main__":
    main()
