"""
调度器
======
按 sources.yaml 配置的频率，定时触发采集流水线。
支持单次运行和守护进程模式。

用法:
    python -m tools.knowledge.scheduler --once
    python -m tools.knowledge.scheduler --daemon
"""

import json
import logging
import signal
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import yaml

from .pipeline import run_pipeline

logger = logging.getLogger(__name__)

# ============================================================
# 可配置参数
# ============================================================
STATE_FILE = str(Path(__file__).parent / "logs" / "scheduler_state.json")
CHECK_INTERVAL_SECONDS = 600          # 检查间隔（10分钟）
FREQUENCY_MAP = {                     # 频率→秒
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
}
# ============================================================

_shutdown_requested = False


def _load_sources(sources_path: str = None) -> dict:
    """加载采集源配置"""
    if sources_path is None:
        sources_path = str(Path(__file__).parent / "sources.yaml")
    with open(sources_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_state() -> dict:
    """加载上次运行状态"""
    sp = Path(STATE_FILE)
    if sp.exists():
        try:
            with open(sp, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass
    return {"last_runs": {}, "pipeline_runs": []}


def _save_state(state: dict):
    """保存运行状态"""
    sp = Path(STATE_FILE)
    sp.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now().isoformat()
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _is_due(source_name: str, frequency: str, last_run: Optional[str]) -> bool:
    """检查采集源是否到达触发时间"""
    freq_seconds = FREQUENCY_MAP.get(frequency, FREQUENCY_MAP["daily"])

    if not last_run:
        return True

    try:
        last_dt = datetime.fromisoformat(last_run)
        elapsed = (datetime.now() - last_dt).total_seconds()
        return elapsed >= freq_seconds
    except (ValueError, TypeError):
        return True


def run_once(domain: Optional[int] = None, dry_run: bool = False) -> dict:
    """执行一轮采集"""
    logger.info(f"执行单轮采集 | domain={'ALL' if domain is None else domain}")
    result = run_pipeline(domain=domain, dry_run=dry_run)

    # 更新状态
    state = _load_state()
    state["pipeline_runs"].append({
        "timestamp": datetime.now().isoformat(),
        "domain": domain,
        "result": {k: v for k, v in result.items() if k != "log_file"}
    })
    # 保留最近100次运行记录
    if len(state["pipeline_runs"]) > 100:
        state["pipeline_runs"] = state["pipeline_runs"][-100:]

    _save_state(state)
    return result


def run_daemon(domain: Optional[int] = None) -> None:
    """守护进程模式：按频率循环触发"""
    logger.info(f"守护进程启动 | 检查间隔: {CHECK_INTERVAL_SECONDS}s | domain={'ALL' if domain is None else domain}")

    # 信号处理
    def _sig_handler(signum, frame):
        global _shutdown_requested
        logger.info(f"收到信号 {signum}，正在优雅退出...")
        _shutdown_requested = True

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    # 加载采集源
    sources_config = _load_sources()

    while not _shutdown_requested:
        state = _load_state()
        last_runs = state.get("last_runs", {})

        # 收集到期源
        due_sources = []
        for domain_key, source_list in sources_config.get("sources", {}).items():
            try:
                dom_id = int(domain_key.split("_")[1])
            except (IndexError, ValueError):
                continue

            if domain is not None and dom_id != domain:
                continue

            for source in source_list:
                source_name = source["name"]
                frequency = source.get("frequency", "daily")
                last_run = last_runs.get(source_name)

                if _is_due(source_name, frequency, last_run):
                    due_sources.append((dom_id, source))

        if due_sources:
            logger.info(f"到期源: {len(due_sources)} 个，开始采集...")

            for dom_id, source in due_sources:
                if _shutdown_requested:
                    break
                logger.info(f"  采集: [{source['name']}] (域{dom_id})")

            # 执行流水线
            try:
                result = run_pipeline(domain=domain)
                logger.info(f"  完成: 采集 {result['collected']} 篇")

                # 更新各源的上次运行时间
                now = datetime.now().isoformat()
                for _, src in due_sources:
                    last_runs[src["name"]] = now
                state["last_runs"] = last_runs
                _save_state(state)

            except Exception as e:
                logger.error(f"流水线执行失败: {e}", exc_info=True)
        else:
            logger.debug("无到期源")

        # 等待下次检查
        if not _shutdown_requested:
            time.sleep(CHECK_INTERVAL_SECONDS)

    logger.info("守护进程已退出。")


# ============================================================
# CLI入口
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="调度器")
    parser.add_argument("--once", action="store_true", help="只运行一轮")
    parser.add_argument("--daemon", action="store_true", help="守护进程模式（持续运行）")
    parser.add_argument("--domain", type=int, choices=[1, 2, 3], help="指定域编号")
    parser.add_argument("--dry-run", action="store_true", help="仅采集不归档")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(Path(__file__).parent / "logs" / "scheduler.log", encoding="utf-8")
        ]
    )

    if args.once or not args.daemon:
        # 默认行为：单次运行
        result = run_once(domain=args.domain, dry_run=args.dry_run)
        print(f"\n调度完成:")
        print(f"  采集: {result['collected']} | 摘要: {result['summarized']} | 归档: {result['archived']}")
    elif args.daemon:
        run_daemon(domain=args.domain)


if __name__ == "__main__":
    main()
