# 我把数据分析流程做成了一个AI Skill

> 来源：公众号「数据打工人的自我修养」，作者「数你皮」
> 日期：2026-05-23 采集
> 存档路径：已整合到 data-analyst-cn v2.0

## 核心观点

- AI能完成数据分析 90% 的工作，但最后 10% 靠分析师
- 作者用 Claude Code + Rust 写贴图软件失败：AI 写完代码但跑崩，没有专业能力无法修复
- 市场本质是供需，关键是成为少数人

## 实际工作流（6步）

1. 需求分析
2. 提示词 → AI 写 SQL
3. 审核修改 SQL → 执行导出数据集
4. 提示词 + data-analysis skill → HTML 报告
5. AI 校验报告数据
6. 人工审核修改

## Skill 依赖设计

- sql-generation（SQL生成skill）
- Business_Overview.md（业务知识文档）

## 分析框架

- 五步法：数据理解 → 指标定义 → 方法选择 → 洞察提取 → 报告输出
- CRVA原则：Concrete / Relevant / Valuable / Actionable
- 洞察格式：【发现】{数据事实} 【含义】{业务解释} 【建议】{行动方向}

## 分析方法库（6类）

趋势分析 | 异常检测 | 根因分析 | 对比分析 | 关联分析 | 预测建模

## 对融策的借鉴

1. 依赖链设计：sql-generation → data-analysis 管道式协作
2. CRVA洞察格式：直接可用于审计报告问题发现
3. 已整合到 data-analyst-cn v2.0
