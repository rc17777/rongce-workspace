"""给 openclaw.json 加 session.reset 每日重置策略（带备份）"""
import json
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

CFG = r"C:\Users\scrccpa\.openclaw\openclaw.json"
BAK = r"C:\Users\scrccpa\.openclaw\openclaw.json.bak-sessionreset"

shutil.copy2(CFG, BAK)
cfg = json.load(open(CFG, encoding="utf-8"))

cfg["session"] = {
    "reset": {
        "mode": "daily",
        "atHour": 4,
    }
}

json.dump(cfg, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("OK - session.reset written, backup at", BAK)
