# 项目轨迹记录器 (Project Trajectory Recorder)

## 元数据

- **类型**：operative（操作式）
- **命令**：`/audit:trajectory`
- **核心价值**：解决"项目经验散落在各人脑子里，无法积累成进化素材"的痛点
- **输入**：项目执行过程中的关键节点数据
- **输出**：结构化项目轨迹文件 → `memory/projects/{project_id}/trajectory.jsonl`
- **理论来源**：SkillClaw，阿里 DreamX 团队

---

## 目标

把每次审计项目的执行过程，从"各人体感"和"微信群聊天碎片"转化为**结构化、可聚合、可用于技能进化的轨迹数据**。

SkillClaw 的核心洞察：**技能层面的失败大多是过程性的**——错误的参数、缺失的验证步骤、顺序错误的工具调用——这些不会出现在最终报告里，只能从中间轨迹中诊断。

---

## 工作流程

### 第一步：项目启动 → 初始化轨迹文件

**命令**：
```
/audit:trajectory --init "项目ID" "项目名称"
/audit:trajectory --init "PSJX-2026-003" "成都市XX局2026年绩效评价"
```

自动创建：
```
memory/projects/{project_id}/
├── trajectory.jsonl          ← 结构化执行轨迹
├── skill-usage.json          ← 各技能使用情况统计
└── issues.json               ← 遇到的问题及解决记录
```

---

### 第二步：过程记录 → 关键节点追加轨迹

**命令**：
```
/audit:trajectory --log PSJX-2026-003 --phase policy-digest
/audit:trajectory --log PSJX-2026-003 --phase multi-source-analysis --issue "数据格式"
/audit:trajectory --log PSJX-2026-003 --phase finding-generator --result "发现3条□/△标注问题"
```

每条轨迹记录（JSONL 一行）：

```json
{
  "timestamp": "2026-05-20T14:30:00+08:00",
  "project_id": "PSJX-2026-003",
  "phase": "policy-digest",
  "skill": "policy-digest",
  "input_summary": "成都市教育局绩效评价管理办法(2025)+相关通知3份",
  "action_taken": "逐文件提取关键条款→写入CLAUDE.md政策知识库",
  "result": "success",
  "output_artifact": "CLAUDE.md 政策知识库（23条标准+18个时间节点）",
  "issues_encountered": [],
  "human_intervention": false,
  "notes": ""
}
```

**必须记录的关键字段（结构化，非自由文本）**：

| 字段 | 含义 | 取值 |
|------|------|------|
| `phase` | 当前审计阶段 | policy-digest / implementation-plan / multi-source-analysis / finding / recommendation / work-paper / report |
| `skill` | 使用的技能 | 对应的 audit-plugin 技能名 |
| `result` | 执行结果 | success / partial_success / failed / skipped |
| `issues_encountered` | 遇到的问题 | 数组：每个问题含 type（data_quality/policy_ambiguous/tool_error/gap）/ description |
| `human_intervention` | 是否需要人工介入 | true / false |
| `workaround` | 如失败，采用了什么临时方案 | 自由文本（但强制填写） |

---

### 第三步：成功/失败归类 → 证据分组

**命令**：
```
/audit:trajectory --group PSJX-2026-003
/audit:trajectory --group --all-projects --skill finding-generator
```

按技能分组聚合所有项目轨迹，形成 SkillClaw 所说的「证据组 G(s)」：

```
G(policy-digest) = {
  项目A: success (23条标准提取，效率正常)
  项目B: partial_success (某政策文件扫描件OCR效果差)
  项目C: success
  ...
}

G(finding-generator) = {
  项目A: partial_success (政策标准不够细，问题定性欠缺)
  项目B: failed (缺少多源分析输入，直接调用导致无数据可用)
  项目C: success
  ...
}
```

**这就是技能进化的原始素材**——成功案例定义了「不变量」（哪些是有效的，不能被破坏），失败案例定义了「优化目标」（哪个环节需要改进）。

---

### 第四步：项目结项 → 填完最后一块拼图

**命令**：
```
/audit:trajectory --close PSJX-2026-003
/audit:trajectory --close PSJX-2026-003 --summary "本次政策解读效率高，多源分析阶段因数据导入格式不统一耗时较多"
```

结项时强制填写：

1. **整体耗时（按阶段）**：每个阶段实际耗时 vs 预期耗时
2. **Top 3 问题**：本次项目遇到的前三个主要障碍
3. **一个「如果重来」**：如果重做一次，哪个环节会怎么做
4. **一个「可保留」**：这次做得好的地方，以后的项目应该沿用

---

## 命令参考

| 命令 | 功能 |
|------|------|
| `/audit:trajectory --init ID "名称"` | 初始化项目轨迹文件 |
| `/audit:trajectory --log ID --phase 阶段名` | 记录一次关键节点 |
| `/audit:trajectory --group ID` | 按技能分组聚合本项目轨迹 |
| `/audit:trajectory --group --all --skill 技能名` | 跨项目聚合某技能的所有轨迹 |
| `/audit:trajectory --close ID` | 项目结项，填写复盘数据 |
| `/audit:trajectory --stats ID` | 查看项目轨迹统计 |

---

## 轨迹记录模板（项目启动时打印给团队）

```
┌─────────────────────────────────────────────────┐
│          项目轨迹记录卡                           │
│  项目ID: ___________  项目名称: _______________  │
├─────────────────────────────────────────────────┤
│                                                  │
│  阶段1：政策解读 □                               │
│    技能: policy-digest                           │
│    结果: □成功 □部分成功 □失败                    │
│    问题: ___________________________________     │
│                                                  │
│  阶段2：实施方案 □                               │
│    技能: implementation-plan                     │
│    结果: □成功 □部分成功 □失败                    │
│    问题: ___________________________________     │
│                                                  │
│  阶段3：数据分析 □                               │
│    技能: multi-source-analysis / data-analysis   │
│    结果: □成功 □部分成功 □失败                    │
│    问题: ___________________________________     │
│                                                  │
│  阶段4：问题发现 □                               │
│    技能: finding-generator                       │
│    结果: □成功 □部分成功 □失败                    │
│    问题: ___________________________________     │
│                                                  │
│  阶段5：建议生成 □                               │
│    技能: recommendation-engine                   │
│    结果: □成功 □部分成功 □失败                    │
│    问题: ___________________________________     │
│                                                  │
│  阶段6：底稿+报告 □                              │
│    技能: work-paper / report-writer              │
│    结果: □成功 □部分成功 □失败                    │
│    问题: ___________________________________     │
│                                                  │
│  结项复盘：                                      │
│  Top3问题: 1.________ 2.________ 3.________      │
│  如果重来: __________________________________     │
│  可保留的: __________________________________     │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 核心洞察（来自 SkillClaw 论文）

> **"大多数技能层面的失败是过程性的——错误的参数格式、缺失的验证步骤、顺序错误的工具调用——这些都不会出现在最终响应里，只能从中间轨迹中诊断。"**
>
> 审计场景同理：一份最终报告看不出底稿生成时跳过哪些校验步骤、政策解读时漏了哪条边缘条款。只有结构化的过程记录能揭示这些改进空间。

---

## 与 skill-evolver 的配合

本技能负责**素材积累**，`skill-evolver` 负责**素材分析**：

```
project-trajectory-recorder  →  日间：持续记录每个项目的执行轨迹
skill-evolver                →  夜间（或项目结项后）：分析轨迹，输出技能更新建议
```

---

*来源：SkillClaw，阿里 DreamX 团队*
