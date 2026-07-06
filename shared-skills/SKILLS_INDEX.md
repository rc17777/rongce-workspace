# SKILLS_INDEX.md — 技能索引

> 自动生成于 2026-07-06 · 15 个共享技能

## 🔴 业务线技能（11个）

| 技能 | 业务线 | 核心方法 | 文件数 |
|------|--------|----------|--------|
| `audit-jingze` | 经济责任审计 | 四道关（立项/招投标/阴阳合同/控制价） | 1 |
| `budget-audit` | 收支审计+预算执行 | 四模块（预算偏差/三公经费/非税/转移支付） | 7 |
| `special-fund-audit` | 专项资金审计 | 四类资金（社保/教育/民政/保障房） | 7 |
| `procurement-audit-models` | 招投标审计 | 11层围标串标检测体系 | 23 |
| `engineering-audit` | 工程竣工决算 | 四维检测（变更/造价/进度/合规） | 7 |
| `energy-audit` | 能源审计+碳中和 | 双模块（能耗单耗/碳排放） | 5 |
| `subsidy-audit` | 政府补贴审计 | 三阶段（申报/拨付/使用核查） | 6 |
| `fiscal-supervision-model` | 财政监督检查 | 30条识别规则+数据分析模型 | 4 |
| `audit-report-review` | 审计报告复核 | 15+6维检查法+12条业务线校准 | 2 |
| `perf-audit-checklist` | 预算绩效管理 | 事前/事中/事后发现逻辑检查 | 1 |
| `special-bond-audit` | 专项债审计 | 发行/使用/管理/偿还四环节 | 2 |

## 🟡 通用方法技能（4个）

| 技能 | 用途 | 核心工具 |
|------|------|----------|
| `financial-fraud-detection` | 财务造假检测 | Benford定律 + 异常交易模式 |
| `apriori-audit` | 关联规则分析 | Apriori算法（围标/共现/缺失关联） |
| `audit-text-mining` | 文本挖掘 | 中文分词/词频/词云/关键词搜索 |
| `cot-capture` | 思维链沉淀 | 审计老法师经验→结构化CoT数据集 |

## 🟢 待补充

以下业务线技能在共享仓库中，但 SKILL.md 尚需完善：

- `audit-meeting-review` (会议记录审查)
- `audit-rectification` (审计整改)
- `audit-risk-portrait` (风险画像)
- `penetrating-audit` (穿透式审计)
- `regulatory-audit-response` (监管审计应对)
- `rpa-audit-automation` (RPA自动化)
- `gov-subsidy-penetration-audit` (补贴穿透)

## 使用指南

每个技能目录包含：
- `SKILL.md` — 核心指令文件（Agent 读取入口）
- `references/` — 参考资料、方法论文档
- `scripts/` — 可执行分析脚本

在 Agent 对话中引用技能：
```
用 procurement-audit-models 分析这个开标记录
```
或直接发 SKILL.md 路径给 Agent 作为 system prompt 的补充。
