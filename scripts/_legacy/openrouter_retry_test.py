#!/usr/bin/env python3
"""重试第一轮失败的免费模型，加大间隔"""
import json
import os
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"
REPORT_PATH = Path(__file__).parent.parent / "output" / "openrouter_model_test.json"

def load_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        key = cfg.get("env", {}).get("vars", {}).get("OPENROUTER_API_KEY", "")
        if key and "REDACTED" not in key:
            return key
    return ""

def test_model(model_id: str, api_key: str, timeout: int = 45) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openclaw.ai",
        "X-Title": "OpenClaw Model Retest",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Say just 'OK'."}],
        "max_tokens": 5,
        "temperature": 0,
    }
    start = time.time()
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
        elapsed = round((time.time() - start) * 1000)
        if resp.status_code == 200:
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            reply = msg.get("content") or ""
            if isinstance(reply, str):
                reply = reply.strip()
            refusal = msg.get("refusal", "")
            finish = choice.get("finish_reason", "")
            if refusal:
                return {"id": model_id, "status": "refused", "error": f"拒绝: {refusal[:100]}", "latency_ms": elapsed}
            if not reply and finish != "stop":
                return {"id": model_id, "status": "empty", "error": f"空响应(finish={finish})", "latency_ms": elapsed}
            return {"id": model_id, "status": "ok", "latency_ms": elapsed, "reply": reply[:80]}
        elif resp.status_code == 429:
            return {"id": model_id, "status": "rate_limited", "error": "429", "latency_ms": elapsed}
        else:
            err = ""
            try:
                err = resp.json().get("error", {}).get("message", resp.text[:200])
            except:
                err = resp.text[:200]
            return {"id": model_id, "status": "error", "error": f"{resp.status_code} {err}", "latency_ms": elapsed}
    except requests.Timeout:
        return {"id": model_id, "status": "timeout", "error": "超时", "latency_ms": timeout*1000}
    except Exception as e:
        return {"id": model_id, "status": "error", "error": str(e)[:200], "latency_ms": round((time.time()-start)*1000)}

def main():
    api_key = load_api_key()
    if not api_key:
        print("❌ 无 API Key")
        sys.exit(1)
    
    if not REPORT_PATH.exists():
        print("❌ 无第一轮报告")
        sys.exit(1)
    
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    results = report.get("results", [])
    
    # 找出需要重试的：rate_limited 和 error (NoneType)
    to_retry = [r for r in results if r["status"] in ("rate_limited", "error") 
                and r.get("error") and "429" not in str(r.get("error", ""))]
    to_retry += [r for r in results if r["status"] == "rate_limited"]
    # 去重
    seen = set()
    unique = []
    for r in to_retry:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)
    to_retry = unique
    
    if not to_retry:
        print("没有需要重试的模型")
        return
    
    print(f"🔄 重试 {len(to_retry)} 个模型 (间隔2秒)")
    print("=" * 70)
    
    retry_results = []
    ok_count = 0
    
    for i, item in enumerate(to_retry, 1):
        mid = item["id"]
        print(f"[{i:2d}/{len(to_retry)}] {mid:<55} ", end="", flush=True)
        time.sleep(2)
        
        r = test_model(mid, api_key)
        retry_results.append(r)
        
        if r["status"] == "ok":
            ok_count += 1
            print(f"✅ {r['latency_ms']}ms | {r.get('reply', '')[:60]}")
        else:
            print(f"❌ [{r['status']}] {r.get('error', '')[:80]}")
    
    print()
    print("=" * 70)
    print(f"📊 重试结果: {len(to_retry)}→{ok_count}个可用")
    
    for r in retry_results:
        if r["status"] == "ok":
            print(f"  ✅ {r['id']:<55} {r['latency_ms']}ms")

if __name__ == "__main__":
    main()
