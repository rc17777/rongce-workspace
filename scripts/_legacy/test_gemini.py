"""单测 gemini-3.1-pro-preview 是否恢复"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

cfg = json.load(open(r"C:\Users\scrccpa\.openclaw\openclaw.json", encoding="utf-8"))
p = cfg["models"]["providers"]["custom-cbwyy-gemini"]
KEY = p["apiKey"]
BASE = p["baseUrl"].rstrip("/")

body = json.dumps({
    "model": "gemini-3.1-pro-preview",
    "messages": [{"role": "user", "content": "回复两个字：正常"}],
    "max_tokens": 20,
}).encode()

req = urllib.request.Request(BASE + "/chat/completions" if BASE.endswith("/v1") else BASE + "/v1/chat/completions",
                             data=body,
                             headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
        print("HTTP 200 OK")
        print("回复:", data["choices"][0]["message"]["content"][:100])
except Exception as e:
    print("FAILED:", repr(e)[:200])
    if hasattr(e, "read"):
        try:
            print("BODY:", e.read().decode()[:300])
        except Exception:
            pass
