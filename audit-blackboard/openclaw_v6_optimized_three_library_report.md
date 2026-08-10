# OpenClaw V6 三库深度优化报告

## 当前盘点

- 早期 36 条 V6 OCR 候选：保留为历史草稿，不计入当前正式优化口径。
- 当前 deep + magazine 算法/规则/指标/证据包：871 条
- 当前规则指标库：2178 条
- 当前案例证据库：559 条
- 当前三库原始合计：3608 条

## 硬过滤优化后结果

- 算法候选库：359 条（剔除格式、目录、概述、通知、会议活动等弱算法资产）
- 规则指标库：2615 条（含从算法候选库硬降级的 10 条规则/复核资产）
- 案例证据库：559 条
- 优化版 OpenClaw staging：v5 135 条 + 硬过滤算法候选 359 条 = 494 条

## 优化动作

- 从算法候选库剥离证据包、会议活动、短讯、准则通知类噪声。
- 将规则包、指标包、内控包统一进入规则指标库。
- 硬性降级：格式、目录、前言、概述、重要性必要性、思维训练、通知活动等。
- 本轮从算法候选库硬降级：10 条。
- 对所有算法/规则/证据增加 `quality_score` 和 `quality_tier`。

## 算法候选库场景 Top 15

- 监督检查与经费舞弊: 83
- 预算执行与财政管理: 73
- 民生与社保医保: 57
- 农业农村审计: 39
- 金融审计: 26
- 税务审计: 22
- 绩效评价: 16
- 经济责任审计: 15
- 全场景通用: 9
- 能源与双碳审计: 8
- 工程与投资审计: 7
- 资源环境审计: 4

## 算法候选质量分布

- A: 355
- B: 4

## 规则指标类型分布

- audit_rule: 1945
- audit_rule_pack: 173
- indicator_pack: 158
- control_rule: 148
- control_pack: 96
- indicator_rule: 85
- downgraded_rule_or_evidence: 10

## 规则指标质量分布

- A: 54
- B: 177
- C: 1965
- D: 419

## 案例证据质量分布

- B: 513
- C: 18
- D: 28

## 已写入文件

- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_optimized_algorithm_candidate_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_optimized_algorithm_candidate_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_optimized_algorithm_candidate_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_optimized_algorithm_candidate_library.csv`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_optimized_rule_indicator_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_optimized_rule_indicator_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_optimized_rule_indicator_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_optimized_rule_indicator_library.csv`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_optimized_case_evidence_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_optimized_case_evidence_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_optimized_case_evidence_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_optimized_case_evidence_library.csv`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\algorithm_registry_v6_optimized_staging.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry_v6_optimized_staging.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\algorithms_by_scene_v6_optimized.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithms_by_scene_v6_optimized.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_optimized_three_library_manifest.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_optimized_three_library_manifest.json`

## 使用建议

先以优化版三库作为业务复核底稿。`algorithm_registry_v6_optimized_staging.json` 只装入硬过滤算法候选，规则指标和案例证据通过独立库关联。