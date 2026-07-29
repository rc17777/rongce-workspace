---
type: 业务驾驶舱
title: "绩效评价驾驶舱"
business_line: "绩效评价"
scene: "绩效评价"
audit_stage: "全流程"
document_type: "业务驾驶舱"
keywords: [绩效评价, 工作流, 融策]
source: "融策自建"
source_date: 2026-07-11
effective_date: 2026-07-11
validity: "内部有效"
evidence_level: "工作指引"
source_path: ""
status: "active"
updated: 2026-07-11
---
# 绩效评价｜业务驾驶舱

> 从项目启动到报告整改的可执行入口，不是文章目录。

## 立即开工
- [[02-主题数据库/绩效评价/项目启动|① 项目启动]]
- [[02-主题数据库/绩效评价/资料清单|② 资料清单]]
- [[02-主题数据库/绩效评价/风险与识别规则|③ 风险与识别规则]]
- [[02-主题数据库/绩效评价/现场核查与访谈|④ 现场核查与访谈]]
- [[02-主题数据库/绩效评价/底稿报告与复核|⑤ 底稿报告与复核]]

## 项目与知识动态视图
```dataview
TABLE audit_stage AS 环节, document_type AS 类型, updated AS 更新
FROM "02-主题数据库/绩效评价"
WHERE file.name != "_index"
SORT audit_stage ASC
```

## 场景入口
- [[场景/场景-绩效评价]]
