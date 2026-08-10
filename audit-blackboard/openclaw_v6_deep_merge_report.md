# OpenClaw V6 全量深挖合并报告

- OCR来源：`E:\2026\审计方法&政策文件\_ocr_output`
- 基准库：`C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry.json`
- v5现有算法：135
- 本次新增算法/规则/指标/证据包：436
- 合并后v6 staging总资产：571
- 规则指标库：1308 条
- 案例证据库：96 条
- 55本书覆盖校验：每本 5-10 条，违规文件数 0

## 资产类型分布

- 算法候选: 117
- 规则包: 114
- 指标包: 92
- 内控包: 55
- 案例规则包: 37
- 证据包: 21

## 来源分布

- book: 399
- article: 37

## 书籍目录产出

- 通用: 136
- 预算: 107
- 绩效: 53
- 经责: 52
- 能源: 33
- 工程: 18

## 场景分布 Top 20

- 绩效评价: 336
- 监督检查与经费舞弊: 250
- 预算执行与财政管理: 196
- 工程与投资审计: 100
- 经济责任审计: 88
- 招投标与政府采购: 74
- 资源环境审计: 61
- 金融审计: 40
- 农业农村审计: 37
- 能源与双碳审计: 33
- 财政与政府债务: 31
- 国企审计: 30
- 民生与社保医保: 21
- 税务审计: 8

## 优先级与动作

- 优先级：{'P0': 42, 'P1': 394}
- 合并动作：{'新增': 436}
- 编号冲突：0
- 名称完全冲突：0

## 已写入文件

- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_deep_algorithm_package_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_deep_algorithm_package_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_deep_rule_indicator_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_deep_rule_indicator_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_deep_case_evidence_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_deep_case_evidence_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\algorithm_registry_v6_deep_staging.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry_v6_deep_staging.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\algorithms_by_scene_v6_deep.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithms_by_scene_v6_deep.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_deep_algorithm_package_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_deep_algorithm_package_library.csv`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_deep_rule_indicator_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_deep_rule_indicator_library.csv`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_deep_case_evidence_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_deep_case_evidence_library.csv`

## 合并策略

本次没有覆盖 v5 主库 `algorithm_registry.json`，而是新增 `algorithm_registry_v6_deep_staging.json` 和 `algorithms_by_scene_v6_deep.json`。建议先做业务复核、字段映射和回测，再决定是否切换主库。

## 场景清洗补充

已按 OCR 目录和书名对场景做二次清洗，避免工程、预算、能源等书籍被关键词误分到弱相关场景。
