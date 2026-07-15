"""恢复 gemini-3.1-pro-preview 到默认降级链原位（第3位，pro之后qwen之前）"""
import json
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

CFG = r"C:\Users\scrccpa\.openclaw\openclaw.json"
BAK = r"C:\Users\scrccpa\.openclaw\openclaw.json.bak-gemini-restore"

shutil.copy2(CFG, BAK)
cfg = json.load(open(CFG, encoding="utf-8"))

model = cfg["agents"]["defaults"]["model"]
fb = model.get("fallbacks", [])
GEM = "custom-cbwyy-gemini/gemini-3.1-pro-preview"

if GEM in fb:
    print("已在链中，无需恢复")
else:
    # 插到 deepseek-v4-pro 之后（原位第3）
    anchor = "custom-cbwyy-top-v1/deepseek-v4-pro"
    if anchor in fb:
        fb.insert(fb.index(anchor) + 1, GEM)
    else:
        fb.insert(0, GEM)
    model["fallbacks"] = fb
    json.dump(cfg, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("已恢复，当前降级链:")
    for i, m in enumerate(fb, 1):
        print(f"  {i}. {m}")
