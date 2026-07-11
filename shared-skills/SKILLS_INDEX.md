# SKILLS_INDEX.md — 技能索引

> 自动生成于 2026-07-06 · 15 个共享技能 · 版本生命周期: draft → reviewed → stable → deprecated

## 🔴 业务线技能（11个）

| 技能 | 业务线 | 难度 | 状态 | 核心方法 |
|------|--------|------|:---:|----------|
| `procurement-audit-models` | 招投标审计 | 高级 | 🟢 stable | 11层围标串标检测体系 |
| `audit-report-review` | 审计报告复核 | 高级 | 🟢 stable | 15+6维检查法+12条业务线校准 |
| `audit-jingze` | 经济责任审计 | 高级 | 🟢 stable | 四道关（立项/招投标/阴阳合同/控制价） |
| `budget-audit` | 收支审计+预算执行 | 中级 | 🟡 reviewed | 四模块（预算偏差/三公经费/非税/转移支付） |
| `engineering-audit` | 工程竣工决算 | 高级 | 🟡 reviewed | 四维检测（变更/造价/进度/合规） |
| `fiscal-supervision-model` | 财政监督检查 | 高级 | 🟡 reviewed | 30条识别规则+数据分析模型 |
| `perf-audit-checklist` | 预算绩效管理 | 中级 | 🟡 reviewed | 事前/事中/事后发现逻辑检查 |
| `special-fund-audit` | 专项资金审计 | 中级 | 🟡 reviewed | 四类资金（社保/教育/民政/保障房） |
| `subsidy-audit` | 政府补贴审计 | 中级 | 🟡 reviewed | 三阶段（申报/拨付/使用核查） |
| `energy-audit` | 能源审计+碳中和 | 中级 | 🔴 draft | 双模块（能耗单耗/碳排放） |
| `special-bond-audit` | 专项债审计 | 高级 | 🔴 draft | 四环节（发行/使用/管理/偿还） |

## 🟡 通用方法技能（4个）

| 技能 | 用途 | 难度 | 状态 | 核心工具 |
|------|------|------|:---:|----------|
| `financial-fraud-detection` | 财务造假检测 | 高级 | 🟢 stable | Benford定律 + 异常交易模式 |
| `apriori-audit` | 关联规则分析 | 高级 | 🟢 stable | Apriori算法（支持度/置信度/提升度） |
| `audit-text-mining` | 文本挖掘 | 中级 | 🟡 reviewed | 中文分词/词频/词云/关键词搜索 |
| `cot-capture` | 思维链沉淀 | 高级 | 🟡 reviewed | 审计老法师经验→结构化CoT数据集 |

---

## 版本状态说明

| 状态 | 含义 | 变更规则 |
|:----:|------|----------|
| 🔴 draft | 草稿，个人验证中 | 自由修改 |
| 🟡 reviewed | 已审核，可供团队试用 | 修改需开新分支 |
| 🟢 stable | 稳定版，正式使用 | 锁定，变更必须 base on 此版新建 draft |
| ⚫ deprecated | 已废弃 | 归档到 `_archived/` |

### 升级流程

```
draft ──PR审核通过──→ reviewed ──团队验证通过──→ stable ──不再维护──→ deprecated
  ↑                      │                         │
  └──── 发现问题 ────────┘                         │
                                                   └── 新建draft基于此版 ──→ ...
```

## 待补充业务线

以下业务线在个人库（`~/.openclaw/skills/`）中有 Skill，尚未标准化并入共享库：

- `audit-meeting-review` (会议记录审查·望闻问切)
- `audit-rectification` (审计整改标准化)
- `audit-risk-portrait` (审计风险画像)
- `audit-card-generator` (审计卡片生成)
- `audit-project-selection` (审计立项精准化)
- `penetrating-audit` (穿透式审计)
- `regulatory-audit-response` (监管审计应对)
- `rpa-audit-automation` (RPA自动化)
- `bim-engineering-audit` (BIM工程审计)
- `gov-subsidy-penetration-audit` (政府补贴穿透)
