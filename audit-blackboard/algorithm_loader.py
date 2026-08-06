# -*- coding: utf-8 -*-
"""
algorithm_loader.py — 算法注册表加载器（融策 22Agent 体系 ↔ 135个政府审计算法 v5.0）

用法示例:
    from algorithm_loader import (
        load_registry, get_algorithms_for_agent, get_agent_for_scene,
        get_algorithm_detail, list_algorithms_by_scene, search_algorithms,
        get_algorithm_count, list_by_biz_line, reload_registry,
    )

    reg    = load_registry()                          # 加载注册表
    algos  = get_algorithms_for_agent("data_scout")   # Agent 负责的算法列表（含名称/类型/复杂度）
    agents = get_agent_for_scene("绩效评价")           # 业务场景 → 负责 Agent（按覆盖数降序）
    detail = get_algorithm_detail("PERF-OUTLIER-001") # 算法完整信息
    lst    = list_algorithms_by_scene("社保审计")     # 场景 → 算法列表
    count  = get_algorithm_count()                    # 总数/类型/优先级/复杂度统计
    biz    = list_by_biz_line("预算执行")             # 按业务线列出算法
"""
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(BASE_DIR, "algorithm_registry.json")

_registry = None


def load_registry(path: str = REGISTRY_PATH) -> dict:
    """从 algorithm_registry.json 加载注册表（带缓存，线程不安全）"""
    global _registry
    if _registry is not None:
        return _registry
    if not os.path.exists(path):
        raise FileNotFoundError(f"算法注册表不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        _registry = json.load(f)
    return _registry


def reload_registry(path: str = REGISTRY_PATH) -> dict:
    """强制重新加载（注册表文件更新后调用）"""
    global _registry
    _registry = None
    return load_registry(path)


# ── v5.0 新增 API ──────────────────────────────────────────────────────────

def get_algorithms_for_agent(agent_id: str) -> list:
    """
    返回该 Agent 负责的算法列表（含 名称/类型/复杂度/优先级 摘要）。
    
    Returns:
        [{sn, name, type, complexity, priority, scene}, ...]
    """
    reg = load_registry()
    sns = reg.get("agent_algorithm_map", {}).get(agent_id, [])
    algos = reg.get("algorithms", {})
    return [
        {
            "sn": sn,
            "name": algos[sn].get("name", ""),
            "type": algos[sn].get("type", ""),
            "complexity": algos[sn].get("complexity", ""),
            "priority": algos[sn].get("priority", ""),
            "scene": algos[sn].get("scene", [])[:3],
        }
        for sn in sns if sn in algos
    ]


def get_algorithm_detail(sn: str) -> dict:
    """返回算法完整信息（含 card 原始要素）"""
    reg = load_registry()
    algo = reg.get("algorithms", {}).get(sn)
    if algo is None:
        raise KeyError(f"算法不存在: {sn}")
    return algo


def get_agent_for_scene(scene: str) -> list:
    """
    按业务场景找 Agent（返回 Agent ID 列表，按算法覆盖数降序）。
    匹配规则：scene 命中算法的 scene 列表或其 biz_line。
    """
    reg = load_registry()
    hits = {}
    for sn, algo in reg.get("algorithms", {}).items():
        fields = algo.get("scene", []) + [algo.get("biz_line", ""), algo.get("biz_scene", "")]
        if any(scene in f for f in fields):
            for ag in algo.get("assigned_agents", []):
                hits[ag] = hits.get(ag, 0) + 1
    return sorted(hits, key=lambda x: -hits[x])


def list_algorithms_by_scene(scene: str) -> list:
    """按业务场景列出算法（返回摘要列表）"""
    reg = load_registry()
    out = []
    for sn, algo in reg.get("algorithms", {}).items():
        fields = algo.get("scene", []) + [algo.get("biz_line", ""), algo.get("biz_scene", "")]
        if any(scene in f for f in fields):
            out.append({
                "sn": sn,
                "name": algo.get("name"),
                "type": algo.get("type"),
                "complexity": algo.get("complexity"),
                "priority": algo.get("priority"),
                "assigned_agents": algo.get("assigned_agents"),
            })
    return out


def list_by_biz_line(biz_line: str) -> list:
    """
    v5.0 新增：按业务线列出算法（如"预算执行""社保审计"）。
    
    Returns:
        [{sn, name, type, complexity, priority, agents}, ...]
    """
    reg = load_registry()
    out = []
    for sn, algo in reg.get("algorithms", {}).items():
        if biz_line in algo.get("biz_line", ""):
            out.append({
                "sn": sn,
                "name": algo.get("name"),
                "type": algo.get("type"),
                "complexity": algo.get("complexity"),
                "priority": algo.get("priority"),
                "agents": algo.get("assigned_agents"),
            })
    return sorted(out, key=lambda x: (x["priority"] or "P2", x["sn"]))


def get_algorithm_count() -> dict:
    """
    v5.0 新增：返回注册表统计信息。
    
    Returns:
        {total, by_type: {旗舰: N, 骨架: N}, by_complexity: {...},
         by_priority: {...}, by_agent: {agent_id: N}, agent_count: N}
    """
    reg = load_registry()
    algos = reg.get("algorithms", {})
    by_type = {}
    by_comp = {}
    by_pri = {}
    by_agent = {}
    for a in algos.values():
        by_type[a.get("type", "?")] = by_type.get(a.get("type", "?"), 0) + 1
        by_comp[a.get("complexity", "?")] = by_comp.get(a.get("complexity", "?"), 0) + 1
        by_pri[a.get("priority", "?")] = by_pri.get(a.get("priority", "?"), 0) + 1
        for ag in a.get("assigned_agents", []):
            by_agent[ag] = by_agent.get(ag, 0) + 1
    return {
        "version": reg.get("version"),
        "total": len(algos),
        "by_type": by_type,
        "by_complexity": by_comp,
        "by_priority": by_pri,
        "by_agent": by_agent,
        "agent_count": len(reg.get("agent_algorithm_map", {})),
    }


# ── 向后兼容 API ───────────────────────────────────────────────────────────

def search_algorithms(keyword: str, fields: tuple = ("name", "scene", "risk_mechanism", "family")) -> list:
    """按关键词模糊搜索算法（默认搜名称/场景/风险机制）"""
    reg = load_registry()
    out = []
    for sn, algo in reg.get("algorithms", {}).items():
        for f in fields:
            val = algo.get(f)
            if isinstance(val, list):
                val = " ".join(val)
            if val and keyword in str(val):
                out.append(sn)
                break
    return out


def get_algorithm_stats() -> dict:
    """向后兼容：等同于 get_algorithm_count()"""
    return get_algorithm_count()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("== v5.0 注册表统计 ==")
    stats = get_algorithm_count()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\n== data_scout 负责算法 ({len(get_algorithms_for_agent('data_scout'))}个) ==")
    for x in get_algorithms_for_agent("data_scout")[:5]:
        print(f"  {x['sn']} {x['name'][:30]} [{x['type']}/{x['complexity']}]")
    print("  ...")
    print(f"\n== '绩效评价' 场景 Agent ==")
    print(get_agent_for_scene("绩效评价"))
    print(f"\n== '预算执行' 业务线算法 ==")
    for x in list_by_biz_line("预算执行")[:3]:
        print(f"  {x['sn']} {x['name'][:40]} [{x['priority']}]")
