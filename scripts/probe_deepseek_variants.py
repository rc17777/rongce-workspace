#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick probe: test the two model id variants the user suggested against cbwyy.top/v1."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
prov = config["models"]["providers"]["custom-cbwyy-top-v1"]
base = prov["baseUrl"].rstrip("/")
key = prov["apiKey"]

candidates = [
    "deepseek-v4-flash.custom-cbwyy-top-v1",
    "deepseek-v4-pro.custom-cbwyy-top-v1",
    "custom-cbwyy-top-v1/deepseek-v4-flash",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "deepseek-chat",
    "deepseek-reasoner",
]

for model in candidates:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
        "temperature": 0,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"[OK ] {model} -> HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        detail = e.read(200).decode("utf-8", errors="replace").replace("\n", " ")
        print(f"[FAIL] {model} -> HTTP {e.code} {detail[:160]}")
    except Exception as e:
        print(f"[ERR ] {model} -> {type(e).__name__}: {e}")

# also list what models the token can actually see
try:
    req = urllib.request.Request(f"{base}/models", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    ids = [m.get("id") for m in data.get("data", [])]
    print("\n== token 可见模型列表 ==")
    for i in ids:
        print(f"  - {i}")
except Exception as e:
    print(f"\n[models list ERR] {type(e).__name__}: {e}")
