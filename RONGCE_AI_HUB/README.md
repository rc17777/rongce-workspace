# 融策 AI 统一中枢

> 目的：把以往的技能、记忆、知识库统一成一个“可检索、可调用、可维护”的入口，而不是把所有内容粗暴合并成一个巨大文件。

## 目录结构

```text
RONGCE_AI_HUB/
├── README.md                 # 本文件：统一入口
├── ROUTING.md                # 调用规则：什么问题用什么来源
├── indexes/
│   ├── skills.json            # 当前已安装技能索引
│   ├── memory.json            # 长期记忆/日记/记忆库索引
│   └── knowledge.json         # Obsidian 知识库一级目录索引
├── business-lines/           # 12大业务线标准文件（2026-07-14建）
│   ├── 经济责任审计.md
│   ├── 收支审计.md
│   ├── 预算执行审计.md
│   ├── 专项资金审计.md
│   ├── 往来款清理.md
│   ├── 招投标审计.md
│   ├── 国企审计.md
│   ├── 成本效益审计.md
│   ├── 能源审计.md
│   ├── 工程竣工决算财务审计.md
│   ├── 预算绩效管理.md
│   └── 政府补贴审计.md
├── models/
│   └── 专项审计报告AI复核模型_v2.0.md  # 融策报告复核标准模型
├── rule-library/
│   ├── README.md              # 审计规则库入口
│   ├── rule-template.md       # 单条规则标准模板
│   ├── first-50-extraction-tasks.md # 首批50条规则抽取任务表
│   └── case-to-rule-workflow.md     # 从案例到规则的提炼流程
└── ROADMAP.md                # 建设路线图
```

## 三类资产如何“合一”

### 1. 技能 Skill

实际位置：

- `C:\Users\scrccpa\.openclaw\skills`

用途：

- 做事的方法、流程、脚本、工具调用说明。
- 例如审计报告复核、串标检测、PPT、图像生成、draw.io、智析等。

使用原则：

- 用户需求命中某个技能时，先读对应 `SKILL.md`。
- 不把技能正文全部塞进记忆，避免上下文爆炸。

### 2. 记忆 Memory

实际位置：

- `C:\Users\scrccpa\.openclaw\workspace\MEMORY.md`
- `C:\Users\scrccpa\.openclaw\workspace\memory\`
- `C:\Users\scrccpa\.openclaw\memory\main.sqlite`

用途：

- 用户偏好、公司背景、已做事项、系统经验教训。

使用原则：

- 涉及“以前说过/之前做过/我的偏好/历史项目/待办/日期/人员”时，必须先查 memory。
- 不把隐私记忆扩散到群聊或外部文件。

### 3. 知识库 Knowledge Base

实际位置：

- `C:\Users\scrccpa\Documents\Obsidian Vault`

用途：

- 审计文章、案例、法规、方法论、OCR资料、wiki、raw资料。

使用原则：

- 涉及审计知识、案例、法规、方法论、报告素材时，先按索引定位目录，再读取相关文档。
- 知识库是内容来源，不等同于记忆；引用时要尽量说明来源路径。

### 4. 标准模型 Model

实际位置：

- `C:\Users\scrccpa\.openclaw\workspace\RONGCE_AI_HUB\models`

用途：

- 沉淀融策内部可复用的方法模型、质控矩阵、评分规则和底稿模板。
- 例如专项审计报告AI复核模型、项目风险画像模型、串标检测模型等。

当前模型：

- `models/专项审计报告AI复核模型_v2.0.md`：四层十五维、三类证据、四级风险、五张底稿的报告复核模型。

使用原则：

- 涉及报告复核、质量控制、底稿闭环时，先调用对应模型，再结合技能和知识库执行。
- 模型负责“标准和结构”，技能负责“怎么操作”，知识库负责“法规案例和素材”。

### 5. 审计规则库 Rule Library

实际位置：

- `C:\Users\scrccpa\.openclaw\workspace\RONGCE_AI_HUB\rule-library`

用途：

- 将 Obsidian 案例、历史底稿、公开审计案例、政策法规中的已验证问题，提炼为可执行、可复核、可进入底稿的规则资产。
- 服务文本分析审计工具一期五个模块：会议纪要、合同、凭证、人员、投标/报告/验收文本相似度。

当前文件：

- `rule-library/README.md`：规则库定位、分级和模块说明。
- `rule-library/rule-template.md`：单条规则标准颗粒度模板。
- `rule-library/first-50-extraction-tasks.md`：首批50条规则抽取任务表。
- `rule-library/case-to-rule-workflow.md`：从案例到规则的提炼流程。

使用原则：

- 涉及“审计规则、疑点规则、文本分析规则、案例提炼、规则库建设”时，优先调用规则库。
- 规则必须绑定案例来源或法规依据，不做无来源关键词堆砌。
- 规则按 A底稿级、B疑点级、C提示级分层，避免把线索误当问题。

## 推荐工作流

用户提出任务后：

1. 判断是否涉及历史/偏好/ prior work → 查记忆。
2. 判断是否有专门技能 → 读对应技能。
3. 判断是否需要案例/法规/资料 → 查知识库。
4. 判断是否需要规则化、模型化、工具化 → 查规则库或标准模型。
5. 综合输出，必要时把新结论写回 daily memory 或 MEMORY.md。

## 维护规则

- 新技能：放入 `.openclaw\skills` 后更新 `indexes\skills.json`。
- 新长期经验：写入 `MEMORY.md`。
- 当日流水：写入 `memory\YYYY-MM-DD.md`。
- 新资料：放入 Obsidian Vault，并更新知识库索引。
- 新审计规则：先按 `rule-library/rule-template.md` 建草稿，再经项目试运行后升级状态。
- 不提交 API Key、账号、密码、cookie。

## 当前索引文件

- 技能索引：`indexes/skills.json`
- 记忆索引：`indexes/memory.json`
- 知识库索引：`indexes/knowledge.json`
