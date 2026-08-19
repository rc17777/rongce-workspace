# -*- coding: utf-8 -*-
"""model_routing_v6 自测：验证四信号 × 四方法决策正确性"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.model_routing_v6 import Router, stats

r = Router(log_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "test_trajectory.jsonl"))

cases = []
# ① 风险策略（最高优先）：报告签字 → safety_net + 人工审批
cases.append(("风险-报告签字", r.route({"task_id": "t1", "scenario": "daily_chat", "risk": "report_signing"}),
              {"method": "risk", "tier": "safety_net", "require_approval": True}))
# ② 风险：付款
cases.append(("风险-付款", r.route({"task_id": "t2", "scenario": "lightweight", "risk": "payment"}),
              {"method": "risk", "tier": "safety_net", "require_approval": True}))
# ③ 中风险：合同审查（未登记操作保守中风险）
cases.append(("风险-未登记操作", r.route({"task_id": "t3", "risk": "weird_op_xyz"}),
              {"method": "risk", "tier": "strong", "require_approval": False}))
# ④ 级联升级：同一错误2次 → 从 efficient 升到 numerical
cases.append(("级联-同错2次", r.route({"task_id": "t4", "scenario": "lightweight",
              "trajectory": {"same_error_count": 2}}),
              {"method": "cascade", "tier": "numerical"}))
# ⑤ 级联升级：3轮无进展 → 升级，且带交接单
d5 = r.route({"task_id": "t5", "scenario": "data_check", "trajectory": {"no_progress_rounds": 3}})
cases.append(("级联-3轮无进展", d5, {"method": "cascade", "tier": "strong"}))
assert d5["handoff"] is not None, "升级必须带交接单"
# ⑥ 级联冷却：刚升过级，10分钟内不再升
d6a = r.route({"task_id": "t6", "scenario": "lightweight", "trajectory": {"same_error_count": 2}})
d6b = r.route({"task_id": "t6", "scenario": "lightweight", "trajectory": {"same_error_count": 2}})
cases.append(("级联-冷却期不重复升", (d6a, d6b), {"first": "cascade", "second": "rule"}))
# ⑦ 阶段路由：plan → strong
cases.append(("阶段-plan", r.route({"task_id": "t7", "stage": "plan"}), {"method": "stage", "tier": "strong"}))
# ⑧ 阶段路由：execute → numerical
cases.append(("阶段-execute", r.route({"task_id": "t8", "stage": "execute"}), {"method": "stage", "tier": "numerical"}))
# ⑨ 阶段路由：acceptance → safety_net + deterministic
cases.append(("阶段-acceptance", r.route({"task_id": "t9", "stage": "acceptance"}),
              {"method": "stage", "tier": "safety_net", "deterministic_check": True}))
# ⑩ 分类路由：跨文件推理特征 → strong
cases.append(("分类-跨文件推理", r.route({"task_id": "t10", "scenario": "lightweight",
              "features": ["cross_file_reasoning"]}),
              {"method": "classification", "tier": "strong"}))
# ⑪ 长上下文：>128K → long_context
cases.append(("分类-长上下文", r.route({"task_id": "t11", "scenario": "lightweight", "context_chars": 150000}),
              {"method": "classification", "tier": "long_context"}))
# ⑫ 规则路由：Agent 优先
cases.append(("规则-Agent", r.route({"task_id": "t12", "agent": "review_sentinel"}),
              {"method": "rule", "model": "custom-cbwyy-claude/claude-sonnet-5"}))
# ⑬ 规则路由：场景兜底
cases.append(("规则-场景", r.route({"task_id": "t13", "scenario": "gov_document"}),
              {"method": "rule", "model": "custom-cbwyy-qwen/qwen3.7-plus"}))
# ⑭ 优先级：风险 > 轨迹 > 阶段 > 分类 > 规则（风险压过一切）
cases.append(("优先级-风险压过阶段", r.route({"task_id": "t14", "stage": "execute", "risk": "delete_data"}),
              {"method": "risk", "tier": "safety_net"}))
# ⑮ 优先级：轨迹升级优先于阶段（无风险时）
cases.append(("优先级-轨迹先于阶段", r.route({"task_id": "t15", "stage": "explore",
              "trajectory": {"tool_call_repeat_count": 3}}),
              {"method": "cascade"}))
# ⑯ v5 兼容接口
from config.model_routing_v6 import get_best_route, get_agent_route
rb = get_best_route(agent_name="data_scout")
cases.append(("v5兼容-get_best_route", rb, {"0": "agent"}))
# ⑰ 系统状态：模型不可用 → fallback
from config.model_routing_v6 import SYSTEM_STATE
SYSTEM_STATE["custom-cbwyy-claude/claude-sonnet-5"] = {"available": False, "error_rate": 0.9}
d17 = r.route({"task_id": "t17", "scenario": "compliance_check"})
cases.append(("系统状态-不可用走fallback", d17, {"method": "rule",
              "model": "custom-cbwyy-qwen/qwen3.7-plus"}))
SYSTEM_STATE.clear()

fails = 0
for name, got, want in cases:
    ok = True
    detail = ""
    if isinstance(want, dict):
        for k, v in want.items():
            if k == "first":
                ok = got[0]["method"] == v and ok
                continue
            if k == "second":
                ok = got[1]["method"] == v and ok
                continue
            gv = got.get(k) if isinstance(got, dict) else (got[int(k)] if k.isdigit() else None)
            if gv != v:
                ok = False
                detail = f"  [{k}] want={v} got={gv}"
    if not ok:
        fails += 1
        print(f"❌ {name}{detail}  → {got}")
    else:
        print(f"✅ {name}")

print(f"\n共 {len(cases)} 项，失败 {fails} 项")
print("轨迹统计:", stats(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "test_trajectory.jsonl")))
sys.exit(1 if fails else 0)
