---
type: 业务驾驶舱
title: "预算编制驾驶舱"
business_line: "预算编制"
scene: "预算编制"
audit_stage: "全流程"
document_type: "业务驾驶舱"
keywords: [预算编制, 工作流, 融策]
source: "融策自建"
source_date: 2026-07-11
effective_date: 2026-07-11
validity: "内部有效"
evidence_level: "工作指引"
source_path: ""
status: "active"
updated: 2026-07-11
---
# 预算编制｜业务驾驶舱

> 从项目启动到报告整改的可执行入口，不是文章目录。

## 立即开工
- [[工程咨询/预算编制/项目启动|① 项目启动]]
- [[工程咨询/预算编制/资料清单|② 资料清单]]
- [[工程咨询/预算编制/风险与识别规则|③ 风险与识别规则]]
- [[工程咨询/预算编制/现场核查与访谈|④ 现场核查与访谈]]
- [[工程咨询/预算编制/底稿报告与复核|⑤ 底稿报告与复核]]

## 项目与知识动态视图
```dataview
TABLE audit_stage AS 环节, document_type AS 类型, updated AS 更新
FROM "工程咨询/预算编制"
WHERE file.name != "_index"
SORT audit_stage ASC
```

## 场景入口
- [[场景/场景-预算编制]]
