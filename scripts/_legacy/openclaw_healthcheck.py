#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Health check the OpenClaw default model chain.

The script is intentionally small and read-only: it reads ~/.openclaw/openclaw.json,
pings the configured primary model and fallbacks, then appends one JSONL record to
logs/openclaw_healthcheck.jsonl. It never prints or stores API keys.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

TZ = timezone(timedelta(hours=8))
WORKSPACE = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
LOG_PATH = WORKSPACE / "logs" / "openclaw_healthcheck.jsonl"


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def model_chain(config: dict[str, Any]) -> list[str]:
    model_cfg = config.get("agents", {}).get("defaults", {}).get("model", {})
    primary = model_cfg.get("primary")
    fallbacks = model_cfg.get("fallbacks", []) or []
    chain = [primary, *fallbacks]
    return [m for m in chain if isinstance(m, str) and "/" in m]


def split_model(ref: str) -> tuple[str, str]:
    provider, model = ref.split("/", 1)
    return provider, model


def request_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(400).decode("utf-8", errors="replace")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        detail = e.read(400).decode("utf-8", errors="replace")
        return e.code, detail
    except Exception as e:  # healthcheck should classify every failure
        return 0, f"{type(e).__name__}: {e}"


def ping_model(ref: str, provider_cfg: dict[str, Any], timeout: int) -> dict[str, Any]:
    provider, model = split_model(ref)
    api_type = provider_cfg.get("api", "")
    base_url = str(provider_cfg.get("baseUrl", "")).rstrip("/")
    api_key = str(provider_cfg.get("apiKey", ""))
    started = time.perf_counter()

    result: dict[str, Any] = {
        "model": ref,
        "provider": provider,
        "api": api_type,
        "ok": False,
        "status": None,
        "latency_ms": None,
        "error": None,
    }

    if not base_url or not api_key:
        result["error"] = "missing baseUrl or apiKey"
        return result

    if api_type == "openai-completions":
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
            "stream": False,
        }
    elif api_type == "anthropic-messages":
        url = f"{base_url}/v1/messages" if not base_url.endswith("/v1") else f"{base_url}/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        }
    else:
        result["error"] = f"unsupported api type: {api_type}"
        return result

    status, detail = request_json(url, headers, payload, timeout)
    result["latency_ms"] = round((time.perf_counter() - started) * 1000)
    result["status"] = status
    if 200 <= status < 300:
        result["ok"] = True
    else:
        result["error"] = detail[:300]
    return result


def run(timeout: int) -> dict[str, Any]:
    config = load_config()
    providers = config.get("models", {}).get("providers", {})
    chain = model_chain(config)
    results = []

    for ref in chain:
        provider, _ = split_model(ref)
        provider_cfg = providers.get(provider)
        if not isinstance(provider_cfg, dict):
            results.append({
                "model": ref,
                "provider": provider,
                "ok": False,
                "status": None,
                "latency_ms": None,
                "error": "provider not found in openclaw.json",
            })
            continue
        results.append(ping_model(ref, provider_cfg, timeout))

    primary_ok = bool(results and results[0].get("ok"))
    any_ok = any(r.get("ok") for r in results)
    all_ok = bool(results) and all(r.get("ok") for r in results)
    status = "ok" if all_ok else "degraded" if any_ok else "failed"

    return {
        "time": now_iso(),
        "config": str(CONFIG_PATH),
        "chain": chain,
        "status": status,
        "primary_ok": primary_ok,
        "any_ok": any_ok,
        "results": results,
    }


def append_log(report: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")


def print_markdown(report: dict[str, Any]) -> None:
    print(f"## OpenClaw 模型链健康检查 — {report['time']}")
    print("")
    print(f"状态: {report['status'].upper()}")
    print(f"配置: `{report['config']}`")
    print("")
    print("| 模型 | 状态 | HTTP | 延迟(ms) | 说明 |")
    print("|---|---:|---:|---:|---|")
    for item in report["results"]:
        ok = "OK" if item.get("ok") else "FAIL"
        status = item.get("status") if item.get("status") is not None else ""
        latency = item.get("latency_ms") if item.get("latency_ms") is not None else ""
        error = (item.get("error") or "").replace("\n", " ").replace("|", "/")
        print(f"| `{item.get('model')}` | {ok} | {status} | {latency} | {error[:120]} |")
    print("")
    print(f"日志: `{LOG_PATH}`")


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenClaw default model chain healthcheck")
    parser.add_argument("--timeout", type=int, default=20, help="per-model timeout seconds")
    parser.add_argument("--json", action="store_true", help="print compact JSON instead of markdown")
    parser.add_argument("--quiet-ok", action="store_true", help="print HEALTHCHECK_OK only when all models pass")
    args = parser.parse_args()

    try:
        report = run(timeout=args.timeout)
    except Exception as e:
        report = {
            "time": now_iso(),
            "config": str(CONFIG_PATH),
            "chain": [],
            "status": "failed",
            "primary_ok": False,
            "any_ok": False,
            "results": [{"model": "config", "ok": False, "error": f"{type(e).__name__}: {e}"}],
        }

    append_log(report)

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    elif args.quiet_ok and report["status"] == "ok":
        print("HEALTHCHECK_OK")
    else:
        print_markdown(report)

    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
