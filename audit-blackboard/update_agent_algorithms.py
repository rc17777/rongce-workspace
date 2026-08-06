# -*- coding: utf-8 -*-
"""
update_agent_algorithms.py — 为 Agent 规格 JSON 追加 algorithms 字段（只追加不删除）

用法:
    python update_agent_algorithms.py

说明:
    - 从 algorithm_registry.json 的 agent_algorithm_map 读取每个 Agent 的算法列表
    - 在 agent_specs/<agent_id>.json 顶层插入 algorithms 字段（位于 desc 之后）
    - 保持原有字段不变，向后兼容
    - 文件用 UTF-8 无 BOM 写回，ensure_ascii=False
"""
import sys
import os
import json

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SPECS_DIR = os.path.join(BASE, "agent_specs")
REGISTRY = os.path.join(BASE, "algorithm_registry.json")

# 需要更新算法的 Agent（含 底稿工匠 workpaper_crafter —— 映射表引用了它）
TARGET_AGENTS = [
    "data_scout",            # 数据侦察兵（26个，最多）
    "bid_hunter",            # 招投标猎手
    "performance_evaluator", # 绩效评价师
    "budget_estimator",      # 预算工程师
    "settlement_auditor",    # 结算审计师
    "fiscal_reviewer",       # 财政评审员
    "contract_hound",        # 合同猎犬
    "law_inspector",         # 法规检察官
    "review_sentinel",       # 复核哨兵
    "workpaper_crafter",     # 底稿工匠（FUND-SIPHON-001）
]

# Agent ID → 中文名（仅用于 usage 示例）
AGENT_NAMES = {
    "data_scout": "数据侦察兵", "bid_hunter": "招投标猎手",
    "performance_evaluator": "绩效评价师", "budget_estimator": "预算工程师",
    "settlement_auditor": "结算审计师", "fiscal_reviewer": "财政评审员",
    "contract_hound": "合同猎犬", "law_inspector": "法规检察官",
    "review_sentinel": "复核哨兵", "workpaper_crafter": "底稿工匠",
}


def build_algorithms_block(agent_id: str, assigned: list) -> dict:
    example_sn = assigned[0] if assigned else ""
    return {
        "version": "v4.0",
        "registry": "audit-blackboard/algorithm_registry.json",
        "loader": "audit-blackboard/algorithm_loader.py",
        "assigned": assigned,
        "usage": (
            f"from algorithm_loader import get_algorithm_detail, get_algorithms_for_agent; "
            f"algos = get_algorithms_for_agent('{agent_id}'); "
            f"algo = get_algorithm_detail('{example_sn}')"
        ),
    }


def main():
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    agent_map = reg["agent_algorithm_map"]

    updated, skipped = [], []
    for agent_id in TARGET_AGENTS:
        path = os.path.join(SPECS_DIR, f"{agent_id}.json")
        if not os.path.exists(path):
            skipped.append((agent_id, "规格文件不存在"))
            continue
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)

        assigned = agent_map.get(agent_id, [])
        block = build_algorithms_block(agent_id, assigned)

        # 只追加不删除：若已存在则覆盖 assigned（保持最新），否则插入 desc 之后
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
        updated.append((agent_id, len(assigned)))

    print(f"✅ 已更新 {len(updated)} 个 Agent 规格:")
    for agent_id, n in updated:
        print(f"   {agent_id} ({AGENT_NAMES.get(agent_id,'?')}): {n} 个算法")
    for agent_id, reason in skipped:
        print(f"⚠ 跳过 {agent_id}: {reason}")


if __name__ == "__main__":
    main()
