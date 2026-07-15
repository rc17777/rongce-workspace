"""解析 gateway 日志，找掉线/重启事件"""
import json
import sys, re
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

log = r"C:\Users\scrccpa\AppData\Local\Temp\openclaw\openclaw-2026-07-15.log"
events = []
for line in open(log, encoding="utf-8"):
    try:
        d = json.loads(line.strip())
    except:
        continue
    msg = d.get("message", "")
    t = d.get("time", "")
    level = d.get("_meta", {}).get("logLevelName", "")
    if any(k in msg for k in ["protocol mismatch", "disconnect", "restart", "SIGUSR1", "shutdown", "crash", "uncaught", "pairing"]):
        events.append((t, level, msg[:180]))
    elif level == "ERROR":
        events.append((t, "ERROR", msg[:180]))

for t, lv, msg in events[-30:]:
    print(f"[{lv}] {t} {msg}")
