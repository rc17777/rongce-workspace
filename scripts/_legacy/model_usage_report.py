import json, sys, io, os, glob
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sessions_dir = r"C:\Users\scrccpa\.openclaw\agents\main\sessions"
files = sorted(glob.glob(os.path.join(sessions_dir, "*.jsonl")), key=os.path.getmtime, reverse=True)

model_stats = defaultdict(lambda: {
    "calls": 0, "input_tokens": 0, "output_tokens": 0,
    "cache_read": 0, "cache_write": 0, "cost": 0.0,
    "errors": 0, "sessions": set()
})

session_models = defaultdict(lambda: {"model": None, "provider": None, "calls": 0})

for fpath in files[:30]:
    fname = os.path.basename(fpath)
    with open(fpath, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except:
                continue
            
            t = obj.get("type", "")
            
            # Track model changes
            if t == "model_change":
                session_models[obj.get("id", "")] = {
                    "model": obj.get("modelId", "?"),
                    "provider": obj.get("provider", "?"),
                    "calls": 0
                }
            
            # Track completions
            if t in ("completion", "assistant"):
                usage = obj.get("usage")
                if not usage:
                    continue
                
                provider = obj.get("provider", "unknown")
                model = obj.get("model", obj.get("modelId", "unknown"))
                model_id = f"{provider}/{model}"
                
                stats = model_stats[model_id]
                stats["calls"] += 1
                stats["input_tokens"] += usage.get("input", 0) or 0
                stats["output_tokens"] += usage.get("output", 0) or 0
                stats["cache_read"] += usage.get("cacheRead", 0) or 0
                stats["cache_write"] += usage.get("cacheWrite", 0) or 0
                stats["sessions"].add(fname)
                
                c = usage.get("cost", {}) or {}
                stats["cost"] += c.get("total", 0) or 0
                
                stop = obj.get("stopReason", "")
                if stop and "error" in str(stop).lower():
                    stats["errors"] += 1

print("=" * 80)
print("MODEL USAGE REPORT (last 30 sessions)")
print("=" * 80)

grand = {"calls": 0, "input": 0, "output": 0, "cache": 0, "cost": 0}

for mid in sorted(model_stats.keys(), key=lambda m: -model_stats[m]["calls"]):
    s = model_stats[mid]
    if s["calls"] == 0:
        continue
    total = s["input_tokens"] + s["output_tokens"]
    cache_pct = s["cache_read"] / max(s["input_tokens"], 1) * 100
    print(f"\n  [Provider/Model] {mid}")
    print(f"    Calls:         {s['calls']:>6}")
    print(f"    Input:         {s['input_tokens']:>10,} tokens")
    print(f"    Output:        {s['output_tokens']:>10,} tokens")
    print(f"    Total:         {total:>10,} tokens")
    print(f"    Cache hit:     {cache_pct:.0f}% ({s['cache_read']:,})")
    print(f"    Sessions:      {len(s['sessions'])}")
    if s["cost"] > 0:
        print(f"    Cost:          ${s['cost']:.4f}")
    if s["errors"]:
        print(f"    Errors:        {s['errors']}")
    
    grand["calls"] += s["calls"]
    grand["input"] += s["input_tokens"]
    grand["output"] += s["output_tokens"]
    grand["cache"] += s["cache_read"]
    grand["cost"] += s["cost"]

gt = grand["input"] + grand["output"]
print(f"\n{'='*80}")
print(f"GRAND TOTAL: {grand['calls']} calls, {gt:,} tokens, ${grand['cost']:.4f}")
print(f"  Input: {grand['input']:,}  Output: {grand['output']:,}  Cache: {grand['cache']:,}")
print(f"  Sessions scanned: {len(files[:30])}")
print(f"  Unique models:    {len([m for m in model_stats if model_stats[m]['calls']>0])}")

# Model change summary
print(f"\n--- Model Switches by Session ---")
for sid in sorted(session_models.keys()):
    if session_models[sid]["model"]:
        sm = session_models[sid]
        print(f"  {sid[:8]}: {sm['provider']}/{sm['model']}")
