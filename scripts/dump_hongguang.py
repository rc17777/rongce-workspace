import json
path = r"C:\Users\scrccpa\Desktop\报告\2.部门预算项目绩效自评复核报告20260722\评审数据提取.json"
d = json.load(open(path, encoding="utf-8"))

# key paragraphs
for p in d["paragraphs"]:
    t = p["text"]
    if any(k in t for k in ["标宋","黑体","一、","二、","三、","四、","五、","六、", "2025","2026","得分","复核","自评","偏离","问题","建议","红光"]):
        fonts = "/".join(sorted({(r["east_asia"] or r["font"]) for r in p["runs"] if (r["east_asia"] or r["font"])}))
        print(f"[{p['index']}] align={p['alignment']} font={fonts or '--'} | {t[:120]}")

print("\n=== TABLES ===")
for t in d["tables"]:
    print(f"\n--- Table {t['table']} ({len(t['rows'])} rows) ---")
    for r in t["rows"][:3]:
        print(" | ".join(r[:8]))
    if len(t["rows"]) > 3:
        print("...")
        for r in t["rows"][-2:]:
            print(" | ".join(r[:8]))

print("\n=== SHEETS ===")
for s in d["sheets"]:
    print(f"\n--- Sheet [{s['sheet']}] ({len(s['rows'])} rows) ---")
    for i, r in enumerate(s["rows"]):
        print(f"  R{i+1}: {' | '.join(r[:10])}")
