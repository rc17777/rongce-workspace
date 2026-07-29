"""
主流水线
========
串行执行: collector → summarizer → archiver → lifecycle
支持域过滤、dry-run模式、自动日志记录。

用法:
    python -m tools.knowledge.pipeline --domain 1 --dry-run
    python -m tools.knowledge.pipeline --domain 2
    python -m tools.knowledge.pipeline  # 全量
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from .collector import Collector
from .summarizer import summarize
from .archiver import archive
from .lifecycle import run_lifecycle_check

# ============================================================
# 可配置参数
# ============================================================
LOG_DIR = str(Path(__file__).parent / "logs")
# ============================================================


def _setup_logging() -> str:
    """设置日志：同时输出到文件和控制台"""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"

    # 根日志配置
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 文件handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(fh)

    # 控制台handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return str(log_file)


def _serialize_articles(articles) -> list[dict]:
    """将采集/摘要对象序列化为dict列表"""
    result = []
    for a in articles:
        if hasattr(a, "__dict__"):
            d = {}
            for k, v in a.__dict__.items():
                if not k.startswith("_"):
                    d[k] = v
            result.append(d)
        elif isinstance(a, dict):
            result.append(a)
    return result


def run_pipeline(domain: Optional[int] = None,
                 dry_run: bool = False,
                 use_api: bool = False) -> dict:
    """
    执行完整知识流水线

    Args:
        domain: 指定域编号（1/2/3），None表示全部
        dry_run: 仅采集不归档
        use_api: 是否使用大模型API摘要

    Returns:
        dict: {collected, summarized, archived, warnings, conflicts, zombies}
    """
    log_file = _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"流水线启动 | domain={'ALL' if domain is None else domain} | "
                f"dry_run={dry_run} | use_api={use_api}")

    result = {
        "collected": 0,
        "summarized": 0,
        "archived": 0,
        "warnings": 0,
        "conflicts": 0,
        "zombies": 0,
        "log_file": log_file,
    }

    # ============================================================
    # 第1步: 采集
    # ============================================================
    logger.info("=" * 50)
    logger.info("第1步: 采集")
    logger.info("=" * 50)

    try:
        collector = Collector()
        raw_articles = collector.collect(domain=domain, dry_run=dry_run)
        result["collected"] = len(raw_articles)
        logger.info(f"采集完成: {len(raw_articles)} 篇")
    except Exception as e:
        logger.error(f"采集失败: {e}", exc_info=True)
        return result

    if not raw_articles:
        logger.info("无新文章，流水线结束。")
        return result

    # ============================================================
    # 第2步: 摘要
    # ============================================================
    logger.info("=" * 50)
    logger.info("第2步: 摘要")
    logger.info("=" * 50)

    try:
        raw_dicts = _serialize_articles(raw_articles)
        summarized = summarize(raw_dicts, use_api=use_api)
        result["summarized"] = len(summarized)
        logger.info(f"摘要完成: {len(summarized)} 篇")
    except Exception as e:
        logger.error(f"摘要失败: {e}", exc_info=True)
        return result

    # ============================================================
    # 第3步: 归档
    # ============================================================
    if not dry_run:
        logger.info("=" * 50)
        logger.info("第3步: 归档")
        logger.info("=" * 50)

        try:
            summarized_dicts = _serialize_articles(summarized)
            archive_result = archive(summarized_dicts)
            result["archived"] = archive_result.get("archived", 0)
            logger.info(f"归档完成: 新增 {result['archived']} 篇")

            # 准备新条目用于冲突检测
            new_entries_for_conflict = archive_result.get("kb_entries", [])
        except Exception as e:
            logger.error(f"归档失败: {e}", exc_info=True)
            new_entries_for_conflict = []
    else:
        logger.info("第3步: 归档（dry-run模式，跳过）")
        new_entries_for_conflict = []

    # ============================================================
    # 第4步: 生命周期管理
    # ============================================================
    if not dry_run:
        logger.info("=" * 50)
        logger.info("第4步: 生命周期管理")
        logger.info("=" * 50)

        try:
            lc_result = run_lifecycle_check(new_entries=new_entries_for_conflict or None)
            result["warnings"] = len(lc_result.get("warnings", []))
            result["conflicts"] = len(lc_result.get("conflicts", []))
            result["zombies"] = len(lc_result.get("zombies", []))
            logger.info(f"生命周期报告: {lc_result.get('report_path', 'N/A')}")
        except Exception as e:
            logger.error(f"生命周期检查失败: {e}", exc_info=True)
    else:
        logger.info("第4步: 生命周期管理（dry-run模式，跳过）")

    # ============================================================
    # 完成
    # ============================================================
    logger.info("=" * 50)
    logger.info(f"流水线完成 | 采集 {result['collected']} | 摘要 {result['summarized']} | "
                f"归档 {result['archived']}")
    if not dry_run:
        logger.info(f"生命周期 | 警告 {result['warnings']} | 冲突 {result['conflicts']} | "
                    f"僵尸 {result['zombies']}")
    logger.info(f"日志文件: {log_file}")

    return result


# ============================================================
# CLI入口
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="知识流水线")
    parser.add_argument("--domain", type=int, choices=[1, 2, 3], help="指定域编号")
    parser.add_argument("--dry-run", action="store_true", help="仅采集不归档")
    parser.add_argument("--use-api", action="store_true", help="使用大模型API摘要")
    args = parser.parse_args()

    result = run_pipeline(
        domain=args.domain,
        dry_run=args.dry_run,
        use_api=args.use_api
    )

    print(f"\n{'='*50}")
    print(f"流水线结果:")
    print(f"  采集: {result['collected']} 篇")
    print(f"  摘要: {result['summarized']} 篇")
    print(f"  归档: {result['archived']} 篇")
    print(f"  日志: {result['log_file']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
