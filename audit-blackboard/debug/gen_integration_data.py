# -*- coding: utf-8 -*-
"""Generate mapping data for the integration doc"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")

reg = json.load(open(r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry.json", encoding="utf-8"))
agent_map = reg["agent_algorithm_map"]
algos = reg["algorithms"]

# Agent summary for the matrix
AGENT_NAMES_CN = {
    "data_scout": "数据侦察兵", "bid_hunter": "招投标猎手", "contract_hound": "合同猎犬",
    "law_inspector": "法规检察官", "workpaper_crafter": "底稿工匠", "report_writer": "报告笔杆子",
    "review_sentinel": "复核哨兵", "budget_estimator": "预算工程师", "settlement_auditor": "结算审计师",
    "fiscal_reviewer": "财政评审员", "performance_evaluator": "绩效评价师", "expert_bias_detector": "评标偏离度",
    "meeting_minutes_analyzer": "会议纪要分析", "ocr_processor": "OCR预处理", "data_classifier": "数据分类员",
    "data_desensitizer": "数据脱敏", "adjustment_scribe": "调整分录师", "plan_writer": "方案撰写师",
}

print("## Agent-算法映射矩阵\n")
print("| Agent | ID | 算法数 | 旗舰 | 骨架 | 核心职责 |")
print("|-------|-----|--------|------|------|----------|")
for ag in sorted(agent_map, key=lambda x: -len(agent_map[x])):
    sns = agent_map[ag]
    fg = sum(1 for s in sns if algos[s].get("type") == "旗舰")
    sk = sum(1 for s in sns if algos[s].get("type") == "骨架")
    print(f"| {AGENT_NAMES_CN.get(ag, ag)} | `{ag}` | {len(sns)} | {fg} | {sk} | |")
print(f"| **合计** | | **{sum(len(v) for v in agent_map.values())}** | **{sum(1 for a in algos.values() if a['type']=='旗舰')}** | **{sum(1 for a in algos.values() if a['type']=='骨架')}** | |")

# Per-agent top-level algorithm list (flagship first)
print("\n\n## 各Agent算法分配明细\n")
for ag in sorted(agent_map, key=lambda x: -len(agent_map[x])):
    sns = agent_map[ag]
    if not sns:
        continue
    fg_list = [s for s in sns if algos[s].get("type") == "旗舰"]
    sk_list = [s for s in sns if algos[s].get("type") == "骨架"]
    print(f"\n### {AGENT_NAMES_CN.get(ag, ag)} (`{ag}`) — {len(sns)}个算法\n")
    if fg_list:
        print("**旗舰（P0）：**")
        for s in fg_list:
            a = algos[s]
            print(f"- `{s}` {a['name']} [{a['complexity']}] — {', '.join(a.get('scene',[])[:2])}")
    if sk_list:
        print("**骨架（P1）：**")
        for s in sk_list:
            a = algos[s]
            print(f"- `{s}` {a['name']} [{a['complexity']}] — {', '.join(a.get('scene',[])[:2])}")

# Type & complexity stats
print("\n\n## 统计摘要\n")
from collections import Counter
print("- 复杂度分布:", dict(Counter(a["complexity"] for a in algos.values())))
print("- 风险机制分布:", dict(Counter(a["risk_mechanism"] for a in algos.values())))
by_pri = Counter(a["priority"] for a in algos.values())
print(f"- 优先级分布: P0={by_pri.get('P0',0)} (旗舰), P1={by_pri.get('P1',0)} (骨架)")
