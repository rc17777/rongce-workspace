"""
生命周期管理
============
检查KB条目的时效性、冲突检测、僵尸条目清理。

用法:
    python -m tools.knowledge.lifecycle --rag-root rag/
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# 可配置参数
# ============================================================
RAG_ROOT = str(Path(__file__).parent.parent.parent / "rag")
ZOMBIE_THRESHOLD_MONTHS = 24          # 僵尸条目阈值（月）
TEMP_RULE_CHECK_YEARS = 2             # "暂行""试行"文件最长有效期（年）
CONFLICT_SIMILARITY_THRESHOLD = 0.6   # 冲突检测相似度阈值
# ============================================================


def _parse_kb_metadata(filepath: Path) -> Optional[dict]:
    """解析KB条目的frontmatter元数据"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"无法读取 {filepath}: {e}")
        return None

    # 解析 YAML frontmatter
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return None

    frontmatter = m.group(1)
    metadata = {}
    for line in frontmatter.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()

    metadata["_file"] = str(filepath)
    metadata["_content"] = content
    metadata["_size"] = len(content)
    return metadata


def _check_timeliness(metadata: dict, current_date: datetime) -> Optional[dict]:
    """
    检查时效性
    - 含有"暂行""试行"的文件，超过N年自动标记
    """
    title = metadata.get("title", "")
    content = metadata.get("_content", "")
    combined = f"{title} {content}"

    is_temporary = bool(re.search(r'暂行|试行', combined))
    if not is_temporary:
        return None

    # 解析日期
    date_str = metadata.get("date", "")
    try:
        entry_date = datetime.fromisoformat(date_str.split(" ")[0])
    except (ValueError, AttributeError):
        # 无法解析日期，用文件修改时间
        try:
            entry_date = datetime.fromtimestamp(Path(metadata["_file"]).stat().st_mtime)
        except (KeyError, OSError):
            return None

    years_old = (current_date - entry_date).days / 365.25
    if years_old > TEMP_RULE_CHECK_YEARS:
        return {
            "type": "timeliness_expired",
            "id": metadata.get("id", ""),
            "file": metadata.get("_file", ""),
            "detail": f"暂行/试行文件已超过 {years_old:.1f} 年（阈值 {TEMP_RULE_CHECK_YEARS} 年）",
            "action": "需复查是否已转为正式文件"
        }

    return None


def _check_conflicts(new_entries: list[dict], existing_index: dict) -> list[dict]:
    """检查新归档条目是否与已有KB冲突"""
    conflicts = []
    existing_entries = existing_index.get("entries", [])

    for new_entry in new_entries:
        new_keywords = set(new_entry.get("keywords", []))
        new_title = new_entry.get("title", "")

        for existing in existing_entries:
            if existing.get("id") == new_entry.get("id"):
                continue

            existing_keywords = set(existing.get("keywords", []))
            # 关键词重叠检测
            if new_keywords and existing_keywords:
                overlap = len(new_keywords & existing_keywords) / max(len(new_keywords), 1)
                if overlap > CONFLICT_SIMILARITY_THRESHOLD:
                    conflicts.append({
                        "type": "keyword_conflict",
                        "new_id": new_entry.get("id", ""),
                        "existing_id": existing.get("id", ""),
                        "overlap_score": round(overlap, 2),
                        "detail": f"关键词重叠度 {overlap:.0%}，请核实两篇内容是否矛盾"
                    })

    return conflicts


def _check_zombie_entries(entries: list[dict], current_date: datetime) -> list[dict]:
    """检查僵尸条目（超过阈值未被引用或更新的条目）"""
    zombies = []

    for entry in entries:
        date_str = entry.get("date", "") or entry.get("archived_at", "")
        try:
            entry_date = datetime.fromisoformat(date_str.split(" ")[0])
        except (ValueError, AttributeError):
            continue

        months_old = (current_date - entry_date).days / 30.44
        if months_old > ZOMBIE_THRESHOLD_MONTHS:
            zombies.append({
                "type": "zombie_entry",
                "id": entry.get("id", ""),
                "title": entry.get("title", ""),
                "file": entry.get("file", ""),
                "months_old": round(months_old, 1),
                "action": "建议降级为归档或删除"
            })

    return zombies


def run_lifecycle_check(new_entries: Optional[list[dict]] = None,
                        rag_root: Optional[str] = None) -> dict:
    """
    执行生命周期全量检查

    Args:
        new_entries: 本次新增的KB条目（用于冲突检测）
        rag_root: RAG根目录

    Returns:
        dict: {warnings, conflicts, zombies, report_path}
    """
    root = Path(rag_root or RAG_ROOT)
    current_date = datetime.now()

    # 1. 扫描所有KB条目
    warnings = []
    patterns = ["audit/*.md", "engineering/*.md", "ai-trends/*.md"]
    for pat in patterns:
        for filepath in root.glob(pat):
            meta = _parse_kb_metadata(filepath)
            if not meta:
                continue
            result = _check_timeliness(meta, current_date)
            if result:
                warnings.append(result)

    # 2. 加载索引
    index_path = root / "index.json"
    existing_index = {}
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            existing_index = json.load(f)

    # 3. 冲突检测
    conflicts = _check_conflicts(new_entries or [], existing_index)

    # 4. 僵尸条目检测
    all_entries = existing_index.get("entries", [])
    zombies = _check_zombie_entries(all_entries, current_date)

    # 5. 生成报告
    report_lines = [
        "# KB生命周期管理报告",
        f"生成时间: {current_date.isoformat()}",
        "",
        f"## 统计",
        f"- KB条目总数: {len(all_entries)}",
        f"- 时效性警告: {len(warnings)}",
        f"- 冲突检测: {len(conflicts)}",
        f"- 僵尸条目: {len(zombies)}",
        "",
    ]

    if warnings:
        report_lines += ["## ⚠️ 时效性警告", ""]
        for w in warnings:
            report_lines.append(f"- [{w['id']}] {w['detail']} → {w['action']}")

    if conflicts:
        report_lines += ["", "## 🔴 内容冲突", ""]
        for c in conflicts:
            report_lines.append(f"- 新条目 [{c['new_id']}] 与已有 [{c['existing_id']}] 关键词重叠 {c['overlap_score']}")

    if zombies:
        report_lines += ["", "## 💤 僵尸条目（超期未使用）", ""]
        for z in zombies:
            report_lines.append(f"- [{z['id']}] {z['title']} — {z['months_old']} 个月未更新")

    report_lines += ["", "---", "*本报告由融策知识Agent自动生成。*"]

    report_path = root / "lifecycle_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logger.info(f"生命周期检查完成: 警告 {len(warnings)}, 冲突 {len(conflicts)}, 僵尸 {len(zombies)}")

    return {
        "warnings": warnings,
        "conflicts": conflicts,
        "zombies": zombies,
        "report_path": str(report_path)
    }


# ============================================================
# CLI入口
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="生命周期管理")
    parser.add_argument("--rag-root", help="RAG根目录")
    parser.add_argument("--new-entries", help="新归档条目JSON（用于冲突检测）")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    new_entries = None
    if args.new_entries:
        with open(args.new_entries, "r", encoding="utf-8") as f:
            new_entries = json.load(f)

    result = run_lifecycle_check(new_entries=new_entries, rag_root=args.rag_root)
    print(f"\n生命周期报告: {result['report_path']}")
    print(f"时效警告: {len(result['warnings'])} | 冲突: {len(result['conflicts'])} | 僵尸: {len(result['zombies'])}")


if __name__ == "__main__":
    main()
