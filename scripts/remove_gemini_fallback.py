"""从默认降级链移除无权限的 gemini-3.1-pro-preview（带备份）"""
import json
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

CFG = r"C:\Users\scrccpa\.openclaw\openclaw.json"
BAK = r"C:\Users\scrccpa\.openclaw\openclaw.json.bak-gemini403"

shutil.copy2(CFG, BAK)
cfg = json.load(open(CFG, encoding="utf-8"))

model = cfg["agents"]["defaults"]["model"]
before = model.get("fallbacks", [])
after = [m for m in before if "gemini" not in m]
model["fallbacks"] = after

json.dump(cfg, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("移除前:", len(before), "个 fallback")
print("移除后:", len(after), "个 fallback")
print("已移除:", [m for m in before if m not in after])
print("备份:", BAK)
