# 融策 AI 统一中枢

> 目的：把以往的技能、记忆、知识库统一成一个“可检索、可调用、可维护”的入口，而不是把所有内容粗暴合并成一个巨大文件。

## 目录结构

```text
RONGCE_AI_HUB/
├── README.md                 # 本文件：统一入口
├── indexes/
│   ├── skills.json            # 当前已安装技能索引
│   ├── memory.json            # 长期记忆/日记/记忆库索引
│   └── knowledge.json         # Obsidian 知识库一级目录索引
└── ROUTING.md                 # 调用规则：什么问题用什么来源
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

## 推荐工作流

用户提出任务后：

1. 判断是否涉及历史/偏好/ prior work → 查记忆。
2. 判断是否有专门技能 → 读对应技能。
3. 判断是否需要案例/法规/资料 → 查知识库。
4. 综合输出，必要时把新结论写回 daily memory 或 MEMORY.md。

## 维护规则

- 新技能：放入 `.openclaw\skills` 后更新 `indexes\skills.json`。
- 新长期经验：写入 `MEMORY.md`。
- 当日流水：写入 `memory\YYYY-MM-DD.md`。
- 新资料：放入 Obsidian Vault，并更新知识库索引。
- 不提交 API Key、账号、密码、cookie。

## 当前索引文件

- 技能索引：`indexes/skills.json`
- 记忆索引：`indexes/memory.json`
- 知识库索引：`indexes/knowledge.json`
