import sys; sys.path.insert(0, 'config')
from model_routing_v6 import *

print("=" * 60)
print("  融策模型路由 v6.0 — 验证")
print(f"  模型池: {len(MODEL_POOL)}个 | Agent: {len(AGENT_MODEL_ROUTES)}个 | 场景: {len(SCENARIO_MODEL_ROUTES)}个")
print("=" * 60)

tests = [
    ("review_sentinel", None, "复核哨兵"),
    (None, "final_review", "终审场景"),
    ("contract_hound", None, "合同猎犬"),
    ("law_inspector", None, "法规检察官"),
    ("data_scout", None, "数据侦察兵"),
    ("report_writer", None, "报告笔杆子"),
    ("plan_writer", None, "方案撰写师"),
    ("performance_evaluator", None, "绩效评价师"),
    (None, "daily_chat", "日常对话"),
    (None, "compliance_check", "合规审查"),
    (None, "china_reasoning", "国产推理"),
]

for agent, scenario, label in tests:
    t, key, route = get_best_route(agent, scenario)
    p = route["primary"].split("/")[-1]
    f = [f.split("/")[-1] for f in route["fallbacks"][:3]]
    tier = get_model_tier(route["primary"])
    cost = get_cost_estimate(route["primary"])
    print(f"\n  {label}: {t}={key}")
    print(f"    Primary: {p} (T{tier} · {cost})")
    print(f"    Fallbacks: {f}")

print(f"\n{'='*60}")
print(f"  全局Fallback链: {len(GLOBAL_DEFAULT['fallbacks'])}级")
print(f"  Primary: {GLOBAL_DEFAULT['primary'].split('/')[-1]}")
ids = [f.split("/")[-1] for f in GLOBAL_DEFAULT["fallbacks"]]
for i, fid in enumerate(ids, 1):
    print(f"    {i:2d}. {fid}")
