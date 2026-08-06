# -*- coding: utf-8 -*-
"""Debug performance_evaluator assignment"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
reg = json.load(open(r"C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry.json", encoding="utf-8"))
algo = reg["algorithms"]
for sn in ["FUND-FRAUD-001", "ENV-CHECKLIST-001", "CONCESS-FEE-001", "PERF2-001", "PERF2-002", "PERF2-003", "PERF2-004", "PERF-COST-001", "PERF-OUTLIER-001", "PERF-DEVIATION-001"]:
    a = algo.get(sn)
    if a:
        print(f"{sn}: agents={a['assigned_agents']} hint='{a['agent_hint']}'")
    else:
        print(f"{sn}: NOT FOUND")
print("\nperformance_evaluator list:", reg["agent_algorithm_map"]["performance_evaluator"])
