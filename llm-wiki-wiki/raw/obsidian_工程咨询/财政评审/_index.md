---
type: 业务驾驶舱
title: "财政评审驾驶舱"
business_line: "财政评审"
scene: "财政评审"
audit_stage: "全流程"
document_type: "业务驾驶舱"
keywords: [财政评审, 工作流, 融策]
source: "融策自建"
source_date: 2026-07-11
effective_date: 2026-07-11
validity: "内部有效"
evidence_level: "工作指引"
source_path: ""
status: "active"
updated: 2026-07-11
---
# 财政评审｜业务驾驶舱

> 从项目启动到报告整改的可执行入口，不是文章目录。

## 立即开工
- [[工程咨询/财政评审/项目启动|① 项目启动]]
- [[工程咨询/财政评审/资料清单|② 资料清单]]
- [[工程咨询/财政评审/风险与识别规则|③ 风险与识别规则]]
- [[工程咨询/财政评审/现场核查与访谈|④ 现场核查与访谈]]
- [[工程咨询/财政评审/底稿报告与复核|⑤ 底稿报告与复核]]

## 项目与知识动态视图
```dataview
TABLE audit_stage AS 环节, document_type AS 类型, updated AS 更新
FROM "工程咨询/财政评审"
WHERE file.name != "_index"
SORT audit_stage ASC
```

## 场景入口
- [[场景/场景-财政评审]]
