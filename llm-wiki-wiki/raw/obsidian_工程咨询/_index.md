---
type: 业务总览
title: "工程咨询业务驾驶舱"
business_line: "工程咨询"
scene: "工程咨询"
audit_stage: "全流程"
document_type: "业务总览"
keywords: [工程咨询, 工作流, 融策]
source: "融策自建"
source_date: 2026-07-11
effective_date: 2026-07-11
validity: "内部有效"
evidence_level: "工作指引"
source_path: ""
status: "active"
updated: 2026-07-11
---
# 工程咨询业务驾驶舱

- [[工程咨询/预算编制/_index|预算编制]]
- [[工程咨询/财政评审/_index|财政评审]]
- [[工程咨询/工程结算/_index|工程结算]]
- [[工程咨询/全过程工程咨询/_index|全过程工程咨询]]

```dataview
TABLE business_line AS 业务线, audit_stage AS 环节, updated AS 更新
FROM "工程咨询"
WHERE type != "业务总览"
SORT business_line ASC
```
