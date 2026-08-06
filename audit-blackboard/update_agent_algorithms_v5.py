# -*- coding: utf-8 -*-
"""
update_agent_algorithms_v5.py — 为 18 个 Agent 规格 JSON 追加 v5.0 algorithms 字段

用法: python update_agent_algorithms_v5.py
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SPECS_DIR = os.path.join(BASE, "agent_specs")
REGISTRY = os.path.join(BASE, "algorithm_registry.json")

ALL_AGENTS = [
    "data_scout", "bid_hunter", "contract_hound", "law_inspector",
    "workpaper_crafter", "report_writer", "review_sentinel",
    "budget_estimator", "settlement_auditor", "fiscal_reviewer",
    "performance_evaluator", "expert_bias_detector",
    "meeting_minutes_analyzer", "ocr_processor", "data_classifier",
    "data_desensitizer", "adjustment_scribe", "plan_writer",
]

reg = json.load(open(REGISTRY, encoding="utf-8"))
agent_map = reg["agent_algorithm_map"]
algos = reg["algorithms"]

updated = []
skipped = []

for agent_id in ALL_AGENTS:
    path = os.path.join(SPECS_DIR, f"{agent_id}.json")
    if not os.path.exists(path):
        skipped.append((agent_id, "规格文件不存在"))
        continue
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)

    assigned = agent_map.get(agent_id, [])
    flagship = [sn for sn in assigned if algos.get(sn, {}).get("type") == "旗舰"]
    skeleton = [sn for sn in assigned if algos.get(sn, {}).get("type") == "骨架"]

    example_sn = assigned[0] if assigned else ""
    block = {
        "version": "v5.0",
        "total_assigned": len(assigned),
        "registry": "audit-blackboard/algorithm_registry.json",
        "loader": "from audit_blackboard.algorithm_loader import get_algorithms_for_agent, get_algorithm_detail",
        "assigned": assigned,
        "quick_ref": {
            "旗舰": flagship,
            "骨架": skeleton,
        },
        "usage": (
            f"from algorithm_loader import get_algorithms_for_agent, get_algorithm_detail; "
            f"algos = get_algorithms_for_agent('{agent_id}'); "
            f"{('algo = get_algorithm_detail(\"' + example_sn + '\")') if example_sn else '# 该Agent暂无分配算法'}"
        ),
    }

    # 追加或覆盖 algorithms 字段（保持其余字段不变）
    if "algorithms" in spec:
        spec["algorithms"] = block
    else:
        new_spec = {}
        inserted = False
        for k, v in spec.items():
            new_spec[k] = v
            if k == "desc" and not inserted:
                new_spec["algorithms"] = block
                inserted = True
        if not inserted:
            new_spec["algorithms"] = block
        spec = new_spec

    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    updated.append((agent_id, len(assigned), len(flagship), len(skeleton)))

print(f"✅ 已更新 {len(updated)} 个 Agent 规格:")
print(f"{'Agent':<26} {'总计':>4} {'旗舰':>4} {'骨架':>4}")
print("-" * 42)
for aid, total, fg, sk in updated:
    print(f"{aid:<26} {total:>4} {fg:>4} {sk:>4}")
for aid, reason in skipped:
    print(f"⚠ 跳过 {aid}: {reason}")
