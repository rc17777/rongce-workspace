# OpenClaw V6 杂志案例算法提炼报告

- 来源目录：`D:\openclaw-workspace\knowledge\11-杂志文献`
- OCR文件总数：463
- 整期期刊索引文件：28
- 文章/案例文件：435
- 生成杂志案例算法/规则/证据包：435
- 生成案例规则：870
- 生成案例证据：463
- 基准库：`C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry_v6_deep_staging.json`
- 基准库资产数：571
- 合并后 magazine staging 总资产：1006
- 编号冲突：0
- 名称完全冲突：0

## 资产类型分布

- 杂志案例算法: 261
- 杂志指标包: 66
- 杂志证据包: 43
- 杂志内控包: 41
- 杂志规则包: 24

## 优先级/复杂度

- 优先级：{'P1': 208, 'P0': 227}
- 复杂度：{'L2': 105, 'L3': 319, 'L4': 11}

## 场景分布 Top 20

- 金融审计: 226
- 预算执行与财政管理: 193
- 监督检查与经费舞弊: 176
- 财政与政府债务: 172
- 全场景通用: 139
- 招投标与政府采购: 84
- 民生与社保医保: 80
- 绩效评价: 77
- 农业农村审计: 52
- 国企审计: 42
- 税务审计: 40
- 资源环境审计: 5
- 工程与投资审计: 4
- 经济责任审计: 1

## 杂志来源分布

- 财政监督: 318
- 四川注册会计师: 94
- 审计观察: 18
- 中国注册会计师: 5

## 已写入文件

- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_magazine_case_algorithm_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_magazine_case_algorithm_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_magazine_case_rule_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_magazine_case_rule_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_magazine_case_evidence_library.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_magazine_case_evidence_library.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\algorithm_registry_v6_magazine_staging.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry_v6_magazine_staging.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\algorithms_by_scene_v6_magazine.json`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithms_by_scene_v6_magazine.json`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_magazine_case_algorithm_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_magazine_case_algorithm_library.csv`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_magazine_case_rule_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_magazine_case_rule_library.csv`
- outputs: `C:\Users\scrccpa\Documents\Codex\2026-08-08\new-chat-2\outputs\openclaw_v6_magazine_case_evidence_library.csv`
- openclaw: `C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\openclaw_v6_magazine_case_evidence_library.csv`

## 合并策略

本次没有覆盖 v5 或 v6 deep 主文件，而是新增 `algorithm_registry_v6_magazine_staging.json`。整期期刊大文件作为证据索引保留，拆分文章逐篇生成算法/规则/证据包。政策通知、准则指引归入规则/内控包；会议活动和短讯归入证据包；数据方法、审计案例、风险识别文章保留为案例算法。