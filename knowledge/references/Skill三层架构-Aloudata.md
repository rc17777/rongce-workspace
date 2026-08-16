# 三层Skill架构：从查数工具到高阶分析师

> 来源: Aloudata 团队（原创），2026-04-01
> 领域: AI Agent 架构设计 / OpenClaw Skill 最佳实践

## 三层架构

```
调度层: scheduled-report      → 录制分析流程 + 定时自动重跑
编排层: analysis-report        → 组织报告结构 + 调度子技能串成文档
能力层: metric-query + metric-attribution + anomaly-detection + forecast-simulation
```

## 四个新 Skill

| Skill | 功能 | 核心逻辑 |
|:------|:-----|:--------|
| anomaly-detection | 时序异常检测 | 3σ原则定基线→判断真异常vs正常波动 |
| forecast-simulation | 趋势预测+What-if | 线性外推+前提假设声明+边界情景设计 |
| analysis-report | 报告编排 | 不自己做分析，知道报告结构→调度子技能→串联叙事 |
| scheduled-report | 定时执行 | 录制对话分析流程→时间参数相对化→自动重跑 |

## 核心洞察

1. **Skill 不能批量生成** — "装进 Skill 之后，Agent 就在这个层面上运作"
2. **语义层 × Skill = 乘数效应** — 语义层提供数据基础，Skill 编码分析方法论
3. **分析闭环** — 发现问题 → 预测走势 → 压测边界 → 归因溯源 → 整合报告 → 自动重放
4. **Skill 的壁垒是分析深度** — 不是生成数量，是"知道什么场景下3σ合适、什么场景它会失灵"

## 融策可借鉴

### 三层映射

| Aloudata | 融策对应 | 差距 |
|:---------|:--------|:-----|
| 能力层 | data-analyst-cn / procurement-audit / apriori-audit | ✅ 已覆盖 |
| 编排层 | audit-plugin report-writer | ⚠️ 原型，需升级为 analysis-report 模式 |
| 调度层 | cron + audit_pipeline.py | ⚠️ 缺少"录制→定时重放"能力 |

### 可直接加载的 Skill（来自 ClawHub）

- anomaly-detection: 3σ时序异常检测 → 可用于审计异常数据筛查
- forecast-simulation: 趋势预测+What-if → 可用于预算执行预测/资金流向模拟
- analysis-report: 报告编排 → 可用于串联审计分析步骤生成报告
- scheduled-report: 定时执行 → 可用于审计巡检自动化
