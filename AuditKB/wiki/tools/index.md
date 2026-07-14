# 工具技能索引

> 整合时间：2026-06-03
> 更新频率：随技能创建/更新自动维护

## PPT/演示文稿生成

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| **audit-report-ppt** | 审计报告/咨询报告PPT生成 | 做PPT/生成PPT/汇报材料/审计报告PPT |

## 审计数据分析

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| audit-data-analyst | 审计数据全流程分析（SQL/Python/异常检测） | 数据分析/异常检测/数据清洗 |
| audit-sql-patterns | SQL模板+4大案例（法院/农业险/医保/公积金） | SQL审计/查询模板 |
| audit-anomaly-detect | 异常值自动发现（Z分数/IQR/孤立森林） | 异常检测/离群点 |
| aloudata-anomaly-detection | 指标异常检测 | 指标监控/异常告警 |

## 报告生成

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| audit-report-structured | 标准审计报告生成 | 生成报告/审计报告 |
| audit-report-writer | 审计报告写作辅助 | 写报告/报告润色 |
| audit-capa-tracker | 整改问题跟踪 | 整改跟踪/整改状态 |

## 取证与核查

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| audit-scan-to-text | 扫描件/照片/PDF取证材料OCR | 扫描件/OCR/图片识别 |
| audit-contract-analyze | 招投标/采购合同合规分析 | 合同审查/合同分析 |
| audit-evidence-three-point | 审计证据三核对 | 证据充分/取证 |
| audit-law-check | 审计/财政法规检查 | 法规检查/合法性 |

## 政策监控

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| audit-policy-monitor | 审计/财政最新政策变化监控 | 政策变化/法规更新 |
| audit-pricing-monitor | 两新补贴价格备案真实性检查 | 价格检查/补贴审计 |
| audit-watchdog | 快速判断是否触碰审计红线 | 红线判断/违规判断 |

## 政府审计专项

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| rongce-gov-audit | 政府审计核心技能（90个技能之首） | 政府审计/经责审计/预算执行 |
| two-new-audit-checklist | 家电以旧换新/数码购新补贴审计清单 | 两新/以旧换新/补贴审计 |
| two-heavy-audit-checklist | 两重建设项目审计清单 | 两重/基建/项目审计 |
| eco-responsibility-audit | 经济责任审计全流程 | 经责审计/领导干部审计 |
| bid-collusion-audit | 串标围标审计（PDF元数据/关系图谱） | 串标/围标/招投标审计 |

## 文档处理

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| officecli-docx | Word文档操作（生成/编辑/格式） | Word/文档/DOCX |
| officecli-pptx | PowerPoint操作 | PPT/演示文稿 |
| officecli-xlsx | Excel操作 | Excel/XLSX |
| word-cn-format | Word中文格式标准化 | 中文格式/格式标准化 |

## 策略咨询

| 技能名 | 功能 | 触发词 |
|--------|------|--------|
| mbb-strategist | McKinsey/BCG/Bain战略框架 | 战略/咨询/框架 |
| brainstorm | 头脑风暴 | 头脑风暴/想法 |
| multi-round-design | 多轮迭代设计法 | 设计/迭代方案 |

## 参考：技能体系架构

```
受众层：audit-report-ppt（PPT生成）← 本页新增
       audit-report-writer（文字报告）
素材层：audit-data-analyst / audit-sql-patterns（数据支撑）
       audit-scan-to-text（取证材料）
工具层：officecli-docx/pptx/xlsx（文档生成）
       audit-law-check / audit-contract-analyze（合规审查）
保障层：skill-vetter（质量审查）
       audit-capa-tracker（整改跟踪）
```

## 🔗 逻辑链

本文逻辑链是"清单遍历型"型：

```
技能目录（AuditKB/wiki/tools/index.md）
  ↓ 按功能分类（PPT/数据分析/报告/取证/政策/政府专项/文档/策略）
  ↓ 按触发词索引（便于AI自动调用）
  ↓ 技能体系架构图（从受众到保障的分层）
```

**关键特征**：按功能域+触发词双索引，支撑AI技能自动调用
**与相似条目的区别**：这是技能索引工具页，不是案例库也不是规则库