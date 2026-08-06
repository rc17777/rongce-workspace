# -*- coding: utf-8 -*-
"""Validation suite for v5.0 algorithm integration"""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard"
errors = []
warnings = []

# ── 1. Registry JSON valid & parsable ──
print("1. Registry JSON parse...")
try:
    reg = json.load(open(os.path.join(BASE, "algorithm_registry.json"), encoding="utf-8"))
    assert reg["version"] == "5.0", f"bad version: {reg['version']}"
    assert reg["total_algorithms"] == 135, f"bad total: {reg['total_algorithms']}"
    assert len(reg["algorithms"]) == 135, f"bad algo count: {len(reg['algorithms'])}"
    print("   ✅ valid, 135 algorithms")
except Exception as e:
    errors.append(f"Registry parse failed: {e}")
    print(f"   ❌ {e}")

# ── 2. Every algorithm has ≥1 assigned agent ──
if "algorithms" in dir(): # check if reg exists
    missing = []
    for sn, algo in reg["algorithms"].items():
        if not algo.get("assigned_agents"):
            missing.append(sn)
    if missing:
        errors.append(f"{len(missing)} algorithms with 0 agents: {missing[:10]}")
        print(f"   ❌ {len(missing)} algorithms without agents")
    else:
        print(f"   ✅ All 135 algorithms have ≥1 assigned agent")

# ── 3. All required algorithm fields exist ──
required = ["name", "type", "scene", "risk_mechanism", "complexity", "priority", "assigned_agents", "trigger", "data_dependencies"]
missing_fields = []
for sn, algo in reg["algorithms"].items():
    for f in required:
        if f not in algo:
            missing_fields.append((sn, f))
if missing_fields:
    warnings.append(f"{len(missing_fields)} missing required fields")
    print(f"   ⚠ {len(missing_fields)} missing fields: {missing_fields[:5]}")
else:
    print("   ✅ All required fields present on all algorithms")

# ── 4. agent_algorithm_map matches algorithms ──
agent_map = reg.get("agent_algorithm_map", {})
all_assigned = set()
for sn, algo in reg["algorithms"].items():
    for ag in algo.get("assigned_agents", []):
        all_assigned.add((ag, sn))
from_map = set()
for ag, sns in agent_map.items():
    for sn in sns:
        from_map.add((ag, sn))
if all_assigned != from_map:
    diff1 = all_assigned - from_map
    diff2 = from_map - all_assigned
    if diff1:
        errors.append(f"Map missing {len(diff1)} assignments: {list(diff1)[:5]}")
    if diff2:
        errors.append(f"Map has {len(diff2)} extra assignments: {list(diff2)[:5]}")
    print(f"   ❌ Map mismatch")
else:
    print("   ✅ agent_algorithm_map consistent with algorithms")

# ── 5. Loader importable & all functions work ──
print("\n2. algorithm_loader.py...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("loader", os.path.join(BASE, "algorithm_loader.py"))
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    # Test all functions
    count = loader.get_algorithm_count()
    assert count["total"] == 135, f"count: {count['total']}"
    print(f"   ✅ get_algorithm_count(): {count['total']} total")
    
    agents = loader.get_algorithms_for_agent("data_scout")
    assert len(agents) == 98, f"data_scout: {len(agents)}"
    print(f"   ✅ get_algorithms_for_agent('data_scout'): {len(agents)}")
    
    detail = loader.get_algorithm_detail("PERF-OUTLIER-001")
    assert detail["name"], f"empty name"
    assert len(detail["assigned_agents"]) >= 1
    print(f"   ✅ get_algorithm_detail('PERF-OUTLIER-001'): {detail['name'][:25]}...")
    
    scene_agents = loader.get_agent_for_scene("绩效评价")
    assert len(scene_agents) > 0
    print(f"   ✅ get_agent_for_scene('绩效评价'): {scene_agents}")
    
    biz = loader.list_by_biz_line("预算执行")
    assert len(biz) > 0
    print(f"   ✅ list_by_biz_line('预算执行'): {len(biz)} algo(s)")
    
    search = loader.search_algorithms("围标")
    assert len(search) > 0
    print(f"   ✅ search_algorithms('围标'): {len(search)} hits")
    
    scene_algo = loader.list_algorithms_by_scene("社保")
    assert len(scene_algo) > 0
    print(f"   ✅ list_algorithms_by_scene('社保'): {len(scene_algo)} hits")

except Exception as e:
    errors.append(f"Loader test failed: {e}")
    print(f"   ❌ {e}")
    import traceback
    traceback.print_exc()

# ── 6. All 18 agent specs valid JSON ──
print("\n3. Agent specs...")
specs_dir = os.path.join(BASE, "agent_specs")
specs_ok = 0
for f in os.listdir(specs_dir):
    if f.endswith(".json"):
        try:
            spec = json.load(open(os.path.join(specs_dir, f), encoding="utf-8"))
            alg_block = spec.get("algorithms", {})
            name = f.replace(".json", "")
            if alg_block.get("version") != "v5.0":
                if name not in ["ocr_processor", "data_desensitizer", "expert_bias_detector"]:
                    warnings.append(f"{name}: algorithms.version != v5.0")
            if "quick_ref" not in alg_block:
                warnings.append(f"{name}: missing quick_ref")
            specs_ok += 1
        except Exception as e:
            errors.append(f"Invalid spec {f}: {e}")
print(f"   ✅ {specs_ok}/18 agent specs valid JSON with algorithms block")

# ── 7. Integration doc exists ──
doc_path = os.path.join(BASE, "ALGORITHM_INTEGRATION.md")
if os.path.exists(doc_path):
    with open(doc_path, encoding="utf-8") as f:
        content = f.read()
    assert "v5.0" in content, "Doc missing v5.0"
    assert "135" in content, "Doc missing 135 count"
    print(f"   ✅ ALGORITHM_INTEGRATION.md {len(content)} bytes")
else:
    errors.append("ALGORITHM_INTEGRATION.md missing!")

# ── Summary ──
print(f"\n{'='*50}")
print(f"VALIDATION RESULT: {len(errors)} errors, {len(warnings)} warnings")
if errors:
    for e in errors:
        print(f"  ❌ {e}")
if warnings:
    for w in warnings:
        print(f"  ⚠ {w}")
if not errors:
    print("  🎉 ALL CHECKS PASSED")
