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
SCENE_CATALOG_PATH = os.path.join(BASE_DIR, "algorithms_by_scene.json")
TAXONOMY_PATH = os.path.join(BASE_DIR, "scene_taxonomy.json")

_registry = None
_scene_catalog = None


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
    global _registry, _scene_catalog
    _registry = None
    _scene_catalog = None
    return load_registry(path)


def load_scene_catalog(path: str = SCENE_CATALOG_PATH) -> dict:
    """加载按业务场景组织的算法目录（algorithms_by_scene.json，带缓存）"""
    global _scene_catalog
    if _scene_catalog is not None:
        return _scene_catalog
    if not os.path.exists(path):
        raise FileNotFoundError(f"场景目录不存在: {path}（请运行 build_scene_catalog.py 生成）")
    with open(path, "r", encoding="utf-8") as f:
        _scene_catalog = json.load(f)
    return _scene_catalog


def _scene_keyword_match(query: str) -> str | None:
    """用 scene_taxonomy 的场景规则关键词做二次匹配：
    输入"社保审计"→ 命中"民生与社保医保"场景。"""
    try:
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            tax = json.load(f)
    except Exception:
        return None
    for scene, kws in tax.get("scene_rules", []):
        for kw in kws:
            if kw and kw in query:
                return scene
    return None


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


# ── v5.0 场景目录 API（基于 scene_taxonomy + algorithms_by_scene） ─────────────

def list_scenes() -> list:
    """
    列出算法库全部一级业务场景及算法数。
    
    Returns:
        [{scene, total, flagship, skeleton}, ...]（total 含主+附加归属）
    """
    cat = load_scene_catalog()
    out = []
    for scene, items in cat.get("scenes", {}).items():
        if not items:
            continue
        flag = sum(1 for i in items if i["type"] == "旗舰")
        skel = sum(1 for i in items if i["type"] == "骨架")
        out.append({"scene": scene, "total": len(items), "flagship": flag, "skeleton": skel})
    return out


def list_algorithms_by_scene(scene: str, fuzzy: bool = True) -> list:
    """
    按业务场景列出算法。
    
    优先匹配标准场景目录（algorithms_by_scene.json 的 14 个一级场景），
    未命中时（fuzzy=True）回退到注册表字段的文本包含匹配。
    
    Returns:
        [{sn, name, type, priority, complexity, risk_mechanism, agents, primary_scene, extra_scenes}]
    """
    cat = load_scene_catalog()
    scenes = cat.get("scenes", {})
    # 精确场景名
    if scene in scenes and scenes[scene]:
        return scenes[scene]
    # 模糊：场景名包含关系
    for sname, items in scenes.items():
        if scene in sname or sname in scene:
            if items:
                return items
    # taxonomy 关键词匹配（如"社保审计"→"民生与社保医保"）
    kw_scene = _scene_keyword_match(scene)
    if kw_scene and scenes.get(kw_scene):
        return scenes[kw_scene]
    if not fuzzy:
        return []
    # 回退：注册表文本包含匹配
    reg = load_registry()
    out = []
    for sn, algo in reg.get("algorithms", {}).items():
        fields = algo.get("scene", []) + [algo.get("biz_line", ""), algo.get("biz_scene", "")]
        if any(scene in f for f in fields):
            out.append({
                "sn": sn,
                "name": algo.get("name"),
                "type": algo.get("type"),
                "priority": algo.get("priority"),
                "complexity": algo.get("complexity"),
                "risk_mechanism": algo.get("risk_mechanism"),
                "agents": algo.get("assigned_agents"),
                "primary_scene": None,
                "extra_scenes": [],
            })
    return out


def get_scene_catalog_summary() -> dict:
    """场景目录总览：算法数、场景数、主场景分布"""
    cat = load_scene_catalog()
    scenes = cat.get("scenes", {})
    primary = {}
    for sname, items in scenes.items():
        for it in items:
            primary[it["sn"]] = it.get("primary_scene", sname)
    from collections import Counter
    dist = Counter(primary.values())
    return {
        "version": cat.get("version"),
        "total_algorithms": cat.get("total_algorithms"),
        "scene_count": len([s for s in scenes if scenes[s]]),
        "primary_distribution": dict(dist),
    }


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
    print(f"\n== 场景目录（前6个场景） ==")
    for s in list_scenes()[:6]:
        print(f"  {s['scene']}: {s['total']}个(旗舰{s['flagship']})")
    print(f"\n== '社保审计' 场景算法（前5） ==")
    for x in list_algorithms_by_scene("社保审计")[:5]:
        print(f"  {x['sn']} {x['name'][:35]} [{x['type']}]")
    print(f"\n== '预算执行' 业务线算法 ==")
    for x in list_by_biz_line("预算执行")[:3]:
        print(f"  {x['sn']} {x['name'][:40]} [{x['priority']}]")
