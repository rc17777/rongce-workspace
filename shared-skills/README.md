# 融策 Shared Skills — 团队共享技能仓库

> v0.1 · 2026-07-06 · 从 Nacos Skill Registry 理念落地

## 这是什么

融策团队 AI Agent 技能的**统一仓库**。类比 Nacos Skill Registry，但轻量级：
- **Git 版本控制** → 每次修改有记录、能回滚
- **三类分区** → 业务技能 / 审计方法 / 通用工具
- **统一 SKILL.md 规范** → 任何 Agent 都能读取

## 目录结构

```
shared-skills/
├── README.md              ← 本文件
├── SKILLS_INDEX.md        ← 技能索引
├── _business/             ← 12大业务线技能
│   ├── audit-jingze/         经责审计
│   ├── budget-audit/         收支/预算审计
│   ├── special-fund-audit/   专项资金审计
│   ├── procurement-audit/    招投标审计
│   ├── engineering-audit/    工程审计
│   ├── energy-audit/         能源审计
│   ├── subsidy-audit/        政府补贴审计
│   ├── fiscal-supervision/   财政监督检查
│   ├── audit-report-review/  审计报告复核
│   ├── perf-audit-checklist/ 绩效审计检查
│   └── special-bond-audit/   专项债审计
├── _methods/              ← 通用审计分析方法
│   ├── financial-fraud/      财务造假检测
│   ├── apriori-audit/        关联规则分析
│   ├── audit-text-mining/    文本挖掘
│   └── cot-capture/          思维链沉淀
└── _tools/                ← 通用工具（模板/脚本）
    └── templates/            报告/底稿模板
```

## 使用方式

### 在 OpenClaw 中使用
将 `shared-skills/` 路径添加到 OpenClaw 的 `skillsPath` 配置中。

### 在其他 Agent 中使用
每个 Skill 目录结构标准（SKILL.md + references/ + scripts/），兼容 Claude Code / Codex / Cursor 等。

### 团队协作
```bash
git pull                    # 获取最新技能
git checkout -b skill-xxx   # 修改某技能前开分支
# 修改 SKILL.md 后
git add . && git commit -m "更新经责审计四道关 v1.1"
git push
```

## 质量标准

提交到 shared-skills 的 Skill 必须满足：
- [x] 有完整的 SKILL.md（含 `description` frontmatter）
- [x] 触发词明确
- [x] 引用资料（references/）齐全
- [x] 不含敏感信息（内部系统地址、客户数据等）

## 版本策略

| 阶段 | 含义 | Git 操作 |
|------|------|----------|
| draft | 草稿，个人测试中 | feature 分支 |
| reviewed | 已审核，可团队测试 | PR → main |
| stable | 稳定版，正式使用 | tag v1.0.0 |
| deprecated | 已废弃 | 归档到 `_archived/` |

---

> 「当每个人都在写 Prompt 时，团队真正需要的不是更多 Prompt，而是一套能被共用、被迭代、被审核、被分发的 Skills 体系。」— Nacos Skill Registry 文章启示
