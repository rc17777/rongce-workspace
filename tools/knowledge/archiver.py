"""
归档器
======
将摘要后的内容按域归档为 Markdown KB 条目，生成索引文件。

用法:
    python -m tools.knowledge.archiver --input summarized.json
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# 可配置参数
# ============================================================
RAG_ROOT = str(Path(__file__).parent.parent.parent / "rag")
INDEX_FILE = "index.json"
# ============================================================

DOMAIN_DIRS = {
    1: "audit",
    2: "engineering",
    3: "ai-trends",
}

DOMAIN_KB_PREFIX = {
    1: "KB-AUDIT",
    2: "KB-ENG",
    3: "KB-AI",
}


def _slugify(text: str, max_len: int = 50) -> str:
    """生成文件名友好的 slug"""
    # 保留中英文、数字、连字符
    cleaned = re.sub(r'[^\w\u4e00-\u9fff-]', '_', text)
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = cleaned.strip('_')
    return cleaned[:max_len]


def _generate_kb_id(domain: int, year: int, counter: int) -> str:
    """生成KB条目ID"""
    prefix = DOMAIN_KB_PREFIX.get(domain, "KB-OTHER")
    return f"{prefix}-{year}-{counter:04d}"


def _get_next_counter(domain_dir: Path, year: int) -> int:
    """获取下一个可用的KB编号"""
    existing = list(domain_dir.glob(f"KB-*-{year}-*.md"))
    nums = []
    for f in existing:
        m = re.search(rf'{year}-(\d+)', f.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def _generate_markdown(article: dict, kb_id: str) -> str:
    """生成KB条目的Markdown内容"""
    return f"""---
id: {kb_id}
domain: {article.get("domain", 1)}
source: {article.get("source_name", "")}
date: {article.get("publish_date", "")}
archived_at: {datetime.now().strftime("%Y-%m-%d %H:%M")}
priority: {article.get("priority", "P2")}
tags: {json.dumps(article.get("keywords", []), ensure_ascii=False)}
---

# {article.get("title", "未命名")}

## 核心要点
{article.get("core_point", "")}

## 适用场景
{article.get("applicable_scenario", "")}

## 摘要
{article.get("full_summary", "")}

## 原文链接
{article.get("url", "")}
"""
    return content


def archive(articles: list[dict], rag_root: Optional[str] = None) -> dict:
    """
    归档摘要后的文章

    Args:
        articles: 摘要后的文章列表
        rag_root: RAG根目录路径（默认使用项目 rag/ 目录）

    Returns:
        dict: {archived: int, skipped: int, kb_entries: list}
    """
    root = Path(rag_root or RAG_ROOT)
    current_year = datetime.now().year

    archived_count = 0
    skipped_count = 0
    kb_entries = []
    
    # 批次内计数器（修复：避免所有条目获得相同ID）
    batch_counters: dict[int, int] = {}

    for article in articles:
        domain = article.get("domain", 1)
        domain_dir_name = DOMAIN_DIRS.get(domain, "other")
        domain_dir = root / domain_dir_name
        domain_dir.mkdir(parents=True, exist_ok=True)

        # 检查URL是否已归档（简单的文件名检查）
        url_slug = _slugify(article.get("url", "").split("/")[-1])
        date_str = article.get("publish_date", "").split(" ")[0]
        filename = f"{date_str}_{url_slug}.md" if date_str else f"{url_slug}.md"

        filepath = domain_dir / filename
        if filepath.exists():
            logger.debug(f"跳过（已存在）: {filename}")
            skipped_count += 1
            continue

        # 生成KB ID（批次内递增）
        file_counter = _get_next_counter(domain_dir, current_year)
        if domain not in batch_counters:
            batch_counters[domain] = file_counter
        kb_id = _generate_kb_id(domain, current_year, batch_counters[domain])
        batch_counters[domain] += 1

        # 写文件
        content = _generate_markdown(article, kb_id)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        archived_count += 1
        kb_entries.append({
            "id": kb_id,
            "title": article.get("title", ""),
            "file": str(filepath.relative_to(root)),
            "domain": domain,
            "priority": article.get("priority", "P2"),
            "date": article.get("publish_date", ""),
            "source": article.get("source_name", ""),
            "keywords": article.get("keywords", []),
        })
        logger.info(f"归档 [{kb_id}] {article.get('title', '')[:50]}...")

    # 更新索引
    _update_index(root, kb_entries)

    logger.info(f"归档完成: 新增 {archived_count} 篇, 跳过 {skipped_count} 篇")
    return {
        "archived": archived_count,
        "skipped": skipped_count,
        "kb_entries": kb_entries
    }


def _update_index(root: Path, new_entries: list[dict]):
    """更新KB索引文件"""
    index_path = root / INDEX_FILE

    # 加载现有索引
    existing = {}
    if index_path.exists():
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, KeyError):
            existing = {}

    # 合并新条目
    existing_entries = existing.get("entries", [])
    existing_ids = {e["id"] for e in existing_entries}

    for entry in new_entries:
        if entry["id"] not in existing_ids:
            existing_entries.append(entry)
            existing_ids.add(entry["id"])

    # 按域和标签组织
    by_domain = {}
    by_tag = {}
    for entry in existing_entries:
        dom = entry.get("domain", 0)
        by_domain.setdefault(dom, []).append(entry["id"])
        for kw in entry.get("keywords", []):
            by_tag.setdefault(kw, []).append(entry["id"])

    index_data = {
        "updated_at": datetime.now().isoformat(),
        "total_entries": len(existing_entries),
        "entries": existing_entries,
        "by_domain": {str(k): v for k, v in by_domain.items()},
        "by_tag": by_tag,
    }

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    logger.info(f"索引已更新: {len(existing_entries)} 个条目")


# ============================================================
# CLI入口
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="归档器")
    parser.add_argument("--input", required=True, help="输入JSON文件路径（摘要结果）")
    parser.add_argument("--rag-root", help="RAG根目录（默认: rag/）")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    with open(args.input, "r", encoding="utf-8") as f:
        articles = json.load(f)

    result = archive(articles, rag_root=args.rag_root)
    print(f"\n归档完成: 新增 {result['archived']} 篇, 跳过 {result['skipped']} 篇")


if __name__ == "__main__":
    main()
