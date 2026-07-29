---
type: 业务驾驶舱
title: "采购招投标审计驾驶舱"
business_line: "采购招投标审计"
scene: "采购招投标审计"
audit_stage: "全流程"
document_type: "业务驾驶舱"
keywords: [采购招投标审计, 工作流, 融策]
source: "融策自建"
source_date: 2026-07-11
effective_date: 2026-07-11
validity: "内部有效"
evidence_level: "工作指引"
source_path: ""
status: "active"
updated: 2026-07-11
---
# 采购招投标审计｜业务驾驶舱

> 从项目启动到报告整改的可执行入口，不是文章目录。

## 立即开工
- [[02-主题数据库/采购招投标审计/项目启动|① 项目启动]]
- [[02-主题数据库/采购招投标审计/资料清单|② 资料清单]]
- [[02-主题数据库/采购招投标审计/风险与识别规则|③ 风险与识别规则]]
- [[02-主题数据库/采购招投标审计/现场核查与访谈|④ 现场核查与访谈]]
- [[02-主题数据库/采购招投标审计/底稿报告与复核|⑤ 底稿报告与复核]]

## 项目与知识动态视图
```dataview
TABLE audit_stage AS 环节, document_type AS 类型, updated AS 更新
FROM "02-主题数据库/采购招投标审计"
WHERE file.name != "_index"
SORT audit_stage ASC
```

## 场景入口
- [[场景/场景-采购招投标审计]]
