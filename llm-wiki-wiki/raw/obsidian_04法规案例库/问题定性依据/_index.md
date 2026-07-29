---
type: 定性索引
title: "问题定性依据"
business_line: "通用"
scene: "通用"
audit_stage: "全流程"
document_type: "定性索引"
keywords: [通用, 工作流, 融策]
source: "融策自建"
source_date: 2026-07-11
effective_date: 2026-07-11
validity: "内部有效"
evidence_level: "工作指引"
source_path: ""
status: "active"
updated: 2026-07-11
---
# 问题定性依据

```dataview
TABLE business_line AS 业务线, validity AS 有效性, updated AS 更新时间
FROM "04-法规案例库/问题定性依据"
WHERE file.name != "_index"
SORT updated DESC
```
