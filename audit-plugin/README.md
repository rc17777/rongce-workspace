# 融策审计插件 (RongCe Audit Plugin)

> 基于 Anthropic claude-for-legal 架构思想，为融策会计师事务所 **政府专项审计** 定制的 AI 工作流。
>
> **核心定位**：解决政府专项审计的两大难点——
> 1. 政策文件吃不透 → **policy-digest** 深度解读
> 2. 问题深度广度不够、建议不可落地 → **finding-generator + recommendation-engine** 交叉分析

## 审计业务流程 → 插件流程

```
你的业务流程                    audit-plugin 对应
─────────────────────────────────────────────────
① 学习政策文件         ←→     policy-digest
② 写实施方案           ←→     implementation-plan
③ 数据分析             ←→     multi-source-analysis
                                  data-analysis-methods
   （查阅/访谈/实地/函证/
     穿行测试/财务核查/
     对比分析/复核计算 +
     描述性统计/相关性/
     回归/聚类/异常检测/
     关联规则/时间序列）
④ 做底稿+写报告+汇报   ←→     finding-generator
                              recommendation-engine
                              economic-responsibility-evaluator
                              work-paper
                              report-writer
⑤ 技能组织与持续优化   ←→     skill-dependency-graph
                              project-trajectory-recorder
                              skill-evolver
```

## 快速开始

### 1. 喂政策文件
```
/audit:policy-digest  D:\项目\政策文件\
```
一次性读入所有相关政策文件，自动提取：
- 关键要求与红线标准
- 时间节点
- 资金管理规定
- 绩效指标
- 可引用的政策依据条款

输出：填入 CLAUDE.md 的政策知识库部分。

### 2. 生成实施方案
```
/audit:implementation-plan
```
基于政策知识库 + 审计目的，自动生成：
- 审计范围与重点
- 审计方法组合
- 关键风险点预判
- 时间安排

输出：结构化实施方案草稿（DRAFT）。

### 3. 多源数据分析
```
/audit:multi-source-analysis
```
对接财务数据 + 业务数据 + 非结构化文本，按政策要求逐一对照。

### 4. 生成底稿 + 报告
```
/audit:work-paper      → 自动生成审计底稿
/audit:report-writer   → 自动生成审计报告 + 汇报材料
```

### 5. 经责审计量化评价（经济责任审计专用）
```
/audit:econ-responsibility   → 基于发现清单生成五维量化评分 + 责任认定 + 履职评价
```
适用于国企/事业单位领导干部经济责任审计，将"凭经验打分"变为标准化量化评价。
- 5大维度17项指标自动评分（权重30/25/25/12/8%）
- 直接责任/领导责任/无责任三级自动判定
- 5条撰写红线自动检查
- 评分卡可直接嵌入 report-writer 的经责报告模板

配套模板：`output/经济责任审计量化评价指标模板.xlsx`

## 命令索引

| 命令 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `/audit:policy-digest` | 政策文件解读 | 政策文件(PDF/Word) | 政策知识库（CLAUDE.md） |
| `/audit:implementation-plan` | 实施方案生成 | CLAUDE.md + 业主需求 | 实施方案草稿 |
| `/audit:multi-source-analysis` | 多源数据分析 | 财务+业务+文本数据 | 分析底稿 |
| `/audit:data-analysis-methods` | 数据分析方法指南 | 审计问题+数据 | 方法选择+代码模板+工具建议 |
| `/audit:finding-generator` | 问题发现与深度挖掘 | 分析结果 + 政策库 | 问题清单（含政策依据） |
| `/audit:recommendation-engine` | 可落地建议生成 | 问题清单 | 建议方案 |
| `/audit:work-paper` | 审计底稿生成 | 所有分析结果 | 标准化底稿 |
| `/audit:report-writer` | 报告+汇报材料 | 底稿 + 建议 | 审计报告、PPT汇报 |
| `/audit:econ-responsibility` | 经责审计量化评价 | 发现清单 + 被审计人信息 | 五维评分卡 + 责任认定 + 履职评价 |
| `/audit:skill-graph` | 技能依赖图构建与检索 | 技能清单+inputs/outputs声明 | 类型化技能依赖图+执行就绪技能链 |
| `/audit:trajectory` | 项目轨迹结构化记录 | 项目执行关键节点 | 轨迹JSONL+问题清单+复盘数据 |
| `/audit:evolve` | 技能进化分析 | 项目轨迹聚合+当前技能 | Refine/Create/Skip建议+版本记录 |

## 信任层设计

每个 Agent 的输出标注：
- ⚠️ **DRAFT — 需CPA复核**
- 📌 **政策依据**：引用具体文件名称、文号、条款
- 🔍 **置信度**：高/中/低
- 🚪 **关键判断需人类确认**：问题定性、处罚建议

## 插件结构

```
audit-plugin/
├── CLAUDE.md                    ← 政策知识库 + 审计方案（共享上下文）
├── README.md                    ← 本文件
├── .mcp.json                    ← 外部系统连接器
├── skills/
│   ├── policy-digest/           ← ① 政策文件解读
│   ├── implementation-plan/     ← ② 实施方案生成
│   ├── multi-source-analysis/   ← ③ 多源数据综合分析
│   ├── data-analysis-methods/   ← ③+ 数据分析方法（五步法+7大方法+工具选型）
│   ├── finding-generator/       ← ④ 问题发现与深度挖掘
│   ├── recommendation-engine/   ← ⑤ 可落地建议生成
│   ├── work-paper/              ← ⑥ 底稿生成
│   ├── report-writer/           ← ⑦ 报告+汇报材料
│   ├── economic-responsibility-evaluator/ ← ⑧ 经责审计量化评价
│   ├── skill-dependency-graph/  ← ⑨ 技能依赖图（GoS理论）
│   ├── project-trajectory-recorder/ ← ⑩ 项目轨迹记录（SkillClaw理论）
│   └── skill-evolver/           ← ⑪ 技能进化器（SkillClaw理论）
└── references/                  ← 方法论参考
    └── data-analysis-methodology.md  ← 数据分析方法论全文
```

## 与 claude-for-legal 的对齐

| claude-for-legal | audit-plugin | 说明 |
|-----------------|--------------|------|
| 冷启动面试 | policy-digest（政策文件喂入） | 把"律所方法论"换成"政策文件要求" |
| CLAUDE.md 实务档案 | CLAUDE.md 政策知识库+审计方案 | 共享上下文，串上下文不串流程 |
| 按领域拆 Agent | 按审计步骤拆 Agent | 每个 Agent 独立，都读 CLAUDE.md |
| 输出永远是草稿 | 输出永远是草稿 | DRAFT + 来源 + 置信度 + Gate |

---

## 更新日志

### v3.1 — 2026-06-01：人机边界增强

> 来源：「芮听柠说」《AI扫完数据，然后呢？这五件事它永远做不了》
> 归档：`knowledge/references/AI扫完数据五件事它永远做不了-芮听柠说.md`

**核心命题：** AI在审计中的物理边界——明确AI停在哪、人的价值从哪开始。

三项技能增强：

| 技能 | 新增内容 | 对应"AI做不了的事" |
|------|---------|-------------------|
| **multi-source-analysis** | 五维交叉验证框架（财务/实物/访谈/外部/时间） + "单一来源不支撑结论"原则 | ④跨信息源交叉验证 |
| **finding-generator** | ①舞弊逻辑逆向推演（攻击者视角6条路径）②职业怀疑三步校准法 ③非结构化信息解读与访谈观察笔记规范 | ①②③舞弊推演+怀疑校准+非结构化解读 |
| **report-writer** | 签字前结论可靠性检验四问 + DRAFT→READY FOR SIGNATURE 门控 | ⑤结论责任承担与判断力 |

**新增参数：**
- `/audit:finding-generator --mode attacker-view` — 攻击者视角逆向推演
- `/audit:finding-generator --include-unstructured` — 读访谈观察笔记
- `/audit:finding-generator --calibrate` — 职业怀疑三步校准
- `/audit:report-writer --self-check` — 签字前四问自检

---

*"审计缺的不是 AI 能力，是把审计方法论翻译成 AI 可理解语言的中间层。"*
*—— 对于政府专项审计，这个中间层的关键是：政策文件结构化 + 多源数据交叉分析。*
