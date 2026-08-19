import sys; sys.path.insert(0, 'config')
from model_routing_v7 import *

print("=" * 64)
print("  融策模型路由 v7.0 — 全量验证")
print("=" * 64)

# ─── 基础统计 ───
tiers = {}
regions = {}
for mid, info in MODEL_POOL.items():
    t = info.get("tier", "?")
    r = info.get("region", "?")
    tiers[t] = tiers.get(t, 0) + 1
    regions[r] = regions.get(r, 0) + 1
print(f"\n  模型池: {len(MODEL_POOL)}个")
for t in sorted(tiers): 
    print(f"    T{t}: {tiers[t]}个")
for r in sorted(regions):
    print(f"    {r}: {regions[r]}个")

# ─── 敏感项目检测 ───
print(f"\n  ─── 敏感项目检测 ───")
for test in [
    ("X县经济责任审计", "经责"),
    ("XX市专项资金检查", "专项"),
    ("国企年报审计", "国企"),
    ("Y县招投标专项检查", "招投标"),
    ("Z区补充耕地补贴审计", "补贴"),
    ("一般绩效评价", "绩效"),
    ("日常咨询", ""),
]:
    name, ptype = test
    sensitive = is_sensitive_project(name, ptype)
    print(f"    {'🔴' if sensitive else '🟢'} {name}/{ptype}: {'敏感' if sensitive else '普通'}")

# ─── Agent路由 ───
print(f"\n  ─── Agent路由（普通项目）───")
key_agents = [
    "review_sentinel", "contract_hound", "law_inspector",
    "data_scout", "report_writer", "plan_writer",
    "performance_evaluator",
]
for agent in key_agents:
    t, k, route = get_best_route(agent_name=agent)
    p = route["primary"].split("/")[-1]
    f = [m.split("/")[-1] for m in route["fallbacks"][:3]]
    region = get_model_region(route["primary"])
    print(f"    {agent:<22s} {p:<16s}[{region}] → {f}")

# ─── Agent路由（敏感项目） ───
print(f"\n  ─── Agent路由（敏感项目：经责审计）───")
print(f"  ⚙️ 开关 SENSITIVE_FORCE_DOMESTIC_PRIMARY = {SENSITIVE_FORCE_DOMESTIC_PRIMARY}")
pi = {"name": "X县经济责任审计", "type": "经责"}
for agent in key_agents:
    t, k, route = get_best_route(agent_name=agent, project_info=pi)
    p = route["primary"].split("/")[-1]
    f = [m.split("/")[-1] for m in route["fallbacks"][:3]]
    region = get_model_region(route["primary"])
    # Check all fallbacks are domestic
    all_domestic = all(
        MODEL_POOL.get(m, {}).get("region") == "国产" 
        for m in route["fallbacks"]
    )
    primary_domestic = MODEL_POOL.get(route["primary"], {}).get("region") == "国产"
    assert all_domestic, f"{agent} 敏感链混入海外fallback: {route['fallbacks']}"
    if SENSITIVE_FORCE_DOMESTIC_PRIMARY:
        assert primary_domestic, f"{agent} 敏感项目primary非国产: {route['primary']}"
    flag = "🛡️" if primary_domestic else "⚠️"
    print(f"    {agent:<22s} {p:<16s}[{region}] {flag}全国产={all_domestic} → {f}")

# ─── 场景路由 ───
print(f"\n  ─── 场景路由 ───")
scenarios = [
    ("final_review", False), ("consulting", False),
    ("sensitive_project", True), ("china_reasoning", False),
    ("long_document", False), ("creative", False),
]
for sc, is_sens in scenarios:
    route = get_scenario_route(sc, is_sens)
    p = route["primary"].split("/")[-1]
    f = [m.split("/")[-1] for m in route["fallbacks"][:3]]
    region = get_model_region(route["primary"])
    flag = "🔴" if sc == "sensitive_project" else ""
    print(f"    {flag}{sc:<20s} {p:<16s}[{region}] → {f}")

# ─── 全局Fallback链 ───
print(f"\n  ─── 普通项目Fallback ({len(GLOBAL_DEFAULT['fallbacks'])}级) ───")
p = GLOBAL_DEFAULT["primary"].split("/")[-1]
print(f"    1ry: {p} [国产]")
for i, m in enumerate(GLOBAL_DEFAULT["fallbacks"], 2):
    short = m.split("/")[-1]
    r = get_model_region(m)
    print(f"    {i:2d}: {short:<30s}[{r}]")

print(f"\n  ─── 敏感项目Fallback ({len(SENSITIVE_FALLBACK['fallbacks'])}级) ───")
p = SENSITIVE_FALLBACK["primary"].split("/")[-1]
print(f"    1ry: {p} [国产]")
for i, m in enumerate(SENSITIVE_FALLBACK["fallbacks"], 2):
    short = m.split("/")[-1]
    r = get_model_region(m)
    assert r == "国产", f"敏感链混入海外模型: {m}"
    print(f"    {i:2d}: {short:<30s}[{r}]")

print(f"\n  ✅ 全量验证通过")
