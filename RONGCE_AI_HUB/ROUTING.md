# 融策 AI 统一调用规则

## 总原则

把“技能、记忆、知识库”当成一个统一中枢使用，但物理上保持分层：

- Skill = 怎么做
- Memory = 我们之前怎么定的、用户偏好和历史上下文
- Knowledge = 外部/业务资料、案例、法规、方法论

## 路由表

| 用户问题类型 | 优先来源 | 操作 |
|---|---|---|
| 以前做过什么、上次结论、用户偏好、日期、待办 | Memory | 先 memory_search / 读 MEMORY.md 或 daily memory |
| 审计报告复核、串标检测、绩效审计、经责审计、PPT/Word/Excel/绘图/生图 | Skill | 读取最匹配技能的 SKILL.md 后执行 |
| 审计案例、法规依据、政策、方法论、历史文章 | Knowledge | 从 Obsidian Vault 目录定位资料并读取 |
| 复杂业务任务 | 三者合用 | Memory 定上下文，Skill 定流程，Knowledge 补资料 |
| 新形成的重要规则/偏好 | Memory | 写入 daily memory，必要时提炼到 MEMORY.md |
| 新资料、新案例、新文章 | Knowledge | 放入 Obsidian Vault 或记录来源 |
| 新工具、新方法 | Skill | 创建/更新 skill，并登记索引 |

## 使用顺序模板

### 审计类任务

1. 查 Memory：项目背景、用户偏好、历史模板。
2. 查 Skill：审计专项技能，比如 audit-report-review / perf-audit-checklist / procurement-audit-models。
3. 查 Knowledge：Obsidian 里的案例、法规、方法论。
4. 生成结果。
5. 把关键结论写回 memory。

### 文档/报告/PPT 类任务

1. 查 Memory：格式偏好、模板偏好、公司口径。
2. 查 Skill：officecli-docx / officecli-pptx / bid-document / powerpoint-pptx 等。
3. 查 Knowledge：素材、案例、政策依据。
4. 输出文件或修改建议。

### 图片/设计类任务

1. 查 Skill：cbwxy-image-2 / seedream-image-generation / posterdesign / visual-toolkit。
2. 查 Memory：品牌配色、字体、模板。
3. 生成图片或提示词。

## 禁止事项

- 不把真实 API Key 写进索引、memory、git。
- 不把个人记忆泄露到群聊。
- 不把所有知识库全文复制进一个大文件。
- 不在未确认情况下启用企业微信外发类技能。

## 当前关键入口

- 统一中枢：`C:\Users\scrccpa\.openclaw\workspace\RONGCE_AI_HUB`
- 技能库：`C:\Users\scrccpa\.openclaw\skills`
- 长期记忆：`C:\Users\scrccpa\.openclaw\workspace\MEMORY.md`
- 每日记忆：`C:\Users\scrccpa\.openclaw\workspace\memory`
- 知识库：`C:\Users\scrccpa\Documents\Obsidian Vault`
