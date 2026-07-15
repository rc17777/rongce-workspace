#!/usr/bin/env python3
"""
模型健康检查脚本 v1.0
用法: python scripts/model_health_check.py [--json] [--alert]
- 每日运行一次，13模型逐一 ping
- 支持 JSON 输出供监控系统读取
- 支持 --alert 模式：仅输出异常
"""

import json
import sys
import time
from datetime import datetime
import urllib.request
import urllib.error

# 绕过系统代理——OpenClaw Gateway 自身不经过 Python 代理
PROXY_HANDLER = urllib.request.ProxyHandler({})
OPENER = urllib.request.build_opener(PROXY_HANDLER)

# 13模型配置
MODELS = {
    "deepseek-v4-flash": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-Bq4EalSwLmehZ3xXa55b7TzRX4HIlbTppgdKQ0ElOab09AZa",
        "api": "openai",
        "category": "free"
    },
    "deepseek-v4-pro": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-Bq4EalSwLmehZ3xXa55b7TzRX4HIlbTppgdKQ0ElOab09AZa",
        "api": "openai",
        "category": "low"
    },
    "qwen3.7-plus": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-9Jwqw4U5ahchjaLgVqzvfJQvm3itJEv2GHTV8KAofagQrf77",
        "api": "openai",
        "category": "low"
    },
    "claude-fable-5": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-V3KPfTqMi3x13gtbftyVH94pAA9YOLQXYAVElYV9WRabYDzh",
        "api": "openai",
        "category": "low"
    },
    "claude-sonnet-5": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-R0ndBzSRNP6GWAW82HspfjwKxJvPwBeoHPrkznz8rjCNL3SH",
        "api": "openai",
        "category": "medium"
    },
    "claude-opus-4-8": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-1rL8MpWIH16CZ64xZLV6buNHS7dlmIdBk5HGOYs5hV0nOHcJ",
        "api": "openai",
        "category": "high"
    },
    "gpt-5.5": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU",
        "api": "openai",
        "category": "medium"
    },
    "gpt-5.6-luna": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-p3ynqetGeLU5T5TpzXFAFimCaTrvIT6kpqGkbP2SrpqvpbrJ",
        "api": "openai",
        "category": "medium"
    },
    "gpt-5.6-sol": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-eulyTfe7nRmr5ruwQH85kIfHkc8PPd88EoYGX0yadzlrkEpv",
        "api": "openai",
        "category": "medium"
    },
    "gpt-5.6-terra": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-9qOvtLFgtvohPegNNGiwPr7fye1SgSCIW1C2viiKFp1b8lzh",
        "api": "openai",
        "category": "medium"
    },
    "gemini-3.1-pro-preview": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-dxNjrEh4rXIinsnHVLAKE17e1yqf6XFhtWZuPrnyzg5lfISw",
        "api": "openai",
        "category": "preview"
    },
    "gpt-image-2": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-KVp2E6u9FnnRA3BQxSNvbWKW6zd2JsDQa8YlmR4ZxGtVsXIQ",
        "api": "openai",
        "category": "special"
    },
    "doubao-seed-2.0-lite": {
        "url": "https://cbwyy.top/v1/chat/completions",
        "key": "sk-8Up5r8WtFOQrckhQCxOxaRYES5KAWQqgKMdrJng1l0DJ9gix",
        "api": "openai",
        "category": "low"
    }
}

CHECK_MSG = [{"role": "user", "content": "reply OK"}]
ANTHROPIC_MSG = {"model": "claude-fable-5", "messages": CHECK_MSG, "max_tokens": 5}


def check_openai(model_id: str, cfg: dict) -> dict:
    payload = {"model": model_id, "messages": CHECK_MSG, "max_tokens": 5}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(cfg["url"], data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg['key']}"})
    try:
        with OPENER.open(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
            ok = "choices" in body and len(body["choices"]) > 0
            return {"status": "ok" if ok else "error", "code": resp.status, "msg": body.get("choices", [{}])[0].get("message", {}).get("content", "")[:20]}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        return {"status": "error", "code": e.code, "msg": body}
    except Exception as e:
        return {"status": "error", "code": 0, "msg": str(e)[:200]}


def check_anthropic(model_id: str, cfg: dict) -> dict:
    """Anthropic API uses different endpoint format"""
    payload = {"model": model_id, "messages": CHECK_MSG, "max_tokens": 5}
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": cfg["key"],
        "anthropic-version": "2023-06-01"
    }
    req = urllib.request.Request(cfg["url"], data=data, headers=headers)
    try:
        with OPENER.open(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
            ok = "content" in body and len(body.get("content", [])) > 0
            return {"status": "ok" if ok else "error", "code": resp.status, "msg": str(body.get("content", [{}])[0].get("text", ""))[:20]}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        return {"status": "error", "code": e.code, "msg": body}
    except Exception as e:
        return {"status": "error", "code": 0, "msg": str(e)[:200]}


def main():
    json_mode = "--json" in sys.argv
    alert_mode = "--alert" in sys.argv

    results = []
    ok_count = 0
    error_count = 0
    fatal_alerts = []

    if not json_mode:
        print(f"🔍 模型健康检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    for model_id, cfg in MODELS.items():
        start = time.time()
        if cfg["api"] == "anthropic":
            result = check_anthropic(model_id, cfg)
        else:
            result = check_openai(model_id, cfg)
        elapsed = time.time() - start

        result["model"] = model_id
        result["category"] = cfg["category"]
        result["elapsed"] = round(elapsed, 2)

        if result["status"] == "ok":
            ok_count += 1
        else:
            error_count += 1
            if cfg["category"] in ("high", "medium"):
                fatal_alerts.append(model_id)

        results.append(result)
        status_icon = "✅" if result["status"] == "ok" else "❌"

        if not json_mode:
            print(f"  {status_icon} {model_id:30s} {result['code']:>4}  {elapsed:.2f}s  [{cfg['category']}]")

    # 代理故障检测
    all_errors = error_count > 0
    proxy_down = error_count >= 10  # 几乎所有模型都失败 = 代理挂了
    only_gemini_down = error_count == 1 and "gemini-3.1-pro-preview" in [r["model"] for r in results if r["status"] != "ok"]

    if not json_mode:
        print("=" * 60)
        print(f"  ✅ {ok_count} | ❌ {error_count} | 总计 {len(results)}")
        if proxy_down:
            print("🔴 致命：疑似 cbwyy.top 代理全面故障！所有模型不可用！")
        elif all_errors:
            print(f"🟡 部分故障：{error_count} 个模型异常")
        if only_gemini_down:
            print("🟡 gemini 预览版不可用，长文档层降级到 sonnet 分段读")
        print("=" * 60)

    if json_mode:
        output = {
            "timestamp": datetime.now().isoformat(),
            "ok": ok_count,
            "error": error_count,
            "total": len(results),
            "proxy_down": proxy_down,
            "fatal_alerts": fatal_alerts,
            "results": results
        }
        print(json.dumps(output, ensure_ascii=False))

    if alert_mode:
        if proxy_down:
            print("ALERT:PROXY_DOWN", end="")
        elif error_count > 0:
            print(f"ALERT:{error_count}_MODELS_DOWN:{','.join(fatal_alerts)}", end="")

    sys.exit(2 if proxy_down else (1 if error_count > 0 else 0))


if __name__ == "__main__":
    main()
