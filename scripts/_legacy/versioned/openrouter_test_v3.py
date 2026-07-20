#!/usr/bin/env python3
"""第三轮：针对性重测——reasoning模型加大token，rate-limited加长间隔"""
import json, os, sys, time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"

def load_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key: return key
    cfg_path = Path.home() / ".openclaw" / "openclaw.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        key = cfg.get("env", {}).get("vars", {}).get("OPENROUTER_API_KEY", "")
        if key and "REDACTED" not in key: return key
    return ""

def test(model_id, api_key, max_tokens=50, timeout=60):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openclaw.ai",
        "X-Title": "OpenClaw Model Test v3",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Say just 'OK'."}],
        "max_tokens": max_tokens,
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
            if isinstance(reply, str): reply = reply.strip()
            if reply: return {"status": "ok", "latency_ms": elapsed, "reply": reply[:100]}
            return {"status": "empty", "error": f"finish={choice.get('finish_reason','?')}", "latency_ms": elapsed}
        elif resp.status_code == 429:
            return {"status": "rate_limited", "error": "429", "latency_ms": elapsed}
        else:
            err = resp.text[:300]
            try: err = resp.json().get("error", {}).get("message", err)
            except: pass
            return {"status": "error", "error": f"{resp.status_code} {err}", "latency_ms": elapsed}
    except Exception as e:
        return {"status": "error", "error": str(e)[:200], "latency_ms": round((time.time()-start)*1000)}

def main():
    api_key = load_api_key()
    if not api_key: print("no key"); sys.exit(1)
    
    # Round A: empty-reasoning models — boost max_tokens to 200
    reasoning_models = [
        "liquid/lfm-2.5-1.2b-thinking:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "nvidia/nemotron-3.5-content-safety:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "poolside/laguna-xs.2:free",
        "poolside/laguna-m.1:free",
        "openrouter/owl-alpha",
    ]
    
    print("🔬 Round A: reasoning/empty models (max_tokens=200)")
    print("=" * 70)
    for mid in reasoning_models:
        print(f"  {mid:<55} ", end="", flush=True)
        time.sleep(1)
        r = test(mid, api_key, max_tokens=200)
        emoji = "✅" if r["status"] == "ok" else "❌"
        print(f"{emoji} {r['status']} {r.get('reply', '')[:60]}")
    
    # Round B: rate-limited popular models — wait 15s each
    rate_limited = [
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "google/gemma-4-26b-a4b-it:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "moonshotai/kimi-k2.6:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "qwen/qwen3-coder:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
    ]
    
    print("\n🔬 Round B: rate-limited models (间隔15秒)")
    print("=" * 70)
    for mid in rate_limited:
        print(f"  {mid:<55} ", end="", flush=True)
        time.sleep(15)
        r = test(mid, api_key)
        emoji = "✅" if r["status"] == "ok" else "❌"
        print(f"{emoji} {r['status']} {r.get('reply', '')[:60]}")

if __name__ == "__main__":
    main()
