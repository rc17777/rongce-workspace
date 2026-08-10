# -*- coding: utf-8 -*-
"""
update_aux_agents_v5.py — 补齐8个辅助Agent的 algorithms 字段（v5.0）

- 数据源：algorithm_registry.json 的 agent_algorithm_map（唯一事实来源）
- 8个目标：adjustment_scribe / data_classifier / data_desensitizer /
           expert_bias_detector / meeting_minutes_analyzer / ocr_processor /
           plan_writer / report_writer
- 无算法Agent标注：data_desensitizer(纯工具)、ocr_processor(纯工具)、
  expert_bias_detector(registry无分配条目)
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard"
SPECS_DIR = os.path.join(BASE, "agent_specs")
REGISTRY = os.path.join(BASE, "algorithm_registry.json")

TARGETS = [
    "adjustment_scribe",
    "data_classifier",
    "data_desensitizer",
    "expert_bias_detector",
    "meeting_minutes_analyzer",
    "ocr_processor",
    "plan_writer",
    "report_writer",
]

# 无算法Agent的标注说明
NOTES = {
    "data_desensitizer": "纯工具Agent（数据脱敏预处理层）：不依赖算法资产库，total_assigned=0",
    "ocr_processor": "纯工具Agent（OCR预处理层）：不依赖算法资产库，total_assigned=0",
    "expert_bias_detector": "无算法依赖：registry 的 agent_algorithm_map 中无分配条目（评标偏离度检测待分配），total_assigned=0",
}

reg = json.load(open(REGISTRY, encoding="utf-8"))
agent_map = reg["agent_algorithm_map"]
algos = reg["algorithms"]

results = {}
for agent_id in TARGETS:
    path = os.path.join(SPECS_DIR, f"{agent_id}.json")
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)

    assigned = list(agent_map.get(agent_id, []))
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
    if agent_id in NOTES:
        block["note"] = NOTES[agent_id]

    # 覆盖 algorithms 字段（保持其余字段不变）
    spec["algorithms"] = block

    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    results[agent_id] = (len(assigned), len(flagship), len(skeleton))
    print(f"✅ {agent_id:<26} total={len(assigned):<3} 旗舰={len(flagship):<3} 骨架={len(skeleton):<3} assigned={assigned}")

# ---- 全量18个Agent统计（供矩阵文档使用）----
print("\n--- 全量18个Agent统计 ---")
all_stats = {}
for aid in agent_map:
    assigned = list(agent_map.get(aid, []))
    fg = [sn for sn in assigned if algos.get(sn, {}).get("type") == "旗舰"]
    sk = [sn for sn in assigned if algos.get(sn, {}).get("type") == "骨架"]
    all_stats[aid] = (len(assigned), len(fg), len(sk))
    print(f"{aid:<26} total={len(assigned):<3} 旗舰={len(fg):<3} 骨架={len(sk):<3}")

total_assign = sum(v[0] for v in all_stats.values())
total_fg = sum(v[1] for v in all_stats.values())
total_sk = sum(v[2] for v in all_stats.values())
print(f"\n合计分配: {total_assign} 次 | 旗舰: {total_fg} | 骨架: {total_sk}")
print("DONE_AUX_UPDATE")
