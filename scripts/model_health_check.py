#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test all 11 model providers with a minimal API call."""
import os, sys, io, json, time, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Provider configs (matching openclaw.json)
PROVIDERS = {
    "custom-cbwyy-top-v1": {
        "env_key": "OC_KEY_TOP_V1",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["deepseek-v4-flash", "deepseek-v4-pro"]
    },
    "custom-cbwyy-qwen": {
        "env_key": "OC_KEY_QWEN",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["qwen3.7-plus"]
    },
    "custom-cbwyy-gpt55": {
        "env_key": "OC_KEY_GPT55",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["gpt-5.5"]
    },
    "custom-cbwyy-luna": {
        "env_key": "OC_KEY_LUNA",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["gpt-5.6-luna"]
    },
    "custom-cbwyy-sol": {
        "env_key": "OC_KEY_SOL",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["gpt-5.6-sol"]
    },
    "custom-cbwyy-terra": {
        "env_key": "OC_KEY_TERRA",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["gpt-5.6-terra"]
    },
    "custom-cbwyy-claude": {
        "env_key": "OC_KEY_CLAUDE",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["claude-sonnet-5"]
    },
    "custom-cbwyy-fable": {
        "env_key": "OC_KEY_FABLE",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["claude-fable-5"]
    },
    "custom-cbwyy-opus": {
        "env_key": "OC_KEY_OPUS",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["claude-opus-4-8"]
    },
    "custom-cbwyy-doubao": {
        "env_key": "OC_KEY_DOUBAO",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["doubao-seed-2.0-lite"]
    },
    "custom-cbwyy-image": {
        "env_key": "OC_KEY_IMAGE",
        "base_url": "https://cbwyy.top/v1",
        "api_type": "openai",
        "test_models": ["gpt-image-2"]
    },
}

TEST_PROMPT = "Reply with exactly one word: OK"

def test_openai(api_key, base_url, model):
    """Test OpenAI-compatible API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "max_tokens": 10
    }
    try:
        r = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return True, f"OK [{content.strip()[:30]}] (in:{usage.get('prompt_tokens','?')} out:{usage.get('completion_tokens','?')})"
        else:
            msg = r.text[:200]
            return False, f"HTTP {r.status_code}: {msg}"
    except requests.Timeout:
        return False, "TIMEOUT (30s)"
    except Exception as e:
        return False, f"ERROR: {str(e)[:100]}"

def test_anthropic(api_key, base_url, model):
    """Test Anthropic Messages API."""
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    payload = {
        "model": model,
        "max_tokens": 10,
        "messages": [{"role": "user", "content": TEST_PROMPT}]
    }
    # Try /v1/messages first, then /messages
    urls = [f"{base_url}/v1/messages", f"{base_url}/messages"]
    last_error = None
    for url in urls:
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})
                return True, f"OK [{content.strip()[:30]}] (in:{usage.get('input_tokens','?')} out:{usage.get('output_tokens','?')})"
            else:
                last_error = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.Timeout:
            last_error = "TIMEOUT (30s)"
        except Exception as e:
            last_error = f"ERROR({url}): {str(e)[:100]}"
    return False, last_error or "All endpoints failed"

print("=" * 70)
print("MODEL CONNECTIVITY TEST")
print("=" * 70)

results = []
for prov_name, prov_cfg in PROVIDERS.items():
    env_key = prov_cfg["env_key"]
    api_key = os.environ.get(env_key, "")
    
    if not api_key:
        print(f"\n  {prov_name}")
        print(f"    ❌ API KEY NOT SET (env var {env_key})")
        for model in prov_cfg["test_models"]:
            results.append((f"{prov_name}/{model}", "❌", "API Key not configured"))
        continue
    
    key_preview = api_key[:12] + "..."
    
    for model in prov_cfg["test_models"]:
        label = f"{prov_name}/{model}"
        sys.stdout.write(f"\n  Testing {label}... ")
        sys.stdout.flush()
        
        if prov_cfg["api_type"] == "openai":
            ok, detail = test_openai(api_key, prov_cfg["base_url"], model)
        else:
            ok, detail = test_anthropic(api_key, prov_cfg["base_url"], model)
        
        status = "✅" if ok else "❌"
        print(f"{status} {detail}")
        results.append((label, status, detail))
        
        time.sleep(0.5)  # Brief pause between calls

print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
pass_count = sum(1 for _, s, _ in results if s == "✅")
fail_count = sum(1 for _, s, _ in results if s == "❌")
print(f"  Total: {len(results)} models tested")
print(f"  Pass:  {pass_count} ✅")
print(f"  Fail:  {fail_count} ❌")

if fail_count > 0:
    print(f"\n  Failed models:")
    for label, status, detail in results:
        if status == "❌":
            print(f"    {label}: {detail}")
